#!/usr/bin/env python3
"""GitHub HMAC webhook ingress for the existing Revive runner.
Only a loopback HTTP endpoint is exposed. HTTPS transport is provisioned separately.
"""
from __future__ import annotations
import argparse,contextlib,hashlib,hmac,json,os,re,signal,sqlite3,subprocess,sys,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import revive_runner as runner

EVENTS={'issues':{'opened','edited','closed','reopened','labeled','unlabeled'},'issue_comment':{'created','edited','deleted'},'pull_request':{'opened','edited','closed','reopened','synchronize','labeled','unlabeled'},'pull_request_review':{'submitted','edited','dismissed'},'pull_request_review_comment':{'created','edited','deleted'}}

def load_secret(config):
 argv=config['webhook']['secret_command']
 if not isinstance(argv,list) or not argv or not all(isinstance(a,str) for a in argv):raise ValueError('secret_command must be a trusted argv array')
 # Capture secret only in process RAM. No shell, command-line secret or plaintext cache.
 p=subprocess.run(argv,capture_output=True,timeout=30)
 if p.returncode:raise RuntimeError('Webhook secret retrieval failed')
 secret=p.stdout.strip()
 if len(secret)<32 or len(secret)>4096:raise ValueError('Webhook secret length invalid')
 return secret

class EventQueue:
 def __init__(self,path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
  with self.connect() as db:
   db.execute('CREATE TABLE IF NOT EXISTS deliveries (delivery_id TEXT PRIMARY KEY,event TEXT NOT NULL,action TEXT NOT NULL,number INTEGER,sender_id INTEGER,received REAL NOT NULL,state TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,last_attempt REAL,result TEXT)')
  os.chmod(self.path,0o600)
 @contextlib.contextmanager
 def connect(self):
  db=sqlite3.connect(self.path,timeout=10);db.row_factory=sqlite3.Row
  try:
   db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
   with db:yield db
  finally:db.close()
 def persist(self,delivery,event,action,number,sender,accepted):
  with self.connect() as db:
   cursor=db.execute('INSERT OR IGNORE INTO deliveries(delivery_id,event,action,number,sender_id,received,state) VALUES(?,?,?,?,?,?,?)',(delivery,event,action,number,sender,time.time(),'pending' if accepted else 'ignored'))
   return cursor.rowcount==1
 def pending(self):
  with self.connect() as db:return [dict(r) for r in db.execute("SELECT * FROM deliveries WHERE state='pending' ORDER BY CASE WHEN action IN ('closed','unlabeled') THEN 0 ELSE 1 END,received LIMIT 100")]
 def result(self,delivery,complete,result):
  with self.connect() as db:db.execute('UPDATE deliveries SET state=?,attempts=attempts+1,last_attempt=?,result=? WHERE delivery_id=?',('processed' if complete else 'pending',time.time(),result,delivery))
 def count(self,state):
  with self.connect() as db:return db.execute('SELECT count(*) FROM deliveries WHERE state=?',(state,)).fetchone()[0]

class App:
 def __init__(self,config_path,secret=None):
  self.config_path=str(Path(config_path).resolve());self.config=runner.load_config(config_path);self.options=self.config['webhook'];self.secret=secret if secret is not None else load_secret(self.config)
  if self.options.get('host','127.0.0.1') not in {'127.0.0.1','::1'}:raise ValueError('Receiver must bind loopback only')
  if not re.fullmatch(r'/[A-Za-z0-9/_-]+',self.options.get('path','/webhooks/github')):raise ValueError('Invalid fixed webhook path')
  self.queue=EventQueue(Path(self.config['state_dir'])/'webhook-deliveries.sqlite3');self.wake=threading.Event();self.stop=threading.Event()
  self.marker=Path(self.config['state_dir'])/'source-event.marker'
 def accept(self,headers,body):
  signature=headers.get('X-Hub-Signature-256','')
  if not re.fullmatch(r'sha256=[0-9a-fA-F]{64}',signature):return 401,{'error':'invalid-signature'}
  expected='sha256='+hmac.new(self.secret,body,hashlib.sha256).hexdigest()
  if not hmac.compare_digest(expected,signature.lower()):return 401,{'error':'invalid-signature'}
  delivery=headers.get('X-GitHub-Delivery','');event=headers.get('X-GitHub-Event','')
  if not re.fullmatch(r'[A-Za-z0-9-]{8,100}',delivery):return 400,{'error':'invalid-delivery-id'}
  try:payload=json.loads(body)
  except (json.JSONDecodeError,UnicodeDecodeError):return 400,{'error':'invalid-json'}
  if not isinstance(payload,dict):return 400,{'error':'invalid-json-object'}
  repo=payload.get('repository') or {}
  if not isinstance(repo,dict) or not isinstance(repo.get('id'),int) or isinstance(repo.get('id'),bool):return 400,{'error':'invalid-repository'}
  if repo.get('id')!=self.options['repository_id'] or repo.get('full_name','').lower()!=self.config['repository'].lower():return 403,{'error':'wrong-repository'}
  sender_obj=payload.get('sender') or {}
  if not isinstance(sender_obj,dict):return 400,{'error':'invalid-sender'}
  sender=sender_obj.get('id');action=payload.get('action','')
  if sender is not None and (not isinstance(sender,int) or isinstance(sender,bool)):return 400,{'error':'invalid-sender'}
  if not isinstance(action,str):return 400,{'error':'invalid-action'}
  subject=payload.get('issue') or payload.get('pull_request') or {}
  if not isinstance(subject,dict):return 400,{'error':'invalid-subject'}
  number=subject.get('number')
  if number is not None and (not isinstance(number,int) or isinstance(number,bool) or number<=0):return 400,{'error':'invalid-number'}
  trusted={int(u['id']) for u in self.config['trusted_users']}
  own_note='<!-- revive-runner:' in str((payload.get('comment') or {}).get('body',''))
  accepted=event in EVENTS and action in EVENTS[event] and sender in trusted and not own_note and number is not None
  # Persist and commit before acknowledging. Failures propagate to HTTP503 for GitHub redelivery.
  inserted=self.queue.persist(delivery,event,action,number,sender,accepted)
  if accepted:
   runner.atomic(self.marker,{'delivery_id':delivery,'received_ns':time.time_ns()})
   self.wake.set()
  return 202,{'status':'accepted' if accepted else 'ignored','duplicate':not inserted,'delivery_id':delivery}
 def drain_once(self):
  pending=self.queue.pending()
  if not pending:return {'status':'quiet'}
  try:result=runner.poll(self.config_path,execute=True)
  except Exception as exc:
   self.queue.result(pending[0]['delivery_id'],False,'dispatch-error:'+type(exc).__name__)
   return {'status':'dispatch-error'}
  status=result.get('status')
  if status in {'dispatched','busy','orphaned-engine','needs_attention'}:
   self.queue.result(pending[0]['delivery_id'],False,status);return result
  # A quiet poll during repair backoff is not a terminal outcome. Preserve the
  # event so the next due retry runs without waiting for hourly reconciliation.
  state=runner.load_state(self.config).get('issues',{})
  retrying=[(n,r) for n,r in state.items() if r.get('status') in {'failed','queued'}]
  for number,record in retrying:
   try:current=runner.fresh_issue(self.config,int(number))
   except Exception:
    self.queue.result(pending[0]['delivery_id'],False,'retry-source-check-error');return {'status':'retry-source-check-error'}
   if runner.eligible(current,self.config):
    self.queue.result(pending[0]['delivery_id'],False,'repair-backoff');return {'status':'repair-backoff'}
  # Only globally quiet/terminal reconciliation clears this captured batch.
  # Events arriving during the poll are a later durable batch, never erased.
  # No payload body is executed.
  for row in pending:self.queue.result(row['delivery_id'],True,status or 'reconciled')
  return result
 def dispatch_loop(self):
  retry=max(1,float(self.options.get('busy_retry_seconds',5)));reconcile=max(300,float(self.options.get('reconcile_seconds',3600)));next_reconcile=time.monotonic()
  while not self.stop.is_set():
   status='quiet';error=None
   try:
    if self.queue.count('pending'):
     result=self.drain_once();status=result.get('status','unknown');wait=retry
    elif time.monotonic()>=next_reconcile:
     try:
      # Persist the reconciliation wake itself before starting work, so a
      # startup/hourly dispatch also survives failure/backoff without a webhook row.
      self.queue.persist('local-reconcile-'+str(time.time_ns()),'reconcile','sweep',None,None,True)
      result=self.drain_once();status='reconcile-'+result.get('status','unknown')
     except Exception as exc:status='reconcile-error';error=type(exc).__name__
     next_reconcile=time.monotonic()+(retry if error else reconcile);wait=retry
    else:wait=min(60,next_reconcile-time.monotonic())
   except Exception as exc:status='queue-dispatch-error';error=type(exc).__name__;wait=retry
   # Observable private health, never a false healthy success after API failure.
   try:runner.atomic(Path(self.config['state_dir'])/'webhook-dispatch-status.json',{'observed_at':time.time(),'status':status,'error_type':error,'next_reconcile_in':max(0,next_reconcile-time.monotonic())})
   except OSError:pass
   self.wake.wait(max(0.1,wait));self.wake.clear()

def handler_for(app):
 class Handler(BaseHTTPRequestHandler):
  protocol_version='HTTP/1.1'
  def setup(self):super().setup();self.connection.settimeout(10)
  def log_message(self,*args):pass  # Never log signature, payload, secret or request bodies.
  def reply(self,code,value):
   raw=json.dumps(value).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Connection','close');self.end_headers();self.wfile.write(raw)
  def do_GET(self):self.reply(404,{'error':'not-found'})
  def do_POST(self):
   if self.path!=app.options.get('path','/webhooks/github'):self.reply(404,{'error':'not-found'});return
   if self.headers.get('Transfer-Encoding'):self.reply(400,{'error':'chunked-transfer-not-supported'});return
   try:length=int(self.headers.get('Content-Length','-1'))
   except ValueError:self.reply(400,{'error':'invalid-length'});return
   if length<0 or length>int(app.options.get('max_body_bytes',2097152)):self.reply(413,{'error':'payload-too-large'});return
   if self.headers.get_content_type()!='application/json':self.reply(415,{'error':'json-required'});return
   try:
    raw=self.rfile.read(length)
    if len(raw)!=length:self.reply(400,{'error':'incomplete-body'});return
    code,value=app.accept(self.headers,raw);self.reply(code,value)
   except (TimeoutError,OSError):self.reply(408,{'error':'request-timeout'})
   except Exception:self.reply(503,{'error':'durable-queue-unavailable'})
 return Handler

def serve(config_path):
 app=App(config_path);server=ThreadingHTTPServer((app.options.get('host','127.0.0.1'),int(app.options.get('port',18472))),handler_for(app));server.daemon_threads=True
 thread=threading.Thread(target=app.dispatch_loop,name='revive-durable-dispatch',daemon=True);thread.start()
 # Ctrl-C/service SIGTERM exits receiver, not already-owned implementation workers.
 def stop(signum,frame):app.stop.set();app.wake.set();threading.Thread(target=server.shutdown,daemon=True).start()
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 try:server.serve_forever(poll_interval=.5)
 finally:app.stop.set();app.wake.set();server.server_close();thread.join(timeout=15)

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['serve','status','drain']);p.add_argument('--config',required=True);a=p.parse_args()
 if a.action=='serve':serve(a.config)
 else:
  app=App(a.config)
  print(json.dumps(app.drain_once() if a.action=='drain' else {'pending':app.queue.count('pending'),'processed':app.queue.count('processed'),'ignored':app.queue.count('ignored')}))
if __name__=='__main__':main()

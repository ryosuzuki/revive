import hashlib,hmac,http.client,importlib.util,json,os,sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'automation'))
import revive_webhook as w
class WebhookTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.secret=b'test-only-synthetic-key-not-a-credential'*2
  self.config={'repository':'owner/revive','state_dir':str(self.root),'checkout':str(self.root/'checkout'),'worktree_parent':str(self.root),'trusted_users':[{'id':42,'login':'trusted'}],'webhook':{'repository_id':123,'host':'127.0.0.1','port':18472,'path':'/webhooks/github','secret_command':['not-run']}}
  self.path=self.root/'config.json';self.path.write_text(json.dumps(self.config));self.app=w.App(self.path,secret=self.secret)
 def tearDown(self):self.tmp.cleanup()
 def payload(self):return {'action':'opened','repository':{'id':123,'full_name':'owner/revive'},'sender':{'id':42},'issue':{'number':7}}
 def accept(self,payload=None,delivery='synthetic-delivery-123',event='issues',signature=None):
  raw=json.dumps(self.payload() if payload is None else payload).encode();headers={'X-GitHub-Delivery':delivery,'X-GitHub-Event':event,'X-Hub-Signature-256':signature or 'sha256='+hmac.new(self.secret,raw,hashlib.sha256).hexdigest()};return self.app.accept(headers,raw)
 def test_valid_hmac_persists_before_ack(self):
  code,result=self.accept();self.assertEqual(code,202);self.assertEqual(result['status'],'accepted');self.assertEqual(self.app.queue.count('pending'),1);self.assertTrue(self.app.marker.exists())
 def test_wrong_signature_never_persists(self):
  self.assertEqual(self.accept(signature='sha256'+'='+'0'*64)[0],401);self.assertEqual(self.app.queue.count('pending'),0)
 def test_wrong_repository_id_never_persists(self):
  p=self.payload();p['repository']['id']=999;self.assertEqual(self.accept(p)[0],403);self.assertEqual(self.app.queue.count('pending'),0)
 def test_duplicate_delivery_exactly_one_pending(self):
  self.accept();code,r=self.accept();self.assertEqual(code,202);self.assertTrue(r['duplicate']);self.assertEqual(self.app.queue.count('pending'),1)
 def test_untrusted_sender_is_ignored_not_dispatched(self):
  p=self.payload();p['sender']['id']=999;self.assertEqual(self.accept(p)[1]['status'],'ignored');self.assertEqual(self.app.queue.count('pending'),0)
 def test_own_progress_comment_does_not_trigger_feedback_loop(self):
  p=self.payload();p['action']='created';p['comment']={'body':'progress <!-- revive-runner:7-1-progress -->'};self.assertEqual(self.accept(p,event='issue_comment')[1]['status'],'ignored')
 def test_busy_delivery_survives_restart(self):
  self.accept()
  with patch.object(w.runner,'poll',return_value={'status':'busy'}):self.app.drain_once()
  app=w.App(self.path,secret=self.secret);self.assertEqual(app.queue.count('pending'),1)
  with patch.object(w.runner,'poll',return_value={'status':'dispatched','issue':7}):app.drain_once()
  self.assertEqual(app.queue.count('pending'),1)
  with patch.object(w.runner,'poll',return_value={'status':'idle'}):app.drain_once()
  self.assertEqual(app.queue.count('pending'),0);self.assertEqual(app.queue.count('processed'),1)
 def test_two_issue_deliveries_survive_first_dispatch(self):
  self.accept();p=self.payload();p['issue']['number']=8;self.accept(p,delivery='synthetic-delivery-456')
  with patch.object(w.runner,'poll',return_value={'status':'dispatched','issue':7}):self.app.drain_once()
  self.assertEqual(self.app.queue.count('pending'),2)
  with patch.object(w.runner,'poll',return_value={'status':'dispatched','issue':8}):self.app.drain_once()
  self.assertEqual(self.app.queue.count('pending'),2)
  with patch.object(w.runner,'poll',return_value={'status':'idle'}):self.app.drain_once()
  self.assertEqual(self.app.queue.count('processed'),2)
 def test_failed_attempt_backoff_does_not_drop_retry(self):
  self.accept();w.runner.atomic(w.runner.state_path(self.config),{'issues':{'7':{'status':'failed','attempt':1}}})
  issue={'state':'open','labels':[{'name':'revive:ready'}],'user':{'id':42}}
  with patch.object(w.runner,'poll',return_value={'status':'idle'}),patch.object(w.runner,'fresh_issue',return_value=issue):self.assertEqual(self.app.drain_once()['status'],'repair-backoff')
  self.assertEqual(self.app.queue.count('pending'),1)
 def test_startup_reconciles_immediately_without_event(self):
  def waited(_):self.app.stop.set()
  with patch.object(w.runner,'poll',return_value={'status':'idle'}) as poll,patch.object(self.app.wake,'wait',side_effect=waited):self.app.dispatch_loop()
  poll.assert_called_once()
 def test_startup_dispatch_retains_repair_wake(self):
  def waited(_):self.app.stop.set()
  with patch.object(w.runner,'poll',return_value={'status':'dispatched','issue':7}),patch.object(self.app.wake,'wait',side_effect=waited):self.app.dispatch_loop()
  self.assertEqual(self.app.queue.count('pending'),1)
 def test_transient_sqlite_failure_does_not_kill_dispatcher(self):
  calls=[]
  def waited(_):
   calls.append(True)
   if len(calls)==2:self.app.stop.set()
  with patch.object(self.app.queue,'count',side_effect=[OSError('synthetic transient DB failure'),0]),patch.object(w.runner,'poll',return_value={'status':'idle'}) as poll,patch.object(self.app.wake,'wait',side_effect=waited),patch.object(w.runner,'atomic') as health:self.app.dispatch_loop()
  poll.assert_called_once();self.assertEqual(health.call_args_list[0].args[1]['status'],'queue-dispatch-error');self.assertEqual(health.call_args_list[1].args[1]['status'],'reconcile-idle')
 def test_dispatch_failure_retains_durable_pending(self):
  self.accept()
  with patch.object(w.runner,'poll',side_effect=RuntimeError('synthetic transient failure')):self.assertEqual(self.app.drain_once()['status'],'dispatch-error')
  self.assertEqual(self.app.queue.count('pending'),1)
 def test_queue_storage_failure_does_not_ack(self):
  with patch.object(self.app.queue,'persist',side_effect=OSError('disk-full')):
   with self.assertRaises(OSError):self.accept()
 def test_malformed_signed_json_is_rejected(self):
  raw=b'not json';headers={'X-GitHub-Delivery':'delivery-123','X-GitHub-Event':'issues','X-Hub-Signature-256':'sha256='+hmac.new(self.secret,raw,hashlib.sha256).hexdigest()};self.assertEqual(self.app.accept(headers,raw)[0],400)
 def test_signed_bad_repository_type_is_rejected(self):
  p=self.payload();p['repository']=[];self.assertEqual(self.accept(p)[0],400)
 def test_public_bind_rejected(self):
  self.config['webhook']['host']='0.0.0.0';self.path.write_text(json.dumps(self.config))
  with self.assertRaises(ValueError):w.App(self.path,secret=self.secret)
 def test_secret_command_captures_only_ram(self):
  with patch.object(w.subprocess,'run') as p:
   p.return_value.returncode=0;p.return_value.stdout=self.secret+b'\n';self.assertEqual(w.load_secret(self.config),self.secret);self.assertEqual(p.call_args.kwargs['capture_output'],True);self.assertNotIn('shell',p.call_args.kwargs)
 def test_receiver_scope_and_body_limit_actual_http(self):
  server=w.ThreadingHTTPServer(('127.0.0.1',0),w.handler_for(self.app));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5);c.request('GET','/');self.assertEqual(c.getresponse().status,404);c.close()
   c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5);c.request('POST','/webhooks/github',headers={'Content-Length':'999999999','Content-Type':'application/json'});self.assertEqual(c.getresponse().status,413);c.close()
  finally:server.shutdown();server.server_close();thread.join(timeout=5)
if __name__=='__main__':unittest.main()

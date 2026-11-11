import importlib.util,json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parents[1]/'automation/revive_runner.py'
spec=importlib.util.spec_from_file_location('lifecycle_runner',p);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class LifecycleTests(unittest.TestCase):
 def config(self,d):return {'repository':'owner/revive','trusted_users':[{'id':42,'login':'trusted'}],'state_dir':str(d),'checkout':str(d/'checkout'),'worktree_parent':str(d),'retry_delay_seconds':0,'max_attempts':3}
 def issue(self):return {'number':1,'title':'Test','body':'### Paper slug\n\ntest-paper\n','state':'open','labels':[{'name':'revive:ready'}],'user':{'id':42,'login':'trusted'}}
 def test_pagination_reaches_second_page(self):
  with patch.object(r,'api',side_effect=[[{'id':i} for i in range(100)],[{'id':100}]]) as a:
   self.assertEqual(len(r.api_pages('repos/x/y/issues?state=open')),101);self.assertIn('page=2',a.call_args[0][0])
 def test_latest_trusted_stop_directive_fences_and_resume_restores(self):
  i=self.issue();i['trusted_comments']=[{'body':'/revive stop'}];self.assertFalse(r.eligible(i,self.config(Path('/x'))))
  i['trusted_comments'].append({'body':'/revive resume'});self.assertTrue(r.eligible(i,self.config(Path('/x'))))
 def test_revision_change_is_fenced(self):
  i=self.issue();old=r.fingerprint(i);i['body']+='\nStop old direction'
  with patch.object(r,'fresh_issue',return_value=i):
   with self.assertRaises(r.RequestChanged):r.fence(self.config(Path('/x')),1,old)
 def test_cancellation_is_fenced(self):
  i=self.issue();i['state']='closed'
  with patch.object(r,'fresh_issue',return_value=i):
   with self.assertRaises(r.RequestCancelled):r.fence(self.config(Path('/x')),1,'old')
 def test_orphan_engine_prevents_new_worker(self):
  with tempfile.TemporaryDirectory() as x:
   d=Path(x);cfg=d/'c.json';c=self.config(d);cfg.write_text(json.dumps(c));r.atomic(r.state_path(c),{'issues':{'1':{'status':'failed','engine_pid':321,'engine_birth':'birth'}}})
   with patch.object(r,'identity_alive',return_value=True),patch.object(r.subprocess,'Popen') as launch:
    self.assertEqual(r.poll(cfg,True)['status'],'orphaned-engine');launch.assert_not_called()
 def test_pid_reuse_not_signalable_identity(self):
  with patch.object(r,'alive',return_value=True),patch.object(r,'process_birth',return_value='new'):
   self.assertFalse(r.identity_alive(123,'old'))
 def test_actual_owned_process_cleanup(self):
  proc=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True)
  birth=r.process_birth(proc.pid)
  try:r.stop_engine(proc,birth);self.assertIsNotNone(proc.poll())
  finally:
   if proc.poll() is None:proc.kill();proc.wait()
 def test_api_failure_after_launch_reaps_actual_engine(self):
  with tempfile.TemporaryDirectory() as x:
   d=Path(x);c=self.config(d);cfg=d/'c.json';cfg.write_text(json.dumps(c));i=self.issue();w=d/'worktree';(w/'papers/test-paper').mkdir(parents=True)
   r.atomic(r.state_path(c),{'issues':{'1':{'status':'running','attempt':1,'started':time.time(),'fingerprint':r.fingerprint(i)}}})
   proc=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True);birth=r.process_birth(proc.pid)
   oldterm=r.signal.getsignal(r.signal.SIGTERM);oldint=r.signal.getsignal(r.signal.SIGINT)
   try:
    with patch.object(r,'fresh_issue',return_value=i),patch.object(r,'prepare_worktree',return_value=(w,'revive/issue-1-attempt-1')),patch.object(r,'note'),patch.object(r,'fence',side_effect=RuntimeError('API unreachable')),patch.object(r,'process_birth',return_value=birth),patch.object(r.subprocess,'Popen',return_value=proc):r.worker(cfg,1,1)
    self.assertIsNotNone(proc.poll());state=r.load_state(c)['issues']['1'];self.assertEqual(state['status'],'failed');self.assertIsNone(state['engine_pid'])
   finally:
    r.signal.signal(r.signal.SIGTERM,oldterm);r.signal.signal(r.signal.SIGINT,oldint)
    if proc.poll() is None:proc.kill();proc.wait()
 def test_closed_or_wrong_head_pr_never_reconciles(self):
  c=self.config(Path('/x'));record={'branch':'revive/issue-1-attempt-1','verification_receipt':{'passed':True,'head':'aaa'}}
  base={'url':'https://github.com/owner/revive/pull/2','state':'OPEN','headRefOid':'aaa','headRefName':record['branch'],'baseRefName':'main','headRepositoryOwner':{'login':'owner'},'headRepository':{'name':'revive'},'isCrossRepository':False}
  for override in [{'state':'CLOSED'},{'headRefOid':'bbb'},{'baseRefName':'other'},{'headRepositoryOwner':{'login':'attacker'}},{'isCrossRepository':True}]:
   with patch.object(r,'gh',return_value=json.dumps([{**base,**override}])):self.assertIsNone(r.verified_pr(c,record))
  with patch.object(r,'gh',return_value=json.dumps([base])):self.assertEqual(r.verified_pr(c,record)['headRefOid'],'aaa')
  self.assertIsNone(r.verified_pr(c,{'branch':record['branch']}))
 def test_unapproved_room_image_rejected(self):
  with tempfile.TemporaryDirectory() as x:
   p=Path(x)/'room.png';p.write_bytes(b'\x89PNG\r\n\x1a\nprivate pixels')
   with self.assertRaises(ValueError):r.audit_public([p])
   digest=r.hashlib.sha256(p.read_bytes()).hexdigest();manifest={'assets':[{'path':'room.png','sha256':digest,'origin':'synthetic','source':'generated fixture','license':'CC0'}]}
   with self.assertRaises(ValueError):r.audit_public([p],manifest)
   r.audit_public([p],manifest,[digest])
 def test_typed_apk_video_cannot_pass_with_unit_tests_only(self):
  with tempfile.TemporaryDirectory() as x:
   c=self.config(Path(x));i=self.issue();i['body']+='\n### Required acceptance\n\nsource, software-tests, apk, video\n'
   self.assertEqual(r.required_acceptance(i),['apk','software-tests','source','video'])
   with self.assertRaises(r.AcceptanceBlocked):r.acceptance(c,1,i,{'tests':[{'result':'passed'}]})
 def test_physical_device_needs_operator_receipt(self):
  with tempfile.TemporaryDirectory() as x:
   c=self.config(Path(x));i=self.issue();i['body']+='\n### Required acceptance\n\nphysical-device\n'
   with self.assertRaises(r.AcceptanceBlocked):r.acceptance(c,1,i,{'acceptance':{'physical-device':{'status':'passed','evidence':'agent says so'}}})
 def test_zero_tests_is_not_success(self):
  with tempfile.TemporaryDirectory() as x:
   d=Path(x);(d/'tests').mkdir()
   with self.assertRaises(RuntimeError):r.independently_test(d)
 def test_exhausted_retries_visible_attention(self):
  with tempfile.TemporaryDirectory() as x:
   d=Path(x);cfg=d/'c.json';c=self.config(d);cfg.write_text(json.dumps(c));i=self.issue();record={'status':'failed','fingerprint':r.fingerprint(i),'revision_attempt':3,'attempt':3}
   r.atomic(r.state_path(c),{'issues':{'1':record}})
   with patch.object(r,'api_pages',return_value=[i]),patch.object(r,'fresh_issue',return_value=i),patch.object(r,'note') as note:
    self.assertEqual(r.poll(cfg,True)['status'],'needs_attention');note.assert_called_once()
   self.assertEqual(r.load_state(c)['issues']['1']['status'],'needs_attention')
 def test_checkpoint_branch_reused_not_recreated(self):
  with tempfile.TemporaryDirectory() as x:
   d=Path(x);c=self.config(d);w=d/'old';w.mkdir();record={'worktree':str(w),'branch':'revive/issue-1-attempt-1'}
   with patch.object(r,'run',side_effect=['','git@github.com:owner/revive.git','revive/issue-1-attempt-1\n']) as calls:
    path,branch=r.prepare_worktree(c,1,2,'test-paper',record);self.assertEqual(path,w);self.assertEqual(branch,record['branch']);self.assertFalse(any('worktree' in a.args[0] for a in calls.call_args_list))
if __name__=='__main__':unittest.main()

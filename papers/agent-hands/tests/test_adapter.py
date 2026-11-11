import unittest,tempfile,wave
from pathlib import Path
from agent_hands.markup import parse
from agent_hands.adapter import unity_plan,refine_audio
class AdapterTests(unittest.TestCase):
 def registry(self):return {'bottle':{'id':'bottle','label':'Bottle','position':[.2,.8,1.2],'size':[.08,.25,.08],'axes':[[1,0,0],[0,1,0],[0,0,1]],'parts':{'cap':'T:center:center'}}}
 def test_regions_and_paper_ids_reach_shared_plan(self):
  registry=self.registry();p=parse('[RegionOfObject; object:bottle, region:cap]cap [Numeric; gesture:two]two.',registry);p['question']='Where is the cap?'
  result=unity_plan(p,registry,3)
  self.assertEqual(result['events'][0]['paperEvent'],'RegionOfObject');self.assertAlmostEqual(result['objects'][-1]['position'][1],.925);self.assertEqual(result['events'][1]['pose'],'two');self.assertFalse(result['gaze'])
 def test_paper_spatiality_syntax(self):
  p=parse('[RegionOfObject; gesture:point, spatiality:bottle_T_middle_center]cap',self.registry());self.assertEqual(p['events'][0]['attributes']['region'],'T:center:center')
 def test_atomic_both_interrupt(self):
  registry=self.registry();p=parse('[PointObject; object:bottle]this [Comparison; object:bottle, handedness:double]compare.',registry);result=unity_plan(p,registry,3)
  a,b=result['events'];self.assertEqual(b['hand'],'both');self.assertLessEqual(a['start']+a['duration'],b['start']+.001)
 def test_rms_bounds(self):
  registry=self.registry();p=unity_plan(parse('[PointObject; object:bottle]bottle.',registry),registry,1)
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'silent.wav'
   with wave.open(str(f),'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\0\0'*24000)
   result=refine_audio(p,f);self.assertGreaterEqual(result['events'][0]['start'],0);self.assertIn('not forced alignment',result['alignment'])
if __name__=='__main__':unittest.main()

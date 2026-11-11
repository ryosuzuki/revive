import unittest,numpy as np
from agent_hands.registration import register_box,resolve_region,ray_triangle
from agent_hands.markup import parse,schedule

class SpatialTests(unittest.TestCase):
 def test_front_plane_to_center_and_region(self):
  obj=register_box('x','box',[0,0,2],{'position':[0,0,0],'rotation':[0,0,0,1]}, {'width':100,'height':100,'fx':50,'fy':50,'cx':50,'cy':50},[25,25,75,75],[1,1,1])
  np.testing.assert_allclose(obj['position'],[0,0,2.5]);np.testing.assert_allclose(resolve_region(obj),[0,0,2])
  with self.assertRaises(ValueError):resolve_region(obj,'made-up')
 def test_rotation_and_offcenter_principal_point(self):
  # Camera looks +X; surface is two metres in front.
  q=[0,np.sqrt(.5),0,np.sqrt(.5)]
  obj=register_box('x','box',[2,0,0],{'position':[0,0,0],'rotation':q},{'width':100,'height':100,'fx':50,'fy':50,'cx':40,'cy':60},[30,50,50,70],[1,1,.2])
  np.testing.assert_allclose(obj['position'],[2.1,0,0],atol=1e-8)
 def test_ray_rejects_behind_and_parallel(self):
  self.assertIsNone(ray_triangle([0,0,0],[0,0,-1],[-1,-1,2],[1,-1,2],[0,1,2]))
  np.testing.assert_allclose(ray_triangle([0,0,0],[0,0,1],[-1,-1,2],[1,-1,2],[0,1,2]),[0,0,2])
 def test_repeated_words_and_defaults(self):
  p=parse('Here and [PointObject; object:x]here.',{'x':{}})
  self.assertEqual(p['events'][0]['wordIndex'],2)
  self.assertEqual(p['events'][0]['attributes']['gesture'],'palm')
  timed=schedule(p,3);self.assertGreater(timed['events'][0]['start'],0)
  self.assertLessEqual(timed['events'][0]['start']+timed['events'][0]['duration'],3)
 def test_unknown_references_rejected(self):
  for t in ('[PointObject; object:unseen]here','[Unknown]here','[Positive; gesture:arbitrary]yes','[Positive]'):
   with self.assertRaises(ValueError):parse(t,{'x':{}})
 def test_adjacent_and_no_events(self):
  self.assertEqual(len(parse('[Positive][Attention]Good.',{})['events']),2)
  self.assertEqual(parse('Nothing special.',{})['events'],[])

if __name__=='__main__':unittest.main()

class SchedulerTests(unittest.TestCase):
 def test_double_interrupt_and_seek(self):
  from agent_hands.scheduler import Scheduler
  s=Scheduler([{'id':'Attention','start':0,'duration':2,'attributes':{}},{'id':'Comparison','start':1,'duration':3,'attributes':{}}])
  states=s.advance(1.5)
  self.assertEqual(states['left']['order'],1);self.assertEqual(states['right']['order'],1)
  self.assertIsNone(s.advance(5)['right']);self.assertIsNotNone(s.advance(.5)['left'])
 def test_contact_and_timeout(self):
  from agent_hands.scheduler import Scheduler
  s=Scheduler([{'id':'Celebration','start':0,'duration':1,'attributes':{}}])
  self.assertTrue(s.advance(2)['left']['interactive']);self.assertIsNone(s.advance(3,contacts=['left'])['left'])
  self.assertIsNone(s.advance(9)['left'])

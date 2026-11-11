import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agent_hands.capture import project
from agent_hands.events import validate_plan,active_events,hand_pose
from agent_hands.grounding import ray_mesh
class CoreTests(unittest.TestCase):
 def object(self):return {'id':'mug','label':'Mug','position':[1,1,2],'size':[.2,.2,.2]}
 def plan(self):return {'objects':[self.object()],'events':[{'start':1,'duration':2,'gesture':'point','targetId':'mug'}]}
 def test_projection_offcenter(self):
  k={'fx':800,'fy':700,'cx':600,'cy':650};cam={'rotation':[0,0,0,1],'position':[0,0,0]}
  self.assertEqual(project([.5,.2,2],cam,k),[800,580,2])
  self.assertIsNone(project([0,0,-1],cam,k))
 def test_registry_no_fabricated_target(self):
  p=self.plan();p['events'][0]['targetId']='imaginary'
  with self.assertRaises(ValueError):validate_plan(p)
 def test_gaze_rejected(self):
  p=self.plan();p['gaze']=True
  with self.assertRaises(ValueError):validate_plan(p)
 def test_seek_is_stateless(self):
  p=validate_plan(self.plan());self.assertEqual(active_events(p,0),[]);a=active_events(p,1.5);active_events(p,9);self.assertEqual(active_events(p,1.5),a)
 def test_no_same_hand_overlap(self):
  p=self.plan();p['events']*=2
  with self.assertRaises(ValueError):validate_plan(p)
 def test_world_anchoring_changes_with_object(self):
  p=validate_plan(self.plan());e=p['events'][0];o=p['objects'][0];a=hand_pose(e,o,2);o['position'][0]+=3;b=hand_pose(e,o,2);self.assertAlmostEqual(b[0]-a[0],3)
 def test_mesh_convention(self):
  # Three-RH z=-2 is Unity-LH z=+2.
  room={'parts':[{'label':'wall','vertices':[-2,-2,-2,2,-2,-2,0,2,-2],'triangles':[0,1,2]}]}
  hit=ray_mesh([0,0,0],[0,0,1],room);self.assertAlmostEqual(hit[0],2)
if __name__=='__main__':unittest.main()

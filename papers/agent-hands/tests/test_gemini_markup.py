import unittest
from agent_hands.markup import parse
class ProviderMarkupRegression(unittest.TestCase):
 def setUp(self):
  self.registry={'box':{'label':'Box','position':[0,1,.8],'size':[.2,.2,.2],'axes':[[1,0,0],[0,1,0],[0,0,1]]}}
 def test_real_candidate_invalid_whole_region_is_rejected_before_tts(self):
  with self.assertRaisesRegex(ValueError,'Unknown semantic region'):
   parse('[PointObject; object:box, region:whole]this box.',self.registry)
 def test_canonical_region_and_whole_object_are_distinct(self):
  tagged='[RegionOfObject; object:box, region:F:top:center]Top. [PointObject; object:box]Box.'
  result=parse(tagged,self.registry)
  self.assertEqual(result['speech'],'Top. Box.')
  self.assertEqual(result['events'][0]['attributes']['region'],'F:top:center')
  self.assertNotIn('region',result['events'][1]['attributes'])
 def test_region_without_object_rejected(self):
  with self.assertRaisesRegex(ValueError,'requires registered object'):
   parse('[Positive; region:F:center:center]Great.',self.registry)

 def test_debug_word_cursor_and_event_share_audio_timeline(self):
  from agent_hands.markup import schedule
  from agent_hands.adapter import unity_plan,refine_audio
  import tempfile,wave
  from pathlib import Path
  import numpy as np
  raw=parse('A much [PointObject; object:box]larger box.',self.registry)
  raw['tagged']='A much [PointObject; object:box]larger box.'
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'speech.wav'
   samples=(np.sin(np.arange(48000)*.05)*1000).astype('<i2')
   with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(samples.tobytes())
   plan=refine_audio(unity_plan(raw,self.registry,2),path)
  self.assertEqual(len(plan['wordStarts']),4)
  self.assertTrue(all(0<=t<=2 for t in plan['wordStarts']))
  self.assertEqual(plan['events'][0]['start'],plan['wordStarts'][plan['events'][0]['wordIndex']])

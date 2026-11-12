"""Configuration/protocol regressions. Mocked inputs are not inference evidence."""
import os,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch,Mock
from agent_hands.backend import configured_backend
from agent_hands.gemini import GeminiBackend,RESPONSE_MODEL,TTS_MODEL

class ProviderConfiguration(unittest.TestCase):
 def test_paper_models_remain_explicit_defaults(self):
  with patch.dict(os.environ,{'AGENT_HANDS_PROVIDER':'gemini','AGENT_HANDS_API_KEY':'synthetic-test-value'},clear=True):
   backend=configured_backend()
  self.assertEqual(backend.model,RESPONSE_MODEL)
  self.assertEqual(backend.tts_model,TTS_MODEL)
 def test_unapproved_replacement_cannot_fallback_silently(self):
  with patch.dict(os.environ,{'AGENT_HANDS_PROVIDER':'gemini','AGENT_HANDS_RESPONSE_MODEL':'gemini-2.5-flash','AGENT_HANDS_API_KEY':'synthetic-test-value'},clear=True):
   with self.assertRaisesRegex(ValueError,'explicit approval'):configured_backend()
 def test_approved_model_reads_only_explicit_key_path(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'operator-key.txt';path.write_text('synthetic-test-value\n')
   env={'AGENT_HANDS_PROVIDER':'gemini','AGENT_HANDS_RESPONSE_MODEL':'gemini-2.5-flash','AGENT_HANDS_APPROVED_REPLACEMENT':'true','AGENT_HANDS_API_KEY_FILE':str(path)}
   with patch.dict(os.environ,env,clear=True):backend=configured_backend()
  self.assertEqual(backend.model,'gemini-2.5-flash')
 def test_unknown_provider_rejected_including_standalone_tts(self):
  from agent_hands.dialogue import speak
  with patch.dict(os.environ,{'AGENT_HANDS_PROVIDER':'unrecognized'},clear=True):
   with self.assertRaises(ValueError):configured_backend()
   with self.assertRaises(ValueError):speak('test','unused.wav')
 def test_unavailable_provider_model_does_not_retry_another_model(self):
  backend=GeminiBackend('synthetic-test-value');reply=Mock(status_code=404)
  with patch('agent_hands.gemini.requests.post',return_value=reply) as post:
   with self.assertRaisesRegex(RuntimeError,'HTTP404; no fallback'):backend.generate('Harmless protocol test')
  self.assertEqual(post.call_count,1)
  self.assertFalse(post.call_args.kwargs['allow_redirects'])
  self.assertTrue(post.call_args.args[0].startswith('https://generativelanguage.googleapis.com/'))

class ReturnedAudioMatchesAlignment(unittest.TestCase):
 def test_handler_returns_the_same_clip_used_for_timeline_not_second_tts(self):
  with tempfile.TemporaryDirectory() as d:
   with patch.dict(os.environ,{'AGENT_HANDS_RUNTIME':d,'AGENT_HANDS_PROVIDER':'local'}):
    from agent_hands import server
   backend=Mock()
   backend.respond.return_value={'speech':'This is your mug.','words':['This','is','your','mug.'],'events':[{'id':'PointObject','wordIndex':0,'trigger':'This','attributes':{'object':'mug'}}],'tagged':'[PointObject; object:mug]This is your mug.','provenance':{'kind':'mocked software regression'}}
   def synth(text,destination):
    path=Path(destination)
    with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\0\0'*30000)
    return path
   with patch.object(server,'ROOT',Path(d)),patch('agent_hands.backend.configured_backend',return_value=backend),patch('agent_hands.dialogue.speak',side_effect=synth) as tts:
    result=server.dialogue(server.Request(question='Where is my mug?',objects=[{'id':'mug','label':'Mug','position':[0,1,.8],'size':[.1,.1,.1]}]))
    self.assertEqual(tts.call_count,1)
    path=Path(d)/result['audioUrl'].split('/')[-1]
    self.assertTrue(path.is_file())
    self.assertEqual(result['responseDuration'],1.25)
    self.assertEqual(Path(server.audio(path.name).path),path)

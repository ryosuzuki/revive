"""Repair ASR using actual visual evidence, retaining both original and interpreted questions."""
import json,sys,wave,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agent_hands.backend import configured_backend
from agent_hands.dialogue import speak
from agent_hands.adapter import unity_plan,refine_audio

for p in sorted(Path(sys.argv[1]).iterdir()):
 if not (p/'registry.json').exists():continue
 s=json.loads((p/'session.json').read_text());frame=s['frames'][len(s['frames'])//2]
 registry=json.loads((p/'registry.json').read_text())['objects'];image=(p/frame['image']).read_bytes()
 original=' '.join(x['text'].strip()for x in json.loads((p/'transcript.json').read_text())['segments'])
 b=configured_backend();repair=b.generate('The following is imperfect speech recognition. Correct ONLY likely phonetic transcription errors using the visible image and object names; preserve the user intent and sentence. Do NOT answer the question. Return JSON with question and reason. If already sensible leave it unchanged. Visible objects: '+json.dumps([o['label']for o in registry.values()])+'\nTranscription: '+original,image)
 raw=re.sub(r'^```(?:json)?\s*|\s*```$','',repair['text'].strip());interpretation=json.loads(raw)
 (p/'question-interpretation.json').write_text(json.dumps({'original':original,'interpretation':interpretation,'provenance':repair},indent=2))
 result=b.respond(interpretation['question'],registry,image);result['question']=original
 (p/'model-response.json').write_text(json.dumps(result,indent=2));speak(result['speech'],p/'response.wav')
 with wave.open(str(p/'response.wav'))as w:duration=w.getnframes()/w.getframerate()
 plan=refine_audio(unity_plan(result,registry,duration,frame['position']),p/'response.wav');plan['interpretedQuestion']=interpretation['question']
 (p/'plan.json').write_text(json.dumps(plan,indent=2));print(p.name,interpretation,result['speech'],flush=True)

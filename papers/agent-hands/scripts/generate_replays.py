#!/usr/bin/env python3
"""Run fresh perception/dialogue per recording; zero trial IDs, coordinates or canned answers."""
import sys,json,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from agent_hands.backend import Backend
from agent_hands.capture import quaternion_matrix,project
from agent_hands.registration import mesh_hit,register_box
from agent_hands.dialogue import speak
from agent_hands.adapter import unity_plan,refine_audio

def generate(session_path):
 p=Path(session_path);s=json.loads((p/'session.json').read_text());transcript=json.loads((p/'transcript.json').read_text());q=' '.join(x['text'].strip()for x in transcript['segments'])
 # A uniformly selected middle sensor frame is visual context, not a gaze estimate.
 frame=s['frames'][len(s['frames'])//2];im=(p/frame['image']).read_bytes();backend=Backend();result=backend.detect(im,q);(p/'perception.json').write_text(json.dumps(result,indent=2))
 registry={};rejected=[];k=s['intrinsics'];room=json.loads((p/'room-geometry.json').read_text());rot=quaternion_matrix(frame['rotation'])
 for o in result['objects']:
  try:
   b=o['bbox'];x=(b[0]+b[2])/2;y=(b[1]+b[3])/2;direction=rot@np.array([(x-k['cx'])/k['fx'],-(y-k['cy'])/k['fy'],1])
   hit=mesh_hit(frame['position'],direction,room)
   obj=register_box(o['id'],o['label'],hit,frame,k,b,o['size'],o.get('parts'));obj['confidence']=o.get('confidence',.5);obj['provenance']['registration']='offline-VLM candidate center ray + measured mesh; no user confirmation';registry[obj['id']]=obj
  except (ValueError,KeyError) as e:rejected.append({'object':o,'reason':str(e)})
 (p/'registry.json').write_text(json.dumps({'objects':registry,'rejected':rejected,'sourceFrame':frame['source'],'selection':'offline VLM candidates; not gaze or confirmed live selection'},indent=2))
 if not registry:raise ValueError('No grounded objects; inspect perception before retry')
 result=backend.respond(q,registry,im);result['question']=q;(p/'model-response.json').write_text(json.dumps(result,indent=2))
 speak(result['speech'],p/'response.wav')
 with wave.open(str(p/'response.wav')) as w:duration=w.getnframes()/w.getframerate()
 plan=refine_audio(unity_plan(result,registry,duration,frame['position']),p/'response.wav');(p/'plan.json').write_text(json.dumps(plan,indent=2));print(s['id'],q,plan['response'],flush=True)
if __name__=='__main__':
 root=Path(sys.argv[1])
 for p in sorted(root.iterdir()):
  if (p/'session.json').is_file() and not (p/'plan.json').exists():generate(p)

#!/usr/bin/env python3
"""Render actual Unity 3D overlays, then package speech/captions on real captured RGB."""
import argparse,json,math,shlex,subprocess,sys,wave,copy,textwrap
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image,ImageDraw,ImageFont
from agent_hands.capture import quaternion_matrix
import numpy as np

def prepare(p):
 s=json.loads((p/'session.json').read_text());plan=json.loads((p/'plan.json').read_text())
 with wave.open(str(p/'response.wav')) as w:duration=w.getnframes()/w.getframerate()
 frames=copy.deepcopy(s['frames']);step=float(np.median(np.diff([x['time']for x in frames])))
 while frames[-1]['time']<duration:
  f=copy.deepcopy(frames[-1]);f['sourceTime']=s['frames'][-1]['time'];f['time']+=step;f['heldView']=True;frames.append(f)
 frames=[f for f in frames if f['time']<=max(duration,step)];s['frames']=frames;s['duration']=duration
 hands=[json.loads(line)for line in(p/'hands.jsonl').open()]
 for f in frames:
  sample=min(hands,key=lambda h:abs(h['unixMs']-f['unixMs']));rot=quaternion_matrix([sample['trackingRotation'][x]for x in 'xyzw']);offset=np.array([sample['trackingPosition'][x]for x in 'xyz'])
  for side in ['left','right']:
   h=sample[side]
   if h.get('valid')and h.get('tracked'):
    raw=h['rootPosition'];local=np.array([raw['x'],raw['y'],-raw['z']]);f[side+'UserHand']=(rot@local+offset).tolist()
   else:f[side+'UserHand']=[]
 s['contactProvenance']='Raw OVR root RH->Unity z reflection then recorded tracking transform. Timing nearest-neighbour; physical alignment not independently measured.'
 derived=p/'render';derived.mkdir(exist_ok=True);(derived/'session.json').write_text(json.dumps(s))
 import shutil
 for name in ['room-geometry.json','plan.json']:shutil.copyfile(p/name,derived/name)
 return s,derived

def shell(args,**kw):subprocess.run(args,check=True,**kw)

def composite(p,s,render):
 out=p/'composite';out.mkdir(exist_ok=True)
 fontPath='/System/Library/Fonts/Supplemental/Arial.ttf';font=ImageFont.truetype(fontPath,27);small=ImageFont.truetype(fontPath,22)
 plan=json.loads((p/'plan.json').read_text());response=plan['response']
 for i,f in enumerate(s['frames']):
  bg=Image.open(p/f['image']).convert('RGBA');overlay=Image.open(render/f'{i:05d}.png').convert('RGBA');bg=Image.alpha_composite(bg,overlay);d=ImageDraw.Draw(bg)
  heading='AgentHands | Generated response on recorded context | No gaze'
  d.rounded_rectangle((18,18,1262,100),radius=12,fill=(10,18,25,215));d.text((36,29),heading,font=font,fill='white');d.text((36,65),s['id']+' | '+('Held recorded viewpoint'if f.get('heldView')else'Calibrated recorded camera'),font=small,fill=(170,230,235))
  active=[e for e in plan['events']if e['start']<=f['time']<e['start']+e['duration']]
  # Segment by proportional speech time; source text is never rewritten.
  words=response.split();duration=max(.1,s['duration']);ix=min(len(words)-1,int(f['time']/duration*len(words)));first=(ix//13)*13;caption=' '.join(words[first:first+13])
  lines=textwrap.wrap(caption,width=63);h=len(lines)*35+35;d.rounded_rectangle((30,1280-h-25,1250,1255),radius=12,fill=(8,14,24,220))
  for j,line in enumerate(lines):d.text((50,1280-h-7+j*35),line,font=font,fill='white')
  question=plan.get('interpretedQuestion',plan.get('transcript',''));questionLines=textwrap.wrap('Question (visually contextualized ASR): '+question,width=80)
  for j,line in enumerate(questionLines):d.text((36,108+j*28),line,font=small,fill='white',stroke_width=2,stroke_fill=(10,20,30))
  if active:d.text((36,180),' / '.join(e.get('paperEvent',e['gesture'])for e in active),font=small,fill=(130,255,235),stroke_width=2,stroke_fill=(10,20,30))
  bg.convert('RGB').save(out/f'{i:05d}.jpg',quality=94)
 lines=[]
 for i,f in enumerate(s['frames']):
  delta=s['frames'][i+1]['time']-f['time']if i+1<len(s['frames'])else.111111
  lines.extend([f"file 'composite/{i:05d}.jpg'",f'duration {delta}'])
 lines.append(f"file 'composite/{len(s['frames'])-1:05d}.jpg'");(p/'response.ffconcat').write_text('\n'.join(lines)+'\n')
 video=p/(s['id']+'-agent-hands-response.mp4')
 shell(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(p/'response.ffconcat'),'-i',str(p/'response.wav'),'-fps_mode','vfr','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(video)])
 shell(['ffmpeg','-v','error','-i',str(video),'-f','null','-'])
 return video

def main():
 a=argparse.ArgumentParser();a.add_argument('sessions');a.add_argument('--host',required=True,help='Your verified Unity build host SSH alias');args=a.parse_args()
 for p in sorted(Path(args.sessions).iterdir()):
  if not (p/'plan.json').exists():continue
  s,derived=prepare(p);remote='/tmp/openclaw/agent-hands-render/'+s['id'];
  shell(['ssh',args.host,'mkdir -p '+shlex.quote(remote)])
  shell(['rsync','-a',str(derived)+'/',args.host+':'+remote+'/'])
  command='AGENT_HANDS_SESSION='+shlex.quote(remote)+' AGENT_HANDS_PLAN='+shlex.quote(remote+'/plan.json')+' AGENT_HANDS_RENDER='+shlex.quote(remote+'/overlays')+' /Applications/Unity/Hub/Editor/6000.4.5f1/Unity.app/Contents/MacOS/Unity -batchmode -quit -projectPath /tmp/openclaw/agent-hands-build -buildTarget StandaloneOSX -executeMethod RenderReplay.Run -logFile '+shlex.quote(remote+'/unity-render.log')
  shell(['ssh',args.host,command]);shell(['rsync','-a',args.host+':'+remote+'/',str(derived)+'/'])
  video=composite(p,s,derived/'overlays');print(video,flush=True)
if __name__=='__main__':main()

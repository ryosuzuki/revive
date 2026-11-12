#!/usr/bin/env python3
"""Render actual Unity 3D overlays, then package speech/captions on real captured RGB."""
import argparse,json,math,shlex,subprocess,sys,wave,copy,textwrap
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image,ImageDraw,ImageFont
from agent_hands.capture import quaternion_matrix
import numpy as np

def prepare(p,full_timeline=False):
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
 if full_timeline:
  question=copy.deepcopy(json.loads((p/'session.json').read_text())['frames']);qend=question[-1]['time']+step
  for f in question:f['phase']='recorded question'
  wait=[];t=qend
  while t<qend+1.5:
   f=copy.deepcopy(question[-1]);f.update(time=t,phase='thinking',heldView=True);wait.append(f);t+=step
  response_start=qend+1.5
  for f in frames:f['time']+=response_start;f['phase']='response'
  tail=[];t=frames[-1]['time']+step
  while t<response_start+duration+3:
   f=copy.deepcopy(frames[-1]);f.update(time=t,phase='idle after response',heldView=True);tail.append(f);t+=step
  s['frames']=question+wait+frames+tail;s['duration']=response_start+duration+3;s['responseStart']=response_start;s['responseDuration']=duration
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(p/'audio.wav'),'-i',str(p/'response.wav'),'-filter_complex',f"[0:a]adelay={int(s.get('audioOffset',0)*1000)}:all=1,apad,atrim=duration={response_start},asetpts=PTS-STARTPTS[a0];[1:a]apad,atrim=duration={duration+3},asetpts=PTS-STARTPTS[a1];[a0][a1]concat=n=2:v=0:a=1[a]",'-map','[a]','-ar','24000','-ac','1',str(p/'timeline.wav')],check=True)
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
  response_time=f['time']-s.get('responseStart',0)
  phase=f.get('phase','response')
  heading='AgentHands | '+phase+' | No gaze'
  d.rounded_rectangle((18,18,1262,100),radius=12,fill=(10,18,25,215));d.text((36,29),heading,font=font,fill='white');d.text((36,65),s['id']+' | '+('Held recorded viewpoint'if f.get('heldView')else'Calibrated recorded camera'),font=small,fill=(170,230,235))
  active=[e for e in plan['events']if e['start']<=response_time<e['start']+e['duration']]
  # Segment by proportional speech time; source text is never rewritten.
  words=response.split();duration=max(.1,s.get('responseDuration',s['duration']));ix=max(0,min(len(words)-1,int(response_time/duration*len(words))));first=(ix//13)*13;caption=' '.join(words[first:first+13]) if phase=='response' else phase
  if plan.get('wordStarts'):
   import bisect
   ix=max(0,min(len(words)-1,bisect.bisect_right(plan['wordStarts'],response_time)-1));first=(ix//13)*13;caption=' '.join(words[first:first+13]) if phase=='response' else phase
  lines=textwrap.wrap(caption,width=63);h=len(lines)*35+35;d.rounded_rectangle((30,1280-h-25,1250,1255),radius=12,fill=(8,14,24,220))
  for j,line in enumerate(lines):d.text((50,1280-h-7+j*35),line,font=font,fill='white')
  question=plan.get('interpretedQuestion',plan.get('transcript',''));questionLines=textwrap.wrap('Question (visually contextualized ASR): '+question,width=80)
  for j,line in enumerate(questionLines):d.text((36,108+j*28),line,font=small,fill='white',stroke_width=2,stroke_fill=(10,20,30))
  if active:d.text((36,180),' / '.join(e.get('paperEvent',e['gesture'])for e in active),font=small,fill=(130,255,235),stroke_width=2,stroke_fill=(10,20,30))
  # Keep debug readable without obscuring the calibrated room image.
  panel=Image.new('RGB',(1920,1280),(12,20,32));panel.paste(bg.convert('RGB'),(0,0));pd=ImageDraw.Draw(panel)
  pd.text((1300,22),'GestureEvent DEBUG | recorded replay',font=small,fill='white')
  pd.text((1300,62),'RAW MODEL RESPONSE (before TTS):',font=small,fill=(100,240,240))
  raw=plan.get('tagged','(raw model response unavailable)')
  y=100
  for line in textwrap.wrap(raw,width=43):pd.text((1300,y),line,font=small,fill='white');y+=30
  y=max(y+35,570);pd.text((1300,y),'PARSED ACTIVE EVENTS:',font=small,fill=(100,240,240));y+=40
  for e in active:
   for line in textwrap.wrap(json.dumps({key:e.get(key) for key in ['id','paperEvent','targetId','hand','start','duration']}),width=43):pd.text((1300,y),line,font=small,fill=(200,255,150));y+=29
  y=max(y+35,920);pd.text((1300,y),'CURRENT WORD (heuristic alignment):',font=small,fill=(100,240,240));pd.text((1300,y+40),words[ix] if words and phase=='response' else '(no active speech)',font=font,fill=(255,230,90))
  for j,line in enumerate(textwrap.wrap('Fixture provenance: '+str(plan.get('provenance',{}).get('model','unspecified'))+' / macOS speech. NOT a new Gemini response.',width=43)):pd.text((1300,1110+28*j),line,font=small,fill=(190,200,210))
  panel.save(out/f'{i:05d}.jpg',quality=94)
 lines=[]
 for i,f in enumerate(s['frames']):
  delta=s['frames'][i+1]['time']-f['time']if i+1<len(s['frames'])else.111111
  lines.extend([f"file 'composite/{i:05d}.jpg'",f'duration {delta}'])
 lines.append(f"file 'composite/{len(s['frames'])-1:05d}.jpg'");(p/'response.ffconcat').write_text('\n'.join(lines)+'\n')
 video=p/(s['id']+'-agent-hands-response.mp4')
 shell(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(p/'response.ffconcat'),'-i',str(p/('timeline.wav' if 'responseStart' in s else 'response.wav')),'-fps_mode','vfr','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(video)])
 shell(['ffmpeg','-v','error','-i',str(video),'-f','null','-'])
 return video

def main():
 a=argparse.ArgumentParser();a.add_argument('sessions');a.add_argument('--host',required=True,help='Your verified Unity build host SSH alias');a.add_argument('--project',default='/tmp/openclaw/agent-hands-build');a.add_argument('--full-timeline',action='store_true');args=a.parse_args()
 for p in sorted(Path(args.sessions).iterdir()):
  if not (p/'plan.json').exists():continue
  s,derived=prepare(p,args.full_timeline);remote='/tmp/openclaw/agent-hands-render/'+s['id'];
  shell(['ssh',args.host,'mkdir -p '+shlex.quote(remote)])
  shell(['rsync','-a',str(derived)+'/',args.host+':'+remote+'/'])
  command='AGENT_HANDS_SESSION='+shlex.quote(remote)+' AGENT_HANDS_PLAN='+shlex.quote(remote+'/plan.json')+' AGENT_HANDS_RENDER='+shlex.quote(remote+'/overlays')+' AGENT_HANDS_RESPONSE_START='+str(s.get('responseStart',0))+' /Applications/Unity/Hub/Editor/6000.4.5f1/Unity.app/Contents/MacOS/Unity -batchmode -quit -projectPath '+shlex.quote(args.project)+' -buildTarget StandaloneOSX -executeMethod RenderReplay.Run -logFile '+shlex.quote(remote+'/unity-render.log')
  shell(['ssh',args.host,command]);shell(['rsync','-a',args.host+':'+remote+'/',str(derived)+'/'])
  video=composite(p,s,derived/'overlays');print(video,flush=True)
if __name__=='__main__':main()

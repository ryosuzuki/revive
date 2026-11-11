"""Join recorded questions and actual generated Unity responses; never label replay live."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

def run(*args):
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)

root=Path(sys.argv[1]); destination=Path(sys.argv[2]);destination.mkdir(parents=True,exist_ok=True)
font='/System/Library/Fonts/Supplemental/Arial.ttf'
clips=[]
for p in sorted(root.iterdir()):
    response=p/(p.name+'-agent-hands-response.mp4')
    if not response.exists():continue
    s=json.loads((p/'session.json').read_text())
    # Caption text is a local file, not interpreted as ffmpeg filter syntax.
    title=p/'input-title.txt';title.write_text('RECORDED QUESTION | '+p.name+'\nAgentHands reconstruction | No gaze')
    q=p/'question-segment.mp4'
    image=Image.new('RGBA',(1280,1280));draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((18,18,1262,110),radius=12,fill=(0,0,0,210))
    draw.multiline_text((36,32),title.read_text(),font=ImageFont.truetype(font,27),fill='white',spacing=8)
    title_image=p/'input-title.png';image.save(title_image)
    run('-i',p/'source.mp4','-itsoffset',s.get('audioOffset',0),'-i',p/'audio.wav','-loop','1','-i',title_image,'-filter_complex','[0:v][2:v]overlay=0:0,fps=30[v]','-map','[v]','-map','1:a','-af','apad','-t',s['duration'],'-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-ar','24000','-ac','1',q)
    out=destination/(p.name+'-demo.mp4')
    run('-i',q,'-i',response,'-filter_complex','[0:v]setpts=PTS-STARTPTS[v0];[1:v]fps=30,setpts=PTS-STARTPTS[v1];[0:a]asetpts=PTS-STARTPTS[a0];[1:a]asetpts=PTS-STARTPTS[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]','-map','[v]','-map','[a]','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',out)
    run('-i',out,'-f','null','-');clips.append(out);print(out,flush=True)
if len(clips)==3:
    listing=destination/'demo.ffconcat';listing.write_text(''.join("file '"+str(p)+"'\n" for p in clips))
    run('-f','concat','-safe','0','-i',listing,'-c','copy','-movflags','+faststart',destination/'agent-hands-three-trials.mp4')

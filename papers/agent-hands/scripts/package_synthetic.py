#!/usr/bin/env python3
"""Caption explicit synthetic Unity fixture frames; never reads real capture data."""
import argparse,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

a=argparse.ArgumentParser();a.add_argument('frames',type=Path);a.add_argument('output',type=Path);args=a.parse_args();args.output.mkdir(parents=True,exist_ok=True)
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(fontpath,30) if Path(fontpath).exists() else ImageFont.load_default()
small=ImageFont.truetype(fontpath,20) if Path(fontpath).exists() else ImageFont.load_default()
labels=['Point to a registered object','Present an object with an open hand','Measure using two independently scheduled hands','Rotate around an object in 3D']
for i,p in enumerate(sorted(args.frames.glob('*.png'))):
 im=Image.open(p).convert('RGB');d=ImageDraw.Draw(im)
 d.text((34,32),'AgentHands | Unity gesture runtime',font=font,fill='#e7f0f5')
 d.text((34,80),'SYNTHETIC FIXTURE • NO GAZE',font=small,fill='#69d0db')
 d.text((34,565),labels[min(3,i//40)],font=font,fill='white')
 d.text((34,620),'Not live Quest footage or generated conversation.',font=small,fill='#a0b3c2')
 d.rectangle((34,680,926,686),fill='#243241');d.rectangle((34,680,34+int(892*(i+1)/160),686),fill='#69d0db')
 im.save(args.output/f'{i:05d}.png')
subprocess.run(['ffmpeg','-v','error','-y','-framerate','20','-i',str(args.output/'%05d.png'),'-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(args.output/'agent-hands-synthetic-demo.mp4')],check=True)
# Four representative frames from the same actual Unity render, no generated imagery.
sheet=Image.new('RGB',(1440,1080),'#0b121a')
for j,i in enumerate([20,60,100,140]):
 im=Image.open(args.output/f'{i:05d}.png').resize((720,540));sheet.paste(im,((j%2)*720,(j//2)*540))
sheet.save(args.output/'agent-hands-synthetic-preview.jpg',quality=92)

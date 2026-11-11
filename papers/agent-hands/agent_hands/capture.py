"""Lossless metadata import and explicitly mapped RGB conversion, no guessed poses."""
import csv, hashlib, json, subprocess, zipfile
from pathlib import Path
import numpy as np
from PIL import Image


def unpack(archive, destination):
    root=Path(destination).resolve(); root.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            if '__MACOSX' in Path(entry.filename).parts: continue
            target=(root/entry.filename).resolve()
            if not target.is_relative_to(root): raise ValueError('Unsafe ZIP member')
            if ((entry.external_attr >> 16) & 0o170000)==0o120000: raise ValueError('ZIP symlink refused')
            z.extract(entry,root)
    return sorted(p for p in root.iterdir() if p.is_dir())


def pose(row):
    return {'position':[float(row['pose_pos_'+a]) for a in 'xyz'],
            'rotation':[float(row['pose_rot_'+a]) for a in 'xyzw']}


def quaternion_matrix(q):
    x,y,z,w=q; n=x*x+y*y+z*z+w*w
    if n<1e-8: raise ValueError('Zero quaternion')
    x,y,z,w=np.asarray(q)/np.sqrt(n)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def project(point, camera, intrinsics):
    """Unity left-handed metres -> top-left image pixel, sensor optical pose."""
    p=quaternion_matrix(camera['rotation']).T@(np.array(point)-camera['position'])
    if p[2]<=.01: return None
    return [intrinsics['fx']*p[0]/p[2]+intrinsics['cx'],
            -intrinsics['fy']*p[1]/p[2]+intrinsics['cy'],float(p[2])]


def import_take(source,destination):
    src=Path(source); out=Path(destination); out.mkdir(parents=True,exist_ok=True)
    raw=json.loads((src/'left_camera_mruk_intrinsics.json').read_text())
    k={'width':raw['resolution']['width'],'height':raw['resolution']['height'],
       'fx':raw['focalLength']['x'],'fy':raw['focalLength']['y'],
       'cx':raw['principalPoint']['x'],'cy':raw['principalPoint']['y']}
    rows=list(csv.DictReader((src/'left_camera_mruk_frame_metadata.csv').open()))
    rows.sort(key=lambda r:int(r['unix_time_ms']))
    rows=[r for r in rows if r['pose_ok'].lower()=='true' and r['error']=='']
    if not rows: raise ValueError('No accepted sensor frames')
    start=int(rows[0]['unix_time_ms']); frames=[]; images=out/'frames'; images.mkdir(exist_ok=True)
    for i,r in enumerate(rows):
        name=Path(r['file_name'])
        if name.name!=str(name): raise ValueError('Unsafe frame filename')
        data=(src/'left_camera_mruk_rgba'/name).read_bytes()
        if len(data)!=k['width']*k['height']*4: raise ValueError('Wrong RGBA size')
        f=f'{i:05d}.jpg'
        im=Image.frombytes('RGBA',(k['width'],k['height']),data).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        im.convert('RGB').save(images/f,quality=94)
        frames.append({'time':(int(r['unix_time_ms'])-start)/1000,'unixMs':int(r['unix_time_ms']),
                       'image':'frames/'+f,**pose(r),'source':str(name)})
    timing=json.loads((src/'audio-timing.json').read_text())
    session={'id':src.name,'version':1,'coordinateSystem':'unity-lh-y-up-meters',
             'startUnixMs':start,'intrinsics':k,'frames':frames,
             'duration':frames[-1]['time'], 'imageOrientation':'raw-bottom-up -> vflip',
             'audioOffset':(timing.get('estimatedFirstSampleUnixMs',start)-start)/1000,
             'audioTimingQuality':timing.get('timingQuality','unknown'),
             'sourceFrames':len(rows),'gaze':False}
    (out/'session.json').write_text(json.dumps(session,indent=2))
    import shutil
    for f in ['audio.wav','hands.jsonl','room-geometry.json','left-hand-skeleton.json','right-hand-skeleton.json']:
        if (src/f).exists(): shutil.copyfile(src/f,out/f)
    # Explicit VFR file durations retain actual accepted sensor timestamps.
    lines=[]
    for i,f in enumerate(frames):
        lines.append("file 'frames/"+Path(f['image']).name+"'")
        delta=frames[i+1]['time']-f['time'] if i+1<len(frames) else .111111
        lines.append('duration '+str(delta))
    lines.append("file 'frames/"+Path(frames[-1]['image']).name+"'")
    (out/'frames.ffconcat').write_text('\n'.join(lines)+'\n')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(out/'frames.ffconcat'),
                    '-fps_mode','vfr','-c:v','libx264','-pix_fmt','yuv420p','-crf','19',str(out/'source.mp4')],check=True)
    return session

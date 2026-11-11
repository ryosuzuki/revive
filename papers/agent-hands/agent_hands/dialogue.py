import json,os,subprocess,tempfile,uuid
from pathlib import Path
from .events import validate_plan

def answer(question,objects,image=None,head=(0,1.5,0)):
    from .backend import Backend
    from .adapter import unity_plan,refine_audio
    import wave
    registry={}
    for o in objects:
        registry[o['id']]={**o,'axes':o.get('axes',[[1,0,0],[0,1,0],[0,0,1]]),'parts':o.get('parts',{})}
    raw=Backend().respond(question,registry,Path(image).read_bytes() if image else None)
    raw['question']=question
    with tempfile.TemporaryDirectory(prefix='agent-hands-tts-') as d:
        path=speak(raw['speech'],Path(d)/'response.wav')
        with wave.open(str(path)) as w:duration=w.getnframes()/w.getframerate()
        plan=unity_plan(raw,registry,duration,head)
        return refine_audio(plan,path)

def speak(text,destination):
    p=Path(destination);p.parent.mkdir(parents=True,exist_ok=True)
    aiff=p.with_suffix('.aiff')
    subprocess.run(['/usr/bin/say','-v',os.environ.get('AGENT_HANDS_VOICE','Samantha'),'-r','150','-o',str(aiff),'--',text],check=True)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(aiff),'-ar','24000','-ac','1',str(p)],check=True)
    aiff.unlink();return p

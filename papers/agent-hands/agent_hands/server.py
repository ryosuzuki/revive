"""Private-LAN live dialogue bridge; registry and parser are identical to replay."""
import base64,json,os,tempfile,uuid,wave
from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .dialogue import answer
from .events import SpatialObject
app=FastAPI(title='AgentHands private dialogue bridge')
ROOT=Path(os.environ.get('AGENT_HANDS_RUNTIME','/tmp/openclaw/agent-hands-service'));ROOT.mkdir(parents=True,exist_ok=True)
_model=None
class Request(BaseModel):
    audioBase64:str=''
    question:str=''
    mode:str='question'
    objects:list[dict]=[]
    position:list[float]=[]
    head:list[float]=[0,1.5,0]

def transcribe(path):
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model=WhisperModel(os.environ.get('AGENT_HANDS_ASR','base.en'),device='cpu',compute_type='int8')
    segments,_=_model.transcribe(__import__('numpy').frombuffer(__import__('subprocess').check_output(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ac','1','-ar','16000','-']),dtype='float32'),vad_filter=True)
    return ' '.join(s.text.strip() for s in segments).strip()

@app.get('/health')
def health():return {'status':'ready','gaze':False,'modelConfigured':bool(os.environ.get('AGENT_HANDS_MODEL_URL'))}
@app.post('/dialogue')
def dialogue(r:Request):
    try:
        q=r.question.strip()
        if r.audioBase64:
            raw=base64.b64decode(r.audioBase64,validate=True)
            if len(raw)>8*1024*1024:raise ValueError('Audio exceeds bounded request size')
            p=ROOT/(str(uuid.uuid4())+'.wav');p.write_bytes(raw)
            try:q=transcribe(p)
            finally:p.unlink(missing_ok=True)
        if not q:raise ValueError('No speech recognized; please retry')
        if r.mode=='register':
            obj=SpatialObject('object-'+uuid.uuid4().hex[:8],q,r.position,[.15,.15,.15],1,'user-spoken-label + controller-origin position').validate()
            from dataclasses import asdict
            return {'object':asdict(obj),'transcript':q}
        from dataclasses import asdict
        from dataclasses import fields
        objects=[]
        names={f.name for f in fields(SpatialObject)}
        for o in r.objects:
            valid=asdict(SpatialObject(**{k:v for k,v in o.items() if k in names}).validate())
            for extra in ['axes','parts','provenance']:
                if extra in o:valid[extra]=o[extra]
            objects.append(valid)
        if len(r.head)!=3 or not all(__import__('math').isfinite(v) for v in r.head):raise ValueError('Invalid camera position')
        key=uuid.uuid4().hex
        plan=answer(q,objects,head=r.head,audio_destination=ROOT/(key+'.wav'))
        plan['audioUrl']='/audio/'+key+'.wav'
        (ROOT/(key+'.json')).write_text(json.dumps(plan,indent=2))
        return plan
    except (ValueError,KeyError) as e:raise HTTPException(422,str(e))
    except Exception as e:raise HTTPException(503,'Dialogue provider unavailable: '+type(e).__name__)
@app.get('/audio/{name}')
def audio(name:str):
    if not name.endswith('.wav') or Path(name).name!=name:raise HTTPException(404)
    p=ROOT/name
    if not p.is_file():raise HTTPException(404)
    return FileResponse(p,media_type='audio/wav')

class VisualRegistration(BaseModel):
    imageBase64:str
    selection:list[float]
    hit:list[float]
    camera:dict
    intrinsics:dict

@app.post('/register')
def visual_registration(r:VisualRegistration):
    """Exact calibrated live/replay registration entry; never substitutes head gaze.

    A caller must supply a confirmed controller/hand mesh hit and sensor camera
    calibration. The spoken-point Quest fallback deliberately does not fake it.
    """
    from .backend import configured_backend
    from .registration import register_box
    try:
        if len(r.selection)!=2 or len(r.hit)!=3:raise ValueError('Confirmed pixel and mesh hit required')
        image=base64.b64decode(r.imageBase64,validate=True)
        if len(image)>8*1024*1024:raise ValueError('Image exceeds bounded input size')
        data=configured_backend().perceive(image,r.selection)
        obj=register_box('object-'+uuid.uuid4().hex[:8],data['label'],r.hit,r.camera,r.intrinsics,data['bbox'],data['size'],data.get('parts',{}))
        obj['confidence']=float(data.get('confidence',.5));obj['provenance']['model']=data.get('modelProvenance',{})
        return {'object':obj}
    except (ValueError,KeyError)as e:raise HTTPException(422,str(e))
    except Exception as e:raise HTTPException(503,'Visual provider unavailable: '+type(e).__name__)

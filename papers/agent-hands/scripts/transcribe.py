from pathlib import Path
import json,sys,os,subprocess
import numpy as np
from faster_whisper import WhisperModel
model_name=os.environ.get('AGENT_HANDS_ASR','small.en')
model=WhisperModel(model_name,device='cpu',compute_type='int8')
for p in Path(sys.argv[1]).glob('*/audio.wav'):
 audio=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-f','f32le','-ac','1','-ar','16000','pipe:1']),dtype=np.float32)
 segments,info=model.transcribe(audio,beam_size=5,vad_filter=True)
 data={'language':info.language,'segments':[{'start':s.start,'end':s.end,'text':s.text} for s in segments],'model':'faster-whisper/'+model_name,'timingQuality':'audio-relative; capture start offset applied separately'}
 (p.parent/'transcript.json').write_text(json.dumps(data,indent=2));print(p.parent.name,json.dumps(data),flush=True)

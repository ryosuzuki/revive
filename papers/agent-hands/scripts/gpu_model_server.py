"""Private single-worker Qwen3-VL service. Launch via gpu-run, never public-bind."""
import argparse,threading,base64,io,time
from PIL import Image
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
import torch
from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
import uvicorn
p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=18441);p.add_argument('--model',default='Qwen/Qwen3-VL-8B-Instruct');a=p.parse_args()
processor=AutoProcessor.from_pretrained(a.model)
model=Qwen3VLForConditionalGeneration.from_pretrained(a.model,torch_dtype=torch.bfloat16,device_map='cuda')
lock=threading.Lock();app=FastAPI()
class Request(BaseModel):
 prompt:str
 image:str|None=None
 max_tokens:int=1800
@app.get('/health')
def health():return {'ready':True,'model':a.model,'gaze':False}
@app.post('/generate')
def generate(r:Request):
 if len(r.prompt)>24000 or len(r.image or '')>16000000:raise HTTPException(413,'Input too large')
 content=[]
 if r.image:
  img=Image.open(io.BytesIO(base64.b64decode(r.image))).convert('RGB');img.thumbnail((1280,1280));content.append({'type':'image','image':img})
 content.append({'type':'text','text':r.prompt})
 with lock:
  start=time.monotonic()
  batch=processor.apply_chat_template([{'role':'user','content':content}],tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt').to(model.device)
  with torch.inference_mode():out=model.generate(**batch,max_new_tokens=min(3000,max(1,r.max_tokens)),do_sample=False)
  text=processor.batch_decode(out[:,batch['input_ids'].shape[1]:],skip_special_tokens=True)[0]
 return {'text':text,'seconds':time.monotonic()-start,'model':a.model}
uvicorn.run(app,host=a.host,port=a.port)

"""Explicit-model Google provider; never silently substitutes a model or logs keys."""
import base64,json,time,wave
from pathlib import Path
import requests
from .backend import Backend

RESPONSE_MODEL='gemini-2.5-flash-exp'
TTS_MODEL='gemini-2.5-flash-preview-tts'

class GeminiBackend(Backend):
    def __init__(self,key,model=RESPONSE_MODEL,tts_model=TTS_MODEL):
        import re
        if not key or not re.fullmatch(r'[A-Za-z0-9.-]+',model):
            raise ValueError('Explicit API credential and valid model ID required')
        self._key=key;self.model=model;self.tts_model=tts_model
        if not re.fullmatch(r'[A-Za-z0-9.-]+',tts_model):raise ValueError('Invalid TTS model ID')
    def generate(self,prompt,image=None):
        parts=[{'text':prompt}]
        if image:parts.append({'inlineData':{'mimeType':'image/jpeg','data':base64.b64encode(image).decode()}})
        started=time.monotonic()
        reply=self._request(self.model,{'contents':[{'parts':parts}]})
        text=''.join(p.get('text','') for p in reply['candidates'][0]['content']['parts'])
        if not text.strip():raise ValueError('Provider returned no generated text')
        return {'text':text.replace(self._key,'[REDACTED]'),'model':self.model,'provider':'Google Gemini API','seconds':time.monotonic()-started}
    def _request(self,model,body):
        response=requests.post('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',json=body,headers={'x-goog-api-key':self._key},timeout=180,allow_redirects=False)
        if response.status_code!=200:
            raise RuntimeError(f'Configured provider model {model} failed with HTTP{response.status_code}; no fallback performed')
        return response.json()
    def speak(self,text,destination,model=None):
        # Credentials only in headers to the fixed TLS provider origin.
        import re
        model=model or self.tts_model
        if not re.fullmatch(r'[A-Za-z0-9.-]+',model):raise ValueError('Invalid TTS model ID')
        reply=self._request(model,{'contents':[{'parts':[{'text':'Say clearly in English: '+text}]}],'generationConfig':{'responseModalities':['AUDIO'],'speechConfig':{'voiceConfig':{'prebuiltVoiceConfig':{'voiceName':'Kore'}}}}})
        audio=next(p['inlineData'] for p in reply['candidates'][0]['content']['parts'] if 'inlineData' in p)
        if not audio['mimeType'].startswith(('audio/L16','audio/pcm')):raise ValueError('Unsupported provider audio')
        pcm=base64.b64decode(audio['data'],validate=True);match=re.search(r'rate=(\d+)',audio['mimeType']);rate=int(match[1]) if match else 24000
        path=Path(destination);path.parent.mkdir(parents=True,exist_ok=True)
        with wave.open(str(path),'wb') as stream:stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(rate);stream.writeframes(pcm)
        return path

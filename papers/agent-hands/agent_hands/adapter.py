"""Paper-style markup -> shared Unity/replay states, with deterministic hand arbitration."""
import copy
from .markup import schedule
from .registration import resolve_region
MAPPING={'PointObject':'point','RegionOfObject':'point','DirectionOfObject':'trace','ObjectProxy':'rotate','Action':'grasp','Geometry1D':'measure','Geometry2D':'measure','Geometry3D':'measure','Numeric':'open','Positive':'open','Negative':'open','Attention':'beat','Prohibition':'beat','Comparison':'measure','Celebration':'open','Burn':'open','Poisoned':'open','Spoil':'open'}

def unity_plan(parsed,registry,duration,head=(0,1.5,0)):
    parsed=schedule(parsed,duration);objects=[]
    for key,obj in registry.items():objects.append({'id':key,'label':obj['label'],'position':obj['position'],'size':obj['size'],'registration':obj.get('provenance',{}).get('registration','user-explicit'),'confidence':obj.get('confidence',.5)})
    objects.append({'id':'agent-midair','label':'Agent mid-air gesture space','position':[head[0],head[1]-.25,head[2]+.65],'size':[.18,.18,.1],'registration':'camera-relative nonphysical gesture space','confidence':1})
    events=[];last_used={'left':-1.,'right':-1.}
    for i,event in enumerate(parsed['events']):
        a=event['attributes'];target=a.get('object',a.get('target','agent-midair'));kind=event['id'];gesture=MAPPING[kind]
        if kind=='RegionOfObject' or (a.get('region') and target in registry):
            pos=resolve_region(registry[target],a.get('region','F:center:center'));anchor=target+'-region-'+str(i)
            objects.append({'id':anchor,'label':registry[target]['label']+' '+a.get('region','front'),'position':pos,'size':[.025,.025,.025],'registration':'registered semantic region','confidence':registry[target].get('confidence',.5)});target=anchor
        hand='both' if a.get('handedness')=='double' or kind in {'Comparison','Geometry1D','Geometry2D','Geometry3D'} else min(last_used,key=last_used.get)
        start=event['start'];end=min(duration,start+event['duration'])
        for old in events:
            if old['start']+old['duration']>start and (old['hand']==hand or 'both' in (old['hand'],hand)):old['duration']=max(.001,start-old['start'])
        pose=a.get('gesture','palm')
        if kind in {'PointObject','RegionOfObject','DirectionOfObject','Attention','Prohibition'}:pose='point'
        if kind=='Positive':pose='thumbUp'
        if kind=='Negative':pose='thumbDown'
        if kind=='Numeric':pose=a.get('gesture','one')
        effect=a.get('vfx','none')
        if kind in {'Burn','Poisoned','Spoil'}:effect=kind.lower()
        interaction=a.get('interactivity','none')
        if kind=='Celebration':interaction='highFive'
        events.append({'id':f'{i}-{kind}','wordIndex':event['wordIndex'],'start':start,'duration':max(.001,end-start),'gesture':gesture,'targetId':target,'hand':hand,'speech':' '.join(parsed['words'][event['wordIndex']:min(len(parsed['words']),event['wordIndex']+12)]),'pose':pose,'motion':a.get('dynamics','static'),'effect':effect,'interactivity':interaction,'paperEvent':kind,'region':a.get('region','')})
        if hand=='both':last_used={'left':start,'right':start}
        else:last_used[hand]=start
    return {'version':1,'responseDuration':duration,'wordStarts':parsed.get('wordStarts',[]),'gaze':False,'objects':objects,'events':events,'transcript':parsed.get('question',''),'response':parsed['speech'],'tagged':parsed.get('tagged',''),'alignment':parsed['alignment'],'provenance':parsed.get('provenance',{})}

def refine_audio(plan,wav_path):
    """Paper-inspired pause snapping: smoothed RMS minima within +/-120 ms.

    Bounded local refinement, not forced alignment. Word identities never change.
    """
    import wave,numpy as np
    with wave.open(str(wav_path)) as w:
        rate=w.getframerate();channels=w.getnchannels();data=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)
    if channels>1:data=data.reshape(-1,channels).mean(axis=1)
    step=max(1,int(rate*.01));window=max(1,int(rate*.04))
    rms=np.sqrt(np.convolve(data*data,np.ones(window)/window,mode='same'))[::step]
    word_starts=[]
    for center in plan.get('wordStarts',[]):
        lo=max(0,int((center-.12)*rate/step));hi=min(len(rms),int((center+.12)*rate/step)+1)
        adjusted=float((lo+int(np.argmin(rms[lo:hi])))*step/rate) if hi>lo else center
        word_starts.append(max(word_starts[-1]+.001 if word_starts else 0,min(adjusted,len(data)/rate)))
    if word_starts:plan['wordStarts']=word_starts
    candidates=[]
    for e in plan['events']:
        center=word_starts[e['wordIndex']] if word_starts and 'wordIndex' in e else e['start'];lo=max(0,int((center-.12)*rate/step));hi=min(len(rms),int((center+.12)*rate/step)+1)
        adjusted=center if word_starts and 'wordIndex' in e else float((lo+int(np.argmin(rms[lo:hi])))*step/rate) if hi>lo else center
        adjusted=max(0,min(adjusted,max(0,len(data)/rate-.05)))
        candidates.append((e,adjusted))
    previous=-1.
    for e,t in candidates:
        t=max(previous+.001,t);previous=t;e['start']=t
    # Preserve deterministic interruption semantics after snapping.
    for i,e in enumerate(plan['events']):
        for other in plan['events'][i+1:]:
            if e['hand']==other['hand'] or 'both' in (e['hand'],other['hand']):
                e['duration']=min(e['duration'],max(.001,other['start']-e['start']));break
    plan['alignment']='weighted word-length + punctuation; local smoothed RMS minima +/-120ms (not forced alignment)'
    return plan

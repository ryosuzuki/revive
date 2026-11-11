"""Single typed event contract shared by replay and the Quest client."""
from dataclasses import dataclass,asdict,field
import math

GESTURES={'point','present','measure','trace','rotate','grasp','beat','open'}
@dataclass
class SpatialObject:
    id:str
    label:str
    position:list[float]
    size:list[float]
    confidence:float=1.0
    registration:str='controller'
    def validate(self):
        if not self.id or not self.label: raise ValueError('Object ID and label required')
        if len(self.position)!=3 or len(self.size)!=3: raise ValueError('Expected 3D object')
        if not all(math.isfinite(x) for x in self.position+self.size): raise ValueError('Nonfinite spatial object')
        if not all(x>0 for x in self.size): raise ValueError('Positive object size required')
        if not 0<=self.confidence<=1:raise ValueError('Invalid confidence')
        return self
@dataclass
class GestureEvent:
    start:float
    duration:float
    gesture:str
    targetId:str
    hand:str='right'
    speech:str=''
    id:str=''
    pose:str='palm'
    motion:str='static'
    effect:str='none'
    interactivity:str='none'
    paperEvent:str=''
    region:str=''
    def validate(self,objects):
        if self.gesture not in GESTURES:raise ValueError('Unsupported gesture '+self.gesture)
        if self.targetId not in objects:raise ValueError('Unknown target '+self.targetId)
        if not math.isfinite(self.start) or self.start<0 or not math.isfinite(self.duration) or self.duration<=0:raise ValueError('Invalid event time')
        if self.hand not in ('left','right','both'):raise ValueError('Invalid hand')
        return self

def validate_plan(data):
    if data.get('gaze',False):raise ValueError('Gaze excluded by user')
    objects={}
    for item in data.get('objects',[]):
        obj=SpatialObject(**item).validate()
        if obj.id in objects:raise ValueError('Duplicate object ID')
        objects[obj.id]=obj
    events=[GestureEvent(**x).validate(objects) for x in data.get('events',[])]
    events.sort(key=lambda x:(x.start,x.id))
    # Same-hand overlap is rejected, never silently squashed.
    for i,a in enumerate(events):
        for b in events[i+1:]:
            if b.start>=a.start+a.duration:break
            if a.hand==b.hand or 'both' in (a.hand,b.hand):raise ValueError('Overlapping same-hand gestures')
    return {'version':1,'gaze':False,'objects':[asdict(x) for x in objects.values()],
            'events':[asdict(x) for x in events],
            'transcript':str(data.get('transcript','')),'response':str(data.get('response','')),
            'provenance':data.get('provenance',{})}

def active_events(plan,t):
    return [e for e in plan['events'] if e['start']<=t<e['start']+e['duration']]

def ease(t):
    t=max(0,min(1,t));return t*t*(3-2*t)

def hand_pose(event,obj,t):
    """Anchor-relative trajectory, identical formula in Unity GestureRuntime.cs."""
    p=obj['position'];size=obj['size'];u=max(0,min(1,(t-event['start'])/event['duration']))
    envelope=math.sin(math.pi*u);side=-1 if event['hand']=='left' else 1
    center=[p[0]+side*(size[0]/2+.12),p[1]+.08,p[2]-.12]
    gesture=event['gesture']
    if gesture=='point':center=[p[0]+side*(size[0]/2+.14),p[1]+.06,p[2]-.16+.04*envelope]
    elif gesture=='present':center=[p[0],p[1]-size[1]/2-.07,p[2]-.10]
    elif gesture=='measure':center=[p[0]+side*(size[0]/2+.05+.04*envelope),p[1],p[2]-.08]
    elif gesture=='trace':center=[p[0]+(u-.5)*size[0],p[1]+size[1]/2+.05,p[2]-.06]
    elif gesture=='rotate':center=[p[0]+math.cos(u*math.pi*2)*(size[0]/2+.10),p[1]+.12,p[2]+math.sin(u*math.pi*2)*(size[2]/2+.10)]
    elif gesture=='grasp':center=[p[0]+side*(size[0]/2+.04*(1-envelope)),p[1],p[2]-.04]
    elif gesture=='beat':center=[p[0]+side*.18,p[1]+.18+.04*math.sin(u*math.pi*8),p[2]-.14]
    return center

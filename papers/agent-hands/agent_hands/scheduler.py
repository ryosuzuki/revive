"""Deterministic per-hand arbitration and bounded contact interaction state."""
class Scheduler:
 def __init__(self,events):self.events=sorted(enumerate(events),key=lambda x:(x[1]['start'],x[0]));self.reset()
 def reset(self):self.hands={'left':None,'right':None};self.index=0;self.time=-1
 def advance(self,time,contacts=()):
  if time<self.time:self.reset()
  self.time=time
  for side,state in list(self.hands.items()):
   if state and (time>=state['end'] or (state['interactive'] and side in contacts)):
    self.hands[side]=None
  while self.index<len(self.events) and self.events[self.index][1]['start']<=time:
   order,e=self.events[self.index];self.index+=1
   a=e['attributes'];interaction=a.get('interactivity','none')!='none' or e['id']=='Celebration'
   # The timeout belongs to the original event, not the seek time.
   end=e['start']+(8 if interaction else e['duration'])
   if end<=time:continue
   if a.get('handedness')=='double' or e['id']=='Comparison':sides=['left','right']
   else:sides=[next((s for s,v in self.hands.items() if v is None),min(self.hands,key=lambda s:self.hands[s]['start'] if self.hands[s] else -1))]
   for side in sides:self.hands[side]={'event':e,'order':order,'start':e['start'],'end':end,'interactive':interaction}
  return {k:v.copy() if v else None for k,v in self.hands.items()}

"""Paper-style inline event parsing with stable token indexes and bounded timing."""
import re
IDS={'PointObject','RegionOfObject','DirectionOfObject','ObjectProxy','Action','Geometry1D','Geometry2D','Geometry3D','Numeric','Positive','Negative','Attention','Prohibition','Comparison','Celebration','Burn','Poisoned','Spoil'}
ALIASES={'BurnEffect':'Burn','ThumbupExpression':'Positive','StopExpression':'Prohibition'}
TOKEN=re.compile(r"\S+")
TAG=re.compile(r'\[([A-Za-z0-9]+)(?:;([^\[\]]*))?\]')
DEFAULTS={'handedness':'single','gesture':'palm','dynamics':'static','interactivity':'none','vfx':'none','spatiality':'midAir'}
ALLOWED={
'handedness':{'single','double'},'gesture':{'palm','fist','point','hold','grab','thumbUp','thumbDown','one','two','three','cylinder','cube','sphere'},
'dynamics':{'static','rollRotation','pitchRotation','yawRotation','xTranslation','yTranslation','zTranslation'},
'interactivity':{'none','highFive','shakeHand','holdHand'},'vfx':{'none','burn','freeze','glow','poisoned','spoil','explode'}}


def parse(text,registry):
    chunks=[];events=[];cursor=0;length=0
    for match in TAG.finditer(text):
        chunk=text[cursor:match.start()];chunks.append(chunk);length+=len(chunk)
        event_id=ALIASES.get(match[1],match[1])
        if event_id not in IDS:raise ValueError('Unknown event '+event_id)
        attrs=dict(DEFAULTS)
        for part in (match[2] or '').split(','):
            if not part.strip():continue
            k,sep,v=part.strip().partition(':')
            if not sep:raise ValueError('Malformed attribute')
            k=k.lower();v=v.strip()
            if k not in set(DEFAULTS)|{'object','region','target','duration'}:raise ValueError('Unknown attribute '+k)
            if k in ALLOWED and v not in ALLOWED[k]:raise ValueError('Invalid '+k)
            attrs[k]=v
        spatial=attrs.get('spatiality','midAir')
        if spatial!='midAir' and not attrs.get('object') and not attrs.get('target'):
            if spatial in registry:attrs['object']=spatial
            else:
                # Appendix B spatiality combines object ID and a six-face grid.
                pieces=spatial.rsplit('_',3)
                if len(pieces)!=4 or pieces[0] not in registry:raise ValueError('Unknown spatiality reference '+spatial)
                object_id,face,vertical,horizontal=pieces
                vertical={'middle':'center'}.get(vertical,vertical)
                if face not in 'FBTDLR' or vertical not in {'top','center','bottom'} or horizontal not in {'left','center','right'}:raise ValueError('Invalid spatiality grid')
                attrs['object']=object_id;attrs['region']=':'.join((face,vertical,horizontal))
        target=attrs.get('object',attrs.get('target'))
        if target and target not in registry:raise ValueError('Unknown registered object '+target)
        if event_id in {'PointObject','RegionOfObject','DirectionOfObject','ObjectProxy','Action'} and not target:raise ValueError('Spatial event requires registered object')
        events.append({'id':event_id,'character':length,'attributes':attrs})
        cursor=match.end()
    chunks.append(text[cursor:]);clean=''.join(chunks)
    if '[' in clean or ']' in clean:raise ValueError('Unparsed bracket markup')
    words=list(TOKEN.finditer(clean))
    for e in events:
        ix=next((i for i,w in enumerate(words) if w.end()>e['character']),None)
        if ix is None:raise ValueError('Event has no spoken trigger')
        e['wordIndex']=ix;e['trigger']=words[ix][0];del e['character']
    return {'speech':clean,'words':[w[0] for w in words],'events':events}


def schedule(parsed,duration):
    if duration<=0:raise ValueError('Empty audio')
    weights=[max(1,len(w.strip('.,!?;:')))+ (3 if w[-1:] in '.!?;:' else 0) for w in parsed['words']]
    total=sum(weights)
    if not total:raise ValueError('Empty speech')
    starts=[0.]
    for w in weights:starts.append(starts[-1]+w/total*duration)
    events=[]
    for event in parsed['events']:
        i=event['wordIndex'];start=starts[i]
        events.append({**event,'start':start,'duration':min(2.5,duration-start)})
    return {**parsed,'events':events,'duration':duration,'alignment':'word-length and punctuation heuristic; not forced alignment'}

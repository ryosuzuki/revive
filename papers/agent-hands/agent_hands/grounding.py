"""Visual object detections -> measured room-mesh ray intersections."""
import numpy as np
from .capture import quaternion_matrix

def ray_mesh(origin,direction,room):
    origin=np.asarray(origin,dtype=float);direction=np.asarray(direction,dtype=float)
    candidates=[]
    for part in room['parts']:
        verts=np.asarray(part['vertices'],dtype=float).reshape(-1,3).copy();verts[:,2]*=-1 # room three-RH to Unity-LH
        tri=np.asarray(part['triangles'],dtype=int).reshape(-1,3)
        if not len(tri):continue
        v0=verts[tri[:,0]];e1=verts[tri[:,1]]-v0;e2=verts[tri[:,2]]-v0
        h=np.cross(np.broadcast_to(direction,e2.shape),e2);a=np.sum(e1*h,axis=1)
        valid=np.abs(a)>1e-8;f=np.zeros_like(a);f[valid]=1/a[valid]
        s=np.asarray(origin)-v0;u=f*np.sum(s*h,axis=1);q=np.cross(s,e1);v=f*(q@direction);t=f*np.sum(e2*q,axis=1)
        valid&=(u>=0)&(v>=0)&(u+v<=1)&(t>.08)&(t<15)
        if valid.any():
            d=float(t[valid].min());candidates.append((d,(np.asarray(origin)+direction*d).tolist(),part['label']))
    return min(candidates,key=lambda x:x[0]) if candidates else None

def ground_detections(detections,frame,k,room):
    result=[];rejected=[]
    rot=quaternion_matrix(frame['rotation'])
    for n,d in enumerate(detections):
        b=d.get('bbox',[])
        if len(b)!=4 or not all(0<=float(x)<=1 for x in b) or b[2]<=b[0] or b[3]<=b[1]:
            rejected.append({'detection':d,'reason':'invalid normalized bbox'});continue
        px=(b[0]+b[2])/2*k['width'];py=(b[1]+b[3])/2*k['height']
        local=np.array([(px-k['cx'])/k['fx'],-(py-k['cy'])/k['fy'],1]);direction=rot@(local/np.linalg.norm(local))
        hit=ray_mesh(frame['position'],direction,room)
        if not hit:
            rejected.append({'detection':d,'reason':'no measured mesh intersection; no guessed fallback'});continue
        depth=(rot.T@(np.array(hit[1])-frame['position']))[2]
        width=max(.025,(b[2]-b[0])*k['width']/k['fx']*depth)
        height=max(.025,(b[3]-b[1])*k['height']/k['fy']*depth)
        result.append({'id':str(d.get('id',f'object-{n}')),'label':str(d['label']),
                       'position':hit[1],'size':[width,height,min(width,height)],
                       'confidence':float(d.get('confidence',.5)),
                       'registration':'vision-bbox + measured-room-mesh-raycast (coarse surface intersection)'})
    return result,rejected

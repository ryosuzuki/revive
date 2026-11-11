"""Measured ray/mesh selection and Appendix A oriented registration, without gaze."""
import numpy as np
from .capture import quaternion_matrix


def ray_triangle(origin,direction,a,b,c):
    o,d,a,b,c=map(lambda v:np.asarray(v,dtype=float),(origin,direction,a,b,c))
    e1,e2=b-a,c-a; h=np.cross(d,e2); det=np.dot(e1,h)
    if abs(det)<1e-9:return None
    s=o-a; u=np.dot(s,h)/det
    if u<0 or u>1:return None
    q=np.cross(s,e1); v=np.dot(d,q)/det
    if v<0 or u+v>1:return None
    t=np.dot(e2,q)/det
    return (o+d*t).tolist() if t>1e-5 else None


def register_box(object_id,label,hit,camera,intrinsics,bbox,size,parts=None):
    """bbox is top-left RGB pixels; size is inferred metres (not measured).

    Image-center ray intersects the selected front plane. Volume center moves
    half a depth AWAY from camera; axes columns are right/up/front-to-camera.
    """
    hit=np.asarray(hit,float); cp=np.asarray(camera['position'],float)
    size=np.asarray(size,float); box=np.asarray(bbox,float)
    if size.shape!=(3,) or not np.all(np.isfinite(size)) or np.any(size<=0):raise ValueError('Invalid dimensions')
    if box.shape!=(4,) or not np.all(np.isfinite(box)):raise ValueError('Invalid bbox')
    x0,y0,x1,y1=box
    if not (0<=x0<x1<=intrinsics['width'] and 0<=y0<y1<=intrinsics['height']):raise ValueError('BBox outside image')
    front=cp-hit;front[1]=0
    if np.linalg.norm(front)<1e-6:raise ValueError('Degenerate camera-to-surface direction')
    front/=np.linalg.norm(front); up=np.array([0.,1.,0.]); right=np.cross(up,front)
    axes=np.column_stack((right,up,front))
    ray=np.array([((x0+x1)/2-intrinsics['cx'])/intrinsics['fx'],-((y0+y1)/2-intrinsics['cy'])/intrinsics['fy'],1.])
    ray=quaternion_matrix(camera['rotation'])@ray
    denom=np.dot(ray,front)
    if abs(denom)<1e-7:raise ValueError('Ray parallel to front plane')
    t=np.dot(hit-cp,front)/denom
    if t<=0:raise ValueError('Object behind camera')
    center=cp+t*ray-front*size[2]/2
    return {'id':object_id,'label':label,'position':center.tolist(),'size':size.tolist(),
            'axes':axes.tolist(),'parts':parts or {},'provenance':{'registration':'explicit-ray-mesh-hit','dimensions':'model-estimated','gaze':False}}


def resolve_region(obj,region='F:center:center'):
    """Six faces; vertical top/center/bottom, horizontal left/center/right."""
    if region in obj.get('parts',{}):region=obj['parts'][region]
    try:
        face,vertical,horizontal=region.split(':')
        u={'left':-1/3,'center':0.,'right':1/3}[horizontal]
        v={'bottom':-1/3,'center':0.,'top':1/3}[vertical]
        local={'F':(u,v,.5),'B':(-u,v,-.5),'L':(-.5,v,u),'R':(.5,v,-u),'T':(u,.5,-v),'D':(u,-.5,v)}[face]
    except (ValueError,KeyError):raise ValueError('Unknown semantic region: '+region)
    return (np.asarray(obj['position'])+np.asarray(obj['axes'])@(np.asarray(local)*obj['size'])).tolist()


def mesh_hit(origin,direction,geometry):
    """Nearest positive triangle intersection, with explicit recorded mesh axes."""
    origin=np.asarray(origin,float);direction=np.asarray(direction,float)
    if not np.all(np.isfinite(direction)) or np.linalg.norm(direction)<1e-8:raise ValueError('Invalid ray')
    direction/=np.linalg.norm(direction);nearest=None;best=float('inf')
    convention=geometry.get('coordinateSystem')
    if convention not in ('three-rh-y-up-meters','unity-lh-y-up-meters'):raise ValueError('Unknown mesh coordinate system')
    for part in geometry.get('parts',[]):
        vertices=np.array(part.get('vertices',[]),float).reshape(-1,3)
        if convention=='three-rh-y-up-meters':vertices[:,2]*=-1
        indices=np.array(part.get('triangles',part.get('indices',[])),int).reshape(-1,3)
        if not len(indices):continue
        tri=vertices[indices];e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
        h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h)
        valid=np.abs(det)>1e-9;inv=np.zeros_like(det);inv[valid]=1/det[valid]
        s=origin-tri[:,0];u=np.einsum('ij,ij->i',s,h)*inv;q=np.cross(s,e1)
        v=q@direction*inv;t=np.einsum('ij,ij->i',e2,q)*inv
        valid &= (u>=0)&(v>=0)&(u+v<=1)&(t>1e-5)
        if np.any(valid):
            distance=float(t[valid].min())
            if distance<best:best=distance;nearest=origin+direction*distance
    if nearest is None:raise ValueError('Selected ray does not intersect recorded mesh')
    return nearest.tolist()

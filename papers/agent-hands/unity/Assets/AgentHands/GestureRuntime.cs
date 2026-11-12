using System;
using System.Collections.Generic;
using UnityEngine;

namespace AgentHands {
 [Serializable] public class RegisteredObject { public string id,label,registration; public float[] position,size; public float confidence=1; public Vector3 Position=>new Vector3(position[0],position[1],position[2]); public Vector3 Size=>new Vector3(size[0],size[1],size[2]); }
 [Serializable] public class GestureEvent { public float start,duration; public string gesture,targetId,hand,speech,id,pose,motion,effect,interactivity,paperEvent,region; }
 [Serializable] public class GesturePlan {public int version=1;public bool gaze=false;public RegisteredObject[] objects=Array.Empty<RegisteredObject>();public GestureEvent[] events=Array.Empty<GestureEvent>();public string transcript,response,audioUrl,tagged,alignment;}
 public static class GestureMath {
  public static Vector3 Position(GestureEvent e,RegisteredObject o,float t,bool left){
   Vector3 p=o.Position,s=o.Size;float u=Mathf.Clamp01((t-e.start)/e.duration),v=Mathf.Sin(Mathf.PI*u),side=left?-1:1;
   switch(e.gesture){
    case "point":return p+new Vector3(side*(s.x/2+.14f),.06f,-.16f+.04f*v);
    case "present":return p+new Vector3(0,-s.y/2-.07f,-.10f);
    case "measure":return p+new Vector3(side*(s.x/2+.05f+.04f*v),0,-.08f);
    case "trace":return p+new Vector3((u-.5f)*s.x,s.y/2+.05f,-.06f);
    case "rotate":return p+new Vector3(Mathf.Cos(u*Mathf.PI*2)*(s.x/2+.10f),.12f,Mathf.Sin(u*Mathf.PI*2)*(s.z/2+.10f));
    case "grasp":return p+new Vector3(side*(s.x/2+.04f*(1-v)),0,-.04f);
    case "beat":return p+new Vector3(side*.18f,.18f+.04f*Mathf.Sin(u*Mathf.PI*8),-.14f);
    default:return p+new Vector3(side*(s.x/2+.12f),.08f,-.12f);
   }
  }
 }
 public class ArticulatedHand {
  public GameObject root;readonly Transform palm;readonly Transform[,] bones=new Transform[5,3];readonly bool left;readonly Material handMaterial;readonly Transform cubeProxy,sphereProxy,cylinderProxy;
  public ArticulatedHand(bool isLeft,Material material){left=isLeft;material=new Material(material);handMaterial=material;root=new GameObject(left?"Agent left hand":"Agent right hand");palm=Part("Rounded palm",PrimitiveType.Sphere,material);palm.localScale=new Vector3(.070f,.025f,.080f);var wrist=Part("Wrist",PrimitiveType.Capsule,material);wrist.localPosition=new Vector3(0,0,-.050f);wrist.localRotation=Quaternion.Euler(90,0,0);wrist.localScale=new Vector3(.038f,.023f,.025f);
   for(int f=0;f<5;f++)for(int j=0;j<3;j++){bones[f,j]=Part("Finger "+f+" phalanx "+j,PrimitiveType.Capsule,material);bones[f,j].localScale=new Vector3(.014f,.018f,.014f);}
   cubeProxy=Part("Explanatory cube proxy",PrimitiveType.Cube,material);sphereProxy=Part("Explanatory sphere proxy",PrimitiveType.Sphere,material);cylinderProxy=Part("Explanatory cylinder proxy",PrimitiveType.Cylinder,material);foreach(var proxy in new[]{cubeProxy,sphereProxy,cylinderProxy}){proxy.localPosition=new Vector3(0,0,.13f);proxy.localScale=Vector3.one*.07f;proxy.gameObject.SetActive(false);}
  }
  Transform Part(string name,PrimitiveType shape,Material material){var p=GameObject.CreatePrimitive(shape);p.name=name;UnityEngine.Object.Destroy(p.GetComponent<Collider>());p.transform.SetParent(root.transform,false);p.GetComponent<Renderer>().sharedMaterial=material;return p.transform;}
  public void BlendFrom(Vector3 p,Quaternion q,float weight){root.transform.position=Vector3.Lerp(p,root.transform.position,weight);root.transform.rotation=Quaternion.Slerp(q,root.transform.rotation,weight);}
  public void Set(GestureEvent e,RegisteredObject o,float t){root.SetActive(true);var p=GestureMath.Position(e,o,t,left);root.transform.position=p;
   Color tint=e.effect=="burn"?new Color(1,.28f,.08f):e.effect=="freeze"?new Color(.4f,.7f,1):e.effect=="poisoned"?new Color(.6f,.25f,.8f):e.effect=="spoil"?new Color(.45f,.55f,.2f):new Color(.18f,.58f,.65f);handMaterial.color=tint;if(e.effect=="glow"){handMaterial.EnableKeyword("_EMISSION");handMaterial.SetColor("_EmissionColor",tint*2);}else handMaterial.DisableKeyword("_EMISSION");
   Vector3 direction=o.Position-p;if(direction.sqrMagnitude<.001f)direction=Vector3.forward;
   root.transform.rotation=e.gesture=="present"?Quaternion.Euler(-90,0,0):Quaternion.LookRotation(direction,Vector3.up);
   foreach(var proxy in new[]{cubeProxy,sphereProxy,cylinderProxy})proxy.gameObject.SetActive(false);if(e.paperEvent=="ObjectProxy"||e.paperEvent=="Geometry2D"||e.paperEvent=="Geometry3D"){var proxy=e.pose=="sphere"?sphereProxy:e.pose=="cylinder"?cylinderProxy:cubeProxy;proxy.gameObject.SetActive(true);proxy.localScale=e.paperEvent=="Geometry2D"?new Vector3(.10f,.003f,.10f):Vector3.one*.07f;proxy.localRotation=Quaternion.Euler(0,(t-e.start)*45,0);}
   float phase=Mathf.Clamp01((t-e.start)/e.duration)*Mathf.PI*2;
   if(e.motion=="rollRotation")root.transform.Rotate(0,0,Mathf.Sin(phase)*35,Space.Self);if(e.motion=="pitchRotation")root.transform.Rotate(Mathf.Sin(phase)*35,0,0,Space.Self);if(e.motion=="yawRotation")root.transform.Rotate(0,Mathf.Sin(phase)*35,0,Space.Self);
   if(e.motion=="xTranslation")root.transform.position+=Vector3.right*Mathf.Sin(phase)*.06f;if(e.motion=="yTranslation")root.transform.position+=Vector3.up*Mathf.Sin(phase)*.06f;if(e.motion=="zTranslation")root.transform.position+=Vector3.forward*Mathf.Sin(phase)*.06f;if(e.pose=="thumbDown")root.transform.Rotate(0,0,180,Space.Self);
   for(int f=0;f<5;f++){
    float side=left?-1:1;Vector3 basePos=f==0?new Vector3(side*-.045f,-.003f,-.008f):new Vector3(side*((f-1.5f)*.020f),0,.035f);
    float bend=(e.pose=="point"||e.gesture=="point"||e.gesture=="trace")?(f==1?.04f:1.05f):e.pose=="fist"?1.2f:e.pose=="grab"||e.gesture=="grasp"?.65f:.12f;
    if(e.pose=="thumbUp"||e.pose=="thumbDown")bend=f==0?0:1.2f;
    if(e.pose=="one"||e.pose=="two"||e.pose=="three"){int count=e.pose=="one"?1:e.pose=="two"?2:3;bend=f>=1&&f<=count?0:1.2f;}
    Vector3 current=basePos;Quaternion rotation=f==0?Quaternion.Euler(0,side*-48,0):Quaternion.identity;
    for(int j=0;j<3;j++){rotation*=Quaternion.Euler(bend*42,0,0);float len=(f==0?.026f:.033f)*(1-j*.14f);Vector3 next=current+rotation*Vector3.forward*len;var b=bones[f,j];b.localPosition=(current+next)/2;b.localRotation=Quaternion.FromToRotation(Vector3.up,next-current);b.localScale=new Vector3(.014f,len/2+.006f,.014f);current=next;}
   }
  }
 }
 public class GestureRuntime {
  public GesturePlan Plan{get;private set;} readonly ArticulatedHand left,right;readonly Dictionary<string,RegisteredObject> objects=new();readonly Dictionary<string,float> contacts=new();float previous=-1;public string LastInteraction{get;private set;}="none";
  public string State{get;private set;}="idle"; public readonly GameObject Head; bool placed;Vector3 anchor;Quaternion idleOrientation=Quaternion.identity;float lastTime=-1;public string Diagnostics{get;private set;}="";
  public GestureRuntime(Material mat){left=new ArticulatedHand(true,mat);right=new ArticulatedHand(false,mat);Head=GameObject.CreatePrimitive(PrimitiveType.Sphere);Head.name="Agent glowing orb (paper section 3.3)";UnityEngine.Object.Destroy(Head.GetComponent<Collider>());Head.transform.localScale=Vector3.one*.12f;var m=new Material(mat);m.color=new Color(.25f,.8f,1);m.EnableKeyword("_EMISSION");m.SetColor("_EmissionColor",new Color(.2f,.7f,1)*1.3f);Head.GetComponent<Renderer>().sharedMaterial=m;}
  public void Place(Vector3 viewer,Vector3 forward,float dt=.1f){if(forward.sqrMagnitude<.01f)forward=Vector3.forward;var desired=viewer+forward.normalized*.85f;var rotation=Quaternion.LookRotation(forward.normalized,Vector3.up);float blend=1-Mathf.Exp(-Mathf.Max(.001f,dt)*9);anchor=placed?Vector3.Lerp(anchor,desired,blend):desired;idleOrientation=placed?Quaternion.Slerp(idleOrientation,rotation,blend):rotation;placed=true;}
  public void SetState(string state){State=state;}
  void Idle(ArticulatedHand h,bool isLeft,float t){var target=new RegisteredObject{id="idle",position=new[]{anchor.x,anchor.y-.25f,anchor.z},size=new[]{.25f,.10f,.1f}};h.Set(new GestureEvent{gesture="open",pose="palm",duration=100000,start=0},target,0);h.root.transform.position=anchor+idleOrientation*new Vector3(isLeft?-.18f:.18f,-.16f+Mathf.Sin(t*1.2f+(isLeft?0:1))*.008f,-.04f);h.root.transform.rotation=idleOrientation*Quaternion.Euler(-20,isLeft?-15:15,isLeft?-12:12);}

  public void Load(GesturePlan plan){if(plan.gaze)throw new ArgumentException("Gaze is excluded");objects.Clear();foreach(var o in plan.objects){if(o.position==null||o.position.Length!=3||o.size==null||o.size.Length!=3||objects.ContainsKey(o.id))throw new ArgumentException("Invalid object registry");objects.Add(o.id,o);}
   Diagnostics="";foreach(var e in plan.events){if(string.IsNullOrEmpty(e.id))e.id="event-"+Array.IndexOf(plan.events,e);if(e.targetId==null||!objects.ContainsKey(e.targetId)||e.duration<=0||e.start<0)Diagnostics+="Invalid/unresolved event: "+e.id+"\n";}Plan=plan;contacts.Clear();previous=-1;
  }
  public string Seek(float t,Vector3? userLeft=null,Vector3? userRight=null){
   if(t<previous){contacts.Clear();LastInteraction="reset-after-seek";}previous=t;if(!placed)Place(new Vector3(0,1.5f,0),Vector3.forward);
   var lp=left.root.transform.position;var lq=left.root.transform.rotation;var rp=right.root.transform.position;var rq=right.root.transform.rotation;float dt=lastTime<0||t<lastTime?1:Mathf.Max(0,t-lastTime);lastTime=t;float blend=1-Mathf.Exp(-dt*9);
   Idle(left,true,t);Idle(right,false,t);Head.transform.position=anchor+idleOrientation*Vector3.up*(.07f+Mathf.Sin(t*1.2f)*.006f);Head.transform.localScale=Vector3.one*(State=="thinking"?.12f+.008f*Mathf.Sin(t*4):.12f);
   string speech="";if(Plan==null){left.BlendFrom(lp,lq,blend);right.BlendFrom(rp,rq,blend);return speech;}bool any=false;
   foreach(var e in Plan.events){if(e.targetId==null||!objects.ContainsKey(e.targetId)||e.duration<=0||e.start<0)continue;bool interactive=!string.IsNullOrEmpty(e.interactivity)&&e.interactivity!="none";float timeout=interactive?Mathf.Max(e.duration,8):e.duration;if(t<e.start||t>=e.start+timeout)continue;
    bool hasContact=contacts.TryGetValue(e.id,out float contacted);float contactDuration=e.interactivity=="holdHand"?8:e.interactivity=="shakeHand"?2:.6f;if(interactive&&hasContact&&t-contacted>contactDuration)continue;
    any=true;var o=objects[e.targetId];if(e.hand=="left"||e.hand=="both")left.Set(e,o,t);if(e.hand=="right"||e.hand=="both")right.Set(e,o,t);speech=e.speech;
    if(interactive&&hasContact){Vector3? user=userRight??userLeft;if(user.HasValue&&e.interactivity=="holdHand"){if(e.hand=="left"||e.hand=="both")left.root.transform.position=user.Value+Vector3.up*.015f;if(e.hand=="right"||e.hand=="both")right.root.transform.position=user.Value+Vector3.up*.015f;}if(e.interactivity=="shakeHand"){Vector3 shake=Vector3.up*Mathf.Sin((t-contacted)*18)*.025f;if(e.hand=="left"||e.hand=="both")left.root.transform.position+=shake;if(e.hand=="right"||e.hand=="both")right.root.transform.position+=shake;}}
    if(interactive&&!contacts.ContainsKey(e.id)){
     bool hit=false;foreach(var user in new[]{userLeft,userRight}){if(!user.HasValue)continue;if((e.hand=="left"||e.hand=="both")&&Vector3.Distance(user.Value,left.root.transform.position)<.065f)hit=true;if((e.hand=="right"||e.hand=="both")&&Vector3.Distance(user.Value,right.root.transform.position)<.065f)hit=true;}
     if(hit){contacts[e.id]=t;LastInteraction=e.id+":contact";Debug.Log("AGENT_HANDS_CONTACT "+e.id+" t="+t);}else LastInteraction=e.id+":waiting-until-"+(e.start+timeout);
    }
   }if(State!="thinking"&&State!="listening")State=any?"gesturing":"idle";left.BlendFrom(lp,lq,blend);right.BlendFrom(rp,rq,blend);return speech;
  }
 }
}

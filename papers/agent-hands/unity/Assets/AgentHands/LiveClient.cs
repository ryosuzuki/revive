using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.XR;
using UnityEngine.XR.ARFoundation;
using Unity.XR.CoreUtils;
#if UNITY_ANDROID
using UnityEngine.Android;
#endif
namespace AgentHands {
 public class LiveClient:MonoBehaviour {
  [Serializable]class Config{public string server="";}
  [Serializable]class Request{public string audioBase64,question,mode;public RegisteredObject[] objects;public float[] position,head;}
  [Serializable]class Registration{public RegisteredObject @object;public string transcript;}
  Camera cam;GestureRuntime runtime;TextMesh status,caption;AudioSource speaker;AudioClip mic;bool recording,busy,lastA,lastTrigger;string captureMode;float startTime;Vector3 pendingPosition;readonly List<RegisteredObject> objects=new();Config config=new();
  [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]static void Boot(){if(!Application.isEditor)new GameObject("AgentHands live client").AddComponent<LiveClient>();}
  void Start(){Application.targetFrameRate=72;RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;RenderSettings.ambientLight=new Color(.45f,.48f,.52f);var keyLight=new GameObject("Agent hand key light").AddComponent<Light>();keyLight.type=LightType.Directional;keyLight.intensity=.8f;keyLight.transform.rotation=Quaternion.Euler(35,-30,0);
   var rig=new GameObject("AgentHands XR Origin");var o=new GameObject("Main Camera");o.tag="MainCamera";o.transform.SetParent(rig.transform);cam=o.AddComponent<Camera>();cam.nearClipPlane=.03f;cam.farClipPlane=30;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=Color.clear;o.AddComponent<AudioListener>();
   var origin=rig.AddComponent<XROrigin>();origin.Camera=cam;o.AddComponent<ARCameraManager>();new GameObject("AR Session").AddComponent<ARSession>();
   var subs=new List<XRInputSubsystem>();SubsystemManager.GetSubsystems(subs);foreach(var s in subs)s.TrySetTrackingOriginMode(TrackingOriginModeFlags.Floor);
   var material=Resources.Load<Material>("AgentHandMaterial");runtime=new GestureRuntime(material);speaker=o.AddComponent<AudioSource>();
   status=Label("Starting AgentHands…",.22f);caption=Label("",-.17f);
   var path=Path.Combine(Application.persistentDataPath,"server.json");if(File.Exists(path))config=JsonUtility.FromJson<Config>(File.ReadAllText(path));
#if UNITY_ANDROID
   if(!Permission.HasUserAuthorizedPermission(Permission.Microphone))Permission.RequestUserPermission(Permission.Microphone);
#endif
   Debug.Log("AGENT_HANDS_READY v0.1.1 gaze=false server="+config.server);UpdateStatus(string.IsNullOrWhiteSpace(config.server)?"Configure server.json with your private Wi-Fi backend URL, then relaunch.":"A hold: name an object at controller | Trigger hold: ask");
  }
  TextMesh Label(string text,float y){var g=new GameObject("AgentHands instruction");g.transform.SetParent(cam.transform,false);g.transform.localPosition=new Vector3(0,y,1.0f);var t=g.AddComponent<TextMesh>();t.font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");g.GetComponent<MeshRenderer>().sharedMaterial=t.font.material;t.fontSize=48;t.characterSize=.0024f;t.anchor=TextAnchor.MiddleCenter;t.alignment=TextAlignment.Center;t.text=text;return t;}
  void UpdateStatus(string text){status.text="AgentHands • No gaze\n"+text+"\nRegistered objects: "+objects.Count;Debug.Log("AGENT_HANDS_STATUS "+text);}
  void Update(){if(cam==null)return;var head=InputDevices.GetDeviceAtXRNode(XRNode.Head);if(head.TryGetFeatureValue(CommonUsages.devicePosition,out Vector3 hp))cam.transform.localPosition=hp;if(head.TryGetFeatureValue(CommonUsages.deviceRotation,out Quaternion hq))cam.transform.localRotation=hq;
   var dev=InputDevices.GetDeviceAtXRNode(XRNode.RightHand);dev.TryGetFeatureValue(CommonUsages.primaryButton,out bool a);dev.TryGetFeatureValue(CommonUsages.triggerButton,out bool trigger);
   if(!busy&&!recording){if(a&&!lastA){dev.TryGetFeatureValue(CommonUsages.devicePosition,out pendingPosition);BeginRecord("register");}else if(trigger&&!lastTrigger)BeginRecord("question");}
   if(recording&&((captureMode=="register"&&!a)||(captureMode=="question"&&!trigger)||Microphone.GetPosition(null)>=48000*19))EndRecord();lastA=a;lastTrigger=trigger;
   if(runtime.Plan!=null){float t=Time.time-startTime;string line=runtime.Seek(t,TrackedHand(XRNode.LeftHand),TrackedHand(XRNode.RightHand));caption.text=line.Length>0?line:(speaker.isPlaying?runtime.Plan.response:"");}
  }
  Vector3? TrackedHand(XRNode node){var dev=InputDevices.GetDeviceAtXRNode(node);if(dev.TryGetFeatureValue(CommonUsages.handData,out Hand hand)&&hand.TryGetRootBone(out Bone bone)&&bone.TryGetPosition(out Vector3 p))return p;return null;}
  void BeginRecord(string mode){if(string.IsNullOrWhiteSpace(config.server)){UpdateStatus("Configure server.json with your private backend URL, then relaunch.");return;}if(Microphone.devices.Length==0){UpdateStatus("Microphone unavailable. Check permission.");return;}captureMode=mode;mic=Microphone.Start(null,false,20,48000);recording=true;UpdateStatus(mode=="register"?"Say the name of the object at your controller. Release A.":"Ask about registered objects. Release trigger.");}
  void EndRecord(){int count=Microphone.GetPosition(null);Microphone.End(null);recording=false;if(count<4800){UpdateStatus("Speech too short. Hold and speak again.");return;}float[] samples=new float[count*mic.channels];mic.GetData(samples,0);var data=Wav(samples,mic.frequency,mic.channels);StartCoroutine(Send(data));}
  IEnumerator Send(byte[] wav){busy=true;UpdateStatus("Listening / generating spatial response…");var request=new Request{audioBase64=Convert.ToBase64String(wav),question="",mode=captureMode,objects=objects.ToArray(),position=new[]{pendingPosition.x,pendingPosition.y,pendingPosition.z},head=new[]{cam.transform.position.x,cam.transform.position.y,cam.transform.position.z}};
   using(var web=new UnityWebRequest(config.server+"/dialogue","POST")){web.uploadHandler=new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(JsonUtility.ToJson(request)));web.downloadHandler=new DownloadHandlerBuffer();web.SetRequestHeader("Content-Type","application/json");web.timeout=180;yield return web.SendWebRequest();
    if(web.result!=UnityWebRequest.Result.Success){busy=false;UpdateStatus("Connection failed: "+web.error+"\nCheck Wi-Fi and server.json; registry retained.");yield break;}
    if(captureMode=="register"){var r=JsonUtility.FromJson<Registration>(web.downloadHandler.text);if(r.@object!=null){objects.Add(r.@object);UpdateStatus("Registered: "+r.@object.label+". Trigger: ask a question.");}busy=false;yield break;}
    GesturePlan plan=null;try{plan=JsonUtility.FromJson<GesturePlan>(web.downloadHandler.text);runtime.Load(plan);}catch(Exception e){busy=false;UpdateStatus("Invalid generated response: "+e.Message);yield break;}
    if(!string.IsNullOrEmpty(plan.audioUrl)){using(var audio=UnityWebRequestMultimedia.GetAudioClip(config.server+plan.audioUrl,AudioType.WAV)){yield return audio.SendWebRequest();if(audio.result==UnityWebRequest.Result.Success){speaker.clip=DownloadHandlerAudioClip.GetContent(audio);speaker.Play();}}}
    startTime=Time.time;UpdateStatus("Speaking with spatial hands. A: register another object.");Debug.Log("AGENT_HANDS_PLAN events="+plan.events.Length+" objects="+plan.objects.Length+" gaze=false");
   }busy=false;
  }
  static byte[] Wav(float[] samples,int rate,int channels){using var stream=new MemoryStream();using var w=new BinaryWriter(stream);w.Write(System.Text.Encoding.ASCII.GetBytes("RIFF"));w.Write(36+samples.Length*2);w.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt "));w.Write(16);w.Write((short)1);w.Write((short)channels);w.Write(rate);w.Write(rate*channels*2);w.Write((short)(channels*2));w.Write((short)16);w.Write(System.Text.Encoding.ASCII.GetBytes("data"));w.Write(samples.Length*2);foreach(float x in samples)w.Write((short)(Mathf.Clamp(x,-1,1)*32767));return stream.ToArray();}
 }
}

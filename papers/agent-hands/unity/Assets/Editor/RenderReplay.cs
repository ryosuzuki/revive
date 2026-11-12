using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using AgentHands;
public class RenderReplay {
 [Serializable]class K{public int width,height;public float fx,fy,cx,cy;}
 [Serializable]class Frame{public float time;public float[] position,rotation,leftUserHand,rightUserHand;public string image;}
 [Serializable]class Session{public string id;public K intrinsics;public Frame[] frames;}
 [Serializable]class Room{public Part[] parts;}
 [Serializable]class Part{public string label;public float[] vertices;public int[] triangles;}
 static Vector3? Hand(float[] p){return p!=null&&p.Length==3?new Vector3(p[0],p[1],p[2]):(Vector3?)null;}
 public static void Run(){BuildAgentHands.Assets();EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
  string path=Environment.GetEnvironmentVariable("AGENT_HANDS_SESSION"),planPath=Environment.GetEnvironmentVariable("AGENT_HANDS_PLAN"),output=Environment.GetEnvironmentVariable("AGENT_HANDS_RENDER");if(string.IsNullOrEmpty(path)||string.IsNullOrEmpty(output)||string.IsNullOrEmpty(planPath))throw new Exception("Explicit render paths required");Directory.CreateDirectory(output);
  var session=JsonUtility.FromJson<Session>(File.ReadAllText(Path.Combine(path,"session.json")));var plan=JsonUtility.FromJson<GesturePlan>(File.ReadAllText(planPath));var rt=new GestureRuntime(Resources.Load<Material>("AgentHandMaterial"));rt.Load(plan);
  var cam=new GameObject("Calibrated capture camera").AddComponent<Camera>();cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=Color.clear;cam.nearClipPlane=.03f;cam.farClipPlane=30;cam.allowHDR=false;cam.allowMSAA=false;
  var k=session.intrinsics;var matrix=new Matrix4x4();matrix[0,0]=2*k.fx/k.width;matrix[0,2]=1-2*k.cx/k.width;matrix[1,1]=2*k.fy/k.height;matrix[1,2]=2*k.cy/k.height-1;matrix[2,2]=-(cam.farClipPlane+cam.nearClipPlane)/(cam.farClipPlane-cam.nearClipPlane);matrix[2,3]=-2*cam.farClipPlane*cam.nearClipPlane/(cam.farClipPlane-cam.nearClipPlane);matrix[3,2]=-1;cam.projectionMatrix=matrix;
  // Measured room-mesh occlusion is optional and disclosed; no dynamic-object/hand masks are fabricated.
  var roomPath=Path.Combine(path,"room-geometry.json");if(File.Exists(roomPath)&&Environment.GetEnvironmentVariable("AGENT_HANDS_ROOM_OCCLUSION")=="1"){
   var room=JsonUtility.FromJson<Room>(File.ReadAllText(roomPath));var depth=new Material(Shader.Find("AgentHands/MeasuredRoomDepth"));
   foreach(var part in room.parts){if(part.label!="GLOBAL_MESH")continue;var g=new GameObject("Measured room depth");var mesh=new Mesh{indexFormat=IndexFormat.UInt32};var vs=new Vector3[part.vertices.Length/3];for(int i=0;i<vs.Length;i++)vs[i]=new Vector3(part.vertices[i*3],part.vertices[i*3+1],-part.vertices[i*3+2]);mesh.vertices=vs;mesh.triangles=part.triangles;mesh.RecalculateBounds();g.AddComponent<MeshFilter>().sharedMesh=mesh;g.AddComponent<MeshRenderer>().sharedMaterial=depth;}
  }
  RenderSettings.ambientMode=AmbientMode.Flat;RenderSettings.ambientLight=new Color(.45f,.48f,.52f);var light=new GameObject("Key light").AddComponent<Light>();light.type=LightType.Directional;light.intensity=.8f;light.transform.rotation=Quaternion.Euler(35,-30,0);
  var target=new RenderTexture(k.width,k.height,24,RenderTextureFormat.ARGB32);cam.targetTexture=target;var tex=new Texture2D(k.width,k.height,TextureFormat.RGBA32,false);
  float origin=0;float.TryParse(Environment.GetEnvironmentVariable("AGENT_HANDS_RESPONSE_START"),out origin);
  for(int i=0;i<session.frames.Length;i++){var f=session.frames[i];cam.transform.position=new Vector3(f.position[0],f.position[1],f.position[2]);cam.transform.rotation=new Quaternion(f.rotation[0],f.rotation[1],f.rotation[2],f.rotation[3]);rt.Place(cam.transform.position,cam.transform.forward,i>0?f.time-session.frames[i-1].time:.1f);rt.Seek(f.time-origin,Hand(f.leftUserHand),Hand(f.rightUserHand));cam.Render();RenderTexture.active=target;tex.ReadPixels(new Rect(0,0,k.width,k.height),0,0);tex.Apply();File.WriteAllBytes(Path.Combine(output,i.ToString("D5")+".png"),tex.EncodeToPNG());}
  RenderTexture.active=null;cam.targetTexture=null;UnityEngine.Object.DestroyImmediate(tex);UnityEngine.Object.DestroyImmediate(target);Debug.Log("AGENT_HANDS_RENDERED frames="+session.frames.Length+" session="+session.id+" gaze=false");
 }
}

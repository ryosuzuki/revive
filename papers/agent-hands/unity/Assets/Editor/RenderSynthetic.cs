using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using AgentHands;
// Explicit public synthetic fixture: no sensor data, VLM output or physical accuracy claims.
public class RenderSynthetic {
 public static void Run(){
  string output=Environment.GetEnvironmentVariable("REVIVE_SYNTHETIC_OUTPUT");
  if(string.IsNullOrEmpty(output))throw new Exception("REVIVE_SYNTHETIC_OUTPUT required");Directory.CreateDirectory(output);
  BuildAgentHands.Assets();EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
  var cam=new GameObject("Synthetic camera").AddComponent<Camera>();cam.transform.position=new Vector3(0,.08f,-1.0f);cam.transform.rotation=Quaternion.identity;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.045f,.07f,.10f);cam.fieldOfView=48;cam.nearClipPlane=.03f;
  RenderSettings.ambientMode=AmbientMode.Flat;RenderSettings.ambientLight=new Color(.48f,.50f,.55f);var light=new GameObject("Synthetic key").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1;light.transform.rotation=Quaternion.Euler(40,-25,0);
  var obj=new RegisteredObject{id="fixture-box",label="Synthetic box",position=new[]{0f,0f,.25f},size=new[]{.18f,.22f,.16f},registration="synthetic-fixture"};
  var cube=GameObject.CreatePrimitive(PrimitiveType.Cube);cube.name="Synthetic fixture box";cube.transform.position=obj.Position;cube.transform.localScale=obj.Size;cube.GetComponent<Renderer>().material.color=new Color(.85f,.57f,.23f);
  var plan=new GesturePlan{objects=new[]{obj},response="Synthetic point, presentation, measurement and rotation fixture.",events=new[]{
   new GestureEvent{id="synthetic-0",interactivity="none",start=0,duration=2,gesture="point",pose="point",targetId=obj.id,hand="right"},
   new GestureEvent{id="synthetic-1",interactivity="none",start=2,duration=2,gesture="present",pose="palm",targetId=obj.id,hand="left"},
   new GestureEvent{id="synthetic-2",interactivity="none",start=4,duration=2,gesture="measure",pose="palm",targetId=obj.id,hand="both"},
   new GestureEvent{id="synthetic-3",interactivity="none",start=6,duration=2,gesture="rotate",pose="point",targetId=obj.id,hand="right"}}};
  var rt=new GestureRuntime(Resources.Load<Material>("AgentHandMaterial"));rt.Load(plan);var target=new RenderTexture(960,720,24,RenderTextureFormat.ARGB32);cam.targetTexture=target;var tex=new Texture2D(960,720,TextureFormat.RGBA32,false);
  for(int i=0;i<160;i++){rt.Seek(i/20f);cam.Render();RenderTexture.active=target;tex.ReadPixels(new Rect(0,0,960,720),0,0);tex.Apply();File.WriteAllBytes(Path.Combine(output,i.ToString("D5")+".png"),tex.EncodeToPNG());}
  RenderTexture.active=null;Debug.Log("REVIVE_SYNTHETIC_RENDERED frames=160 gaze=false");
 }
}

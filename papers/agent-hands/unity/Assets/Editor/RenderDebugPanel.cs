using System;
using System.IO;
using AgentHands;
using UnityEditor.SceneManagement;
using UnityEngine;
// Renders the actual world-space headset panel, not a composited imitation.
// Input model plan is explicit; this is software preview, never device acceptance.
public class RenderDebugPanel {
 public static void Run(){
  string input=Environment.GetEnvironmentVariable("AGENT_HANDS_DEBUG_PLAN"),output=Environment.GetEnvironmentVariable("AGENT_HANDS_DEBUG_IMAGE");if(string.IsNullOrEmpty(input)||string.IsNullOrEmpty(output))throw new Exception("Explicit input/output required");BuildAgentHands.Assets();EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
  var camera=new GameObject("Panel preview camera").AddComponent<Camera>();camera.tag="MainCamera";camera.transform.position=new Vector3(0,1.5f,0);camera.fieldOfView=60;camera.backgroundColor=new Color(.025f,.04f,.065f);camera.clearFlags=CameraClearFlags.SolidColor;camera.nearClipPlane=.03f;
  RenderSettings.ambientLight=Color.white;var runtime=new GestureRuntime(Resources.Load<Material>("AgentHandMaterial"));runtime.Load(JsonUtility.FromJson<GesturePlan>(File.ReadAllText(input)));runtime.Place(camera.transform.position,camera.transform.forward);runtime.Seek(2);
  var panel=new GameObject("Actual native debug UI").AddComponent<GestureDebugPanel>();panel.Runtime=runtime;panel.Visible=true;panel.TrackingStatus="Software preview; no headset tracking";panel.PlaybackTime=2;panel.SendMessage("LateUpdate");
  var target=new RenderTexture(1280,1280,24,RenderTextureFormat.ARGB32);camera.targetTexture=target;camera.Render();RenderTexture.active=target;var image=new Texture2D(1280,1280,TextureFormat.RGBA32,false);image.ReadPixels(new Rect(0,0,1280,1280),0,0);image.Apply();File.WriteAllBytes(output,image.EncodeToPNG());RenderTexture.active=null;Debug.Log("NATIVE_DEBUG_PANEL_RENDERED software-preview-only");
 }
}

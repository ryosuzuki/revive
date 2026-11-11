using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.XR.Management;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEngine.XR.OpenXR;
using UnityEngine.XR.OpenXR.Features;
using UnityEditor.XR.OpenXR.Features;
public class BuildAgentHands {
 public static void Android(){
  Assets();PlayerSettings.companyName="Programmable Reality Lab";PlayerSettings.productName="AgentHands";PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.Android,"org.prlab.agenthands");PlayerSettings.bundleVersion="0.1.1";PlayerSettings.Android.bundleVersionCode=2;
  PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Android,ScriptingImplementation.IL2CPP);PlayerSettings.Android.targetArchitectures=AndroidArchitecture.ARM64;PlayerSettings.Android.minSdkVersion=AndroidSdkVersions.AndroidApiLevel32;PlayerSettings.Android.targetSdkVersion=AndroidSdkVersions.AndroidApiLevelAuto;
  PlayerSettings.Android.forceInternetPermission=true;PlayerSettings.insecureHttpOption=InsecureHttpOption.DevelopmentOnly;
  var serialized=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset")[0]);var input=serialized.FindProperty("activeInputHandler");if(input!=null){input.intValue=2;serialized.ApplyModifiedPropertiesWithoutUndo();}
  PlayerSettings.colorSpace=ColorSpace.Linear;PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android,false);PlayerSettings.SetGraphicsAPIs(BuildTarget.Android,new[]{GraphicsDeviceType.OpenGLES3});PlayerSettings.stereoRenderingPath=StereoRenderingPath.Instancing;
  var per=AssetDatabase.LoadAssetAtPath<XRGeneralSettingsPerBuildTarget>("Assets/XRGeneralSettings.asset");if(per==null){per=ScriptableObject.CreateInstance<XRGeneralSettingsPerBuildTarget>();AssetDatabase.CreateAsset(per,"Assets/XRGeneralSettings.asset");}
  var general=per.SettingsForBuildTarget(BuildTargetGroup.Android);if(general==null){general=ScriptableObject.CreateInstance<XRGeneralSettings>();AssetDatabase.AddObjectToAsset(general,per);per.SetSettingsForBuildTarget(BuildTargetGroup.Android,general);}
  if(general.Manager==null){var manager=ScriptableObject.CreateInstance<XRManagerSettings>();AssetDatabase.AddObjectToAsset(manager,per);general.Manager=manager;}general.InitManagerOnStart=true;EditorBuildSettings.AddConfigObject("com.unity.xr.management.loader_settings",per,true);
  if(!XRPackageMetadataStore.AssignLoader(general.Manager,"UnityEngine.XR.OpenXR.OpenXRLoader",BuildTargetGroup.Android))throw new Exception("OpenXR loader failed");
  FeatureHelpers.RefreshFeatures(BuildTargetGroup.Android);var settings=OpenXRSettings.GetSettingsForBuildTargetGroup(BuildTargetGroup.Android);settings.renderMode=OpenXRSettings.RenderMode.SinglePassInstanced;
  foreach(var f in settings.GetFeatures<OpenXRFeature>()){string t=f.GetType().FullName;if(t.Contains("OculusTouchControllerProfile")||t.Contains("MetaQuestFeature")||t.EndsWith("ARCameraFeature")||t.EndsWith("ARSessionFeature")||t.EndsWith("OpenXRCompositionLayersFeature"))f.enabled=true;}
  EditorUtility.SetDirty(per);EditorUtility.SetDirty(settings);AssetDatabase.SaveAssets();
  var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);EditorSceneManager.SaveScene(scene,"Assets/AgentHands.unity");EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene("Assets/AgentHands.unity",true)};
  string path=Environment.GetEnvironmentVariable("AGENT_HANDS_APK")??"Builds/agent-hands.apk";Directory.CreateDirectory(Path.GetDirectoryName(path));
  var result=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{"Assets/AgentHands.unity"},locationPathName=path,target=BuildTarget.Android,options=BuildOptions.Development});
  Debug.Log("AGENT_HANDS_BUILD "+result.summary.result+" bytes="+result.summary.totalSize);if(result.summary.result!=BuildResult.Succeeded)throw new Exception("Android build failed");
 }
 public static void Assets(){if(AssetDatabase.LoadAssetAtPath<Material>("Assets/Resources/AgentHandMaterial.mat")==null){var m=new Material(Shader.Find("Standard"));m.color=new Color(.12f,.78f,.84f);m.SetFloat("_Glossiness",.35f);AssetDatabase.CreateAsset(m,"Assets/Resources/AgentHandMaterial.mat");}AssetDatabase.SaveAssets();}
}

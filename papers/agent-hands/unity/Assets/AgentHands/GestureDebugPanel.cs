using System;
using UnityEngine;
namespace AgentHands {
// World-space text also renders in stereo; no IMGUI-only headset panel.
public class GestureDebugPanel:MonoBehaviour {
 public GestureRuntime Runtime;public float PlaybackTime;public bool Visible=true;public string RawOverride;TextMesh text;
 void LateUpdate(){if(Camera.main==null||Runtime==null)return;if(text==null){var g=new GameObject("GestureEvent debug panel");g.transform.SetParent(Camera.main.transform,false);g.transform.localPosition=new Vector3(-.48f,.38f,1.15f);text=g.AddComponent<TextMesh>();text.font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");g.GetComponent<MeshRenderer>().sharedMaterial=text.font.material;text.characterSize=.0014f;text.fontSize=36;text.anchor=TextAnchor.UpperLeft;}
 text.gameObject.SetActive(Visible);if(!Visible)return;var p=Runtime.Plan;string raw=RawOverride??p?.tagged??"(No model response yet)";string words=p?.response??"";var tokens=words.Split(' ');float end=0;if(p!=null)foreach(var e in p.events)end=Mathf.Max(end,e.start+e.duration);int current=Mathf.Clamp((int)(PlaybackTime/Mathf.Max(.1f,end)*tokens.Length),0,Mathf.Max(0,tokens.Length-1));string active="";if(p!=null)foreach(var e in p.events)if(PlaybackTime>=e.start&&PlaybackTime<e.start+e.duration)active+=e.id+" -> "+e.targetId+" / "+e.hand+"\n";
 text.text="GestureEvent debug | X toggle | "+Runtime.State+"\nRAW MODEL (before TTS stripping):\n"+Wrap(raw,75)+"\nPARSED ACTIVE EVENTS:\n"+active+"\nCURRENT WORD (heuristic, not forced alignment):\n"+(tokens.Length>0?tokens[current]:"")+"\nDIAGNOSTICS:\n"+Runtime.Diagnostics;
 }
 static string Wrap(string s,int width){var b=new System.Text.StringBuilder();int col=0;foreach(char c in s){b.Append(c);if(c=='\n')col=0;else if(++col>=width){b.Append('\n');col=0;}}return b.ToString();}
}}

using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEngine;
namespace AgentHands {
public static class DirectPlanParser {
 public static GesturePlan Parse(string raw,RegisteredObject[] registry,Vector3 head,float duration){
 var plan=new GesturePlan{tagged=raw,objects=registry,response=Regex.Replace(raw,@"\[[^\]]*\]",""),alignment="word-position heuristic, not forced alignment"};var objects=new List<RegisteredObject>(registry);objects.Add(new RegisteredObject{id="agent-midair",label="Agent gesture space",position=new[]{head.x,head.y-.25f,head.z+.65f},size=new[]{.18f,.18f,.1f}});plan.objects=objects.ToArray();var events=new List<GestureEvent>();int removed=0,sequence=0;foreach(Match m in Regex.Matches(raw,@"\[([A-Za-z0-9]+)(?:;([^\[\]]*))?\]")){var attrs=new Dictionary<string,string>();foreach(var part in m.Groups[2].Value.Split(',')){int i=part.IndexOf(':');if(i>0)attrs[part.Substring(0,i).Trim()]=part.Substring(i+1).Trim();}string kind=m.Groups[1].Value,target=attrs.ContainsKey("object")?attrs["object"]:"agent-midair";float start=(float)(m.Index-removed)/Math.Max(1,plan.response.Length)*duration;removed+=m.Length;string gesture;switch(kind){case "PointObject":case "RegionOfObject":gesture="point";break;case "DirectionOfObject":gesture="trace";break;case "Action":gesture="grasp";break;case "ObjectProxy":gesture="rotate";break;case "Comparison":case "Geometry1D":case "Geometry2D":case "Geometry3D":gesture="measure";break;case "Attention":case "Prohibition":case "StopExpression":gesture="beat";break;case "Positive":case "ThumbupExpression":case "Negative":case "Numeric":case "Celebration":case "Burn":case "BurnEffect":case "Poisoned":case "Spoil":gesture="open";break;default:throw new ArgumentException("Unsupported GestureEvent "+kind);}
 string pose=attrs.ContainsKey("gesture")?attrs["gesture"]:gesture=="point"?"point":"palm";if(kind=="Positive"||kind=="ThumbupExpression")pose="thumbUp";if(kind=="Negative")pose="thumbDown";events.Add(new GestureEvent{id="event-"+sequence++,paperEvent=kind,targetId=target,start=start,duration=Mathf.Max(.05f,Mathf.Min(2.5f,duration-start)),hand=attrs.ContainsKey("handedness")&&attrs["handedness"]=="double"||gesture=="measure"?"both":"right",gesture=gesture,pose=pose,motion=attrs.ContainsKey("dynamics")?attrs["dynamics"]:"static",effect=attrs.ContainsKey("vfx")?attrs["vfx"]:"none",interactivity=attrs.ContainsKey("interactivity")?attrs["interactivity"]:kind=="Celebration"?"highFive":"none",speech=plan.response});}
 plan.events=events.ToArray();return plan;
 }
}
}

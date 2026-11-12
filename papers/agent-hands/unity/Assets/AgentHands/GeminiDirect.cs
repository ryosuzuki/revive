using System;
using System.Collections;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
namespace AgentHands {
// Key is read only from app-private persistent data and sent only in HTTPS headers
// to the fixed Google provider origin. Never send it to the LAN backend.
public class GeminiDirect {
 public const string PaperResponseModel="gemini-2.5-flash-exp",PaperTtsModel="gemini-2.5-flash-preview-tts";
 [Serializable] public class ModelConfig{public string responseModel=PaperResponseModel,ttsModel=PaperTtsModel;public bool approvedReplacement=false;}
 [Serializable] class Part{public string text;public Inline inlineData;}
 [Serializable] class Inline{public string mimeType,data;}
 [Serializable] class Content{public string role="user";public Part[] parts;}
 [Serializable] class Generation{public string[] responseModalities;public Speech speechConfig;}
 [Serializable] class Speech{public Voice voiceConfig=new Voice();}
 [Serializable] class Voice{public Prebuilt prebuiltVoiceConfig=new Prebuilt();}
 [Serializable] class Prebuilt{public string voiceName="Kore";}
 [Serializable] class Payload{public Content[] contents;public Generation generationConfig;}
 [Serializable] class Candidate{public Content content;}
 [Serializable] class Response{public Candidate[] candidates;}
 public string Error{get;private set;} public string Text{get;private set;}public AudioClip Audio{get;private set;}public ModelConfig Config{get;private set;}=new ModelConfig();
 readonly string root;public GeminiDirect(string dataRoot=null){root=dataRoot??Application.persistentDataPath;}string key;
 public bool Load(){Error=null;key=null;try{string p=Path.Combine(root,"api_key.txt");if(!File.Exists(p)){Error="Missing api_key.txt. See setup instructions.";return false;}key=File.ReadAllText(p).Trim();if(string.IsNullOrEmpty(key)){Error="api_key.txt is empty.";return false;}if(key.Length>512||key.IndexOfAny(new[]{'\r','\n'})>=0){key=null;Error="Invalid API key file format.";return false;}string c=Path.Combine(root,"models.json");Config=File.Exists(c)?JsonUtility.FromJson<ModelConfig>(File.ReadAllText(c)):new ModelConfig();if(Config==null||!SafeModel(Config.responseModel)||!SafeModel(Config.ttsModel)){Error="Invalid model configuration.";return false;}if((Config.responseModel!=PaperResponseModel||Config.ttsModel!=PaperTtsModel)&&!Config.approvedReplacement){Error="Replacement models require explicit approval in models.json.";return false;}return true;}catch{key=null;Error="Could not read app API configuration.";return false;}}
 static bool SafeModel(string id){return !string.IsNullOrEmpty(id)&&System.Text.RegularExpressions.Regex.IsMatch(id,@"\A[a-zA-Z0-9.-]+\z");}
 public IEnumerator Generate(string prompt,byte[] wav=null,bool tts=false){Error=null;Text=null;Audio=null;if(key==null&&!Load())yield break;var parts=wav==null?new[]{new Part{text=prompt}}:new[]{new Part{text=prompt},new Part{inlineData=new Inline{mimeType="audio/wav",data=Convert.ToBase64String(wav)}}};var payload=new Payload{contents=new[]{new Content{parts=parts}},generationConfig=tts?new Generation{responseModalities=new[]{"AUDIO"},speechConfig=new Speech()}:null};string model=tts?Config.ttsModel:Config.responseModel;
 using(var req=new UnityWebRequest("https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent","POST")){req.uploadHandler=new UploadHandlerRaw(Encoding.UTF8.GetBytes(JsonUtility.ToJson(payload)));req.downloadHandler=new DownloadHandlerBuffer();req.SetRequestHeader("Content-Type","application/json");req.SetRequestHeader("x-goog-api-key",key);req.timeout=120;req.redirectLimit=0;yield return req.SendWebRequest();if(req.result!=UnityWebRequest.Result.Success){Error=req.responseCode==401||req.responseCode==403?"API key rejected or permission denied.":req.responseCode==404?"Configured model unavailable; replacement needs approval.":"Provider request failed (HTTP "+req.responseCode+").";yield break;}try{var response=JsonUtility.FromJson<Response>(req.downloadHandler.text);var reply=response.candidates[0].content.parts;var text=new StringBuilder();foreach(var part in reply){if(part.text!=null)text.Append(part.text);if(tts&&part.inlineData!=null){if(!part.inlineData.mimeType.StartsWith("audio/L16")&&!part.inlineData.mimeType.StartsWith("audio/pcm"))throw new Exception();var pcm=Convert.FromBase64String(part.inlineData.data);var samples=new float[pcm.Length/2];for(int i=0;i<samples.Length;i++)samples[i]=(short)(pcm[2*i]|pcm[2*i+1]<<8)/32768f;int rate=24000;var match=System.Text.RegularExpressions.Regex.Match(part.inlineData.mimeType,@"rate=(\d+)");if(match.Success)rate=int.Parse(match.Groups[1].Value);Audio=AudioClip.Create("Provider speech",samples.Length,1,rate,false);Audio.SetData(samples,0);}}Text=text.ToString().Replace(key,"[REDACTED]");if(tts&&Audio==null)Error="Provider returned no supported audio.";if(!tts&&string.IsNullOrWhiteSpace(Text))Error="Provider returned no text.";}catch{Error="Malformed provider response (details withheld).";}}
 }
}
}

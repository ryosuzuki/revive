#!/usr/bin/env python3
import argparse,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agent_hands.capture import unpack,import_take
p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('output');a=p.parse_args()
out=Path(a.output); takes=unpack(a.archive,out/'original')
for take in takes:
 if (take/'left_camera_mruk_intrinsics.json').exists():
  s=import_take(take,out/'sessions'/take.name);print(json.dumps({k:s[k] for k in ['id','duration','sourceFrames','audioOffset']}),flush=True)

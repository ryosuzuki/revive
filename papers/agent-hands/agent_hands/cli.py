import argparse

def main():
 p=argparse.ArgumentParser(prog='agent-hands');commands=p.add_subparsers(dest='command',required=True)
 server=commands.add_parser('serve');server.add_argument('--host',default='127.0.0.1');server.add_argument('--port',type=int,default=18311)
 importer=commands.add_parser('import');importer.add_argument('archive');importer.add_argument('output')
 args=p.parse_args()
 if args.command=='serve':
  import uvicorn
  uvicorn.run('agent_hands.server:app',host=args.host,port=args.port)
 else:
  from pathlib import Path
  from .capture import unpack,import_take
  out=Path(args.output)
  for take in unpack(args.archive,out/'original'):
   if (take/'left_camera_mruk_intrinsics.json').exists():print(import_take(take,out/'sessions'/take.name)['id'])
if __name__=='__main__':main()

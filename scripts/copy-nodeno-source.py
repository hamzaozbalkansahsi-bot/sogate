#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/copy-nodeno-source.py
# Açıklama   : Güncel NODENO uygulama kodunu değiştirmeden ve işletme verisi taşımadan kopyalar.
import argparse,hashlib,json,os,secrets,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
from native_fixture_safety import safe_fixture

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT.parent/'Nodeno';TARGET=ROOT/'native-store/upstream'
parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');args=parser.parse_args()
record=ROOT/'native-store/source-manifest.json';previous=json.loads(record.read_text('utf8')) if record.exists() else {'files':{}}
backup=Path('D:/sexogate-local-artifacts-20261114/private-installs')/('native-capture-backup-'+secrets.token_hex(8))
AREAS={'web','hosting','lib','scripts','tests','docs'}
CODE={'.js','.mjs','.cjs','.php','.py','.css','.html','.md','.sql','.ts','.tsx','.jsx'}
PUBLIC={'.svg','.woff','.woff2','.ttf','.webmanifest','.txt'}
def allowed(path):
 rel=path.relative_to(SOURCE);parts=rel.parts
 if any(part in {'.git','node_modules','__pycache__','artifacts','dist','output','outputs','tmp','cache','private','storage'} for part in parts):return False
 if any(part.startswith(('.env','client_secret')) or part.endswith('.local') for part in parts):return False
 if len(parts)==1:return rel.name in {'package.json','README.md','requirements-catalog.txt'}
 if parts[0]=='data':return rel.as_posix() in {'data/date-time-regions.json','data/store-locales.json'}
 if parts[0] not in AREAS:return False
 if parts[0]=='web' and 'locales' in parts:return path.suffix=='.json' and '.catalogue.' not in path.name
 if parts[0]=='web' and 'assets' in parts and any(p in parts for p in ['suppliers','blog','doors','fronts','products','social']):return False
 if rel.as_posix()=='hosting/.htaccess':return True
 return path.suffix.lower() in CODE or parts[0]=='web' and path.suffix.lower() in PUBLIC

assert SOURCE.is_dir() and (SOURCE/'hosting/index.php').is_file()
assert TARGET.resolve().is_relative_to(ROOT.resolve()) and not TARGET.is_symlink()
files=[p for p in SOURCE.iterdir() if p.is_file() and allowed(p)]
for area in sorted(AREAS|{'data'}):
 for directory,folders,names in os.walk(SOURCE/area,followlinks=False):
  folders[:]=[name for name in folders if name not in {'node_modules','__pycache__','artifacts','dist','output','outputs','tmp','cache','private','storage'} and not name.startswith('.') and not Path(directory,name).is_symlink()]
  if area=='web':folders[:]=[name for name in folders if name not in {'suppliers','blog','doors','fronts','products','social'}]
  if area=='data':folders[:]=[]
  files.extend(p for name in names if (p:=Path(directory,name)).is_file() and allowed(p))
files.sort();manifest={};total=0;source_total=0;sanitizations={}
for path in files:
 if path.is_symlink():raise RuntimeError('SOURCE_SYMLINK_REJECTED')
 rel=path.relative_to(SOURCE);original=path.read_bytes();raw=safe_fixture(rel.as_posix(),original);source_total+=len(original);sha=hashlib.sha256(raw).hexdigest();dest=TARGET/rel
 if raw!=original:sanitizations[rel.as_posix()]={'sourceSha256':hashlib.sha256(original).hexdigest(),'safeSha256':sha,'reason':'Explicit synthetic Stripe fixture literal replaced with runtime-generated dummy value; no application code change'}
 if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()!=sha:
  if not args.refresh or hashlib.sha256(dest.read_bytes()).hexdigest()!=previous['files'].get(rel.as_posix()):raise RuntimeError('EXISTING_COPY_CHANGED: '+rel.as_posix())
  saved=backup/rel;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,saved)
  if record.exists() and not (backup/'source-manifest.json').exists():shutil.copy2(record,backup/'source-manifest.json')
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);manifest[rel.as_posix()]=sha;total+=len(raw)
report={'source':'Nodeno current working tree','sourceCommit':subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip(),'capturedAt':datetime.now(timezone.utc).isoformat(),'workingTreeIncluded':True,'sourceChanged':False,'themeChangesInSource':False,'businessDataCopied':False,'bytes':total,'sourceBytes':source_total,'fixtureSanitizations':sanitizations,'files':manifest}
(ROOT/'native-store/source-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'copiedFiles':len(files),'bytes':total,'byteIdenticalFiles':len(files)-len(sanitizations),'syntheticFixtureExceptions':len(sanitizations),'sourceChanged':False,'customerOrSecretFilesCopied':False}))

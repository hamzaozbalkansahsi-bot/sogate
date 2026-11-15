"""Lossless, hash-verified compression of this task's own captured HTML only."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/supplier-expansion';saved=0;count=0
for directory in ['altinis-pages','alka-visible-pages']:
 folder=(OUT/directory).resolve()
 assert folder.is_relative_to(OUT.resolve())
 for file in folder.glob('*.html'):
  assert not file.is_symlink()and file.resolve().parent==folder
  raw=file.read_bytes()
  if not raw or raw.startswith(b'\x1f\x8b'):continue
  receipt=file.with_suffix('.receipt.json')
  if not receipt.exists():continue
  try:e=json.loads(receipt.read_bytes())
  except ValueError:continue
  if hashlib.sha256(raw).hexdigest()!=e['sha256']:continue
  compressed=gzip.compress(raw,compresslevel=6,mtime=0)
  assert gzip.decompress(compressed)==raw
  if len(compressed)>=len(raw):continue
  # Temporary sibling + atomic replacement, within the explicitly checked task directory.
  temp=file.with_suffix('.html.compressed');temp.write_bytes(compressed);temp.replace(file)
  e['storageEncoding']='gzip';e['storedSha256']=hashlib.sha256(compressed).hexdigest();receipt.write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf8')
  saved+=len(raw)-len(compressed);count+=1
print(json.dumps({'compressedFiles':count,'bytesSaved':saved,'originalResponseHashesPreserved':True}))

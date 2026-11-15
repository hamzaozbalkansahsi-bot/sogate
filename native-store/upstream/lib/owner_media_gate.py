"""The owner-supplied PDF media gate supplements the existing supplier audit."""
from pathlib import Path
import hashlib,json,io,re
from PIL import Image,ImageStat
def verify_owner_catalogues(root,release=None):
 root=Path(root).resolve();all_bytes=release['all_bytes']if release else {};seen=set();counts={}
 for filename,kind in [('door-catalog.json','doors'),('cabinet-fronts.json','fronts')]:
  body=(root/'data'/filename).read_bytes();d=json.loads(body)
  if all_bytes and all_bytes.get('private/'+filename)!=body:raise ValueError('Owner source manifest differs from release')
  assert d['publicationReady']is True and d['reviewRequired']is False and d['review']['contactSheetsInspected']is True
  for row in d['sourceDocuments']:assert hashlib.sha256((root.parent/row['name']).read_bytes()).hexdigest()==row['sha256']
  for row in d['review']['contactSheets']:assert hashlib.sha256((root/row['path']).read_bytes()).hexdigest()==row['sha256']
  if kind=='fronts':
   audit=(root/'artifacts/cabinet-fronts-2026/ocr-audit.json').read_bytes();assert hashlib.sha256(audit).hexdigest()==d['review']['ocrSha256'];rows=json.loads(audit)
   assert {r['sha256']for r in rows}==set(d['assets']) and not any(r['brandMatches']for r in rows)
  for digest,a in d['assets'].items():
   assert re.fullmatch(r'/assets/'+kind+r'/[a-f0-9]{64}\.(png|jpg|webp)',a['path']) and a['sha256']==digest and a['reviewRequired']is False
   path=root/'web'/a['path'].lstrip('/');assert not path.is_symlink();pixels=path.read_bytes();assert hashlib.sha256(pixels).hexdigest()==digest
   if all_bytes:assert all_bytes.get('public'+a['path'])==pixels
   with Image.open(io.BytesIO(pixels))as im:
    im.load();assert list(im.size)==[a['width'],a['height']] and min(im.size)>20
    assert max(ImageStat.Stat(im.convert('RGB')).stddev)>.5,'Blank product image'
   seen.add('public'+a['path'])
  for p in d['products']:assert p['assetHashes']and all(h in d['assets']for h in p['assetHashes'])
  counts[kind]={'products':len(d['products']),'images':len(d['assets'])}
 if all_bytes:assert {f for f in all_bytes if f.startswith(('public/assets/doors/','public/assets/fronts/'))}==seen
 return counts

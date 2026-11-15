"""Concrete approval, rendered image acceptance and recoverable catalogue promotion."""
from pathlib import Path
import hashlib,json,os,shutil,uuid

def sha(body):return hashlib.sha256(body).hexdigest()

def require_safe_runtime():
 if not __debug__:raise RuntimeError('optimized Python cannot run publication safety operations')

def validate_independent_review(review,expected):
 require_safe_runtime()
 if review.get('approved')is not True or any(review.get(k)!=v for k,v in expected.items()):raise ValueError('independent review does not bind the actual release/media/PDF/policy bytes')

def validate_https_media(receipt,plan,manifest,changed_keys):
 require_safe_runtime();aliases={'nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr'};keys=set(changed_keys)
 if receipt.get('releaseHash')!=plan['releaseHash']or receipt.get('mediaVersion')!=plan['mediaVersion']or set(receipt.get('aliases',[]))!=aliases:raise ValueError('HTTPS receipt release/alias binding differs')
 expected={(host,key,mode)for host in aliases for key in keys for mode in ['previous','fresh']};seen=set()
 for row in receipt.get('records',[]):
  token=(row.get('alias'),row.get('key'),row.get('mode'));image=manifest['images'].get(row.get('key'));ref=row.get('reference')
  if token not in expected or token in seen or image is None or manifest['references'].get(ref)!=row.get('key')or row.get('bodySha256')!=image['outputSha']or row.get('status')!=200 or row.get('urlVersion')!=(plan['baseMediaVersion']if row.get('mode')=='previous'else plan['mediaVersion']):raise ValueError('HTTPS required body/URL coverage differs')
  seen.add(token)
 if seen!=expected or not expected:raise ValueError('HTTPS required old/fresh coverage missing')
 for host in aliases:
  health=receipt.get('health',{}).get(host,{})
  if health.get('releaseHash')!=plan['releaseHash']or health.get('mediaVersion')!=plan['mediaVersion']or health.get('mediaReady')is not True:raise ValueError('HTTPS health binding differs')

def validate_live_browser(receipt,plan,manifest,read_screenshot,*,products=('4929','3499','3516','4719','3854','4436')):
 require_safe_runtime()
 if receipt.get('phase')!='live' or receipt.get('origin')!='https://nodenohome.com' or receipt.get('releaseHash')!=plan['releaseHash']or receipt.get('mediaVersion')!=plan['mediaVersion']or receipt.get('allBrowserImageBytesExact')is not True:raise ValueError('browser receipt is not bound to the actual live release')
 expected={(device,pid,int(ref.split(':')[1])):manifest['images'][key]for ref,key in manifest['references'].items()for pid in products if ref.split(':')[0]==pid for device in ['desktop','mobile']};seen=set()
 if not expected or len(receipt.get('views',[]))!=len(expected):raise ValueError('browser required view coverage differs')
 for v in receipt['views']:
  key=(v.get('device'),v.get('product'),v.get('galleryIndex'));image=expected.get(key)
  if key in seen or image is None or any(v.get(k)!=image[n]for k,n in [('imageSha256','outputSha'),('width','width'),('height','height')])or v.get('actualImageResponse')is not True or v.get('visualReview')is not True:raise ValueError('browser view is missing, duplicated or not the actual rendered image response')
  if sha(read_screenshot(v['screenshotPath']))!=v.get('screenshotSha256'):raise ValueError('browser reviewed screenshot bytes changed')
  seen.add(key)
 if seen!=set(expected):raise ValueError('browser required view set differs')

def _atomic_json(path,data):
 temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
 with temp.open('xb')as f:f.write(json.dumps(data,sort_keys=True,indent=2).encode()+b'\n');f.flush();os.fsync(f.fileno())
 os.replace(temp,path)

def promote_transaction(rows,journal_path,*,after_replace=None):
 """Only old/new exact bytes are accepted, including after a process interruption.

 No source or baseline is moved. Every replacement is atomic; the durable journal
 permits an interrupted four-file catalogue promotion to finish safely on retry.
 """
 require_safe_runtime();journal_path=Path(journal_path);spec=[{**r,**{k:str(Path(r[k]).resolve())for k in ['target','staged','previous']}}for r in rows]
 if len({r['target']for r in spec})!=len(spec):raise ValueError('duplicate promotion targets')
 for r in spec:
  if len({r['target'],r['staged'],r['previous']})!=3:raise ValueError('promotion source/target collision')
  if sha(Path(r['staged']).read_bytes())!=r['newSha256']or sha(Path(r['previous']).read_bytes())!=r['oldSha256']:raise ValueError('immutable promotion input changed')
  if sha(Path(r['target']).read_bytes())not in [r['oldSha256'],r['newSha256']]:raise ValueError('concurrent catalogue edit preserved')
 if journal_path.exists():
  journal=json.loads(journal_path.read_bytes())
  if journal.get('files')!=spec:raise ValueError('different catalogue promotion journal')
 else:
  journal={'schema':1,'files':spec,'state':'in_progress'};_atomic_json(journal_path,journal)
 for i,r in enumerate(spec):
  target=Path(r['target'])
  if sha(target.read_bytes())==r['newSha256']:continue
  temp=target.with_name(target.name+'.media-'+uuid.uuid4().hex+'.tmp')
  try:
   with Path(r['staged']).open('rb')as source,temp.open('xb')as dest:shutil.copyfileobj(source,dest,1024*1024);dest.flush();os.fsync(dest.fileno())
   if sha(temp.read_bytes())!=r['newSha256']:raise ValueError('staged catalogue copy differs')
   if sha(target.read_bytes())!=r['oldSha256']:raise ValueError('concurrent catalogue edit preserved')
   os.replace(temp,target);journal['lastReplaced']=i;_atomic_json(journal_path,journal)
   if after_replace:after_replace(i)
  finally:temp.unlink(missing_ok=True)
 if any(sha(Path(r['target']).read_bytes())!=r['newSha256']for r in spec):raise ValueError('incomplete catalogue promotion')
 journal['state']='complete';_atomic_json(journal_path,journal);return journal

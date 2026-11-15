"""Prepare an isolated browser acceptance runtime using the exact release candidate."""
from pathlib import Path
import json,os,subprocess
R=Path(__file__).resolve().parents[1];E=R/'artifacts/social-engine-20261112';proof=json.loads((E/'release.json').read_bytes());C=R/proof['release'];W=E/'preview';P=W/'public';P.mkdir(parents=True,exist_ok=True)
for f in (C/'public').rglob('*'):
 if f.is_file():
  t=P/f.relative_to(C/'public');t.parent.mkdir(parents=True,exist_ok=True)
  if t.exists() and t.read_bytes()!=f.read_bytes():
   assert t.resolve().is_relative_to(P.resolve()) and not t.is_symlink();t.unlink()
  if not t.exists():os.link(f,t)
for name in ['storage','media']:(W/name).mkdir(exist_ok=True)
cleanup=json.loads((R/'artifacts/media-cleanup.json').read_bytes());extensions={'image/jpeg':'jpg','image/png':'png','image/webp':'webp','image/avif':'avif','image/gif':'gif'}
for row in cleanup['images'].values():
 t=W/'media'/(row['outputSha']+'.'+extensions[row['mime']])
 if not t.exists():os.link(R/row['path'],t)
def q(value):return "'"+str(value).replace('\\','/').replace("'","\\'")+"'"
(W/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(C/'private')+",'storageRoot'=>"+q(W/'storage')+",'mediaRoot'=>"+q(W/'media')+"];",encoding='utf8')
program="require "+q(C/'private/social-worker.php')+";$root=$argv[1];$db=nodenoControlDatabase($root);$now=time();$id='social-qa-owner';$db->prepare('INSERT OR IGNORE INTO control_users(id,email,role,password_hash,totp_secret,recovery_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)')->execute([$id,'social-owner@example.test','owner',password_hash('Social-QA-only-password-2026',PASSWORD_BCRYPT),nodenoControlEncrypt($root,'JBSWY3DPEHPK3PXP',$id),'[]',$now,$now]);echo json_encode(nodenoStudioTick($root,$argv[2],$argv[3],$argv[4]));"
result=subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-d','extension=gd','-d','display_errors=0','-r',program,str(W/'storage'),str(C/'private'),str(W/'media'),str(P)],capture_output=True,text=True,encoding='utf8')
if result.returncode:raise RuntimeError(result.stderr[:1200])
record={'prepared':True,'testOnly':True,'releaseHash':proof['releaseHash'],'worker':json.loads(result.stdout),'previewRoot':str(W)};(E/'preview.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))

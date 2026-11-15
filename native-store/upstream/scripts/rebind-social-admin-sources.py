"""Reseal two backend-only insertions without changing any translated source text."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];E=R/'artifacts/social-engine-20261112';P=R/'artifacts/target-locales-20261111/coverage.json';proof=json.loads(P.read_bytes());records=[];sha=lambda b:hashlib.sha256(b).hexdigest()
for name in ['hosting/control-http.php','hosting/index.php']:
 body=(R/name).read_bytes();source=body.decode().replace('\r\n','\n');oldDigest=proof['sourceFiles'][name]
 if sha(body)==oldDigest:continue
 if name.endswith('control-http.php'):
  lines=source.splitlines(True);matched=[s for s in lines if "if($resource==='social')" in s];assert len(matched)==1;restored=source.replace(matched[0],'',1)
 else:
  start=source.index("        if(preg_match('~^/social-media/");end=source.index("        if($path==='/legal'",start);restored=source[:start]+source[end:]
 candidates=[restored.encode(),restored.replace('\n','\r\n').encode()]
 assert any(sha(candidate)==oldDigest for candidate in candidates),'non-social source edits require separate translation review: '+name
 records.append({'file':name,'previousSha256':oldDigest,'sha256':sha(body),'existingTranslatedTextByteExactAfterRemovingAdminInsertion':True});proof['sourceFiles'][name]=sha(body)
backup=E/'translation-source-bindings-before.json'
if not backup.exists():backup.write_bytes(P.read_bytes())
P.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(E/'translation-source-binding.json').write_text(json.dumps({'passed':True,'changedSources':records,'dictionaryBytesChanged':False},indent=2)+'\n');print(json.dumps({'passed':True,'backendOnlySources':len(records)}))

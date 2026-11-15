"""Apply the reviewed formatter to source without overwriting concurrent edits.

The other editor chat was read as idle before the first source migration. Every input is
read again immediately before its own atomic replacement; a changed file stops the operation.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os
R=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args();s=importlib.util.spec_from_file_location('date_source_policy',R/'lib/date_time_policy.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);old={};new={}
 for name in ['app.js','admin.js','admin-social.js','admin-suppliers.js','admin-analytics.js']:
  file=R/'web'/name
  if file.exists():old[file]=file.read_bytes();new[file]=m.rewrite(name,old[file])
 for name,script in [('web/index.html','app.js'),('web/admin.html','admin.js')]:
  file=R/name;old[file]=file.read_bytes();new[file]=m.html_revision(old[file],script)
 file=R/'hosting/payment-documents.php';old[file]=file.read_bytes();before=b"gmdate('Y-m-d H:i:s',(int)$order['created_at']).' UTC";after=b"$e(nodenoHumanDateTime((int)$order['created_at'],(string)($quote['country']??$contact['delivery']['country']??'TR'))).'";new[file]=old[file].replace(before,after)
 if new[file]!=old[file]and b"require_once __DIR__.'/date-time.php';"not in new[file]:new[file]=new[file].replace(b'declare(strict_types=1);',b"declare(strict_types=1);\nrequire_once __DIR__.'/date-time.php';",1)
 changed={file:value for file,value in new.items()if old[file]!=value}
 if args.apply:
  if any(file.read_bytes()!=old[file]for file in old):raise RuntimeError('date_source_changed_before_apply')
  for file,value in changed.items():
   if file.read_bytes()!=old[file]:raise RuntimeError('concurrent_source_edit_detected')
   temporary=file.with_name(file.name+'.date-policy.tmp');temporary.write_bytes(value)
   if file.read_bytes()!=old[file]:temporary.unlink();raise RuntimeError('concurrent_source_edit_detected')
   os.replace(temporary,file)
 report={'applied':args.apply,'files':[{'path':file.relative_to(R).as_posix(),'beforeSha256':hashlib.sha256(old[file]).hexdigest(),'afterSha256':hashlib.sha256(value).hexdigest()}for file,value in changed.items()],'onlyDateCallSitesAndCacheVersionsChanged':True};e=R/'artifacts/date-time-20261112';e.mkdir(exist_ok=True);(e/'source-migration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()

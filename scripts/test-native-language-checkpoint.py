#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-language-checkpoint.py
# Açıklama   : İzole kanıt örneğinde yalnız eksik dilin çalıştığını ve eski kaynak imzasının reddini doğrular.
import copy,json,os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
original=ROOT/'.local/native-languages-mount-local.json';before=original.read_bytes();data=json.loads(before)
assert data['base']=='https://127.0.0.1:3188/test'and data['finalized']and len(data['locales'])==11
fixture=ROOT/'.local/native-languages-resume-fixture.json'
assert not fixture.exists(),'RESUME_FIXTURE_ALREADY_EXISTS'
value=copy.deepcopy(data);value.update(scope='resume-fixture',finalized=False,fixtureOnly=True)
value['locales']=[row for row in value['locales']if row['locale']!='de']
env=os.environ.copy();env.update(SEXOGATE_NATIVE_TEST_URL=data['base'],SEXOGATE_NATIVE_TEST_SCOPE='resume-fixture')
def run():return subprocess.run([sys.executable,'scripts/test-native-languages.py','--retry-failed'],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
try:
 fixture.write_text(json.dumps(value),encoding='utf8');result=run()
 assert result.returncode==0,'RESUME_FAILED'
 complete=json.loads(fixture.read_text('utf8'))
 assert complete['finalized']and len(complete['locales'])==11
 assert complete['attempts']['de']==data['attempts']['de']+1
 assert all(complete['attempts'][key]==value for key,value in data['attempts'].items()if key!='de')
 assert result.stdout.count('"passed":')==1
 complete['scriptSha256']='0'*64;fixture.write_text(json.dumps(complete),encoding='utf8');rejected=run()
 assert rejected.returncode!=0 and 'STALE_LANGUAGE_CHECKPOINT'in rejected.stderr
 assert original.read_bytes()==before
 print(json.dumps({'onlyMissingLocaleExecuted':True,'sourceHashMismatchRejected':True,'originalDeploymentProofUnchanged':True,'realLocalBrowserUsed':True,'fixtureOnly':True}))
finally:fixture.unlink(missing_ok=True)

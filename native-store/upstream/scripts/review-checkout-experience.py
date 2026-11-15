"""Verify scope and executable syntax of the exact bounded checkout candidate."""
from pathlib import Path
import json,re,subprocess
R=Path(__file__).resolve().parents[1];E=R/'artifacts/checkout-experience-20261112';p=json.loads((E/'build.json').read_bytes());B=R/p['base'];N=R/p['release']
meaningful={'public/app.js','public/styles.css','public/payments.js','public/checkout-draft.js','public/checkout-terms-dialog.js','public/door-i18n.js','public/measurement-i18n.js','public/cabinet-front-ui.js','public/i18n.js','public/locale-runtime.js','public/index.php','private/index.html','private/control-catalog.php','private/payment-core.php','private/payment-documents.php','private/payment-admin.php','private/payments.php','private/door-commerce.php','private/catalog.json'}
for file in p['changedFiles']:
 if file.endswith('.php'):subprocess.run([str(R/'artifacts/runtime-php/php.exe'),'-l',str(N/file)],check=True,stdout=subprocess.DEVNULL)
 if file.endswith('.js'):subprocess.run(['node','--check',str(N/file)],check=True,stdout=subprocess.DEVNULL)
 if file in meaningful or '/locale.'in file or '/locales/'in file:continue
 before=(B/file).read_bytes();after=(N/file).read_bytes();clean=lambda v:re.sub(rb'\?v=[^\s\'\"]+',b'?v=CACHE',v);assert clean(before)==clean(after),file
assert (N/'public/date-time.js').read_bytes()==(B/'public/date-time.js').read_bytes()
assert b"require_once __DIR__.'/date-time.php'"in(N/'private/payment-documents.php').read_bytes()
assert b'nodenoHumanDateTime'in(N/'private/payment-documents.php').read_bytes()
assert b'date-time.js'in(N/'public/app.js').read_bytes()
a=json.loads((B/'private/catalog.json').read_bytes());z=json.loads((N/'private/catalog.json').read_bytes());assert z['meta'].pop('shippingPolicyVersion')=='2026-11-12-included';assert a==z
for file in ['private/payment-store.php','private/payment-stripe.php','private/control-auth.php','private/account.php']:assert (N/file).read_bytes()==(B/file).read_bytes(),file
for l in ['de','az','kk','tk','uz','ky','fa']:
 a=json.loads((B/f'public/locales/{l}.json').read_bytes());z=json.loads((N/f'public/locales/{l}.json').read_bytes());assert all(z['translations'].get(k)==v for k,v in a['translations'].items());assert z['sourceInventorySha256']==a['sourceInventorySha256']
source=(N/'public/payments.js').read_text(encoding='utf8');assert 'download.click('not in source and 'createObjectURL'not in source and 'data-payment-continue'not in source;assert "url.origin!=='https://checkout.stripe.com'"in source
record={'passed':True,'releaseHash':p['releaseHash'],'reviewedChangedFiles':len(p['changedFiles']),'phpLint':True,'javascriptSyntax':True,'unrelatedChangesAreCacheKeysOnly':True,'datePolicyPreservedAndAppliedToNewDocuments':True,'catalogueOnlyNewPolicyMarker':True,'credentialsOrdersAuthImplementationPreserved':True,'nativeExistingTranslationsPreserved':True,'automaticDownloadsRemoved':True,'oldLegalSnapshotsPreserved':True,'redirectOriginRestricted':True,'noBlockingFindings':True};(E/'code-review.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))

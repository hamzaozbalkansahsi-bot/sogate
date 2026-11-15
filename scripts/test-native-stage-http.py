#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-stage-http.py
# Açıklama   : Yalnız test yayınını, özel dosya engellerini ve ana sitenin korunmasını doğrular.
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('publisher',ROOT/'scripts/publish-php-test.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
deployment=json.loads((ROOT/'.local/native-stage-deployment.json').read_text('utf8'));assert deployment['activated'];result={}
for route,expected in [('/test/',200),('/test/?page=categories',200),('/test/api/catalog',200),('/test/api/deployment-status',200),('/test/app/config.local.json',403),('/test/.env',403),('/test/private/accounts.sqlite',404),('/test/site.webmanifest',200),('/test/apple-touch-icon.png',200)]:
 status,body,headers=p.get(route);headers={key.lower():value for key,value in headers.items()};assert status==expected,(route,status);result[route]=status
 if route=='/test/':
  html=body.decode('utf8');assert '<title>Tutkunu Keşfet. | SEXOGATE</title>'in html and 'SEXOGATE mobilya koleksiyonu'not in html;assert 'sexogate-branding.js?v=sexogate-'in html
  csp=headers.get('content-security-policy','');assert "script-src 'self'"in csp and "'unsafe-eval'"not in csp and "'unsafe-inline'"not in csp
 if route=='/test/api/deployment-status':
  health=json.loads(body);expected=json.loads((ROOT/'.local/native-catalog-selection.json').read_text('utf8'))if deployment['installation'].get('products')else{'products':0,'reviewedCovers':0};assert health['release']==deployment['release']and health['basePath']=='/test'and health['database']and health['sourceProducts']==expected['products']and health['products']==expected['reviewedCovers']and health['checkoutEnabled']is False
  assert 'no-store'in headers.get('cache-control','')
 if route=='/test/site.webmanifest':
  manifest=json.loads(body);assert manifest['scope']=='/test/'and manifest['start_url']=='/test/'and all(i['src'].startswith('/test/')for i in manifest['icons'])
status,body,_=p.get('/test/api/payments/checkout',{'Content-Type':'application/json','Origin':'https://sexogate.com'},b'{}');assert status==409 and json.loads(body)['error']=='live_sales_not_approved';result['checkoutBlocked']=409
ftp=p.publisher.connect(p.publisher.env_values())
try:
 result['mainUnchanged']=p.fingerprint(ftp)==deployment['mainBefore'];assert result['mainUnchanged']
 assert not any(e['name'].startswith(('__native_install_','__native_maintenance_'))for e in p.publisher.entries(ftp,'/test'))
 assert not any(e['name'].startswith(('native-payload-','native-request','native-maintenance-request'))for e in p.publisher.entries(ftp,'/test/app'))
 result['temporaryHelpersRemoved']=True
finally:ftp.close()
(ROOT/'.local/native-final-http.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))

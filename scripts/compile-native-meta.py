#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/compile-native-meta.py
# Açıklama   : Yerel marka metaverisini ve eksik arayüz çevirilerini veri katmanında derler.
import argparse,json,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent;parser=argparse.ArgumentParser();parser.add_argument('--private',type=Path);parser.add_argument('--public',type=Path);args=parser.parse_args()
if args.private:private=args.private;public=args.public
else:build=json.loads((ROOT/'.local/native-store-build.json').read_text('utf8'));private=Path(build['private']);public=Path(build['public'])
base=Path('D:/sexogate-local-artifacts-20261114/private-installs').resolve()
assert private.resolve().is_relative_to(base) and public.resolve().is_relative_to(base)
copydata=json.loads((ROOT/'native-store/theme/locale-meta.json').read_text('utf8'));copy=copydata['emptyCategoryDescription']
for locale in copy:
 path=private/('locale.'+locale+'.json');data=json.loads(path.read_text('utf8'))
 for source,translations in copydata.get('uiAdditions',{}).items():data['translations'][source]=translations[locale]
 raw=json.dumps(data,ensure_ascii=False).encode('utf8');path.write_bytes(raw);(public/'locales'/(locale+'.json')).write_bytes(raw)
code=r"require $argv[1].'/seo.php';$c=json_decode(file_get_contents($argv[1].'/catalog.json'),true);$f=json_decode(file_get_contents($argv[1].'/config.json'),true);$out=[];foreach(['de','az','kk','tk','uz','ky','fa'] as $l){try{nodenoSeoPage($c,$f,['page'=>'categories','lang'=>$l]);}catch(Throwable $e){foreach($e->getTrace() as $t)if(($t['function']??'')==='nodenoNativeText')$out[$l]=$t['args'][0]??'';}}echo json_encode($out);"
for attempt in range(3):
 result=subprocess.run([str(ROOT/'.local/php-runtime/php.exe'),'-d','zend.exception_ignore_args=0','-r',code,str(private)],capture_output=True)
 assert result.returncode==0,'NATIVE_METADATA_CHECK_FAILED'
 missing=json.loads(result.stdout)
 if not missing:print('Native category metadata: all seven additional locales verified.');break
 for locale,source in missing.items():
  assert re.fullmatch(r'Explore 0 models in the NODENO .+ collection\.',source),'UNRECOGNISED_METADATA_TRANSLATION_REQUIRED: '+locale
  path=private/('locale.'+locale+'.json');data=json.loads(path.read_text('utf8'));data['translations'][source]=copy[locale];raw=json.dumps(data,ensure_ascii=False).encode('utf8');path.write_bytes(raw);(public/'locales'/(locale+'.json')).write_bytes(raw)
else:raise RuntimeError('NATIVE_METADATA_INCOMPLETE')

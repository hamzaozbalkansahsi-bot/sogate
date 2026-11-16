#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-variants.py
# Açıklama   : Aynı seçim/sepet regresyonlarını yeni kaynaktaki gerçek iki beden/renk matrisiyle çalıştırır.
import hashlib,json,os,re,sys
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from native_variant_cases import consent,cart_flow,legacy_and_layout,matrix_english,bulk,rtl,safe_error
ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');suffix=os.environ.get('SEXOGATE_MARKETPLACE_SCOPE','local');assert suffix in ['local','preview','remote'];assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)
sys.excepthook=safe_error;scope='marketplace-variants-'+suffix;folder=ROOT/('docs/screenshots/native-store-'+scope);folder.mkdir(parents=True,exist_ok=True);results=[]
checksum=hashlib.sha256(Path(__file__).read_bytes()+(ROOT/'scripts/native_variant_cases.py').read_bytes()).hexdigest()
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();run={'browser':browser,'engine':engine,'base':BASE,'origin':urlsplit(BASE).scheme+'://'+urlsplit(BASE).netloc,'folder':folder,'cases':[],'teardownErrors':[]}
  try:
   consent(run);candidates=[]
   for item in run['products']:
    schema=item.get('variantSelection',{});active=[v for v in schema.get('variants',[])if v['active']]
    if schema.get('mode')=='matrix'and not schema['blocked']and len({json.dumps(v['values'],sort_keys=True)for v in active})>=2:candidates.append((item,active))
   assert len(candidates)>=2,'TWO_REAL_SOURCE_MATRICES_REQUIRED';(product,values),(matrix,matrixValues)=candidates[:2];examples=(product,values[0]['values'],values[1]['values'],matrix,matrixValues[0])
   assert all(re.fullmatch('sg_ty_[a-f0-9]{16}',item['id'])for item in run['products']),'ARCHIVED_PRODUCTS_REPUBLISHED'
   cart_flow(run,examples);legacy_and_layout(run,examples);matrix_english(run,examples);bulk(run,examples,False);bulk(run,examples,True);rtl(run,examples);assert len(run['cases'])==7
   results.append({'engine':engine,'base':BASE,'release':run['release'],'scriptSha256':checksum,'source':'trendyol_individual_pages','selectionRequired':True,'sizeColorCartLines':True,'editMergeReload':True,'legacyCartRepair':True,'sourceMatrix':True,'bulkAllItems':True,'bulkCancellation':True,'consentNormalHoverFocus':'brand-burgundy/wine','widths':[360,390,430,768,1440],'rtl':True,'realPayment':False,'isolatedCases':run['cases'],'teardownErrors':run['teardownErrors']});print(json.dumps(results[-1]),flush=True)
  finally:browser.close()
(ROOT/('docs/native-'+scope+'-results.json')).write_text(json.dumps({'base':BASE,'scope':scope,'results':results},ensure_ascii=False,indent=2),'utf8')

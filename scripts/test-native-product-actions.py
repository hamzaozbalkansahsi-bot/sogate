#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-product-actions.py
# Açıklama   : Ürün düğmelerinin gerçek tarayıcıda genişlik, dokunma ve seçim davranışını doğrular.
import argparse,json,os,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from native_browser_ready import NativePageReadiness
from native_test_errors import safe_error

sys.excepthook=safe_error
ROOT=Path(__file__).resolve().parent.parent
BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/')
SCOPE=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','actions-local')
assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)
assert re.fullmatch('[a-z-]+',SCOPE)
parser=argparse.ArgumentParser();parser.add_argument('--css-preview',action='store_true');args=parser.parse_args()
if args.css_preview:assert BASE.startswith('https://127.0.0.1:3188/'),'PREVIEW_LOCAL_ONLY'
folder=ROOT/('docs/screenshots/native-store-'+SCOPE);folder.mkdir(parents=True,exist_ok=True)
results=[]
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),viewport={'width':390,'height':844});page=context.new_page();errors=[];network=[];page.on('pageerror',lambda error:errors.append(str(error)));page.on('requestfailed',lambda request:network.append({'path':request.url.split('?',1)[0].split('/test',1)[-1],'error':request.failure}));ready=NativePageReadiness(page,BASE,60000)
  if args.css_preview:page.route('**/sexogate-storefront.css?*',lambda route:route.fulfill(status=200,content_type='text/css',body=(ROOT/'native-store/storefront/storefront.css').read_text('utf8')))
  try:
   page.goto(BASE+'/?lang=tr',wait_until='domcontentloaded');ready.wait()
   gate=page.locator('.sexogate-age-accept')
   if gate.count():gate.click();page.locator('#sexogate-age-gate').wait_for(state='detached')
   consent=page.get_by_role('button',name='Yalnız gerekli',exact=True)
   if consent.count()and consent.is_visible():consent.click()
   data=context.request.get(BASE+'/api/catalog',timeout=60000).json();products=data.get('catalog',data)['products']
   product=next(v for v in products if v.get('variantSelection',{}).get('required')and not v['variantSelection']['blocked'])
   page.goto(BASE+'/?product='+product['id']+'&lang=tr',wait_until='domcontentloaded');ready.wait()
   for width in [360,390,430,768,1440]:
    print(engine+': '+str(width),flush=True);page.set_viewport_size({'width':width,'height':1000});page.evaluate('()=>document.fonts.ready');actions=page.locator('.product-buy-actions');actions.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
    metrics=actions.evaluate('''e=>{const a=e.querySelector('[data-detail-add]'),f=e.querySelector('[data-save]'),r=a.getBoundingClientRect(),s=f.getBoundingClientRect(),b=e.getBoundingClientRect(),range=document.createRange();const text=[...a.childNodes].find(n=>n.nodeType===3&&n.textContent.trim());range.selectNode(text);return {lineRects:range.getClientRects().length,width:r.width,area:b.width,favorite:s.width,height:r.height,favoriteHeight:s.height,top:r.top,favoriteTop:s.top,right:r.right,left:r.left,saveLeft:s.left,saveRight:s.right,color:getComputedStyle(a).backgroundColor}}''')
    assert metrics['lineRects']==1,('WRAPPED_PRIMARY_LABEL',width,metrics)
    assert metrics['width']>=metrics['area']-metrics['favorite']-12,('UNUSED_ACTION_COLUMNS',width,metrics)
    assert abs(metrics['top']-metrics['favoriteTop'])<1 and metrics['height']==metrics['favoriteHeight']>=48,('MISALIGNED_ACTIONS',width,metrics)
    assert metrics['favorite']==52 and metrics['color']=='rgb(90, 10, 32)',metrics
    assert page.locator('.product-shopping-tools>button').evaluate_all('''nodes=>nodes.every(e=>{const r=e.getBoundingClientRect(),style=getComputedStyle(e);return r.height>=44&&parseFloat(style.paddingInlineStart)>=8&&e.scrollWidth<=e.clientWidth+1})'''),'CRAMPED_SECONDARY_ACTION'
    assert page.locator('.detail-secondary>button,.detail-secondary>a').evaluate_all('nodes=>nodes.every(e=>e.getBoundingClientRect().height>=44&&!getComputedStyle(e).textDecorationLine.includes("underline"))'),'SECONDARY_LINK_STYLE'
    assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),'PAGE_OVERFLOW'
    if width in [390,1440]:page.locator('.purchase-choice-row').screenshot(path=str(folder/(engine+'-actions-'+str(width)+'.png')))
   page.set_viewport_size({'width':390,'height':1000});quantity=page.locator('#detail-quantity');before=int(quantity.input_value());page.locator('.purchase-controls button').last.click();assert int(quantity.input_value())==before+1;page.locator('.purchase-controls button').first.click();assert int(quantity.input_value())==before
   favorite=page.locator('.product-buy-actions [data-save]');favorite.click();assert page.locator('.product-buy-actions [data-save]').get_attribute('aria-pressed')=='true';page.locator('.product-buy-actions [data-save]').click()
   compare=page.locator('.product-shopping-tools [data-compare]');compare.click();assert page.locator('.product-shopping-tools [data-compare]').get_attribute('aria-pressed')=='true';page.locator('.product-shopping-tools [data-compare]').click()
   page.locator('.product-buy-actions [data-detail-add]').click();dialog=page.locator('.sg-variant-dialog');dialog.wait_for();assert dialog.locator('.sg-variant-add').is_disabled();page.keyboard.press('Escape');dialog.wait_for(state='detached')
   ready.wait();page.locator('[data-share]').click();page.locator('#share-dialog[open]').wait_for();page.keyboard.press('Escape');page.locator('#share-dialog').wait_for(state='hidden')
   page.goto(BASE+'/?product='+product['id']+'&lang=ar',wait_until='domcontentloaded');ready.wait();assert page.locator('html').get_attribute('dir')=='rtl';assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth');assert page.locator('.product-buy-actions [data-detail-add]').evaluate('e=>e.getBoundingClientRect().width>200');assert not errors,errors
   results.append({'engine':engine,'base':BASE,'release':context.request.get(BASE+'/api/deployment-status').json()['release'],'cssPreview':args.css_preview,'widths':[360,390,430,768,1440],'primarySingleLine':True,'touchTargets':True,'quantityButtons':True,'favoriteAndCompare':True,'variantRequired':True,'shareDialog':True,'rtl':True,'pageErrors':0})
  except Exception:
   print(json.dumps({'pageErrors':errors,'network':network,'fonts':page.evaluate('()=>[...document.fonts].filter(f=>f.status!=="loaded").map(f=>({family:f.family,weight:f.weight,status:f.status}))'),'openDialogs':page.locator('dialog[open]').evaluate_all('nodes=>nodes.map(e=>e.id)')}),flush=True)
   try:page.screenshot(path=str(folder/(engine+'-diagnostic.png')),timeout=5000)
   except Exception as capture_error:print('Diagnostic capture: '+type(capture_error).__name__,flush=True)
   raise
  finally:context.close();browser.close()
(ROOT/('.local/native-'+SCOPE+'.json')).write_text(json.dumps(results,indent=2),encoding='utf8');print(json.dumps(results),flush=True)

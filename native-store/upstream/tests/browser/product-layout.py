"""Purchase controls stay together and essential facts accompany the product image.

Uses real pages and product variants; no CSS values or screenshot hashes are asserted.
"""
from pathlib import Path
import json,os
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];phase=os.environ.get('NODENO_LAYOUT_PHASE','source');origin=os.environ.get('NODENO_LAYOUT_URL','https://127.0.0.1:4193')
out=ROOT/'artifacts/product-layout-reference';out.mkdir(exist_ok=True)
report={'phase':phase,'origin':origin,'testOnly':phase=='source','checks':[],'errors':[]}
def check(condition,message):
 if not condition:raise AssertionError(message)
try:
 with sync_playwright() as p:
  api=p.request.new_context(ignore_https_errors=phase=='source')
  if phase!='source':
   report['releaseHash']=api.get(origin+'/api/health',timeout=180000).json()['releaseHash']
   if os.environ.get('NODENO_QA_RELEASE'):check(report['releaseHash']==os.environ['NODENO_QA_RELEASE'],'Exact release')
  cases=[('tr',1440)] if os.environ.get('NODENO_LAYOUT_RED') else [(lang,width) for lang in ('tr','en','ru','ar') for width in (390,1024,1440)]+[('tr',1920)]
  for engine in ('chromium',) if os.environ.get('NODENO_LAYOUT_RED') else ('chromium','webkit'):
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(p,engine).launch(executable_path=str(executable))
   for lang,width in cases:
    c=browser.new_context(viewport={'width':width,'height':1000},ignore_https_errors=phase=='source',has_touch=width<700);page=c.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
    page.goto(origin+f'/?product=2395&lang={lang}');page.wait_for_load_state('networkidle');expect(page.locator('#account-menu a[href*="page=login"]')).to_be_attached()
    page.evaluate('document.fonts.ready');page.screenshot(path=str(out/f'{phase}-{engine}-{lang}-{width}-before-actions.png'))
    initial=page.evaluate('''()=>{const rect=s=>{const r=document.querySelector(s).getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,right:r.right}};return{image:rect('#gallery-viewport'),facts:rect('.product-spec-overview'),quantity:rect('.purchase-controls'),primary:rect('.product-buy-actions [data-detail-add]'),secondary:rect('.product-buy-actions [data-product-buy]'),pageWidth:document.documentElement.scrollWidth,viewport:innerWidth}}''')
    check(initial['pageWidth']<=width+1,'Page must not scroll sideways')
    if width>=1000:
     check(initial['facts']['y']<initial['image']['bottom'],'Essential specifications are below the product image instead of accompanying it')
     check(initial['primary']['width']>initial['secondary']['width']*1.4,'The primary add action does not stand out from the secondary buy action')
     check(initial['quantity']['y']<initial['primary']['bottom'] and initial['quantity']['bottom']>initial['primary']['y'],'Quantity and purchase actions are separated by unnecessary vertical scrolling')
     check(initial['primary']['bottom']<1000,'Primary purchase action must be available in the first desktop viewport')
     if width==1920:
      reference=next(row['geometry'] for row in report['checks'] if row['engine']==engine and row['lang']==lang and row['width']==1440)
      check(initial['image']['width']<=reference['image']['width']*1.05,'A wide display stretches the product canvas instead of keeping a readable shopping column')
    favorite=page.locator('.product-buy-actions [data-save]');favorite.focus();favorite.press('Space');expect(page.locator('.product-buy-actions [data-save]')).to_be_focused()
    page.locator('#detail-quantity').fill('2');page.locator('#detail-quantity').dispatch_event('change')
    page.locator('.color-option').nth(1).click();expect(page.locator('#detail-quantity')).to_have_value('2')
    chosen=page.locator('.color-option[aria-current=true]').get_attribute('href');chosen_id=__import__('urllib.parse',fromlist=['parse_qs']).parse_qs(__import__('urllib.parse',fromlist=['urlparse']).urlparse(chosen).query)['product'][0]
    page.locator('[data-detail-add]:visible').first.click()
    saved=page.evaluate('JSON.parse(localStorage.getItem("nodeno.cart.v1"))');check(any(row['id']==chosen_id and row['quantity']==2 for row in saved),'Visible selection must be the exact SKU and quantity added')
    if width>=1200:
     page.locator('.product-service-panel [data-specs-link]').first.click();expect(page.locator('#product-shelf-productSimilar')).to_be_visible();check(page.url.endswith('#product-shelf-productSimilar'),'Related section must be a working deep link')
     page.go_back();expect(page.locator('#product-title')).to_be_in_viewport()
    report['checks'].append({'engine':engine,'lang':lang,'width':width,'geometry':initial,'variantQuantity':True,'realCart':True});print(json.dumps({'engine':engine,'lang':lang,'width':width,'passed':True}),flush=True);c.close()
   browser.close()
  api.dispose();check(not report['errors'],str(report['errors']));report['passed']=True
finally:
 (out/f'{phase}-layout-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':report.get('passed',False),'phase':phase,'cases':len(report['checks'])}))

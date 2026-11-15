"""Real browser acceptance: source fixtures, exact packaged release, then live public UI.

Live runs use guest browser state only; no accounts, orders or payments are created.
"""
from pathlib import Path
import json, os, time, uuid
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[2]
PHASE=os.environ.get('NODENO_SHOPPING_PHASE','source')
ORIGIN=os.environ.get('NODENO_SHOPPING_URL','https://127.0.0.1:4193')
assert PHASE in ('source','local','live')
OUT=ROOT/'artifacts/shopping-experience';OUT.mkdir(exist_ok=True)
report={'phase':PHASE,'origin':ORIGIN,'testOnly':PHASE=='source','checks':[],'errors':[],'screenshots':[]}
def check(condition,message):
 if not condition: raise AssertionError(message)
def visit(page,path):
 page.goto(ORIGIN+path);page.wait_for_load_state('networkidle');page.locator('#page h1').first.wait_for()
 page.wait_for_function("document.querySelector('#account-menu')?.textContent.includes('…')===false")
def overflow(page):
 check(not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'),'Root must not overflow horizontally')
def shot(page,name):
 filename=OUT/f'{PHASE}-{name}.png';page.screenshot(path=str(filename),animations='disabled');report['screenshots'].append(str(filename))
def ctx_setup(browser,width,lang):
 context=browser.new_context(ignore_https_errors=PHASE!='live',viewport={'width':width,'height':900},has_touch=width<700,locale='en-US')
 page=context.new_page();page.on('pageerror',lambda error:report['errors'].append(str(error)))
 return context,page

try:
 with sync_playwright() as p:
  api=p.request.new_context(ignore_https_errors=PHASE!='live')
  catalog=api.get(ORIGIN+'/api/catalog').json();products=catalog['products'];byid={x['id']:x for x in products}
  if PHASE!='source':
   health=api.get(ORIGIN+'/api/health',timeout=180000).json();report['releaseHash']=health['releaseHash']
   if os.environ.get('NODENO_QA_RELEASE'):check(health['releaseHash']==os.environ['NODENO_QA_RELEASE'],'Exact release required')
  product=byid['2395'];variants=[x for x in products if x.get('modelId')==product.get('modelId')];check(len(variants)>1,'Real colour family')
  other=next(x for x in products if x.get('modelId')!=product.get('modelId'))
  for engine in ('chromium','webkit'):
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(p,engine).launch(executable_path=str(executable),headless=True)
   for lang in ('tr','en','ru','ar'):
    for width in (390,1440):
     context,page=ctx_setup(browser,width,lang)
     visit(page,'/?'+urlencode({'lang':lang,'page':'catalog'}));overflow(page)
     check(page.locator('[data-compare]').count()>0,'Real card controls')
     if width<700:page.locator('[data-action=filter]').click()
     prefix='mobile' if width<700 else 'desktop'
     for axis,value in [('Width','100'),('Height','110'),('Depth','40')]:page.locator(f'#{prefix}-max-{axis}').fill(value)
     page.locator(('#filter-dialog ' if width<700 else '.desktop-filters ')+'.catalog-filter-form button[type=submit]').click()
     expect(page).to_have_url(__import__('re').compile('maxWidth=100'))
     page.locator('#product-grid').wait_for();overflow(page)
     check(page.locator('.active-filters a').count()==3,'All dimensional filters removable')
     visit(page,'/?'+urlencode({'lang':lang,'product':product['id']}))
     page.locator('[data-fit]').click();page.locator('#fit-width').fill('500');page.locator('#fit-height').fill('500');page.locator('#fit-depth').fill('500');page.locator('#fit-form button[type=submit]').click()
     expect(page.locator('.fit-status')).to_have_attribute('data-status','fits');page.locator('[data-close=fit-dialog]').click()
     page.locator('.product-shopping-tools [data-compare]').click();expect(page.locator('.comparison-tray')).to_be_visible();overflow(page)
     page.locator('.comparison-tray a').click();expect(page.locator('.comparison-table')).to_be_visible();overflow(page)
     check(page.locator('.comparison-table tbody tr').count()>=8,'Actual technical comparison')
     page.locator('#comparison-differences').check();check(page.locator('.comparison-table tbody tr:visible').count()==0,'Single product has no differences')
     visit(page,'/?'+urlencode({'lang':lang,'page':'compare','ids':product['id']+','+other['id']}));expect(page.locator('.comparison-table thead th')).to_have_count(3);overflow(page)
     if lang=='tr':shot(page,f'{engine}-compare-{width}')
     visit(page,'/?'+urlencode({'lang':lang,'page':'catalog'}));page.locator('[data-quick]').first.click();expect(page.locator('#quick-dialog')).to_be_visible();page.locator('#quick-quantity').fill('2');page.locator('[data-quick-add]').click();expected_count=page.evaluate('(lang)=>new Intl.NumberFormat(lang).format(2)',lang);expect(page.locator('#cart-count')).to_have_text(expected_count);overflow(page);page.locator('[data-close=quick-dialog]').click()
     page.locator('[data-collect]').first.click();expect(page.locator('#collection-name')).to_be_visible();page.locator('#collection-name').fill('Salon '+lang);page.locator('#collection-name-form button').click();expect(page.locator('#collection-dialog')).not_to_be_visible()
     visit(page,'/?'+urlencode({'lang':lang,'page':'collections'}));expect(page.locator('.collection-list a')).to_have_count(1);page.locator('.collection-list a').click();expect(page.locator('.collection-products .product-card')).to_have_count(1);overflow(page)
     page.locator('[data-list-rename]').click();expect(page.locator('#collection-name')).to_have_value('Salon '+lang);page.locator('#collection-name').fill('Ev '+lang);page.locator('#collection-name-form button').click();expect(page.locator('.collection-products h2')).to_have_text('Ev '+lang)
     if lang=='tr':shot(page,f'{engine}-collections-{width}')
     visit(page,'/?'+urlencode({'lang':lang,'page':'recent'}));check(page.locator('.product-card').count()>=1,'Real recent products');overflow(page)
     report['checks'].append({'engine':engine,'lang':lang,'width':width,'passed':['dimensionFilters','fitTool','comparison','differenceToggle','quickViewQuantity','guestCollectionCreateRenameReload','recentProducts','noRootOverflow']})
     print(json.dumps({'engine':engine,'lang':lang,'width':width,'passed':True}),flush=True)
     context.close()
   # Turkish scenario exercises state transitions rather than repeating presentation checks.
   context,page=ctx_setup(browser,390,'tr');visit(page,'/?lang=tr')
   page.evaluate('(items)=>localStorage.setItem("nodeno.cart.v1",JSON.stringify(items))',[{'id':variants[0]['id'],'quantity':2},{'id':variants[1]['id'],'quantity':3}]);visit(page,'/?page=cart&lang=tr')
   page.locator(f'[data-cart-variant="{variants[0]["id"]}"]').click();page.locator(f'[data-cart-replace][data-target="{variants[1]["id"]}"]').click();expect(page.locator('.basket-item')).to_have_count(1);expect(page.locator('[data-cart-quantity]')).to_have_value('5')
   page.locator('[data-remove]').click();expect(page.locator('.basket-item')).to_have_count(0);page.locator('[data-shopping=undo-cart]').click();expect(page.locator('[data-cart-quantity]')).to_have_value('5');overflow(page)
   page.locator('#search').fill('utila');page.locator('#search').press('Enter');expect(page).to_have_url(__import__('re').compile('q=utila'))
   page.locator('#search').fill('');page.locator('#search').focus();expect(page.locator('[data-search-term=utila]')).to_be_visible();page.locator('[data-shopping=clear-searches]').click();check(page.evaluate('JSON.parse(localStorage.getItem("nodeno.searches.v1")).length')==0,'Search history clears')
   page.locator('#search').fill(product['code'].replace('-',''));page.locator('#search').press('ArrowDown');check(bool(page.locator('#search').get_attribute('aria-activedescendant')),'Keyboard combobox active option');page.locator('#search').press('Enter');expect(page.locator('#product-title')).to_be_visible()
   page.locator('.product-shopping-tools [data-compare]').click();page.locator('[data-detail-add]:visible').first.click();page.locator('.mobile-purchase').wait_for(state='visible');dock=page.locator('#shopping-dock').bounding_box();purchase=page.locator('.mobile-purchase').bounding_box();check(dock['y']+dock['height']<=purchase['y']+2,'Comparison tray clears purchase bar')
   shot(page,f'{engine}-mobile-product')
   report['checks'].append({'engine':engine,'lang':'tr','width':390,'passed':['cartColourMerge','removeUndo','searchHistoryClear','compactCodeKeyboardSearch','dockClearance']})
   context.close();browser.close()
  check(not report['errors'],'No page exceptions: '+str(report['errors']))
  api.dispose()
 report['passed']=True
finally:
 (OUT/f'{PHASE}-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'phase':PHASE,'passed':report.get('passed',False),'scenarios':len(report['checks']),'pageErrors':len(report['errors'])}))

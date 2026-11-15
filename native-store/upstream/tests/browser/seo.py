"""Real HTML works without page scripts, then SPA navigation maintains the same SEO policy."""
from pathlib import Path
import os,json
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];ORIGIN=os.environ.get('NODENO_SEO_URL','http://127.0.0.1:4186');PHASE=os.environ.get('NODENO_SEO_PHASE','local');OUT=ROOT/'artifacts/control-seo';OUT.mkdir(exist_ok=True)
report={'phase':PHASE,'origin':ORIGIN,'checks':[],'errors':[]}
with sync_playwright() as p:
 api=p.request.new_context();health=api.get(ORIGIN+'/api/health',timeout=180000).json();report['releaseHash']=health['releaseHash']
 if os.environ.get('NODENO_QA_RELEASE'):assert report['releaseHash']==os.environ['NODENO_QA_RELEASE']
 for engine in (('chromium',) if os.environ.get('NODENO_SEO_QUICK') else ('chromium','webkit')):
  executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
  browser=getattr(p,engine).launch(executable_path=str(executable))
  for locale in (() if os.environ.get('NODENO_SEO_QUICK') else ('tr','en','ru','ar')):
   for width in (390,1440):
    context=browser.new_context(viewport={'width':width,'height':1000},java_script_enabled=False);page=context.new_page();response=page.goto(ORIGIN+'/?lang='+locale+'&product=2395');page.wait_for_load_state('networkidle');assert response.status==200
    expect(page.locator('#product-title')).to_be_visible();expect(page.locator('#product-specs')).to_contain_text('91')
    assert page.locator('html').get_attribute('lang')==locale;assert page.locator('html').get_attribute('dir')==('rtl' if locale=='ar' else 'ltr')
    assert page.locator('link[rel=canonical]').get_attribute('href')=='https://nodenohome.com/?lang='+locale+'&product=2395'
    assert page.locator('link[hreflang]').count()==5;assert page.locator('.product-seller').count()==0
    assert all('/?lang=' in href for href in page.locator('.color-option').evaluate_all('(nodes)=>nodes.map(n=>n.href)'))
    encoded=page.locator('script[data-nodeno-seo]').text_content();assert '10078.95' in encoded and 'InStock' not in encoded and 'aggregateRating' not in encoded
    if locale=='tr':page.screenshot(path=str(OUT/f'{PHASE}-{engine}-{width}-no-js.png'))
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    report['checks'].append({'engine':engine,'locale':locale,'width':width,'scripts':False,'content':True,'canonical':True,'structuredFacts':True});context.close()
  for width in ((390,) if os.environ.get('NODENO_SEO_QUICK') else (390,1440)):
   context=browser.new_context(viewport={'width':width,'height':1000},has_touch=width<700);page=context.new_page();page.on('pageerror',lambda error:report['errors'].append(str(error)))
   page.goto(ORIGIN+'/?lang=tr&product=2395');page.wait_for_load_state('networkidle');page.locator('#account-menu a[href*="page=login"]').wait_for(state='attached',timeout=30000);expect(page.locator('[data-detail-add]').first).to_be_attached()
   assert 'Utila 520' in page.title(),'Account hydration overwrote the product title'
   link=page.locator('#bottom-nav a[href*="page=categories"]') if width<700 else page.locator('#root-links a').first;link.click();page.wait_for_load_state('networkidle')
   assert 'product=' not in page.locator('link[rel=canonical]').get_attribute('href');assert 'ProductGroup' not in (page.locator('script[data-nodeno-seo]').text_content() or '')
   cart=page.locator('#bottom-nav a[href*="page=cart"]') if width<700 else page.locator('.cart-link');cart.click();page.wait_for_load_state('networkidle');assert 'noindex' in page.locator('meta[name=robots]').get_attribute('content');assert page.locator('script[data-nodeno-seo]').count()==0
   report['checks'].append({'engine':engine,'locale':'tr','width':width,'scripts':True,'navigationClearsOldMetadata':True,'privateNoindex':True});context.close()
  browser.close()
 api.dispose()
assert not report['errors'];report['passed']=True;(OUT/f'{PHASE}-seo-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'passed':True,'checks':len(report['checks']),'releaseHash':report['releaseHash']}))

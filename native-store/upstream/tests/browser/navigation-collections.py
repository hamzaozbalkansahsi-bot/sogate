"""Navigation targets retain semantic focus without a touch outline; collections open real ranges."""
from pathlib import Path
import json,os
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[2]
PHASE=os.environ.get('NODENO_COLLECTION_PHASE','source')
ORIGIN=os.environ.get('NODENO_COLLECTION_URL','https://127.0.0.1:4193')
MODE=os.environ.get('NODENO_COLLECTION_MODE','all')
OUT=ROOT/'artifacts/navigation-collections';OUT.mkdir(exist_ok=True)
report={'phase':PHASE,'testOnly':PHASE=='source','origin':ORIGIN,'checks':[],'errors':[]}

def visit(page,path):
 page.goto(ORIGIN+path);page.wait_for_load_state('networkidle');expect(page.locator('#page h1')).to_be_visible()

def target_is_quiet(page):
 expect(page.locator('#page h1')).to_be_focused()
 state=page.locator('#page h1').evaluate('(node)=>{const s=getComputedStyle(node);return {style:s.outlineStyle,width:parseFloat(s.outlineWidth)}}')
 assert state['style']=='none' or state['width']==0,('Navigation heading shows a focus frame',state)

try:
 with sync_playwright() as p:
  if PHASE!='source':
   api=p.request.new_context();report['releaseHash']=api.get(ORIGIN+'/api/health',timeout=180000).json()['releaseHash'];assert report['releaseHash']==os.environ['NODENO_QA_RELEASE'];api.dispose()
  for engine in (('webkit',) if os.environ.get('NODENO_COLLECTION_RED') else ('chromium','webkit')):
   executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
   browser=getattr(p,engine).launch(executable_path=str(executable))
   for lang in (('tr',) if os.environ.get('NODENO_COLLECTION_RED') else ('tr','en','ru','ar')):
    for width in ((390,) if os.environ.get('NODENO_COLLECTION_RED') else (390,1440)):
     context=browser.new_context(viewport={'width':width,'height':1000},has_touch=width<700,ignore_https_errors=PHASE=='source',reduced_motion='reduce');page=context.new_page();page.on('pageerror',lambda error:report['errors'].append(str(error)))
     visit(page,'/?lang='+lang)
     nav=page.locator('#bottom-nav a[href*="page=categories"]') if width<700 else page.locator('.room-stories [data-nav]').first
     nav.click();page.wait_for_load_state('networkidle');expect(page.locator('#page h1')).to_be_focused()
     page.screenshot(path=str(OUT/f'{PHASE}-{engine}-{lang}-{width}-navigation.png'))
     if MODE!='collections':target_is_quiet(page)
     home=page.locator('#bottom-nav a[href*="lang="]').first if width<700 else page.locator('.logo')
     home.click();page.wait_for_load_state('networkidle')
     if MODE!='collections':target_is_quiet(page)
     if MODE!='focus':
      cards=page.locator('.collection-discovery-card');expect(cards).to_have_count(4)
      destinations=cards.evaluate_all('(nodes)=>nodes.map(node=>node.href)');assert len(set(destinations))==4
      for index in range(4):
       card=page.locator('.collection-discovery-card').nth(index);card.scroll_into_view_if_needed();photo=card.locator('img');expect(photo).to_be_visible()
       for attempt in range(50):
        if photo.evaluate('(img)=>img.complete&&img.naturalWidth>0'):break
        page.wait_for_timeout(100)
       assert photo.evaluate('(img)=>img.complete&&img.naturalWidth>0'),'Collection image unavailable'
       dimensions=photo.evaluate('(img)=>{const r=img.getBoundingClientRect();return {width:r.width,height:r.height,fit:getComputedStyle(img).objectFit}}');assert dimensions['width']>130 and dimensions['height']>120 and dimensions['fit']=='cover'
       if index==0:page.screenshot(path=str(OUT/f'{PHASE}-{engine}-{lang}-{width}-collections.png'))
       expected=parse_qs(urlparse(destinations[index]).query)['category'][0]
       card.click();page.wait_for_load_state('networkidle');assert parse_qs(urlparse(page.url).query)['category'][0]==expected
       expect(page.locator('.product-grid .product-card').first).to_be_visible()
       if MODE!='collections':target_is_quiet(page)
       page.go_back();page.wait_for_load_state('networkidle');expect(page.locator('.collection-discovery-card')).to_have_count(4)
      assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
     if MODE!='collections':
      visit(page,'/?product=2395&lang='+lang)
      page.locator('.specs-all-link').first.click();section=page.locator('#product-specs');expect(section).to_be_focused()
      assert section.evaluate('(node)=>getComputedStyle(node).outlineStyle')=='none','Product section shows a focus frame'
     # Keyboard focus on an actual control remains visibly identifiable.
     page.locator('#search').click();page.keyboard.press('Tab');active=page.evaluate('()=>{const node=document.activeElement,s=getComputedStyle(node);return {tag:node.tagName,width:parseFloat(s.outlineWidth),style:s.outlineStyle}}')
     assert active['tag']=='BUTTON' and active['width']>=2 and active['style']!='none',('Keyboard focus was removed',active)
     report['checks'].append({'engine':engine,'lang':lang,'width':width,'quietNavigation':MODE!='collections','realCollections':MODE!='focus','keyboardFocus':True});print(json.dumps(report['checks'][-1]),flush=True);context.close()
   browser.close()
  assert not report['errors'];report['passed']=True
except Exception as error:
 report['passed']=False;report['failure']=str(error);raise
finally:
 (OUT/f'{PHASE}-{MODE}-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

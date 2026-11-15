"""Read-only acceptance against the real HTTPS storefront in Chromium and WebKit."""
from pathlib import Path
import json
from urllib.request import urlopen
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];O=R/'artifacts/supplier-expansion/publication/browser';catalog=json.loads(urlopen('https://nodenohome.com/api/catalog',timeout=45).read());rows=[p for p in catalog['products']if p.get('productType')=='supplier-item'];checks=[]
with sync_playwright()as pw:
 for engine,width,lang in [('chromium',1440,'tr'),('webkit',390,'ar')]:
  executable=Path.home()/'AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe'if engine=='chromium'else R/'artifacts/runtime-browsers/webkit-2370/Playwright.exe';browser=getattr(pw,engine).launch(executable_path=str(executable),headless=True);context=browser.new_context(viewport={'width':width,'height':1000 if width>768 else 844},is_mobile=width<768,has_touch=width<768)
  context.add_init_script("localStorage.setItem('nodeno.analytics.consent.v1','false');localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.delivery-country.v1',JSON.stringify('TR'));localStorage.setItem('nodeno.currency.v1',JSON.stringify('TRY'))");page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  p=next(p for p in rows if p['id'].startswith('altinis')and p['salePriceMinor']and p['images'])if width>768 else next(p for p in rows if p.get('variantLabel')and not p.get('variationSelectionRequired')and p['quantityPolicy']['minimum']==3)
  page.goto('https://nodenohome.com/?lang='+lang+'&product='+p['id'],wait_until='domcontentloaded');expect(page.locator('#product-title')).to_have_text(p['modelName'][lang],timeout=45000);page.wait_for_function("()=>{const img=document.querySelector('.gallery-slide img');return img&&img.complete&&img.naturalWidth>0}",timeout=45000);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  if lang=='ar':assert page.locator('html').get_attribute('dir')=='rtl';expect(page.locator('.supplier-options')).to_be_visible();expect(page.locator('#detail-quantity')).to_have_value('3')
  add=page.locator(('.mobile-purchase'if width<768 else'.product-buy-actions')+' [data-detail-add]');expect(add).to_be_enabled(timeout=30000)
  add.click();page.wait_for_function("id=>{const rows=JSON.parse(localStorage.getItem('nodeno.cart.v1')||'[]');return rows.some(r=>r.id===id&&r.quantity>=1)}",arg=p['id'],timeout=15000)
  quantity=page.evaluate("id=>JSON.parse(localStorage.getItem('nodeno.cart.v1')).find(r=>r.id===id).quantity",p['id']);assert quantity==p['quantityPolicy']['minimum']
  page.screenshot(path=str(O/f'live-{engine}-{lang}.png'),full_page=False);assert not errors,errors;checks.append({'engine':engine,'width':width,'lang':lang,'productId':p['id'],'guestCartQuantity':quantity,'passed':True});context.close();browser.close()
report={'passed':True,'live':True,'scenarios':checks};(O/'live-acceptance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

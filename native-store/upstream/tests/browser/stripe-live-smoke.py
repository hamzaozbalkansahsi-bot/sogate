"""Read-only live acceptance using isolated guest baskets; never starts a payment or order."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];OUT=R/'artifacts/stripe-checkout-20261110';expected=json.loads((OUT/'build.json').read_bytes())['releaseHash'];checks=[]
with sync_playwright()as pw:
 browser=pw.chromium.launch(headless=True,executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'))
 for host,width,lang in [('nodenohome.com',1440,'tr'),('nodenohome.com.tr',390,'tr'),('nodenohome.com',390,'ar')]:
  context=browser.new_context(viewport={'width':width,'height':1000 if width>768 else 844},is_mobile=width<768,has_touch=width<768);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  health=context.request.get('https://'+host+'/api/health').json();assert health['releaseHash']==expected and health['mediaReady']is True and health['checkoutEnabled']is False
  page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.delivery-country.v1',JSON.stringify('TR'));localStorage.setItem('nodeno.currency.v1',JSON.stringify('TRY'));localStorage.setItem('nodeno.cart.v1',JSON.stringify([{id:'2395',quantity:2},{id:'2393',quantity:1}]))")
  page.goto('https://'+host+'/?lang='+lang+'&page=checkout',wait_until='networkidle');assert host in page.url
  necessary=page.locator('#insights-banner .insights-actions button').last
  if necessary.is_visible():necessary.click()
  page.locator('[data-action=guest-start]').click();form=page.locator('#guest-checkout-form')
  for name,value in {'name':'Deniz Örnek','email':'deniz@example.test','phone':'+905551112233','city':'İzmir','district':'Buca','postalCode':'35040','line1':'Örnek Mahallesi\nDeneme Sokak 12'}.items():form.locator('[name="'+name+'"]').fill(value)
  form.locator('[name=country]').select_option('TR');form.locator('[type=submit]').click();expect(page.locator('.guest-review')).to_be_visible();expect(page.locator('.payment-totals')).to_be_visible();assert page.locator('.payment-form').count()==0
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.wait_for_function('Array.from(document.querySelectorAll(".checkout-product-photo img")).every(i=>i.complete&&i.naturalWidth>0)');assert not errors,errors
  page.screenshot(path=str(OUT/f'live-{width}-{lang}-review.png'),full_page=True);checks.append({'host':host,'width':width,'locale':lang,'releaseHash':expected,'paymentDisabled':True,'noOverflow':True,'productImagesLoaded':True,'noRuntimeErrors':True});context.close()
 browser.close()
(OUT/'live-acceptance.json').write_text(json.dumps({'passed':True,'releaseHash':expected,'providerTest':False,'realPayments':0,'ordersCreated':0,'checks':checks},indent=2)+'\n');print(json.dumps({'passed':True,'scenarios':len(checks),'releaseHash':expected,'realPayments':0}))

"""Audit native shopping screens using a fresh guest and read-only production."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];O=R/'artifacts/storefront-followup-20261112';O.mkdir(exist_ok=True);results=[]
with sync_playwright()as pw:
 browser=pw.chromium.launch(headless=True,executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'))
 for locale in ['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']:
  context=browser.new_context(viewport={'width':390,'height':900},is_mobile=True,has_touch=True,reduced_motion='reduce');page=context.new_page();page.set_default_timeout(20000);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1');localStorage.setItem('nodeno.analytics.consent.v1','false')")
  page.route('**/*',lambda route:route.continue_()if route.request.method in ['GET','HEAD']else route.abort())
  for route,selector in [('sets&set=bohera-bedroom','[data-set-collection]'),('wholesale','#wholesale-form'),('login','form')]:
   try:
    response=page.goto('https://nodenohome.com/?lang='+locale+'&page='+route,wait_until='networkidle');assert response.status==200
    expect(page.locator('#language')).to_have_value(locale);expect(page.locator(selector).last).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'horizontal overflow'
    assert not errors,errors
    if route.startswith('sets'):
     for sku,quantity in [('4907',1),('4911',2),('4915',1)]:
      row=page.locator('[data-set-model=model-'+sku+']');row.locator('[data-set-include]').check();row.locator('[data-set-quantity]').fill(str(quantity));row.locator('[data-set-quantity]').dispatch_event('change')
     page.locator('[data-set-commit]').click()
     state=page.evaluate("JSON.parse(localStorage.getItem('nodeno.cart.v1'))")
     assert {v['id']:v['quantity']for v in state}=={'4907':1,'4911':2,'4915':1},state
    results.append({'locale':locale,'route':route,'passed':True});print(json.dumps(results[-1]),flush=True)
   except Exception as error:
    page.screenshot(path=str(O/('failure-'+locale+'-'+route.split('&')[0]+'.png')))
    results.append({'locale':locale,'route':route,'passed':False,'error':str(error)[:900],'pageErrors':errors});print(json.dumps(results[-1]),flush=True)
  context.close()
 browser.close()
(O/'shopping-audit.json').write_text(json.dumps({'passed':all(r['passed']for r in results),'checks':results,'livePostsAllowed':False,'ordersCreated':0},ensure_ascii=False,indent=2)+'\n',encoding='utf8')

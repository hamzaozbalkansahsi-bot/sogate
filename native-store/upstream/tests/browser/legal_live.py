"""Read-only live legal UI: does not register, grant consent or start checkout."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/legal-20261110';checks=[]
with sync_playwright()as pw:
 browser=pw.chromium.launch(headless=True,executable_path=str(Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'))
 for locale,width in [('tr',1440),('en',390),('ru',390),('ar',390)]:
  context=browser.new_context(viewport={'width':width,'height':920},is_mobile=width<768,has_touch=width<768);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  response=page.goto('https://nodenohome.com/legal/kvkk?lang='+locale,wait_until='networkidle');assert response.status==200;expect(page.locator('h1')).to_be_visible();assert page.locator('html').get_attribute('dir')==('rtl'if locale=='ar'else'ltr');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(E/('live-legal-'+locale+'.png')),full_page=True)
  page.add_init_script("localStorage.setItem('nodeno.international-welcome.hidden','1')");page.goto('https://nodenohome.com/?page=register&lang='+locale,wait_until='networkidle');expect(page.locator('#register-form')).to_have_attribute('data-membership-version','2026-11-10.3');expect(page.locator('#register-form [name=membership]')).not_to_be_checked();assert page.locator('#footer a[href*="/legal/"]').count()>=5;assert not errors,errors
  current=page.evaluate("async lang=>{const {shopTranslate}=await import('/shop-i18n.js?v=nodeno-legal-20261110-r2');return shopTranslate('returnsBody',lang);}",locale);source=json.loads((R/'data/legal'/('payment-documents.'+locale+'.json')).read_bytes());assert current==source['returns'][0]
  checks.append({'locale':locale,'width':width,'legalDocumentVisible':True,'membershipVersionLoaded':True,'membershipUnchecked':True,'footerLegalLinks':True,'helpAlignedWithPublishedReturns':True,'noRuntimeErrors':True,'noOverflow':True});context.close()
 browser.close()
(E/'browser-live.json').write_text(json.dumps({'passed':True,'checks':checks,'productionUsersCreated':0,'productionOrdersCreated':0,'consentChanges':0},indent=2)+'\n');print(json.dumps({'passed':True,'locales':4,'productionWrites':0}))

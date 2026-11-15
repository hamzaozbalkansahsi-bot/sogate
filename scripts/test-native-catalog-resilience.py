#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-catalog-resilience.py
# Açıklama   : Yerel gerçek vitrinde ilk katalog bağlantısını keser; tek tekrarda gerçek verinin yüklenmesini doğrular.
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from native_browser_ready import NativePageReadiness

ROOT=Path(__file__).resolve().parent.parent;BASE='https://127.0.0.1:3188/test';results=[]
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=True);page=context.new_page();count=[0];errors=[]
  def fail_first(route):
   count[0]+=1
   if count[0]==1:route.abort('connectionreset')
   else:route.continue_()
  page.route(BASE+'/api/catalog',fail_first);page.on('pageerror',lambda error:errors.append(str(error)));ready=NativePageReadiness(page,BASE,30000)
  try:
   page.goto(BASE+'/?lang=tr');ready.wait();assert count[0]==2 and page.locator('#root-links a').count()>0
   assert page.locator('body').get_attribute('data-page')=='home' and not errors,errors
   release=context.request.get(BASE+'/api/deployment-status').json()['release']
   result={'engine':engine,'release':release,'initialConnectionResetInjected':True,'actualCatalogAfterRetry':True,'attempts':2,'pageErrors':0,'realPayment':False};results.append(result);print(json.dumps(result),flush=True)
  finally:context.close();browser.close()
(ROOT/'.local/native-catalog-resilience-local.json').write_text(json.dumps(results,indent=2),encoding='utf8')

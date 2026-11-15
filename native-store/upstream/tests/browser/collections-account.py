"""Isolated source-only real PHP account UI: explicit import, durable CAS and logout."""
from pathlib import Path
import json, uuid
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[2];ORIGIN='https://127.0.0.1:4193'
report={'testOnly':True,'origin':ORIGIN,'checks':[],'errors':[]}
with sync_playwright() as p:
 for engine in ('chromium','webkit'):
  executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
  browser=getattr(p,engine).launch(executable_path=str(executable),headless=True)
  context=browser.new_context(ignore_https_errors=True,viewport={'width':1440,'height':1000});page=context.new_page();page.on('pageerror',lambda error:report['errors'].append(str(error)))
  assert context.request.get(ORIGIN+'/api/health').json()['testOnly'] is True
  page.goto(ORIGIN+'/?page=catalog&lang=tr');page.wait_for_load_state('networkidle');page.locator('[data-collect]').first.click();page.locator('#collection-name').fill('Özel salon');page.locator('#collection-name-form button').click();expect(page.locator('#collection-dialog')).not_to_be_visible()
  token=context.request.get(ORIGIN+'/api/account').json()['csrfToken']
  reply=context.request.post(ORIGIN+'/api/account/register',headers={'Origin':ORIGIN,'X-CSRF-Token':token},data={'name':'Collection UI Tester','email':f'collection-{uuid.uuid4().hex}@example.invalid','password':'Nodeno-collection-ui-123','consent':True});assert reply.status==201,reply.status
  page.goto(ORIGIN+'/?page=collections&lang=tr');page.wait_for_load_state('networkidle');expect(page.locator('[data-shopping=import-lists]')).to_be_visible()
  assert context.request.get(ORIGIN+'/api/account/collections').json()['collections']==[], 'Guest import must be explicit'
  page.locator('[data-shopping=import-lists]').click();expect(page.locator('.collection-list a')).to_have_count(1);page.locator('.collection-list a').click();expect(page.locator('.collection-products .product-card')).to_have_count(1)
  second=context.new_page();second.goto(page.url);second.wait_for_load_state('networkidle');expect(second.locator('.collection-products h2')).to_have_text('Özel salon')
  page.locator('[data-list-rename]').click();page.locator('#collection-name').fill('Birinci cihaz');page.locator('#collection-name-form button').click();expect(page.locator('.collection-products h2')).to_have_text('Birinci cihaz')
  second.locator('[data-list-rename]').click();second.locator('#collection-name').fill('Eski cihaz');second.locator('#collection-name-form button').click();expect(second.locator('#collection-content .error')).to_be_visible()
  assert context.request.get(ORIGIN+'/api/account/collections').json()['collections'][0]['name']=='Birinci cihaz','Stale save must not overwrite another device'
  second.locator('[data-shopping=reload-lists]').last.click();expect(second.locator('#collection-name')).to_be_visible();second.locator('#collection-name').fill('İkinci cihaz');second.locator('#collection-name-form button').click();expect(second.locator('.collection-products h2')).to_have_text('İkinci cihaz')
  page.reload();page.wait_for_load_state('networkidle');expect(page.locator('.collection-products h2')).to_have_text('İkinci cihaz')
  page.locator('#account-trigger').click()
  with page.expect_response('**/api/account/logout') as outgoing:
   page.locator('[data-action=logout]').click()
  assert outgoing.value.status==200,outgoing.value.status
  page.wait_for_function("!new URLSearchParams(location.search).has('page')")
  assert context.request.get(ORIGIN+'/api/account').json()['user'] is None,'Logout must end the session'
  page.goto(ORIGIN+'/?page=collections&lang=tr');page.wait_for_load_state('networkidle');expect(page.locator('.collection-list a')).to_have_count(0)
  assert 'İkinci cihaz' not in page.evaluate('JSON.stringify(localStorage)'),'Private collection data must not be stored in localStorage'
  report['checks'].append({'engine':engine,'passed':['explicitGuestImport','privateServerPersistence','crossTabCASConflict','conflictRetry','reloadPersistence','logoutIsolation']})
  context.close();browser.close()
 assert not report['errors'],report['errors']
 report['passed']=True
(ROOT/'artifacts/shopping-experience/account-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':True,'engines':len(report['checks'])}))

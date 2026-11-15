from pathlib import Path
import json
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[2];ORIGIN='https://127.0.0.1:4193'
report={'testOnly':True,'origin':ORIGIN,'checks':[]}
with sync_playwright() as p:
 for engine in ('chromium','webkit'):
  executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
  b=getattr(p,engine).launch(executable_path=str(executable));c=b.new_context(ignore_https_errors=True,viewport={'width':1440,'height':1000});page=c.new_page()
  page.goto(ORIGIN+'/?page=catalog&lang=tr');page.wait_for_load_state('networkidle')
  page.evaluate('localStorage.setItem("nodeno.cart.v1",JSON.stringify([{id:"2393",quantity:2},{id:"2395",quantity:3}]))');page.goto(ORIGIN+'/?page=cart&lang=tr');page.wait_for_load_state('networkidle')
  page.locator('[data-remove="2393"]').click();expect(page.locator('[data-shopping=undo-cart]')).to_be_visible();page.locator('[data-select="2395"]').uncheck();expect(page.locator('[data-shopping=undo-cart]')).to_have_count(0)
  page.evaluate('localStorage.setItem("nodeno.saved.v1",JSON.stringify(["2393","2395"]))');page.goto(ORIGIN+'/?page=favorites&lang=tr');page.wait_for_load_state('networkidle');page.locator('[data-shopping=favorite-cart]').click();page.goto(ORIGIN+'/?page=cart&lang=tr');page.wait_for_load_state('networkidle');expect(page.locator('[data-cart-quantity="2395"]')).to_have_value('3');expect(page.locator('[data-cart-quantity="2393"]')).to_have_value('1')
  page.goto(ORIGIN+'/?page=catalog&lang=tr');page.wait_for_load_state('networkidle');ids=page.locator('#product-grid [data-compare]').evaluate_all('(buttons)=>buttons.slice(0,5).map(b=>b.dataset.compare)');assert len(ids)==5
  for id in ids:page.locator(f'#product-grid [data-compare="{id}"]').click()
  assert len(page.evaluate('JSON.parse(localStorage.getItem("nodeno.compare.v1"))'))==4
  expect(page.locator(f'#product-grid [data-compare="{ids[-1]}"]')).to_have_attribute('aria-pressed','false')
  page.locator('#product-grid [data-collect]').first.click();page.locator('#collection-name').fill('Silme kontrolü');page.locator('#collection-name-form button').click();expect(page.locator('#collection-dialog')).not_to_be_visible()
  page.goto(ORIGIN+'/?page=collections&lang=tr');page.wait_for_load_state('networkidle');page.locator('.collection-list a').click();page.locator('[data-list-delete]').click();page.locator('[data-close=collection-dialog]').click();expect(page.locator('.collection-list a')).to_have_count(1)
  page.locator('[data-list-remove]').click();expect(page.locator('.collection-products .product-card')).to_have_count(0);page.locator('[data-list-delete]').click();page.locator('[data-list-delete-confirm]').click();expect(page.locator('.collection-list a')).to_have_count(0)
  report['checks'].append({'engine':engine,'passed':['undoInvalidatedBySelectionChange','favoritesBulkKeepsExistingQuantities','comparisonCapacity','deleteRequiresConfirmation','collectionItemRemoval']});c.close();b.close()
report['passed']=True;(ROOT/'artifacts/shopping-experience/state-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'passed':True,'engines':len(report['checks'])}))

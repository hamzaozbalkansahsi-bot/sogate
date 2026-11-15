from pathlib import Path
import json,os
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];ORIGIN=os.environ.get('NODENO_SHOPPING_URL','https://127.0.0.1:4193');phase=os.environ.get('NODENO_SHOPPING_PHASE','source')
results=[]
with sync_playwright() as p:
 for engine in ('chromium','webkit'):
  executable=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe' if engine=='chromium' else ROOT/'artifacts/runtime-browsers/webkit-2370/Playwright.exe'
  b=getattr(p,engine).launch(executable_path=str(executable))
  for width in (390,1440):
   c=b.new_context(viewport={'width':width,'height':900},ignore_https_errors=phase!='live');page=c.new_page();page.goto(ORIGIN+'/?page=catalog&lang=tr');page.wait_for_load_state('networkidle')
   page.locator('#product-grid [data-compare]').first.click();page.locator('#product-grid [data-add]').first.click();expect(page.locator('#toast')).to_be_visible()
   toast=page.locator('#toast').bounding_box();dock=page.locator('#shopping-dock').bounding_box()
   assert toast['y']+toast['height']<=dock['y'],f'{engine}/{width}: notification obscures comparison actions'
   results.append({'engine':engine,'width':width,'noOverlap':True});c.close()
  b.close()
(ROOT/f'artifacts/shopping-experience/{phase}-notifications.json').write_text(json.dumps({'passed':True,'checks':results},indent=2),encoding='utf-8');print(json.dumps({'passed':True,'checks':len(results)}))

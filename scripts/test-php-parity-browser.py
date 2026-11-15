#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php-parity-browser.py
# Açıklama   : NODENO ana sayfa, arama, misafir favori/liste ve karşılaştırma akışını sınar.
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent.parent
remote='--remote' in sys.argv
base='https://sexogate.com/test' if remote else 'http://127.0.0.1:3183/test'
results=[]
axe=(root/'node_modules/axe-core/axe.min.js').read_text(encoding='utf8')
def accessible(page):
 page.evaluate(axe);issues=page.evaluate("async () => (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))");assert not issues,issues
with sync_playwright() as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch(headless=True)
  try:
   for width in [360,390,430,768,1440]:
    context=browser.new_context(viewport={'width':width,'height':900},reduced_motion='reduce');page=context.new_page();page.set_default_timeout(15000);page.set_default_navigation_timeout(60000)
    try:
     page.goto(base+'/');page.wait_for_load_state('networkidle');page.locator('#age-accept').click()
     assert page.locator('.home-vitrine').count()==1,'NODENO hero and side campaigns are missing'
     assert page.locator('.category-circles').count()==1
     assert page.locator('.home-shelf').count()>0
     for link in page.locator('.footer-social a').all():assert not link.inner_text().strip() and link.get_attribute('aria-label')
     if width>768:
      page.locator('[data-mega-toggle]').click();page.locator('#mega-menu').wait_for(state='visible');page.keyboard.press('Escape');assert not page.locator('#mega-menu').is_visible()
     query=page.locator('#header-query');query.fill('sateen');page.locator('#search-suggestions [role=option]').first.wait_for();query.press('ArrowDown');query.press('Enter');page.wait_for_url('**/urun/saten-bag-detayi');page.locator('h1').wait_for();page.locator('[data-personal-action=favorite]').first.click();page.wait_for_function("() => document.querySelector('[data-personal-action=favorite]').getAttribute('aria-pressed')==='true'")
     form=page.locator('#product-purchase');form.locator('input[name=quantity]').fill('2');form.get_by_role('button',name='Sepete ekle',exact=True).click();form.locator('.form-message').filter(has_text='Sepetinize eklendi').wait_for()
     page.goto(base+'/favoriler');page.locator('.personal-grid .product-card').first.wait_for();accessible(page);assert not page.locator('form[data-api="/api/auth/login"]').count();page.locator('[data-personal-select-all]').check();page.locator('[data-personal-bulk] > .personal-bulk-toolbar button').click();page.locator('[data-personal-bulk] .form-message').filter(has_text='Mevcut adetler korundu').wait_for()
     cart=page.request.get(base+'/api/cart').json();assert cart['count']==2,'Bulk add changed existing quantity'
     page.locator('[data-list-product]').first.click();page.locator('#save-list-dialog[open]').wait_for();page.locator('#save-list-form input[name=name]').fill('İç Giyim · Özel');page.locator('#save-list-form button').click();page.locator('#save-list-dialog').wait_for(state='hidden')
     page.goto(base+'/listeler');page.get_by_role('heading',name='İç Giyim · Özel',exact=True).wait_for();rename=page.locator('[data-personal-form=list-rename]');rename.locator('input[name=name]').fill('Şişli · Hediye');rename.locator('button').click();page.get_by_role('heading',name='Şişli · Hediye',exact=True).wait_for()
     page.locator('[data-personal-action=compare]').first.click();page.wait_for_function("() => document.querySelector('[data-personal-action=compare]').getAttribute('aria-pressed')==='true'");page.goto(base+'/karsilastir');page.locator('.comparison-table').wait_for();accessible(page);page.locator('[data-compare-different]').check();assert page.locator('[data-comparison-equal=true]:visible').count()==0
     page.goto(base+'/listeler');page.locator('[data-remove-list]').click();page.locator('#remove-list-dialog[open]').wait_for();page.locator('[data-confirm-remove-list]').click();page.locator('#remove-list-dialog').wait_for(state='hidden');assert page.locator('.personal-list-nav a').count()==0
     page.goto(base+'/urunler');page.wait_for_load_state('networkidle');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
     folder=root/('docs/screenshots/php-parity-remote' if remote else 'docs/screenshots/php-parity-local');folder.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(folder/f'{engine}-catalog-{width}.png'));page.goto(base+'/');page.wait_for_load_state('networkidle');page.screenshot(path=str(folder/f'{engine}-home-{width}.png'),full_page=True)
     results.append({'engine':engine,'width':width,'homeStructure':True,'searchKeyboardTypo':True,'guestFavorites':True,'bulkPreservedQuantity':True,'privateListsCrud':True,'comparison':True,'iconOnlySocial':True})
    finally:context.close()
  finally:browser.close()
(root/('.local/php-parity-browser-remote.json' if remote else '.local/php-parity-browser-local.json')).write_text(json.dumps(results,indent=2),encoding='utf8');print(json.dumps(results))

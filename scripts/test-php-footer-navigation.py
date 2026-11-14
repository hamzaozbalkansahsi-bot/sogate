#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-php-footer-navigation.py
# Açıklama   : Footer sonu, mobil boyut değişimi ve sıçramasız doğal sayfa/geri gezinmesini sınar.
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent.parent;remote='--remote' in sys.argv;base='https://sexogate.com/test' if remote else 'http://127.0.0.1:3183/test';results=[]
with sync_playwright() as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch(headless=True)
  try:
   for width in [360,390,430,768,1440]:
    context=browser.new_context(viewport={'width':width,'height':844},reduced_motion='no-preference');page=context.new_page();page.set_default_navigation_timeout(60000)
    try:
     page.goto(base+'/');page.wait_for_load_state('networkidle');page.locator('#age-accept').click()
     for height in [640,844,710]:
      page.set_viewport_size({'width':width,'height':height});page.evaluate("scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'})");page.wait_for_timeout(100)
      gap=page.evaluate("document.documentElement.scrollHeight-(document.querySelector('footer').getBoundingClientRect().bottom+scrollY)");assert abs(gap)<=2,(engine,width,height,gap)
      assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
     page.evaluate('scrollTo({top:0,behavior:"auto"})');page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');assert page.evaluate('scrollY')<=1,'Global smooth scrolling moves the page during restoration'
     footer=page.locator('footer');links=footer.locator('a[href]').evaluate_all('(nodes)=>nodes.map(n=>n.getAttribute("href"))');assert all('/test/' in link or link.startswith(('https:','mailto:','#')) for link in links)
     for path in ['/blog','/yasal/iade','/yasal/kvkk','/site-haritasi','/iletisim']:
      response=page.goto(base+path);assert response.status==200;(page.locator('h1')).wait_for();assert page.evaluate('scrollY')<=1
     page.goto(base+'/urunler');page.wait_for_load_state('networkidle');page.evaluate("scrollTo({top:220,behavior:'instant'})");old=page.evaluate('scrollY');page.locator('footer a[href$="/blog"]').first.click();page.wait_for_url('**/blog');page.wait_for_load_state('networkidle');assert page.evaluate('scrollY')<=1
     page.go_back();page.wait_for_load_state('networkidle');assert page.url.endswith('/urunler');assert page.evaluate('scrollY')>=old
     folder=root/('docs/screenshots/php-footer-remote' if remote else 'docs/screenshots/php-footer-local');folder.mkdir(parents=True,exist_ok=True);page.evaluate("scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'})");page.screenshot(path=str(folder/f'{engine}-footer-{width}.png'))
     results.append({'engine':engine,'width':width,'footerEnd':True,'resize':True,'scrollRestoration':True,'informationLinks':True})
    finally:context.close()
  finally:browser.close()
(root/('.local/php-footer-remote.json' if remote else '.local/php-footer-local.json')).write_text(json.dumps(results,indent=2),encoding='utf8');print(json.dumps(results))

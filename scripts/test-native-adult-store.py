#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-adult-store.py
# Açıklama   : Yetişkin girişi, mobilya içeriği yokluğu, misafir erişimi ve footer sonunu sınar.
import json,os,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');scope=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','adult-local');assert re.fullmatch('[a-z-]+',scope)
assert BASE in ['https://127.0.0.1:3188/test','https://sexogate.com/test'] or re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate.com)/test/native-preview-[a-f0-9]{16}',BASE)
folder=ROOT/('docs/screenshots/native-store-'+scope);folder.mkdir(parents=True,exist_ok=True);results=[]
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),viewport={'width':390,'height':844});page=context.new_page();page.set_default_navigation_timeout(60000 if BASE.startswith('https://sexogate.com')else 30000);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  try:
   page.goto(BASE+'/');page.wait_for_load_state('networkidle');gate=page.locator('#sexogate-age-gate');gate.wait_for(state='visible');assert not page.locator('#international-welcome').count();assert not page.locator('.welcome-country-map').count();page.keyboard.press('Escape');assert gate.is_visible();page.keyboard.press('Tab');assert gate.locator('.sexogate-age-exit').evaluate('(e)=>e===document.activeElement');page.keyboard.press('Shift+Tab');assert gate.locator('.sexogate-age-accept').evaluate('(e)=>e===document.activeElement')
   page.screenshot(path=str(folder/(engine+'-age-390.png')))
   page.set_viewport_size({'width':1440,'height':950});page.screenshot(path=str(folder/(engine+'-age-1440.png')));gate.locator('.sexogate-age-accept').click();assert not gate.count();assert 'login' not in page.url and 'giris' not in page.url
   for path in ['/','/?page=categories','/?page=collections','/?page=help','/?page=shipping','/blog']:
    response=page.goto(BASE+path);assert response.status==200,(path,response.status);page.wait_for_load_state('networkidle');assert not page.locator('#sexogate-age-gate').count()
    button=page.get_by_role('button',name='Yalnız gerekli',exact=True)
    if button.count()and button.first.is_visible():button.first.click()
    text=page.title()+'\n'+page.locator('body').inner_text();assert not re.search(r'mobilya|kurulum|montaj|çocuk odası|genç odası|Boya miktarı|ölçülü fikirler|İyi tasarım|PTYS Technologies|Orta Asya',text,re.I),(path,text[:350]);assert not page.locator('.welcome-country-map').count()
    for width in [360,390,430,768,1440]:
     page.set_viewport_size({'width':width,'height':844});assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),(path,width)
   page.goto(BASE+'/');page.wait_for_load_state('networkidle');page.set_viewport_size({'width':390,'height':844});page.evaluate('()=>scrollTo(0,document.documentElement.scrollHeight)');page.screenshot(path=str(folder/(engine+'-footer-390.png')))
   gap=page.evaluate('()=>{const f=document.querySelector("#footer").getBoundingClientRect();return document.documentElement.scrollHeight-(f.bottom+scrollY)}');assert gap<=120,('after-footer-gap',gap)
   assert page.locator('.store-footer .social-links a').count()==4
   for link in page.locator('.store-footer .social-links a').all():assert link.inner_text()=='' and link.get_attribute('aria-label')and link.locator('svg').count()==1
   release=context.request.get(BASE+'/api/deployment-status').json()['release'];assert not errors,errors;results.append({'base':BASE,'release':release,'engine':engine,'ageGate':True,'escapeBypassBlocked':True,'keyboardFocus':True,'guestBrowsing':True,'ackSurvivesNavigation':True,'worldMap':False,'furnitureCopy':False,'widths':[360,390,430,768,1440],'footerGap':gap,'iconOnlySocialLinks':4,'pageErrors':0});print(json.dumps(results[-1]),flush=True)
  finally:context.close();browser.close()
(ROOT/('.local/native-adult-'+scope+'.json')).write_text(json.dumps(results,indent=2),encoding='utf8')

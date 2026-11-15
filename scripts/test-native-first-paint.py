#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-first-paint.py
# Açıklama   : İlk sunucu HTML'sinin JavaScript beklemeden aynı küçük resimli ana sayfayı göstermesini sınar.
import json,os,re,ssl,urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/')
scope=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','paint-local')
assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)
assert re.fullmatch('[a-z-]+',scope)
tls=ssl._create_unverified_context()if BASE.startswith('https://127.')else ssl.create_default_context()
release=json.load(urllib.request.urlopen(BASE+'/api/deployment-status',context=tls,timeout=30))['release']
response=urllib.request.urlopen(BASE+'/?lang=tr',context=tls,timeout=30)
soup=BeautifulSoup(response.read(),'html.parser')
assert len(soup.select('main .sg-market-home'))==1,'FIRST_HTML_USES_LEGACY_HOMEPAGE'
assert len(soup.select('main .sg-campaign-card'))==4,'FIRST_HTML_COMPACT_CARD_COUNT'
assert not soup.select('main .main-campaign,main .campaign-copy,main .campaign-photo'),'FIRST_HTML_LEGACY_HERO'
assert len(soup.select('main .sg-campaign-card img'))==4,'FIRST_HTML_REAL_IMAGES'
assert soup.select_one('main h1').get_text(strip=True)=='Tutkunu Keşfet.'
brand=json.loads((ROOT/'native-store/theme/store-copy.json').read_text('utf8'))
for locale,copy in brand.items():
 document=BeautifulSoup(urllib.request.urlopen(BASE+'/?lang='+locale,context=tls,timeout=30).read(),'html.parser')
 assert len(document.select('main .sg-campaign-card'))==4,locale
 assert document.select_one('main h1').get_text(strip=True)==copy['slogan'],locale
 assert document.html['dir']==('rtl'if locale in ['ar','fa']else'ltr'),locale
results=[];folder=ROOT/('docs/screenshots/native-store-'+scope);folder.mkdir(parents=True,exist_ok=True)
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();context=browser.new_context(java_script_enabled=False,ignore_https_errors=BASE.startswith('https://127.'))
  try:
   page=context.new_page();page.set_default_navigation_timeout(60000)
   for width in [390,1440]:
    page.set_viewport_size({'width':width,'height':900});page.goto(BASE+'/?lang=tr');page.locator('.sg-campaign-card').first.wait_for()
    assert page.locator('.sg-campaign-card').count()==4
    assert page.locator('.sg-campaign-card').evaluate_all('(cards)=>cards.every(e=>e.getBoundingClientRect().height<240)')
    assert page.locator('.sg-campaign-card img').evaluate_all('(images)=>images.every(i=>i.complete&&i.naturalWidth>0)')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(folder/f'{engine}-no-javascript-{width}.png'))
   result={'base':BASE,'release':release,'engine':engine,'serverHtmlCompactCards':4,'serverLocales':11,'javascriptDisabled':True,'legacyHero':False,'realImages':True,'widths':[390,1440]};results.append(result);print(json.dumps(result),flush=True)
  finally:context.close();browser.close()
(ROOT/('.local/native-'+scope+'.json')).write_text(json.dumps(results,indent=2),encoding='utf8')

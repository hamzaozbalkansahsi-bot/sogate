#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-selection-admin.py
# Açıklama   : Derlenen gerçek sipariş görünümünü dış erişim ve veritabanı yazımı olmadan izole örnekle sınar.
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent;package=json.loads((ROOT/'.local/native-stage-package.json').read_text('utf8'));source=(Path(package['bundle'])/'public/admin-payments.js').read_text('utf8')
fixture={'id':'isolated-view-order','status':'paid','totalMinor':13001,'contact':{'name':'İzole test','email':'fixture@example.invalid','phone':'','delivery':{}},'seller':{'name':'İzole test satıcısı'},'vatMinor':0,'snapshot':{'lines':[{'name':{'tr':'İzole ürün'},'code':'FIXTURE','quantity':1,'totalMinor':13001,'selectionSnapshot':{'summary':'Beden: XL · Renk: Siyah','sourceSku':'FIXTURE-XL'},'options':{'selection':{'size':'opaque-size-id','color':'opaque-color-id'}}}]}}
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content('<main id="fixture"></main>');script=source+'\nconst fixture='+json.dumps(fixture,ensure_ascii=False)+";await renderPaymentOrders({container:document.querySelector('#fixture'),api:async()=>({data:[fixture]}),esc:value=>String(value??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]))});window.selectionViewReady=true;";page.add_script_tag(type='module',content=script);page.wait_for_function('window.selectionViewReady===true');page.locator('summary').click();text=page.locator('li').inner_text();assert 'Beden: XL · Renk: Siyah'in text and 'FIXTURE-XL'in text;assert 'opaque-size-id'not in text and 'opaque-color-id'not in text;assert errors==[],errors;browser.close()
print(json.dumps({'engines':['chromium','webkit'],'readableOrderSelection':True,'sourceSkuVisible':True,'opaqueIdsHidden':True,'isolatedViewFixture':True,'databaseWritten':False,'stripeCalled':False,'release':package['release']},ensure_ascii=False))

#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-marketplace-cart-notifications.py
# Açıklama   : Yeni pazaryeri kataloğunun gerçek matrisleriyle sepet, mobil toplam ve bildirim yetkilerini doğrular.
import json,os,re,sys,secrets,base64
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from native_browser_ready import NativePageReadiness
from native_test_errors import safe_error
sys.excepthook=safe_error
ROOT=Path(__file__).resolve().parent.parent;BASE=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');scope=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','marketplace-cart-notifications-local')
assert re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',BASE)and scope in ['marketplace-cart-notifications-'+suffix for suffix in ['local','preview','remote']]
folder=ROOT/('docs/screenshots/native-store-'+scope);folder.mkdir(parents=True,exist_ok=True);results=[]
def choose_examples(products):
 assert all(re.fullmatch('sg_ty_[a-f0-9]{16}',product['id'])for product in products),'ARCHIVED_PRODUCTS_REPUBLISHED'
 candidates=[]
 for product in products:
  model=product.get('variantSelection',{})
  if model.get('mode')!='matrix'or not model.get('required')or model.get('blocked'):continue
  active=[];seen=set()
  for variant in model.get('variants',[]):
   if not variant.get('active'):continue
   values=variant['values'];key=json.dumps(values,sort_keys=True)
   assert set(values)=={axis['id']for axis in model['axes']},'INCOMPLETE_SOURCE_MATRIX'
   assert all(any(value['id']==values[axis['id']]for value in axis['values'])for axis in model['axes']),'UNKNOWN_MATRIX_VALUE'
   if key not in seen:active.append(values);seen.add(key)
  if len(active)>=2:candidates.append((product,active))
 assert len(candidates)>=2,'TWO_REAL_SOURCE_MATRICES_REQUIRED'
 return candidates[:2]

def line(product,values):
 return {'id':product['id'],'quantity':1,'options':{'selection':values}}

def description(product,values):
 return ' · '.join({'size':'Beden','color':'Renk'}.get(axis['id'],axis['label'])+': '+next(value['label']for value in axis['values']if value['id']==values[axis['id']])for axis in product['variantSelection']['axes'])

def selection_label(page,product,values):
 key=product['id']+'~'+'.'.join(values[axis['id']]for axis in product['variantSelection']['axes'])
 return page.locator('.basket-item').filter(has=page.locator('[data-selection-edit="'+key+'"]')).locator('.sg-cart-selection')

def edit_first_selection(page,ready,product,values):
 page.locator('[data-selection-edit]').first.click();dialog=page.locator('.sg-variant-dialog');dialog.wait_for(state='visible')
 for axis,value in values.items():dialog.locator('[data-axis="'+axis+'"] [data-choice="'+value+'"]').click()
 assert dialog.locator('.sg-variant-add').is_enabled();element=dialog.element_handle();dialog.locator('.sg-variant-add').click()
 page.wait_for_function('(element)=>!element.isConnected',arg=element);ready.wait()
 stored=page.evaluate('()=>JSON.parse(localStorage.getItem("nodeno.cart.v1")||"[]")')
 edited=[row for row in stored if row['id']==product['id']]
 assert len(stored)==2 and len(edited)==1 and edited[0]['options']['selection']==values,'EDITED_MATRIX_SELECTION_NOT_PERSISTED'
 expect(selection_label(page,product,values)).to_have_text(description(product,values))
def read_notification(context,url):
 # Playwright bu salt okunur GET için yalnız ECONNRESET'i bir kez tekrarlar; HTTP redleri ve yazmalar tekrarlanmaz.
 return context.request.get(url,max_retries=1)
def notify_api(context,products):
 endpoint=BASE+'/api/notifications';state=read_notification(context,endpoint).json();assert 'csrfToken'in state and 'publicKey'in state,state
 origin=BASE.split('/test')[0];headers={'Origin':origin,'X-CSRF-Token':state['csrfToken']};id=products[0]['id'];b64=lambda b:base64.urlsafe_b64encode(b).decode().rstrip('=')
 subscription={'endpoint':'https://fcm.googleapis.com/wp/sexogate-isolated-'+secrets.token_hex(10),'keys':{'p256dh':state['publicKey'],'auth':b64(secrets.token_bytes(16))}}
 data={'consent':True,'productIds':[id],'subscription':subscription}
 assert context.request.post(endpoint,data=data,headers={'Origin':origin}).status==403
 assert context.request.post(endpoint,data=data,headers={**headers,'Origin':'https://example.invalid'}).status==403
 bad={**data,'subscription':{**subscription,'endpoint':'https://127.0.0.1/private'}};assert context.request.post(endpoint,data=bad,headers=headers).status==422
 bad={**data,'productIds':['not_a_public_product']};assert context.request.post(endpoint,data=bad,headers=headers).status==422
 try:
  response=context.request.post(endpoint,data=data,headers=headers);assert response.status==200,{'status':response.status,'body':response.text()[:100]}
  assert read_notification(context,endpoint).json()['enabled']is True
  other=context.browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'))
  try:
   foreign=read_notification(other,endpoint).json();assert foreign['enabled']is False and foreign['productIds']==[]
   denied=other.request.post(endpoint,data=data,headers={'Origin':origin,'X-CSRF-Token':foreign['csrfToken']});assert denied.status==409
   assert other.request.delete(endpoint,data={},headers={'Origin':origin,'X-CSRF-Token':foreign['csrfToken']}).status==200
   assert read_notification(context,endpoint).json()['enabled']is True
  finally:other.close()
  assert context.request.put(endpoint,data={'productIds':[]},headers=headers).status==200
  assert read_notification(context,endpoint).json()['productIds']==[]
 finally:
  assert context.request.delete(endpoint,data={},headers=headers).status==200
 assert read_notification(context,endpoint).json()['enabled']is False
 return {'csrf':True,'origin':True,'ssrf':True,'publicProductValidation':True,'deviceOwnership':True,'subscribeAndRevoke':True,'externalPushSent':False}
with sync_playwright()as p:
 for engine in ['chromium','webkit']:
  browser=getattr(p,engine).launch();context=browser.new_context(ignore_https_errors=BASE.startswith('https://127.0.0.1'),viewport={'width':390,'height':844});context.add_init_script('''window.__sgPermissionRequests=0;if('Notification'in window){const original=Notification.requestPermission;Notification.requestPermission=function(...args){window.__sgPermissionRequests++;return original.apply(this,args);};}''');page=context.new_page();page.set_default_timeout(30000);page.set_default_navigation_timeout(60000);ready=NativePageReadiness(page,BASE,60000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  try:
   page.goto(BASE+'/?lang=tr',wait_until='domcontentloaded');ready.wait();gate=page.locator('.sexogate-age-accept')
   if gate.count():gate.click();page.locator('#sexogate-age-gate').wait_for(state='detached')
   consent=page.get_by_role('button',name='Yalnız gerekli',exact=True)
   if consent.count()and consent.is_visible():consent.click()
   data=context.request.get(BASE+'/api/catalog',timeout=60000).json();products=data.get('catalog',data)['products'];examples=choose_examples(products)
   page.evaluate('(items)=>localStorage.setItem("nodeno.cart.v1",JSON.stringify(items))',[line(product,values[0])for product,values in examples]);page.goto(BASE+'/?page=cart&lang=tr',wait_until='domcontentloaded');ready.wait();assert page.locator('.basket-item').count()==2;assert page.locator('.sg-cart-selection').count()==2
   for index,(product,values)in enumerate(examples):expect(page.locator('.sg-cart-selection').nth(index)).to_have_text(description(product,values[0]))
   for width in [360,390,430,768,1440]:
    print(engine+': cart '+str(width),flush=True);page.set_viewport_size({'width':width,'height':900});assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth')
    assert page.locator('.basket-photo img').evaluate_all('nodes=>nodes.every(e=>e.complete&&e.naturalWidth>0&&getComputedStyle(e).objectFit==="contain")')
    if width<=900:
     box=page.locator('.sg-cart-bar').bounding_box();nav=page.locator('.bottom-nav').bounding_box()
     if nav:assert box['y']+box['height']<=nav['y']+2,(width,box,nav)
     else:assert box['y']+box['height']<=900,(width,box)
     assert page.locator('.sg-cart-bar>.button').is_disabled(),'REAL_CHECKOUT_MUST_STAY_CLOSED'
    if width in [390,1440]:page.screenshot(path=str(folder/(engine+'-cart-'+str(width)+'.png')))
   print(engine+': cart variant edit',flush=True);edit_first_selection(page,ready,examples[0][0],examples[0][1][1]);page.reload(wait_until='domcontentloaded');ready.wait();expect(selection_label(page,examples[0][0],examples[0][1][1])).to_have_text(description(examples[0][0],examples[0][1][1]))
   print(engine+': cart selection',flush=True);page.set_viewport_size({'width':390,'height':900});total=page.locator('.sg-cart-bar strong').inner_text();page.locator('[data-select]').first.uncheck();expect(page.locator('.basket-item[data-selected=true]')).to_have_count(1);expect(page.locator('.sg-cart-bar strong')).not_to_have_text(total)
   page.locator('#select-all').check();expect(page.locator('.sg-cart-bar strong')).to_have_text(total)
   print(engine+': cart quantity',flush=True);quantity=page.locator('[data-cart-quantity]').first;before=int(quantity.input_value());page.locator('[data-cart-step="1"]').first.click();expect(page.locator('[data-cart-quantity]').first).to_have_value(str(before+1));expect(page.locator('.sg-cart-bar strong')).not_to_have_text(total)
   page.locator('[data-sg-cart-summary]').click();summary=page.locator('.sg-cart-summary-dialog[open]');summary.wait_for();assert summary.locator('dl').count()>0;page.keyboard.press('Escape');summary.wait_for(state='detached')
   print(engine+': cart remove',flush=True);page.locator('[data-move]').first.click();expect(page.locator('.basket-item')).to_have_count(1);assert page.evaluate('()=>JSON.parse(localStorage.getItem("nodeno.saved.v1")||"[]").length')>=1
   page.locator('[data-remove]').first.click();expect(page.locator('.basket-item')).to_have_count(0);expect(page.locator('.sg-cart-bar')).to_have_count(0)
   print(engine+': notification API',flush=True);api=notify_api(context,products)
   page.locator('[data-sg-notifications]').last.click();dialog=page.locator('.sg-notify-dialog[open]');dialog.wait_for();page.wait_for_function('()=>document.querySelector(".sg-notify-dialog [role=status]").textContent!=="Hazırlanıyor…"');assert dialog.locator('.button-dark').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(90, 10, 32)';assert dialog.inner_text().find('kilit ekranında')>=0;page.screenshot(path=str(folder/(engine+'-notifications-390.png')));page.keyboard.press('Escape');dialog.wait_for(state='detached')
   assert page.evaluate('()=>window.__sgPermissionRequests')==0;assert not errors,errors;results.append({'engine':engine,'base':BASE,'release':context.request.get(BASE+'/api/deployment-status').json()['release'],'widths':[360,390,430,768,1440],'cartSelectionTotals':True,'quantityUpdates':True,'variantLabels':True,'variantEditReload':True,'source':'trendyol_individual_pages','sourceMatrix':True,'moveToFavoritesAndRemove':True,'summaryDialog':True,'stickyOverlap':False,'notificationApi':api,'permissionNotRequestedAutomatically':True,'pageErrors':0})
  except Exception:
   print(json.dumps({'engine':engine,'pageErrors':errors}),flush=True);page.screenshot(path=str(folder/(engine+'-diagnostic.png')));raise
  finally:context.close();browser.close()
(ROOT/('.local/native-'+scope+'.json')).write_text(json.dumps(results,indent=2),encoding='utf8');print(json.dumps(results),flush=True)

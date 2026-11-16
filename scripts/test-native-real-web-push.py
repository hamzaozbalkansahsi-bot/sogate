#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/test-native-real-web-push.py
# Açıklama   : Yalnız izole Chrome profilinde gerçek push aboneliğini ve tek kontrollü teslimi gözler.
import hashlib,json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from native_browser_ready import NativePageReadiness

ROOT=Path(__file__).resolve().parent.parent;BASE='https://sexogate.com/test'
ready_file=ROOT/'.local/native-real-push-ready.json';result_file=ROOT/'.local/native-real-push-result.json'
ready_file.unlink(missing_ok=True);result={'actualDelivery':False,'physicalIosDevice':False,'realStockEvent':False};context=None
with sync_playwright()as p:
 browser=p.chromium.launch(channel='chrome',headless=True,ignore_default_args=['--disable-background-networking'])
 try:
  context=browser.new_context(permissions=['notifications'],viewport={'width':390,'height':844});context.add_init_script('''if('PushManager'in window){const original=PushManager.prototype.subscribe;PushManager.prototype.subscribe=async function(...args){try{return await original.apply(this,args);}catch(error){window.__sgPushFailure={name:error.name,message:String(error.message).replace(/https:\\/\\/[^ ]+/g,'[endpoint]').slice(0,160)};throw error;}};}''');page=context.new_page();page.set_default_timeout(45000);page.set_default_navigation_timeout(60000);readiness=NativePageReadiness(page,BASE,60000);api_status=[];page.on('response',lambda response:api_status.append(response.status)if response.request.method=='POST'and response.url.endswith('/api/notifications')else None)
  page.goto(BASE+'/?lang=tr',wait_until='domcontentloaded');readiness.wait();gate=page.locator('.sexogate-age-accept')
  if gate.count():gate.click();page.locator('#sexogate-age-gate').wait_for(state='detached')
  necessary=page.get_by_role('button',name='Yalnız gerekli',exact=True)
  if necessary.count()and necessary.is_visible():necessary.click()
  health=context.request.get(BASE+'/api/deployment-status').json();result['release']=health['release'];catalog=context.request.get(BASE+'/api/catalog').json();product=catalog.get('catalog',catalog)['products'][0]
  page.evaluate('(id)=>localStorage.setItem("nodeno.saved.v1",JSON.stringify([id]))',product['id']);page.locator('[data-sg-notifications]').last.click();dialog=page.locator('.sg-notify-dialog');button=dialog.locator('.button-dark');button.wait_for(state='visible');page.wait_for_function('()=>!document.querySelector(".sg-notify-dialog .button-dark").disabled')
  button.click();page.wait_for_function('()=>{const d=document.querySelector(".sg-notify-dialog");return d.querySelector("[role=status]").textContent.includes("açık.")||d.querySelector("[role=status]").textContent.includes("Yeniden deneyin");}',timeout=45000)
  if not dialog.locator('[role=status]').inner_text().endswith('açık.'):
   result['subscribeApiStatuses']=api_status;result['browserDiagnostics']=page.evaluate('''async()=>{const r=await navigator.serviceWorker.ready;const sub=await r.pushManager.getSubscription();return {permission:Notification.permission,existingSubscription:!!sub,workerState:r.active?.state,failure:window.__sgPushFailure};}''')
   raise RuntimeError('browser_push_subscription_unavailable')
  subscription=page.evaluate('async()=>{const registration=await navigator.serviceWorker.ready;return(await registration.pushManager.getSubscription()).toJSON();}')
  tag=hashlib.sha256((str(time.time_ns())+health['release']).encode()).hexdigest();result['subscriptionCreated']=True
  ready={'release':health['release'],'base':BASE,'createdAt':int(time.time()),'endpointHash':hashlib.sha256(subscription['endpoint'].encode()).hexdigest(),'tag':tag,'productId':product['id']};ready_file.write_text(json.dumps(ready),encoding='utf8');print(json.dumps({'subscribed':True,'release':health['release'],'waitingForSingleControlledDelivery':True}),flush=True)
  deadline=time.monotonic()+180
  while time.monotonic()<deadline:
   seen=page.evaluate('async(tag)=>{const registration=await navigator.serviceWorker.ready;const rows=await registration.getNotifications({tag});return rows.map(n=>({title:n.title,body:n.body,url:n.data?.url}));}',tag)
   if seen:
    assert seen[0]['title']=='SEXOGATE'and product.get('name',{}).get('tr','__missing__')not in seen[0]['body'];assert seen[0]['url']==BASE+'/?product='+product['id'];result.update(actualDelivery=True,privateBody=True,notificationObservedBy='Chrome ServiceWorkerRegistration.getNotifications',tag=tag);break
   page.wait_for_timeout(500)
  if not result['actualDelivery']:result['blocked']='delivery_not_observed_in_180_seconds'
 except Exception as error:
  result['blocked']=str(error)if str(error)=='browser_push_subscription_unavailable'else type(error).__name__
 finally:
  if context:
   try:
    state=context.request.get(BASE+'/api/notifications',timeout=15000).json();response=context.request.delete(BASE+'/api/notifications',data={},headers={'Origin':'https://sexogate.com','X-CSRF-Token':state['csrfToken']},timeout=15000);result['testDeviceRevoked']=response.status==200
   except Exception:result['testDeviceRevoked']=False
   context.close()
  browser.close();ready_file.unlink(missing_ok=True);result_file.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True)

"""Opt-in real Stripe sandbox tests against production payment PHP and hosted Checkout.

Credentials and mutable test data stay outside the repository in an owner-only directory.
No live key, live database, live webhook or real payment method is ever used.
"""
from pathlib import Path
import argparse,contextlib,hashlib,http.cookiejar,json,os,re,shutil,socket,subprocess,time,urllib.error,urllib.parse,urllib.request,uuid
from playwright.sync_api import sync_playwright

R=Path(__file__).resolve().parents[2]
PRIVATE=Path.home()/'.codex/private/nodeno-stripe/sandbox-20261110'
OUT=R/'artifacts/stripe-sandbox-20261110'
CLI=R/'artifacts/stripe-cli-runtime/node_modules/@stripe/cli-win32-x64/bin/stripe.exe'
PHP=R/'artifacts/runtime-php/php.exe'
CHROME=Path.home()/'AppData/Local/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-win64/chrome-headless-shell.exe'

def free_port():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

class Sandbox:
 def __init__(self,release=None):
  self.credentials=json.loads((PRIVATE/'credentials.json').read_text(encoding='utf8'))
  assert self.credentials['mode']=='test'and re.fullmatch(r'(?:sk|rk|rkcs)_test_[A-Za-z0-9]+',self.credentials['secretKey'])
  self.run=PRIVATE/('run-'+uuid.uuid4().hex);self.run.mkdir();self.storage=self.run/'data';self.storage.mkdir();self.public=self.run/'public';self.public.mkdir();self.port=free_port();self.origin='http://127.0.0.1:'+str(self.port);self.children=[];self.logs=[]
  self.code=self.run/'code';(self.code/'hosting').mkdir(parents=True);(self.code/'web').mkdir();self.hashes={}
  if release is None:sources=[(p,p.relative_to(R))for p in [*(R/'hosting').glob('*.php'),R/'web/payments.js',R/'web/styles.css']]
  else:
   release=release.resolve();assert release.parent==R/'artifacts'and release.name.startswith('cpanel-release-')
   sources=[(p,Path('hosting')/p.name)for p in(release/'private').glob('*.php')]+[(release/'public'/name,Path('web')/name)for name in ['payments.js','styles.css']]
  for source,relative in sources:
   body=source.read_bytes();(self.code/relative).write_bytes(body);self.hashes[str(relative).replace('\\','/')]=hashlib.sha256(body).hexdigest()
 def api(self,method,path,form=None,idempotency=None):
  assert method in ['GET','POST']and path.startswith('/v1/')and'\n'not in path
  headers={'Authorization':'Bearer '+self.credentials['secretKey'],'Stripe-Version':'2026-10-28.endive','Accept':'application/json'}
  if idempotency:headers['Idempotency-Key']=idempotency
  if form is not None:headers['Content-Type']='application/x-www-form-urlencoded'
  req=urllib.request.Request('https://api.stripe.com'+path,data=None if form is None else urllib.parse.urlencode(form).encode(),headers=headers,method=method)
  try:
   with urllib.request.urlopen(req,timeout=35)as response:return json.load(response)
  except urllib.error.HTTPError as error:
   obj=json.load(error).get('error',{});raise RuntimeError('Stripe '+str(error.code)+' '+str(obj.get('code'))+' '+str(obj.get('param')))from None
 def start(self):
  env={**os.environ,'NODENO_STRIPE_SANDBOX_QA':'isolated-only','NODENO_STRIPE_SANDBOX_ROOT':str(self.storage),'NODENO_STRIPE_SANDBOX_CODE_ROOT':str(self.code)}
  listener_log=open(self.run/'listener-private.log','w',encoding='utf8');self.logs.append(listener_log)
  listener=subprocess.Popen([str(CLI),'--config',str(PRIVATE/'stripe.toml'),'listen','--events','checkout.session.completed,checkout.session.expired,checkout.session.async_payment_succeeded,checkout.session.async_payment_failed,refund.created,refund.updated,refund.failed','--forward-to',self.origin+'/api/payments/stripe/webhook'],stdout=listener_log,stderr=listener_log,env=env,creationflags=subprocess.CREATE_NO_WINDOW);self.children.append(listener)
  deadline=time.time()+40
  while time.time()<deadline:
   text=(self.run/'listener-private.log').read_text(encoding='utf8',errors='replace');match=re.search(r'whsec_[A-Za-z0-9]+',text)
   if match:break
   if listener.poll()is not None:raise RuntimeError('Stripe listener could not start; private diagnostics retained')
   time.sleep(.25)
  else:raise RuntimeError('Stripe listener signing secret timeout')
  seed={**self.credentials,'webhookSecret':match.group(0)};seed_file=self.run/'seed-private.json';seed_file.write_text(json.dumps(seed),encoding='utf8')
  seeded=subprocess.run([str(PHP),str(R/'tests/provider/stripe-sandbox-seed.php'),str(self.storage),str(seed_file)],env=env,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
  if seeded.returncode:raise RuntimeError('Isolated seed failed: '+str(seeded.returncode))
  seed_file.unlink()
  log=open(self.run/'php-private.log','w',encoding='utf8');self.logs.append(log)
  server=subprocess.Popen([str(PHP),'-d','display_errors=0','-d','zend.exception_ignore_args=1','-S','127.0.0.1:'+str(self.port),'-t',str(self.public),str(R/'tests/provider/stripe-sandbox-router.php')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);self.children.append(server)
  for _ in range(100):
   try:
    with urllib.request.urlopen(self.origin+'/api/payments/status',timeout=1)as response:assert json.load(response)['test']is True
    break
   except (OSError,AssertionError):time.sleep(.1)
  else:raise RuntimeError('Isolated PHP runtime unavailable')
  # Verify a real signed event/account binding before the application enables test checkout.
  probe=self.api('POST','/v1/checkout/sessions',{'mode':'payment','allowed_payment_method_types[0]':'card','line_items[0][quantity]':'1','line_items[0][price_data][currency]':'try','line_items[0][price_data][unit_amount]':'10000','line_items[0][price_data][product_data][name]':'NODENO sandbox webhook binding probe','success_url':self.origin+'/?probe=complete'})
  assert probe['livemode']is False
  self.api('POST','/v1/checkout/sessions/'+probe['id']+'/expire',{},'expire_probe_'+uuid.uuid4().hex)
  for _ in range(60):
   with urllib.request.urlopen(self.origin+'/api/payments/status',timeout=3)as response:ready=json.load(response)
   if ready['enabled']is True:break
   time.sleep(.5)
  else:raise RuntimeError('Actual signed sandbox webhook verification did not complete')
  return self
 def stop(self):
  for child in reversed(self.children):
   if child.poll()is None:child.terminate()
   try:child.wait(timeout=8)
   except subprocess.TimeoutExpired:child.kill();child.wait(timeout=8)
  for log in self.logs:log.close()
 def checkout(self,context,scenario):
  response=context.request.get(self.origin+'/api/payments/status');status=response.json();assert status['enabled']is True and status['test']is True
  headers={'Origin':self.origin,'X-CSRF-Token':status['csrfToken']}
  quote=context.request.post(self.origin+'/api/payments/quote',headers=headers,data={'items':[{'id':'sandbox-dolap','quantity':3}],'country':'TR'}).json();assert quote['totalMinor']==33003
  address={'name':'Sandbox Buyer','country':'TR','city':'Izmir','district':'Buca','postalCode':'','line1':'Sandbox test address 1','line2':''}
  contact={'name':'Sandbox Buyer','email':'nodeno-sandbox@example.test','phone':'+905551112233','delivery':address,'sameBilling':True}
  command={'items':[{'id':'sandbox-dolap','quantity':3}],'country':'TR','contact':contact,'locale':'en','quoteRevision':quote['revision'],'termsVersion':status['seller']['termsVersion'],'termsRevision':status['termsRevision'],'acceptTerms':True,'acceptFreight':True,'documentFlowVersion':1,'idempotencyKey':'sandbox_'+scenario+'_'+uuid.uuid4().hex}
  response=context.request.post(self.origin+'/api/payments/checkout',headers=headers,data=command)
  if response.status!=200:raise RuntimeError('Checkout create failed: '+str(response.status)+' '+str(response.json().get('error')))
  order=response.json();assert order['test']is True and order['checkoutUrl'].startswith('https://checkout.stripe.com/')
  duplicate=context.request.post(self.origin+'/api/payments/checkout',headers=headers,data=command).json();assert duplicate['id']==order['id']and duplicate['checkoutUrl']==order['checkoutUrl']
  return order
 def wait_order(self,context,order,expected,timeout=35):
  deadline=time.time()+timeout
  while time.time()<deadline:
   value=context.request.get(self.origin+'/api/payments/order/'+order['returnToken']).json()
   if value['status']==expected:return value
   time.sleep(.4)
  raise RuntimeError('Expected order '+expected+', received '+str(value.get('status')))

def inspect(page):
 return {'title':page.title(),'inputs':page.locator('input').evaluate_all('(xs)=>xs.map(x=>({id:x.id,name:x.name,type:x.type,placeholder:x.placeholder,aria:x.getAttribute("aria-label")}))'),'buttons':page.get_by_role('button').all_text_contents(),'frames':[{'name':f.name,'origin':urllib.parse.urlparse(f.url).netloc}for f in page.frames]}

def fill_card(page,number):
 page.locator('#cardNumber').fill(number);page.locator('#cardExpiry').fill('12/34');page.locator('#cardCvc').fill('123');page.locator('#billingName').fill('Sandbox Buyer')
 button=page.get_by_role('button',name=re.compile(r'^(Pay|\u00d6de)'));assert button.count()==1;button.click()

def find_session(sandbox,order):
 found=[s for s in sandbox.api('GET','/v1/checkout/sessions?limit=50')['data']if s.get('client_reference_id')==order['id']]
 assert len(found)==1;assert found[0]['livemode']is False;return found[0]

def verify_receipts(sandbox,context,order):
 headings={'tr':'Ödemeniz iade edildi','en':'Payment refunded','ru':'Оплата возвращена','ar':'تم رد المبلغ'};checks=[]
 for lang,width in [('tr',1440),('en',390),('ru',390),('ar',390)]:
  page=context.new_page();page.set_viewport_size({'width':width,'height':900});page.goto(sandbox.origin+'/receipt?payment='+order['returnToken']+'&lang='+lang,wait_until='networkidle');page.get_by_role('heading',name=headings[lang],exact=True).wait_for();assert page.locator('.payment-refund').count()==1;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(OUT/('receipt-'+lang+'.png')),full_page=True);checks.append({'locale':lang,'width':width,'correctRefundHeading':True,'refundAmountVisible':True,'noOverflow':True});page.close()
 return checks

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--inspect',action='store_true');parser.add_argument('--release',type=Path);parser.add_argument('--scenario',choices=['success','decline','3ds','3ds-fail','refund'],default='success');args=parser.parse_args();OUT.mkdir(exist_ok=True)
 sandbox=Sandbox(args.release)
 try:
  sandbox.start()
  with sync_playwright()as pw:
   browser=pw.chromium.launch(headless=True,executable_path=str(CHROME))
   context=browser.new_context(viewport={'width':1280,'height':1000},locale='en-US');page=context.new_page()
   order=sandbox.checkout(context,args.scenario);page.goto(order['checkoutUrl'],wait_until='domcontentloaded');page.locator('#cardNumber').wait_for(state='visible',timeout=25000);page.screenshot(path=str(OUT/('checkout-'+args.scenario+'.png')),full_page=True)
   if args.inspect:
    observation=inspect(page);(OUT/'checkout-dom.json').write_text(json.dumps(observation,indent=2)+'\n',encoding='utf8');print(json.dumps(observation),flush=True)
   else:
    number={'success':'4242424242424242','refund':'4242424242424242','decline':'4000000000000002','3ds':'4000000000003220','3ds-fail':'4000000000003220'}[args.scenario]
    fill_card(page,number)
    if args.scenario in ['success','refund']:
     paid=sandbox.wait_order(context,order,'paid',timeout=45);session=find_session(sandbox,order);assert session['payment_status']=='paid'and session['status']=='complete'and paid['totalMinor']==33003
     result={'scenario':args.scenario,'paid':True,'amountMinor':paid['totalMinor'],'testMode':True,'sameCommandSingleOrder':True,'orderId':order['id'],'sessionId':session['id'],'paymentIntent':session['payment_intent'],'sourceHashes':sandbox.hashes}
     if args.scenario=='refund':
      partial=sandbox.api('POST','/v1/refunds',{'payment_intent':session['payment_intent'],'amount':'5000'},'refund_partial_'+order['id']);assert partial['status']=='succeeded'and partial['amount']==5000
      part=sandbox.wait_order(context,order,'partially_refunded');assert part['refundedMinor']==5000
      refund=sandbox.api('POST','/v1/refunds',{'payment_intent':session['payment_intent']},'refund_remaining_'+order['id']);assert refund['status']=='succeeded'and refund['amount']==28003
      after=sandbox.wait_order(context,order,'refunded');assert after['refundedMinor']==33003
      result.update({'providerRefundStatus':refund['status'],'partialRefundMinor':5000,'refundMinor':after['refundedMinor'],'storeStatusAfterRefund':after['status'],'receipts':verify_receipts(sandbox,context,order),'passed':True})
     else:result['passed']=True
     (OUT/(args.scenario+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items()if k not in ['sourceHashes','paymentIntent','sessionId']}),flush=True)
    elif args.scenario=='decline':
     page.get_by_text(re.compile(r'card.*declin|kart.*redd',re.I)).first.wait_for(state='visible',timeout=30000)
     session=find_session(sandbox,order);after=context.request.get(sandbox.origin+'/api/payments/order/'+order['returnToken']).json();assert session['payment_status']=='unpaid'and after['status']!='paid'
     result={'scenario':'decline','passed':True,'testMode':True,'providerPaymentStatus':session['payment_status'],'storeStatus':after['status'],'orderId':order['id'],'sourceHashes':sandbox.hashes};(OUT/'decline.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items()if k!='sourceHashes'}),flush=True);page.screenshot(path=str(OUT/'declined.png'),full_page=True)
    else:
     frames=[];deadline=time.time()+35
     while time.time()<deadline:
      frames=[]
      for frame in page.frames:
       try:
        buttons=frame.get_by_role('button').all_text_contents();body=frame.locator('body').inner_text(timeout=1000)
        if buttons or '3D'in body:frames.append({'name':frame.name,'origin':urllib.parse.urlparse(frame.url).netloc,'buttons':buttons,'text':body[:1500]})
       except Exception:pass
      if any(any(re.search('Complete|Fail authentication',b,re.I)for b in f['buttons'])for f in frames):break
      time.sleep(.5)
     (OUT/'3ds-challenge-dom.json').write_text(json.dumps(frames,indent=2)+'\n',encoding='utf8');print(json.dumps({'challengeDetected':any(f['name']=='stripe-challenge-frame'for f in frames)}),flush=True);page.screenshot(path=str(OUT/'3ds-challenge.png'),full_page=True)
     challenge=next((frame for frame in page.frames if frame.name=='stripe-challenge-frame'),None);assert challenge is not None
     challenge.get_by_role('button',name='Complete'if args.scenario=='3ds'else'Fail',exact=True).click()
     if args.scenario=='3ds':
      paid=sandbox.wait_order(context,order,'paid',timeout=45);session=find_session(sandbox,order);assert session['payment_status']=='paid';result={'scenario':'3ds','passed':True,'testMode':True,'authenticationCompleted':True,'storeStatus':paid['status'],'amountMinor':paid['totalMinor']}
     else:
      deadline=time.time()+35
      while time.time()<deadline:
       session=find_session(sandbox,order)
       if session.get('payment_intent'):
        intent=sandbox.api('GET','/v1/payment_intents/'+session['payment_intent'])
        if intent['status']=='requires_payment_method'and intent.get('last_payment_error'):break
       time.sleep(.7)
      else:raise RuntimeError('3DS failure not confirmed by provider')
      state=context.request.get(sandbox.origin+'/api/payments/order/'+order['returnToken']).json();assert state['status']!='paid'and session['payment_status']=='unpaid';result={'scenario':'3ds-fail','passed':True,'testMode':True,'providerStatus':intent['status'],'providerError':intent['last_payment_error'].get('code'),'storeStatus':state['status']}
     result['sourceHashes']=sandbox.hashes;(OUT/(args.scenario+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items()if k!='sourceHashes'}),flush=True)
   sessions=sandbox.api('GET','/v1/checkout/sessions?limit=10')['data']
   for session in sessions:
    if session.get('client_reference_id')==order['id']and session.get('status')=='open':sandbox.api('POST','/v1/checkout/sessions/'+session['id']+'/expire',{},'expire_'+order['id'])
   browser.close()
 finally:sandbox.stop()

if __name__=='__main__':main()

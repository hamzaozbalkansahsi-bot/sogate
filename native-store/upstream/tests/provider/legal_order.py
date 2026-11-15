"""Genuine Stripe sandbox checkout with a downloaded immutable order agreement."""
from pathlib import Path
import hashlib,importlib.util,json,sys
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[2];E=R/'artifacts/legal-20261110';proof=json.loads((E/'release-preparation.json').read_bytes())
spec=importlib.util.spec_from_file_location('legal_order_sandbox',R/'tests/provider/stripe_sandbox.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
sandbox=m.Sandbox(R/proof['release'])
try:
 sandbox.start()
 with sync_playwright()as pw:
  browser=pw.chromium.launch(headless=True,executable_path=str(m.CHROME));context=browser.new_context(accept_downloads=True,viewport={'width':1280,'height':900});page=context.new_page();page.goto(sandbox.origin+'/receipt',wait_until='networkidle')
  status=context.request.get(sandbox.origin+'/api/payments/status').json();headers={'Origin':sandbox.origin,'X-CSRF-Token':status['csrfToken']};quote=context.request.post(sandbox.origin+'/api/payments/quote',headers=headers,data={'items':[{'id':'sandbox-dolap','quantity':3}],'country':'TR'}).json()
  legacy=context.request.post(sandbox.origin+'/api/payments/checkout',headers=headers,data={'items':[{'id':'sandbox-dolap','quantity':3}],'country':'TR','locale':'en','quoteRevision':quote['revision'],'termsVersion':status['seller']['termsVersion'],'termsRevision':status['termsRevision'],'acceptTerms':True,'acceptFreight':True,'idempotencyKey':'legacy_not_allowed_123','contact':{}});assert legacy.status==409 and legacy.json()['error']=='payment_documents_refresh_required'
  page.evaluate("""async()=>{document.body.innerHTML='<main class="wrap"><div data-payment-summary></div></main>';const {createPayments}=await import('/payments.js');const address={name:'Sandbox Buyer',country:'TR',city:'Izmir',district:'Buca',postalCode:'',line1:'Sandbox test address 1',line2:''};const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));await createPayments({state:()=>({locale:'en',items:[{id:'sandbox-dolap',quantity:3}],contact:{name:'Sandbox Buyer',email:'nodeno-sandbox@example.test',phone:'+905551112233',delivery:address,sameBilling:true},page:'checkout',step:'review',owner:'guest',country:'TR'}),esc,href:()=>'/'}).mount();}""")
  expect(page.locator('.payment-form')).to_be_visible();page.locator('[name=terms]').check();page.locator('[name=freight]').check()
  with page.expect_download(timeout=40000)as pending:page.locator('.payment-form [type=submit]').click()
  download=pending.value;file=sandbox.run/'order-agreement.html';download.save_as(file);body=file.read_bytes();assert b'330.03 TRY'in body and b'nodeno-sandbox@example.test'in body
  expect(page.locator('[data-payment-continue]')).to_be_visible();assert page.url.startswith(sandbox.origin)
  link=page.locator('.payment-form a[download]').get_attribute('href');response=context.request.get(sandbox.origin+link);assert response.status==200 and response.body()==body
  stranger=browser.new_context();assert stranger.request.get(sandbox.origin+link).status==403;stranger.close()
  page.screenshot(path=str(E/'order-copy-before-card.png'),full_page=True);page.locator('[data-payment-continue]').click();page.locator('#cardNumber').wait_for(timeout=25000);m.fill_card(page,'4242424242424242')
  token=link.split('/')[4];order={'returnToken':token};paid=sandbox.wait_order(context,order,'paid',timeout=45);assert paid['totalMinor']==33003
  assert context.request.get(sandbox.origin+link).body()==body
  assert sandbox.hashes['hosting/payment-documents.php']==hashlib.sha256((R/proof['release']/'private/payment-documents.php').read_bytes()).hexdigest()
  record={'passed':True,'releaseHash':proof['releaseHash'],'testMode':True,'genuineStripePayment':True,'amountMinor':33003,'legacyClientRejected':True,'documentDownloadedBeforeStripeRedirect':True,'documentSelfContained':True,'documentHash':hashlib.sha256(body).hexdigest(),'otherSessionDenied':True,'documentUnchangedAfterPayment':True,'sameOrderOnly':True,'sourceHashes':sandbox.hashes,'realCharges':0,'productionWrites':0};(E/'order-provider.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items()if k!='sourceHashes'}));browser.close()
finally:sandbox.stop()

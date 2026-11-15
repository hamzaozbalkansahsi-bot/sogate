# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/native_variant_cases.py
# Açıklama   : Gerçek sunucu akışlarını bağımsız tarayıcı oturumlarında, kritik istekleri bekleyerek doğrular.
import copy,json,os,re,sys,traceback
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from native_browser_ready import NativePageReadiness

ROOT=Path(__file__).resolve().parent.parent

def safe_error(kind,error,trace):
 message=re.sub(r'^.*(?:cookie:|authorization:|x-csrf-token:).*$','[private request headers redacted]',str(error),flags=re.M|re.I)
 print(kind.__name__+': '+message[:1800],file=sys.stderr)
 print([(Path(f.filename).name,f.lineno)for f in traceback.extract_tb(trace)if Path(f.filename).parent.name=='scripts'],file=sys.stderr)

def stored(page):
 return page.evaluate('()=>JSON.parse(localStorage.getItem("nodeno.cart.v1")||"[]")')

def pick(page,values,ready):
 dialog=page.locator('.sg-variant-dialog');dialog.wait_for(state='visible')
 for axis,value in values.items():dialog.locator('[data-axis="'+axis+'"] [data-choice="'+value+'"]').click()
 assert dialog.locator('.sg-variant-add').is_enabled()
 element=dialog.element_handle();dialog.locator('.sg-variant-add').click()
 page.wait_for_function('(el)=>!el.isConnected',arg=element);ready.wait()

def fixture_state(run,cart=None,favorites=None):
 state=copy.deepcopy(run['state']);origin=next(o for o in state['origins']if o['origin']==run['origin'])
 values={item['name']:item['value']for item in origin['localStorage']}
 values['nodeno.cart.v1']=json.dumps(cart or[]);values['nodeno.saved.v1']=json.dumps(favorites or[])
 origin['localStorage']=[{'name':key,'value':value}for key,value in values.items()]
 return state

@contextmanager
def scenario(run,name,state=None):
 print(run['engine']+': '+name,flush=True)
 context=run['browser'].new_context(ignore_https_errors=run['base'].startswith('https://127.0.0.1'),viewport={'width':390,'height':844},**({'storage_state':state}if state else{}))
 page=context.new_page();page.set_default_timeout(30000);page.set_default_navigation_timeout(60000)
 active_errors=[];closing_errors=[];network=[];closing=False
 def page_error(error):(closing_errors if closing else active_errors).append(str(error))
 page.on('pageerror',page_error)
 page.on('requestfailed',lambda r:network.append({'path':urlsplit(r.url).path,'error':r.failure}))
 ready=NativePageReadiness(page,run['base'],60000)
 try:
  yield context,page,ready
  ready.wait();assert not active_errors,{'case':name,'pageErrors':active_errors}
  run['cases'].append(name)
 except Exception:
  print(json.dumps({'case':name,'engine':run['engine'],'network':network[-12:],'pageErrors':active_errors},ensure_ascii=False),flush=True)
  raise
 finally:
  closing=True;context.close()
  run['teardownErrors'].extend({'case':name,'message':error}for error in closing_errors)

def consent(run):
 with scenario(run,'consent')as(context,page,ready):
  page.goto(run['base']+'/?lang=tr',wait_until='domcontentloaded');ready.wait()
  gate=page.locator('#sexogate-age-gate')
  if gate.count():gate.locator('.sexogate-age-accept').click();gate.wait_for(state='detached')
  button=page.locator('.insights-banner .button-dark');button.wait_for(state='visible')
  assert button.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(90, 10, 32)'
  button.hover();page.wait_for_timeout(250)
  assert button.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(142, 15, 56)'
  page.mouse.move(0,0);page.keyboard.press('Tab');button.focus();page.wait_for_timeout(250)
  assert button.evaluate('(e)=>getComputedStyle(e).outlineStyle')!='none'
  page.screenshot(path=str(run['folder']/(run['engine']+'-consent-390.png')))
  page.get_by_role('button',name='Yalnız gerekli',exact=True).click();page.locator('.insights-banner').wait_for(state='detached')
  page.locator('.insights-settings').click();dialog=page.locator('.insights-dialog')
  assert dialog.locator('.button-dark').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(90, 10, 32)'
  dialog.get_by_role('button',name='Kapat',exact=True).click();ready.wait()
  data=context.request.get(run['base']+'/api/catalog',timeout=60000).json()
  run['products']=data.get('catalog',data)['products']
  run['release']=context.request.get(run['base']+'/api/deployment-status',timeout=60000).json()['release']
  run['state']=context.storage_state()

def choose_examples(run):
 candidates=[p for p in run['products']if p.get('variantSelection',{}).get('required')and not p['variantSelection']['blocked']]
 product=next(p for p in candidates if p['variantSelection']['mode']=='options'and any(a['id']=='size'and len(a['values'])>1 for a in p['variantSelection']['axes']))
 values={a['id']:a['values'][0]['id']for a in product['variantSelection']['axes']}
 other={**values,'size':next(a for a in product['variantSelection']['axes']if a['id']=='size')['values'][-1]['id']}
 matrix=next(p for p in candidates if p['variantSelection']['mode']=='matrix'and sum(v['active']for v in p['variantSelection']['variants'])>=2)
 return product,values,other,matrix,next(v for v in matrix['variantSelection']['variants']if v['active'])

def cart_flow(run,examples):
 product,values,other,_,_=examples
 with scenario(run,'cart-options-edit-and-reload',fixture_state(run))as(_,page,ready):
  page.goto(run['base']+'/?product='+product['id']+'&lang=tr',wait_until='domcontentloaded');ready.wait()
  page.locator('[data-detail-add]:visible').first.click();dialog=page.locator('.sg-variant-dialog')
  assert dialog.locator('.sg-variant-add').is_disabled()and dialog.locator('[aria-pressed=true]').count()==0
  assert stored(page)==[];page.keyboard.press('Escape');dialog.wait_for(state='detached');assert stored(page)==[]
  page.locator('[data-detail-add]:visible').first.click();pick(page,values,ready);assert stored(page)[0]['options']['selection']==values
  page.locator('[data-detail-add]:visible').first.click();pick(page,other,ready);assert len(stored(page))==2
  page.locator('a[href*="page=cart"]:visible').first.click();ready.wait()
  assert 'page=cart'in page.url
  assert page.locator('.basket-item').count()==2 and page.locator('.sg-cart-selection').count()==2
  assert stored(page)[0]['key']!=stored(page)[1]['key']
  page.screenshot(path=str(run['folder']/(run['engine']+'-cart-390.png')))
  page.locator('[data-selection-edit]').first.click();pick(page,other,ready)
  assert len(stored(page))==1 and stored(page)[0]['quantity']==2
  page.reload(wait_until='domcontentloaded');ready.wait()
  assert page.locator('.basket-item').count()==1 and stored(page)[0]['options']['selection']==other

def legacy_and_layout(run,examples):
 product,values,_,_,_=examples
 with scenario(run,'legacy-cart-and-responsive-dialog',fixture_state(run,[{'id':product['id'],'quantity':2}]))as(_,page,ready):
  page.goto(run['base']+'/?page=cart&lang=tr',wait_until='domcontentloaded');ready.wait()
  assert page.locator('.sg-selection-pending').count()==1
  assert not stored(page)[0].get('options')
  page.locator('[data-selection-edit]').click();pick(page,values,ready);assert stored(page)[0]['quantity']==2
  for width in [360,390,430,768,1440]:
   page.set_viewport_size({'width':width,'height':900});page.locator('[data-selection-edit]').click();dialog=page.locator('.sg-variant-dialog')
   assert dialog.evaluate('(e)=>{const b=e.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth+1&&b.top>=0&&b.bottom<=innerHeight+1}')
   assert dialog.locator('[data-choice]').evaluate_all('(es)=>es.every(e=>e.getBoundingClientRect().height>=44)')
   assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth')
   page.keyboard.press('Escape');ready.wait()

def matrix_english(run,examples):
 _,_,_,matrix,variant=examples
 with scenario(run,'real-matrix-english',fixture_state(run))as(_,page,ready):
  page.goto(run['base']+'/?product='+matrix['id']+'&lang=en',wait_until='domcontentloaded');ready.wait()
  page.locator('[data-detail-add]:visible').first.click()
  assert page.locator('#sg-variant-title').inner_text()=='Choose your options'
  pick(page,variant['values'],ready)
  assert any(row['id']==matrix['id']and row['options']['selection']==variant['values']for row in stored(page))

def bulk(run,examples,cancel):
 product,values,_,matrix,variant=examples
 with scenario(run,'bulk-cancel'if cancel else'bulk-all-products',fixture_state(run,favorites=[product['id'],matrix['id']]))as(_,page,ready):
  page.goto(run['base']+'/?page=favorites&lang=tr',wait_until='domcontentloaded');ready.wait()
  page.locator('[data-shopping="favorite-cart"]').click();pick(page,values,ready)
  if cancel:
   page.locator('.sg-variant-dialog').wait_for(state='visible');page.keyboard.press('Escape');page.locator('.sg-variant-dialog').wait_for(state='detached')
   assert len(stored(page))==1 and stored(page)[0]['id']==product['id']
  else:
   pick(page,variant['values'],ready)
   assert {row['id']for row in stored(page)}=={product['id'],matrix['id']}

def rtl(run,examples):
 product=examples[0]
 with scenario(run,'rtl',fixture_state(run))as(context,page,ready):
  page.goto(run['base']+'/?product='+product['id']+'&lang=ar',wait_until='domcontentloaded');ready.wait()
  page.locator('[data-detail-add]:visible').first.click()
  assert page.locator('.sg-variant-dialog').get_attribute('dir')=='rtl'
  assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path=str(run['folder']/(run['engine']+'-selection-rtl-390.png')));page.keyboard.press('Escape')
  assert context.request.get(run['base']+'/api/deployment-status',timeout=60000).json()['release']==run['release']

def main():
 sys.excepthook=safe_error
 base=os.environ.get('SEXOGATE_NATIVE_TEST_URL','https://127.0.0.1:3188/test').rstrip('/');scope=os.environ.get('SEXOGATE_NATIVE_TEST_SCOPE','variants-local')
 assert re.fullmatch('[a-z-]+',scope)and re.fullmatch(r'https://(?:127\.0\.0\.1:3188|sexogate\.com)/test(?:/native-preview-[a-f0-9]{16})?',base)
 folder=ROOT/('docs/screenshots/native-store-'+scope);folder.mkdir(parents=True,exist_ok=True);results=[]
 with sync_playwright()as playwright:
  for engine in ['chromium','webkit']:
   browser=getattr(playwright,engine).launch();run={'browser':browser,'engine':engine,'base':base,'origin':urlsplit(base).scheme+'://'+urlsplit(base).netloc,'folder':folder,'cases':[],'teardownErrors':[]}
   try:
    consent(run);examples=choose_examples(run);cart_flow(run,examples);legacy_and_layout(run,examples);matrix_english(run,examples);bulk(run,examples,False);bulk(run,examples,True);rtl(run,examples)
    assert len(run['cases'])==7
    results.append({'engine':engine,'scenario':'isolated-selection-consent-and-bulk','release':run['release'],'selectionRequired':True,'sizeColorCartLines':True,'editMergeReload':True,'legacyCartRepair':True,'sourceMatrix':True,'bulkAllItems':True,'bulkCancellation':True,'consentNormalHoverFocus':'brand-burgundy/wine','widths':[360,390,430,768,1440],'rtl':True,'realPayment':False,'isolatedCases':run['cases'],'teardownErrors':run['teardownErrors']})
   finally:browser.close()
 report={'base':base,'scope':scope,'results':results};(ROOT/('docs/native-'+scope+'-results.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False),flush=True)

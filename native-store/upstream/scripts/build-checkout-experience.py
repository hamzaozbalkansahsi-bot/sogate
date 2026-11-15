"""Build a bounded checkout delta over the pinned, verified current live release."""
from pathlib import Path
import json,hashlib,re,difflib,shutil
R=Path(__file__).resolve().parents[1];E=R/'artifacts/checkout-experience-20261112';proof=json.loads((E/'build.json').read_bytes());B=R/proof['base'];O=R/proof['release'];m=json.loads((B/'private/release.json').read_bytes());assert m['releaseHash']==proof['baseReleaseHash'];patch={}
read=lambda n:(B/n).read_text(encoding='utf8');src=lambda n:(R/n).read_text(encoding='utf8')
def replay(name,target,markers):
 a=read(target).splitlines(True);z=src(name).splitlines(True);out=list(a)
 for tag,i,j,x,y in reversed(difflib.SequenceMatcher(None,a,z,autojunk=False).get_opcodes()):
  if tag!='equal'and any(k in ''.join(z[x:y])for k in markers):out[i:j]=z[x:y]
 return ''.join(out)
app=replay('web/app.js','public/app.js',['checkout-draft.js','loadCheckoutDraft','saveCheckoutDraft','clearCheckoutDraft','restored=validateGuestCheckout',"event.key!=='Enter'"])
app=app.replace('<p class="field-hint">${esc(t(\'guestDraftNote\'))}</p>','');patch['public/app.js']=app.encode()
patch['public/styles.css']=(read('public/styles.css')+'\n/* Checkout experience:'+src('web/styles.css').split('/* Checkout experience:',1)[1]).encode()
s=read('public/payments.js');n=src('web/payments.js');start='export function createPayments(';end=' async function resultPanel';s=s[:s.index(start)]+n[n.index(start):n.index(end)]+s[s.index(end):];line=next(v for v in n.splitlines()if 'preInformation'in v and 'Object.entries(localeCopy'in v);s="import {openCheckoutTerms} from './checkout-terms-dialog.js?v=checkout-experience-20261112-r2';\n"+s;s=s.replace('export const paymentDocumentFlowVersion=1;',line+'\nexport const paymentDocumentFlowVersion=2;');patch['public/payments.js']=s.encode()
for name in ['checkout-draft.js','checkout-terms-dialog.js']:patch['public/'+name]=src('web/'+name).encode()
for name,identifier in [('measurement-i18n.js','measurementCopy'),('cabinet-front-ui.js','frontCopy'),('door-i18n.js','doorCopy')]:
 s=read('public/'+name);line=next(v for v in src('web/'+name).splitlines()if 'Object.assign('+identifier+'[lang],{net:text' in v);patch['public/'+name]=(s+'\n'+line+'\n').encode()
s=read('private/door-commerce.php');n=src('hosting/door-commerce.php');fn=n[n.index('function nodenoShippingCatalog'):n.index('function nodenoDoorOptions')];s=s.replace('function nodenoDoorOptions',fn+'function nodenoDoorOptions',1);needle="function nodenoCommerceQuote(array $catalog,array $items,string $country,string $currency='TRY',?array $fx=null):array {";assert needle in s;s=s.replace(needle,needle+'\n $catalog=nodenoShippingCatalog($catalog);',1);patch['private/door-commerce.php']=s.encode()
s=read('private/control-catalog.php');s=s.replace(" $catalog['products']=$products;$revision="," $catalog['products']=$products;if(($catalog['meta']['shippingPolicyVersion']??'')==='2026-11-12-included'){if(!function_exists('nodenoShippingCatalog'))require_once __DIR__.'/door-commerce.php';$catalog=nodenoShippingCatalog($catalog);}$revision=",1);patch['private/control-catalog.php']=s.encode()
s=read('public/index.php');needle='return nodenoSeoDocument($html,nodenoSeoPage($catalog,$config,$_GET));';assert needle in s;s=s.replace(needle,"require_once $private.'/door-commerce.php';$catalog=nodenoShippingCatalog($catalog);"+needle,1);patch['public/index.php']=s.encode()
for name in ['payment-core.php','payments.php']:
 s=read('private/'+name).replace("['kind'=>'recipient_pays','includedInCharge'=>false,'feeMinor'=>null]","['kind'=>'included','includedInCharge'=>true,'feeMinor'=>0]")
 if name=='payments.php':s=s.replace("($body['acceptTerms']??false)!==true||($body['acceptFreight']??false)!==true||","($body['acceptTerms']??false)!==true||").replace("($body['documentFlowVersion']??null)!==1","($body['documentFlowVersion']??null)!==2")
 patch['private/'+name]=s.encode()
s=read('private/payment-admin.php');n=src('hosting/payment-admin.php');fn=n[n.index('function nodenoShippingSeller'):n.index('function nodenoPaymentConfiguration')];s=s.replace('function nodenoPaymentConfiguration',fn+'function nodenoPaymentConfiguration',1);s=s.replace('return $value;',"if(isset($value['seller']))$value['seller']=nodenoShippingSeller($value['seller']);return $value;",1);patch['private/payment-admin.php']=s.encode()
s=read('private/payment-documents.php');n=src('hosting/payment-documents.php');replacement=re.search(r"\$e\(\(\$quote\['freight'\].*?:\$labels\['freight'\]\)",n).group();s=s.replace("$e($labels['freight'])",replacement,1);patch['private/payment-documents.php']=s.encode()
if "gmdate('Y-m-d H:i:s'" in s:
 s=s.replace("declare(strict_types=1);","declare(strict_types=1);\nrequire_once __DIR__.'/date-time.php';",1).replace("$e($order['id']).' · '.gmdate('Y-m-d H:i:s',(int)$order['created_at']).' UTC", "$e($order['id']).' · '.$e(nodenoHumanDateTime((int)$order['created_at'],(string)($quote['country']??$contact['delivery']['country']??'TR'))).'")
 patch['private/payment-documents.php']=s.encode()
c=json.loads(read('private/catalog.json'));c['meta']['shippingPolicyVersion']='2026-11-12-included';patch['private/catalog.json']=json.dumps(c,ensure_ascii=False,separators=(',',':')).encode()
extra=json.loads(src('data/localization/checkout-shipping-20261112.json'))
for lang in ['de','az','kk','tk','uz','ky','fa']:
 for name in ['public/locales/'+lang+'.json','private/locale.'+lang+'.json']:
  dictionary=json.loads(read(name));dictionary['translations'].update(dict(zip(extra['sources'],extra[lang])));patch[name]=json.dumps(dictionary,ensure_ascii=False,separators=(',',':')).encode()
s=read('public/locale-runtime.js');s=re.sub(r"const defaultRevision='[^']+';","const defaultRevision='checkout-experience-20261112-r2';",s);patch['public/locale-runtime.js']=s.encode()
shipping={'tr':'Türkiye içi standart kargo ürün fiyatlarına dahildir. Yurt dışı nakliye ve gümrük işlemleri için ayrı teklif alınır. Teslimat tarihi ve varsa kurulum hizmetleri siparişiniz için ayrıca netleştirilir.','en':extra['sources'][-1],'ru':'Стандартная доставка по Турции включена в стоимость товаров. Международная перевозка и таможенное оформление согласуются в отдельном предложении. Сроки доставки и услуги установки подтверждаются для вашего заказа.','ar':'الشحن القياسي داخل تركيا مشمول في أسعار المنتجات. يتطلب الشحن الدولي والإجراءات الجمركية عرضاً منفصلاً. تُؤكد مواعيد التسليم وخدمات التركيب لطلبك.'}
s=read('public/i18n.js');s+='\nfor(const [lang,text]of Object.entries('+json.dumps(shipping,ensure_ascii=False)+'))copy[lang].shippingBody=text;\n';patch['public/i18n.js']=s.encode()
changed={n[7:]for n in patch if n.startswith('public/')and n.endswith('.js')};source={n[7:]:patch.get(n,(B/n).read_bytes())for n in m['files']if n.startswith('public/')and n.endswith('.js')};source.update({n[7:]:v for n,v in patch.items()if n.startswith('public/')and n.endswith('.js')})
while True:
 before=set(changed)
 for name,body in source.items():
  if any(re.search(rb'\./'+re.escape(dep.encode())+rb'(?:\?v=[^\s\'\"]+)?[\'\"]',body)for dep in before):changed.add(name)
 if changed==before:break
token=b'checkout-experience-20261112-r2'
for name in changed:
 body=source[name]
 for dep in changed:body=re.sub(rb'(\./'+re.escape(dep.encode())+rb')(?:\?v=[^\s\'\"]+)?(?=[\'\"])',lambda q:q[1]+b'?v='+token,body)
 patch['public/'+name]=body
html=(B/'private/index.html').read_bytes()
for name in ['app.js','styles.css']:html=re.sub(rb'(/'+re.escape(name.encode())+rb')\?v=[^\"\s]+',lambda q:q[1]+b'?v='+token,html)
patch['private/index.html']=html
for name,sha in m['files'].items():
 assert hashlib.sha256((B/name).read_bytes()).hexdigest()==sha;target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name not in patch:shutil.copyfile(B/name,target)
for name,body in patch.items():target=O/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
hashes={**m['files'],**{n:hashlib.sha256(v).hexdigest()for n,v in patch.items()}};f=hashlib.sha256()
for n in sorted(hashes):f.update((n+'\0'+hashes[n]+'\0').encode())
manifest={**m,'files':dict(sorted(hashes.items())),'releaseHash':f.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');proof.update(releaseHash=f.hexdigest(),changedFiles=sorted(patch));(E/'build.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'built':True,'releaseHash':f.hexdigest(),'files':len(patch)}))

"""Prepare a scoped mobile layout correction on the exact current production release."""
from pathlib import Path
import hashlib,json,os,re
R=Path(__file__).resolve().parents[1];E=R/'artifacts/mobile-layout-20261113';VERSION='mobile-layout-20261113-r1'
NAMES=dict(zip(['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'],['Ahşap mobilya ve yardımcı ürünler','Wooden furniture and accessories','Деревянная мебель и вспомогательные изделия','أثاث خشبي ومنتجات مساعدة','Holzmöbel und Zubehör','Taxta mebel və köməkçi məhsullar','Ағаш жиһаз және қосалқы бұйымдар','Agaç mebel we kömekçi önümler','Yog‘och mebel va yordamchi mahsulotlar','Жыгач эмерек жана көмөкчү буюмдар','مبلمان چوبی و محصولات جانبی']))
CSS="""
/* Preserve the entire approved category photograph, including tall furniture and package labels. */
.category-tile-photo{aspect-ratio:1;background:var(--white)}
.category-tile-photo img{display:block;object-fit:contain;object-position:center;transform:none}
@media(hover:none){.product-stage:hover img{transform:none}}
@media(max-width:760px){
 body[data-page=categories] .header-search{min-inline-size:0}
 .header-search input{min-inline-size:0}
 .category-tile-caption strong{hyphens:auto;overflow-wrap:break-word}
}
"""
PRIVACY_CSS="""
/* Explicit rows keep the policy link, wrapped actions and focus indicators apart. */
.insights-dialog{box-sizing:border-box;position:fixed;inset:0;margin:auto;max-inline-size:calc(100vw - 24px);max-block-size:calc(100dvh - 24px);overflow:auto;overscroll-behavior:contain;padding:24px}
.insights-dialog[open]{display:grid;gap:16px}
.insights-dialog h2{margin:0;padding-inline-end:44px;min-inline-size:0;overflow-wrap:break-word}
.insights-dialog p,.insights-banner p{margin:0;overflow-wrap:break-word}
.insights-dialog>a,.insights-banner>a{display:flex;align-items:center;justify-self:start;min-block-size:44px;max-inline-size:100%;line-height:1.5;text-decoration:underline;text-underline-offset:3px}
.insights-dialog .insights-actions{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;min-inline-size:0}
.insights-dialog .insights-actions .button,.insights-banner .insights-actions .button{min-inline-size:0;max-inline-size:100%;min-block-size:44px;height:auto;white-space:normal;overflow-wrap:break-word;line-height:1.5}
.insights-close{position:absolute;inset-inline-end:12px;inset-block-start:12px;inline-size:44px;block-size:44px;display:grid;place-items:center;border:1px solid var(--line,#d9dfd3);border-radius:6px;background:white;color:inherit}
.insights-close svg{inline-size:20px;block-size:20px}
.insights-banner{display:grid;gap:12px;box-sizing:border-box;max-block-size:calc(100dvh - 120px - env(safe-area-inset-bottom));overflow:auto}
@media(max-width:760px){.insights-banner .insights-actions{display:grid;grid-template-columns:minmax(0,1fr)}.insights-dialog{padding:24px 20px}.insights-dialog h2{font-size:22px}}
"""
def insights(s):
 old="dialog.replaceChildren();const title=document.createElement('h2');title.textContent=text.title;"
 new="dialog.replaceChildren();const close=document.createElement('button');close.type='button';close.className='insights-close';close.setAttribute('aria-label',({tr:'Kapat',en:'Close',ru:'Закрыть',ar:'إغلاق',de:'Schließen',az:'Bağla',kk:'Жабу',tk:'Ýapmak',uz:'Yopish',ky:'Жабуу',fa:'بستن'})[locale]||'Close');close.innerHTML='<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" aria-hidden=\"true\"><path d=\"m6 6 12 12M18 6 6 18\"/></svg>';close.onclick=()=>dialog.close();const title=document.createElement('h2');title.id='insights-preferences-title';dialog.setAttribute('aria-labelledby',title.id);title.textContent=text.title;"
 assert s.count(old)==1;s=s.replace(old,new);old='dialog.append(title,p,policyLink(locale,text),buttons);dialog.showModal();';assert s.count(old)==1;return s.replace(old,'dialog.append(close,title,p,policyLink(locale,text),buttons);dialog.showModal();close.focus({preventScroll:true});')
def app(s):
 old="function categoryPhoto(id){";assert s.count(old)==1;s=s.replace(old,old+"if(id==='ahsap-mobilya-malzemeleri'){const p=byId('alka-e1287a544d');if(p?.images?.length)return p;}")
 return re.sub(r'store-insights\.js\?v=[A-Za-z0-9_-]+','store-insights.js?v='+VERSION,s)
def changes_for(base):
 catalog=json.loads(base['all_bytes']['private/catalog.json']);category=next(c for c in catalog['categories']if c['id']=='ahsap-mobilya-malzemeleri');category['name']=NAMES
 changes={'private/catalog.json':json.dumps(catalog,ensure_ascii=False,separators=(',',':')).encode(),'public/app.js':app(base['all_bytes']['public/app.js'].decode()).encode(),'public/styles.css':base['all_bytes']['public/styles.css']+CSS.encode(),'public/store-insights.css':base['all_bytes']['public/store-insights.css']+PRIVACY_CSS.encode(),'public/store-insights.js':insights(base['all_bytes']['public/store-insights.js'].decode()).encode()}
 index=base['all_bytes']['private/index.html'].decode()
 for name in ['app.js','styles.css','store-insights.css']:index=re.sub(re.escape(name)+r'\?v=[A-Za-z0-9_-]+',name+'?v='+VERSION,index)
 changes['private/index.html']=index.encode();return changes

def main():
 proof=json.loads((E/'base.json').read_bytes());B=R/proof['releases'][0];manifest=json.loads((B/'private/release.json').read_bytes());assert manifest['releaseHash']==proof['health']['releaseHash'];base={'all_bytes':{n:(B/n).read_bytes()for n in manifest['files']}};changes=changes_for(base);O=R/'artifacts/cpanel-release-mobile-layout-20261113-r2';assert not O.exists()
 for n in sorted(set(manifest['files'])|set(changes)):
  dest=O/n;dest.parent.mkdir(parents=True,exist_ok=True)
  if n in changes:dest.write_bytes(changes[n])
  else:os.link(B/n,dest)
 hashes={**manifest['files'],**{n:hashlib.sha256(v).hexdigest()for n,v in changes.items()}};h=hashlib.sha256()
 for n in sorted(hashes):h.update((n+'\0'+hashes[n]+'\0').encode())
 updated={**manifest,'files':dict(sorted(hashes.items())),'releaseHash':h.hexdigest()};(O/'private/release.json').write_text(json.dumps(updated,ensure_ascii=False),encoding='utf-8');record={'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':manifest['releaseHash'],'releaseHash':updated['releaseHash'],'changedFiles':sorted(changes),'publicProducts':manifest['products'],'expectedCheckoutEnabled':proof['health']['checkoutEnabled']};(E/'release.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print(record)
 # Apply only the same targeted edits to shared sources; retain unrelated unpublished work.
 for name,fn in [('app.js',app),('store-insights.js',insights)]:
  p=R/'web'/name;current=p.read_text(encoding='utf-8')
  if (name=='app.js'and "byId('alka-e1287a544d')"not in current)or(name=='store-insights.js'and 'insights-preferences-title'not in current):p.write_text(fn(current),encoding='utf-8')
 for name,extra in [('styles.css',CSS),('store-insights.css',PRIVACY_CSS)]:
  p=R/'web'/name;current=p.read_text(encoding='utf-8')
  if extra.strip()not in current:
   if name=='store-insights.css'and '/* Explicit rows keep' in current:current=current[:current.index('/* Explicit rows keep')].rstrip()+'\n'
   p.write_text(current+extra,encoding='utf-8')
 for name in ['data/supplier-storefront.json','data/supplier-catalog.json']:
  p=R/name;data=json.loads(p.read_bytes());found=[c for c in data.get('categories',[])if c['id']=='ahsap-mobilya-malzemeleri']
  for c in found:c['name']=NAMES
  if found:p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
if __name__=='__main__':main()

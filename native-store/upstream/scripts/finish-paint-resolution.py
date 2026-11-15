"""Record every reviewed offer, keeping unresolved source contradictions explicit."""
from pathlib import Path
import csv,importlib.util,json,re
R=Path(__file__).resolve().parents[1];E=R/'artifacts/paint-resolution-20261112'
def module(n,path):
 s=importlib.util.spec_from_file_location(n,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 c=module('resolution_catalogue','scripts/complete-paint-catalogue.py');c.E=E;report=json.loads((E/'checks.json').read_bytes());assert report['remaining']==0
 base=R/json.loads((E/'base.json').read_bytes())['releases'][0];catalog=json.loads((base/'private/catalog.json').read_bytes());seed=json.loads((base/'private/supplier-catalog.json').read_bytes());bindings={p['id']:p for p in seed['products']};seen={};products=[];held=[];decisions=[]
 for p in catalog['products']:
  if not p.get('paintUse'):continue
  b=bindings[p['id']];package=next((s['value']['tr']for s in p['specs']if s['label'].get('en')=='Package size'),'');row={'brand':p['productBrand'],'family':p['paintUse']['family'],'color':b['sourceVariant']['color'],'package':package,'finish':p['modelId'].rsplit('-',1)[-1],'title':b['title']};seen[c.signature(row)]=p['id']
 diamond=json.loads((E/'diamond-candidate.json').read_bytes());diamond['finish']='gloss';products.append(diamond)
 for r in report['checked']:
  d={'sourceProductId':r['sourceProductId'],'checkedAt':r['checkedAt'],'previousReason':r['previousReason'],'sourceUrl':r['original']['sourceUrl']};p=r.get('offer');reason=r.get('error');replacement=None
  if p:
   p['finish']=c.finish(p)
   if not c.m.package_value(p['package']):
    sizes=re.findall(r'\b\d+(?:[.,]\d+)?\s*(?:ml|lt|litre|kg|gr|l)\b',p['title'],re.I)
    if len(set(sizes))==1:p['package']=sizes[0]
   reason=c.m.offer_review(p)
   replacement=seen.get(c.signature(p))if p['family']else None
   if reason in ['title_and_selected_package_conflict','title_and_selected_colour_conflict']:replacement=None
   # A replacement uses its own verified offer and code; the contradictory original is never edited.
   if reason=='manufacturer_600g_and_marketplace_600ml_need_package_confirmation'and'parlak'in c.norm(p['title']+' '+p['color']):replacement='paint-ty-'+diamond['sourceProductId']
   if reason=='title_and_selected_package_conflict':
    amounts=c.m.package_value(p['title'])
    if len(amounts)==1:
     for other in catalog['products']:
      if not other.get('paintUse')or other['paintUse']['family']!=p['family']:continue
      b=bindings[other['id']];size=next((s['value']['tr']for s in other['specs']if s['label'].get('en')=='Package size'),'')
      if c.norm(b['sourceVariant']['color'])==c.norm(p['color'])and c.m.package_value(size)==amounts:replacement=other['id'];break
   if not p['family']:d.update(status='excluded',reason='Hobi ve dönüşüm ürünü kapsamı dışında.')
   elif replacement:d.update(status='covered',replacementId=replacement,reason='Doğru ürün mevcut veya bu yayın için doğrulandı; hatalı/mükerrer ilan ayrıca satışa açılmadı.')
   elif not r.get('qualified'):reason='qualified_merchant_not_verified'
   elif reason is None:
    if p['family']in c.prep.FAMILIES:
     key=c.signature(p)
     if key not in seen:products.append(p);seen[key]='paint-ty-'+p['sourceProductId'];d.update(status='new',replacementId=seen[key],reason='Yeni seçenek kaynak, ambalaj ve satıcı bilgileriyle doğrulandı.')
    else:reason='unsupported_family_review'
  if 'status'not in d:
   d.update(status='blocked',reason=c.REASONS.get(reason,reason or'Kaynak teyidi gerekli.'));h=c.review_record(p or r['original'],reason or'pending_check');h['checkedAt']=__import__('datetime').datetime.fromtimestamp(r['checkedAt'],__import__('datetime').timezone.utc).isoformat();held.append(h)
  decisions.append(d)
 for p in products:p.setdefault('fetchedAt',__import__('datetime').datetime.fromtimestamp(p['sourceEvidence']['at'],__import__('datetime').timezone.utc).isoformat())
 c.save(E/'selected-offers.json',{'products':products,'held':held,'checkedAt':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()});c.save(E/'offers.json',{'products':products,'held':[h for h in held if h['group']=='source']});c.save(E/'review-list.json',held);c.save(E/'decisions.json',decisions)
 with(R/'output/paint-catalogue/NODENO_Boya_Cozum_Sonuclari.csv').open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.writer(f,delimiter=';');w.writerow(['Kaynak kimliği','Durum','Sonuç','Doğru ürün','Kaynak bağlantısı'])
  for d in decisions:w.writerow([d['sourceProductId'],d['status'],d['reason'],d.get('replacementId',''),d['sourceUrl']])
 print(json.dumps({'new':len(products),'decisions':{s:sum(d['status']==s for d in decisions)for s in ['covered','new','excluded','blocked']},'held':len(held)}))
if __name__=='__main__':main()

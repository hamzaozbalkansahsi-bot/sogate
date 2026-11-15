"""Read the approved PDF; record exact SKU membership without inventing missing parts."""
from pathlib import Path
import json,re,hashlib,fitz
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'output/pdf/NODENO_Mobilya_Katalogu_2026_Paylasim_Son.pdf'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
source=json.loads((ROOT/'data/catalog-source.json').read_text(encoding='utf-8'));by_code={('Ndn-'+p['code']).lower():p for p in source['products']}
def kind(code):
 prefix=code.split('-')[0]
 if prefix=='ZSP':prefix=code.split('-')[1]
 return {'MGV':'wardrobeBody','MKP':'wardrobeDoor','MKC':'wardrobeDoor','GRD':'wardrobe','GRA':'wardrobe','BGA':'wardrobe','TGR':'wardrobe','KMD':'nightstand','BKM':'nightstand','MKM':'nightstand','TKM':'nightstand','SFN':'dresser','BSF':'dresser','MSF':'dresser','TSF':'dresser','KRY':'bed','KRB':'bed','KRC':'bed','BKB':'bed','MKB':'bed','TKR':'bed','CMU':'desk','CMS':'desk','TCM':'desk','KTP':'bookcase','TKT':'bookcase','AYN':'mirror','KNS':'sideboard','BKN':'sideboard','MKN':'sideboard','YMS':'diningTable','BYM':'diningTable','MYM':'diningTable','TVC':'tvUnit','BTV':'tvUnit','MTV':'tvUnit','SHP':'table','BSH':'table','MSH':'table'}.get(prefix,'other')
groups={};unmatched={}
with fitz.open(PDF) as doc:
 for page_no in [3,4,5,6,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22]:
  text=doc[page_no-1].get_text();title=text.splitlines()[2];family=title.split()[0];room='bedroom' if 'Yatak' in title else 'youth' if 'Genç' in title else 'living';id=family.lower()+'-'+room
  translated={'bedroom':['Yatak Odası','Bedroom','Спальня','غرفة نوم'],'youth':['Genç Odası','Teen bedroom','Комната подростка','غرفة شباب'],'living':['Yaşam Odası','Living room','Гостиная','غرفة المعيشة']}[room]
  group=groups.setdefault(id,{'id':id,'title':dict(zip(['tr','en','ru','ar'],[family+' '+v for v in translated])),'room':room,'pages':[],'members':[]});group['pages'].append(page_no)
  for code in dict.fromkeys(re.findall(r'Ndn-[A-Za-z0-9-]+',text)):
   p=by_code.get(code.lower())
   if not p:
    row=unmatched.setdefault(code,{'code':code,'pages':[]});row['pages'].append(page_no);continue
   existing=next((m for m in group['members'] if m['productId']==p['id']),None)
   if existing:existing['pages'].append(page_no)
   else:group['members'].append({'productId':p['id'],'code':code,'kind':kind(p['code']),'pages':[page_no]})
fixed=[{'productId':p['id'],'sourceCode':p['code'],'sourceTitle':p['title']} for p in source['products'] if p['id'] in ['4786','4883','5003']]
mapping={'schema':1,'sourcePdf':'output/pdf/'+PDF.name,'pdfSha256':sha(PDF),'sourceCatalogSha256':sha(ROOT/'data/catalog-source.json'),'identitiesSha256':sha(ROOT/'data/catalog-identities.json'),'sets':list(groups.values()),'unmatched':list(unmatched.values()),'fixedSetProducts':fixed}
(ROOT/'data/furniture-sets.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'groups':len(groups),'members':sum(len(g['members']) for g in groups.values()),'unmatched':list(unmatched),'fixedSetProducts':len(fixed)},ensure_ascii=False))

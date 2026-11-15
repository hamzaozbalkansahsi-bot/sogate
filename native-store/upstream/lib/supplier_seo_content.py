"""Correct inherited default material facts using explicit supplier variant choices."""
from copy import deepcopy
MATERIALS={
 'cam':('Çam','Pine','Сосна','صنوبر'), 'kayin':('Kayın','Beech','Бук','زان'),
 'mese':('Meşe','Oak','Дуб','بلوط'), 'ayous':('Ayous','Ayous','Абаш','أيوس'),
 'ihlamur':('Ihlamur','Lime wood','Липа','خشب الزيزفون'), 'kestane':('Kestane','Chestnut','Каштан','كستناء'),
 'limba':('Limba','Limba','Лимба','ليمبا'), 'disbudak':('Dişbudak','Ash','Ясень','مران')}
LOCALES=['tr','en','ru','ar']
def enrich_supplier(product,source,detail):
 p=deepcopy(product);d=deepcopy(detail);material=next((a['value']for a in source.get('variantAttributes',[])if a['name']=='Ağaç Cinsi'),None)
 wood=MATERIALS.get((material or'').removesuffix('-kisa-boy'))
 if p.get('modelId')=='alka-family-30373':
  generic=('Desenli Faturalı Kapı Çıtası','Patterned Rebated Door Moulding','Узорчатый дверной молдинг с четвертью','حلية باب مزخرفة بحافة متدرجة')
  names=dict(zip(LOCALES,generic))
  if wood:names={l:wood[i]+' '+names[l]for i,l in enumerate(LOCALES)}
  p['name']=names;p['modelName']=deepcopy(names);p['description']=deepcopy(names)
 if wood:
  paragraphs={l:d['description'][l].split('\n\n')for l in LOCALES};indices=[i for i,t in enumerate(paragraphs['tr'])if t.strip()=='Ağaç cinsi ıhlamur ağacıdır.']
  if indices:
   assert len(set(len(v)for v in paragraphs.values()))==1,'Material paragraphs must stay aligned'
   values=[f'Ağaç cinsi: {wood[0]}.',f'Wood species: {wood[1]}.',f'Порода дерева: {wood[2]}.',f'نوع الخشب: {wood[3]}.']
   for i in indices:
    for j,l in enumerate(LOCALES):paragraphs[l][i]=values[j]
   d['description']={l:'\n\n'.join(paragraphs[l])for l in LOCALES}
 return p,d

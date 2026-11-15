"""Source-preserving content, units and translation tokens for the wood suppliers."""
import copy,re
from decimal import Decimal
from bs4 import BeautifulSoup,SoupStrainer

BRAND=re.compile(r'\b(?:alka(?:\s+ah[şs]ap)?|alt[ıi]n\s*[iİı]?[şs]\s*a[ğg]a[çc]|adore)\b',re.I)
NUMBER=re.compile(r'\d+(?:[.,]\d+)?')
def protect_numbers(text):
 values=[]
 def replace(match):values.append(match.group());return 'ZXQ'+str(len(values)-1)+'ZXQ'
 return NUMBER.sub(replace,text),values
def restore_numbers(text,values):
 for i,value in enumerate(values):
  token='ZXQ'+str(i)+'ZXQ'
  if text.count(token)!=1:raise ValueError('translation_numeric_token_changed')
  text=text.replace(token,value)
 if re.search(r'ZXQ\d+ZXQ',text):raise ValueError('translation_unbound_token')
 return text

def validate_dimension_layout(source,target):
 """Clauses may move; dimensions and numeric ranges retain their internal order."""
 numbers=re.findall(r'ZXQ\d+ZXQ',target)
 patterns=[r'ZXQ\d+ZXQ(?:\s*[xX×]\s*ZXQ\d+ZXQ){1,2}',r'(?<!\w)ZXQ\d+ZXQ\s*[–−-]\s*ZXQ\d+ZXQ(?!\w)']
 for pattern in patterns:
  for match in re.finditer(pattern,source):
   expected=re.findall(r'ZXQ\d+ZXQ',match[0])
   if expected[0]not in numbers:raise ValueError('translation_dimension_missing')
   position=numbers.index(expected[0])
   if numbers[position:position+len(expected)]!=expected:raise ValueError('translation_dimension_order_changed')
def display_title(value):
 text=re.sub(r'\b\d+(?:[.,]\d+)?\s*[xX×]\s*\d+(?:[.,]\d+)?(?:\s*[xX×]\s*\d+(?:[.,]\d+)?)?\s*(?:cm|mm)?\b','',value,flags=re.I)
 text=re.sub(r'\b\d+(?:[.,]\d+)?\s*(?:cm|mm)\b','',text,flags=re.I)
 text=re.sub(r'\s+',' ',text).strip(' -–|,')
 words=[]
 for word in text.split():
  if any(c.isdigit()for c in word):words.append(word);continue
  if word in ['MDF','PVC','CNC','TV','L']:words.append(word);continue
  low=word.replace('İ','i').replace('I','ı').lower();words.append(low[0].upper()+low[1:])
 return ' '.join(words)or value
def inherit_variant(child,parent):
 result=copy.deepcopy(child)
 if not result.get('description'):result['description']=parent.get('description','')
 if not result.get('salesUnit'):result['salesUnit']=parent.get('salesUnit')
 materials={'cam':'Çam','kayın':'Kayın','kayin':'Kayın','ayous':'Ayous','ihlamur':'Ihlamur','ıhlamur':'Ihlamur','mese':'Meşe','meşe':'Meşe','kestane':'Kestane'}
 for a in result.get('variantAttributes',[]):
  if a['name']=='Ağaç Cinsi':
   material=materials.get(a['value'],a['value']);result['title']=re.sub(r'^(Çam|Kayın|Ayous|Ihlamur|Meşe|Kestane)\b',material,parent['title'],flags=re.I)
 return result
def quantity_policy(product):
 text=product.get('description','');unit=product.get('salesUnit');out={'unit':{'Adet':'piece','Metre':'metre','Boyu':'length','Kilo':'kg','Takım':'set'}.get(unit,'quote'),'minimum':1,'step':1}
 if unit=='Metre':
  match=re.search(r'En\s+az\s+(\d+)\s+Metre\s+ve\s+katları',text,re.I)
  if match:out['minimum']=out['step']=int(match[1])
 length=re.search(r'standart\s+boyu\s+(\d+(?:[.,]\d+)?)\s+metre',text,re.I)
 if length:out['stockLengthM']=str(Decimal(length[1].replace(',','.')))
 return out
def public_content(product,html=None):
 paragraphs=[];dimensions={};title=product['title'];first=product.get('description','').split('\n')[0]
 if html:
  soup=BeautifulSoup(html,'lxml',parse_only=SoupStrainer(class_='product-detail'));detail=soup.select_one('.product-detail')
  if detail:
   for node in detail.select('p,h2,h3,h4,li,summary'):
    if node.find_parent(['p','li','summary']):continue
    text=node.get_text(' ',strip=True)
    if text:paragraphs.append(text)
   for table in detail.select('table'):
    rows=[[c.get_text(' ',strip=True)for c in row.select('th,td')]for row in table.select('tr')]
    if len(rows)>=2 and len(rows[0])==len(rows[1]):
     for label,value in zip(rows[0],rows[1]):
      key={'genişlik':'width','derinlik':'depth','yükseklik':'height'}.get(label.lower())
      match=re.fullmatch(r'(\d+(?:[.,]\d+)?)\s*cm',value,re.I)
      if key and match:dimensions[key]=float(Decimal(match[1].replace(',','.')))
    for row in rows:
     if len(row)==2 and row[0]and row[1]:paragraphs.append(row[0]+': '+row[1])
 if not paragraphs:paragraphs=re.split(r'[✔✓]\s*|\n+',product.get('description',''))
 result=[];seen=set()
 for text in paragraphs:
  text=re.sub(r'\s+',' ',text).strip()
  if not text or text in seen or text.casefold()==title.casefold():continue
  if html and len(paragraphs)>1 and len(first)<160 and text.casefold()==first.casefold():continue
  if any(x in text.lower()for x in ['whatsapp','bize yazın','koleksiyonları','hakkında detaylı bilgi','müşteri hizmetlerimiz']):continue
  if re.search(r'https?://|\bwww\.',text):continue
  if BRAND.search(text):
   text=BRAND.sub('NODENO',text)
   if 'koleksiyon' in text.lower():continue
  if len(text)>100 and text.count(',')>6 and not any(c in text for c in '.:?!'):continue
  seen.add(text);result.append(text)
 return {'title':display_title(title),'paragraphs':result,'dimensions':dimensions}

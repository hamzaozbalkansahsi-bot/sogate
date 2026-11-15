import {translateText,translateCategory,translationIsComplete} from './translations.mjs';
import {safeMediaUrl} from './server.mjs';
import {resolveCatalogIdentities} from './catalog-identities.mjs';

const locales=['tr','en','ru','ar'];
const categoryAliases=new Map([['adore-gaming','oyuncu-mobilyalari'],['adoregaming-tgif','tgif-serisi']]);
const publicCategoryId=value=>categoryAliases.get(String(value))||String(value).replace(/(^|[-_])adore(?:gaming)?(?=[-_]|$)/gi,'$1nodeno');
// Presentation only: source records, product identities and trusted media URLs
// keep their original values. Unicode boundaries also protect unrelated models.
const supplierName='(?:adore(?:[\\s_-]*m[oö]b[iıİ]lya)?|адор[еэ](?:[\\s_-]*мобил(?:ья|я))?|[اأإآ]دور(?:ي|ه)?(?:[\\s_-]*(?:موبيليا|موبليا|للأثاث|الأثاث))?)';
const supplierBrand=new RegExp(`(?<![\\p{L}\\p{N}_])${supplierName}(?![\\p{L}\\p{N}_])`,'iu');
const presentationBrand=new RegExp(`(?<![\\p{L}\\p{N}_])${supplierName}(?![\\p{L}\\p{N}_])(['’](?:n[ıiuüİ]n|[ıiuüİ]n|[dt][ae]n?|y?[aeıiuüİ]|l[ıiuüİ]k?))?`,'giu');
function brandSuffix(value) {
 if(!value)return '';
 const suffix=value.slice(1).toLocaleLowerCase('tr-TR');
 if(/^n?[ıiuü]n$/.test(suffix))return "'nun";
 if(/^[dt][ae]n$/.test(suffix))return "'dan";
 if(/^[dt][ae]$/.test(suffix))return "'da";
 if(/^y?[ae]$/.test(suffix))return "'ya";
 if(/^y?[ıiuü]$/.test(suffix))return "'yu";
 if(/^l[ıiuü]k?$/.test(suffix))return suffix.endsWith('k')?"'luk":"'lu";
 return value;
}
const clean=(value)=>String(value||'').normalize('NFC').replace(presentationBrand,(_,suffix)=>'NODENO'+brandSuffix(suffix)).replace(/[ \t]+/g,' ').replace(/\n{3,}/g,'\n\n').trim();
const localized=(value,kind)=>Object.fromEntries(locales.map(lang=>[lang,clean(lang==='tr'?value:translateText(value,lang,{kind}))]));
// A supplier patent/distributor statement must not become a NODENO claim.
// Drop that line, retaining any genuine technical lines in the same source row.
const specificationText=(value)=>String(value||'').split(/\r?\n/).filter(line=>!(supplierBrand.test(line)&&/(?:patent|запатент|براءة|distribüt|distributor|дистрибьют|موزع)/iu.test(line))).join('\n').trim();
const supplierPatentDesign=new RegExp(`(?<![\\p{L}\\p{N}_])${supplierName}(?:['’]n[ıiuüİ]n)?\\s+patentl[iİ]\\s+(?:özel\\s+)?tasarımı`,'giu');
const descriptionText=(value)=>String(value||'').replace(supplierPatentDesign,'Özel tasarımı');
const sellerPolicy=(value)=>/(?:garanti|sipariş|kargo|ücretsiz|iade|indirim|fiyat|müşteri hizmet|0850|\bdhl\b|\bhoroz\b|ödeme|güvence|distribüt|(?:sadece|yalnızca).*mağaza|türkiye.*ilk|ilk.*\badore\b)/.test(String(value||'').toLocaleLowerCase('tr-TR'));
const merchantCategoryNames={
 kampanya:{tr:'Koleksiyon seçkisi',en:'Collection edit',ru:'Подборка коллекции',ar:'مختارات المجموعة'},
 'ozel-gunler':{tr:'Özel seçkiler',en:'Special selections',ru:'Особые подборки',ar:'مختارات خاصة'},
 'sepette-ek':{tr:'Tamamlayıcı seçimler',en:'Complementary selections',ru:'Дополнительные решения',ar:'اختيارات مكملة'},
 'kupon-ozel':{tr:'Ürün seçkisi',en:'Product edit',ru:'Подборка товаров',ar:'مختارات المنتجات'},
 'efsane-kasim':{tr:'Sezon seçkisi',en:'Seasonal edit',ru:'Сезонная подборка',ar:'مختارات الموسم'},
};

export function normalizeCatalog(source,{identities}={}) {
 const identityMap=resolveCatalogIdentities(source,identities);
 const ids=new Set(), codes=new Set(), media={};
 const report={productsMissingImages:0,productsMissingDescription:0,productsMissingSpecs:0,translationPending:{en:0,ru:0,ar:0},sourceComplete:Boolean(source.meta?.complete),catalogueIdentities:identityMap.size};
 const categories=(source.categories||[]).filter(c=>c.id).map(c=>({id:publicCategoryId(c.id),parentId:c.parentId?publicCategoryId(c.parentId):null,name:merchantCategoryNames[c.id]||Object.fromEntries(locales.map(lang=>[lang,clean(translateCategory(clean(c.name||c.title||String(c.id).replaceAll('-',' ')),c.id,lang))])),count:0}));
 const categoryMap=new Map(categories.map(c=>[c.id,c]));
 if(categoryMap.size!==categories.length)throw new Error('Duplicate public category ID');
 const products=(source.products||[]).map(p=>{
  const id=String(p.id||'');
  if(!/^[A-Za-z0-9_-]+$/.test(id) || ids.has(id)) throw new Error('Invalid or duplicate product ID');
  if(!p.code || codes.has(p.code)) throw new Error('Missing or duplicate product code');
  ids.add(id);codes.add(p.code);
  media[id]=(p.images||[]).filter(safeMediaUrl);
  if(!media[id].length) report.productsMissingImages++;
  if(!p.description) report.productsMissingDescription++;
  if(!p.specs?.length) report.productsMissingSpecs++;
  const identity=identityMap.get(id),code=identity?.code||p.code;
  const title=identity?.name.tr||clean(p.title)||code;
  const name=identity?{...identity.name}:localized(title,'title');
  const categoryIds=[...new Set((p.categoryIds||[]).map(publicCategoryId).filter(v=>categoryMap.has(v)))];
  const counted=new Set();
  for(const cid of categoryIds) {
   let category=categoryMap.get(cid);
   while(category && !counted.has(category.id)){counted.add(category.id);category.count++;category=categoryMap.get(category.parentId);}
  }
  // Supplier delivery offers and warranties are retained in the private source
  // archive; they are not a commitment by an unconfigured NODENO merchant.
  const sourceSpecs=(p.specs||[]).filter(s=>!/(?:teslimat|garanti|kullanım şart)/i.test(String(s.label).toLocaleLowerCase('tr-TR'))).map(s=>({...s,value:specificationText(s.value)})).filter(s=>s.value&&!sellerPolicy(s.value));
  const specs=sourceSpecs.map(s=>({label:localized(clean(s.label),'specLabel'),value:localized(clean(s.value),'specValue')}));
  const dimensions=sourceSpecs.find(s=>/ölçü/i.test(s.label))?.value||'';
  const finish=sourceSpecs.find(s=>/ren[kg]/i.test(s.label))?.value||'';
  // Mapped titles can intentionally differ from the supplier's marketing
  // series. Use the verified physical details rather than conflicting names.
  // Source prose remains archived; all technical rows below are preserved.
  const trDescription=identity||sellerPolicy(p.description)?'':clean(descriptionText(p.description));
  const description={tr:trDescription||[title+'.',identity?.notes?.tr||'',dimensions?`Ölçüler: ${clean(dimensions)}.`:'',finish?`Renk: ${clean(finish)}.`:'',`Ürün kodu: ${code}.`].filter(Boolean).join(' ')};
  for(const lang of ['en','ru','ar']) {
   const parts=[name[lang]+'.'];
   if(identity?.notes?.[lang])parts.push(identity.notes[lang]);
   if(dimensions) parts.push(({en:'Dimensions: ',ru:'Размеры: ',ar:'الأبعاد: '})[lang]+translateText(clean(dimensions),lang,{kind:'specValue'})+'.');
   if(finish) parts.push(({en:'Finish: ',ru:'Отделка: ',ar:'اللون: '})[lang]+translateText(clean(finish),lang,{kind:'specValue'})+'.');
   parts.push(({en:'Product code: ',ru:'Код товара: ',ar:'رمز المنتج: '})[lang]+code+'.');
   description[lang]=parts.join(' ');
  }
  const translationPending=[];
  for(const lang of ['en','ru','ar']) {
   if((!identity&&!translationIsComplete(title,lang,{kind:'title'})) || sourceSpecs.some(s=>!translationIsComplete(clean(s.value),lang,{kind:'specValue'}))) {translationPending.push(lang);report.translationPending[lang]++;}
  }
  const coverIndex=Math.max(0,media[id].findIndex(url=>!new URL(url).pathname.toLowerCase().endsWith('.gif')));
  return {id,code,name,description,...(identity?.notes?{scopeNote:{...identity.notes}}:{}),categoryIds,images:media[id].map((_,index)=>`/media/${id}/${index}`),coverIndex,specs,salePrice:null,availability:'unknown',translationPending};
 });
 const catalog={brand:{name:'NODENO',slogan:{tr:'İyi tasarım. Kolay yaşam.',en:'Good design. Easy living.',ru:'Хороший дизайн. Лёгкая жизнь.',ar:'تصميم جيد. حياة أسهل.'}},categories,products,meta:{productCount:products.length,categoryCount:categories.length,importedAt:source.meta?.generatedAt||null,incompleteCount:report.productsMissingImages+report.productsMissingSpecs,sourceComplete:report.sourceComplete,translationPending:report.translationPending}};
 return {catalog,media,report};
}

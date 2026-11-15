/* native-locale-copy */
import {localeCopy} from './locale-runtime.js?v=storefront-recovery-20261112-r1';
import {groupSpecs} from './product-specs.js?v=storefront-recovery-20261112-r1';

import {storeLocales,localizedValue} from './locale-runtime.js?v=storefront-recovery-20261112-r1';
const languages=new Set(storeLocales);
const local=(value,locale)=>localizedValue(value,locale);
const fields=localeCopy({tr:['Ölçüler','Renk','Ürün kodu'],en:['Dimensions','Finish','Product code'],ru:['Размеры','Отделка','Код товара'],ar:['الأبعاد','اللون','رمز المنتج']});
export function withoutColorSuffix(title,color){
 if(!color)return title;
 const escaped=String(color).replace(/[.*+?^${}()|[\]\\]/gu,'\\$&');
 return String(title).replace(new RegExp('\\s*[-–—]\\s*'+escaped+'\\s*$','iu'),'').trim()||title;
}
export function productAbout(product,locale='tr'){
 const lang=languages.has(locale)?locale:'tr',groups=groupSpecs(product.specs);
 let prose=local(product.description,lang).trim();
 const name=local(product.name,lang).trim();
 if(name&&prose.startsWith(name+'.'))prose=prose.slice(name.length+1).trim();
 const dimensions=product.specs?.find(s=>/ölçü/iu.test(local(s.label,'tr')));
 const color=product.specs?.find(s=>/ren[kg]/iu.test(local(s.label,'tr')));
 // Remove only exact identity fields already rendered separately. Never split
 // sentences on periods: decimals and substantive source prose must survive.
 for(const [label,value]of [[fields[lang][0],local(dimensions?.value,lang)],[fields[lang][1],local(color?.value,lang)||local(product.variantColor,lang)],[fields[lang][2],product.code]]){
  if(value)prose=prose.replace(label+': '+value+'.','').trim();
 }
 const highlights=[...new Set(groups.features.flatMap(row=>local(row.spec.value,lang).split(/\r?\n/u)).map(line=>line.trim()).filter(Boolean))];
 return {paragraphs:prose?prose.split(/\n\s*\n/u).map(s=>s.trim()).filter(Boolean):[],highlights};
}

export function productSuggestions(product,products,categories,recentIds=[]){
 const key=p=>p.modelId||p.id,map=new Map(categories.map(c=>[c.id,c]));
 const unique=list=>{const seen=new Set([key(product)]);return list.filter(p=>{if(!p||seen.has(key(p)))return false;seen.add(key(p));return true;});};
 const root=id=>{const seen=new Set();while(map.get(id)?.parentId&&!seen.has(id)){seen.add(id);id=map.get(id).parentId;}return id;};
 const current=new Set(product.categoryIds),roots=new Set(product.categoryIds.map(root));
 const sharedLeaf=p=>p.categoryIds.some(id=>current.has(id)&&map.get(id)?.parentId);
 const similar=unique(products.filter(sharedLeaf));const used=new Set(similar.map(key));
 const complementary=unique(products.filter(p=>!used.has(key(p))&&!sharedLeaf(p)&&p.categoryIds.some(id=>roots.has(root(id)))));
 const byId=new Map(products.map(p=>[p.id,p]));
 return {similar,complementary,recent:unique(recentIds.map(id=>byId.get(String(id))).filter(Boolean))};
}

export function productShareData({title,url,locale='tr'}){
 const target=new URL(url);
 const production=target.protocol==='https:'&&['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr'].includes(target.hostname);
 const preview=target.protocol==='http:'&&['localhost','127.0.0.1'].includes(target.hostname);
 if(!production&&!preview)throw new TypeError('Unsupported product share URL');
 const invitation=localeCopy({tr:'Görmeni istediğim bir ürün var;',en:'There is a product I would like you to see;',ru:'Хочу показать тебе один товар;',ar:'هناك منتج أود أن تراه؛'})[locale]||'Görmeni istediğim bir ürün var;';
 return {title:String(title||'NODENO'),url:target.href,text:invitation+' '+target.href};
}

export function shareChannels(data){
 return {whatsapp:'https://wa.me/?text='+encodeURIComponent(data.text),facebook:'https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(data.url),x:'https://twitter.com/intent/tweet?text='+encodeURIComponent(data.text),email:'mailto:?subject='+encodeURIComponent(data.title)+'&body='+encodeURIComponent(data.text),sms:'sms:?body='+encodeURIComponent(data.text)};
}

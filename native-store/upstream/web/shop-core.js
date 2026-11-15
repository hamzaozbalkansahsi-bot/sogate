import {isSupplierProduct,supplierQuantity,supplierPolicy} from './supplier-products.js?v=storefront-recovery-20261112-r1';
import {localized} from './i18n.js?v=storefront-recovery-20261112-r1';
import {shopTranslate} from './shop-i18n.js?v=storefront-recovery-20261112-r1';
import {storeLocales} from './locale-runtime.js?v=storefront-recovery-20261112-r1';

import {rankProductSearch} from './catalog-search.js?v=storefront-recovery-20261112-r1';
import {numericDimensions} from './product-specs.js?v=storefront-recovery-20261112-r1';
import {isDoor,doorOptions,doorLineKey,doorPrice,cartLineKey} from './door-core.js?v=storefront-recovery-20261112-r1';
import {displayMoney} from './currency.js?v=storefront-recovery-20261112-r1';
import {isCabinetFront,frontOptions,frontLineKey,frontPrice} from './cabinet-front-core.js?v=storefront-recovery-20261112-r1';
const MAX_QUANTITY=99;
export function normalizeCart(value,products) {
 const known=new Map(products.map(p=>[String(p.id),p])), merged=new Map();
 if(!Array.isArray(value)) return [];
 for(const item of value){
  if(!item || typeof item!=='object') continue;
  const id=String(item.id), quantity=Number(item.quantity);
  if(!known.has(id)||!Number.isFinite(quantity)||!Number.isInteger(quantity)||quantity<1) continue;
  const product=known.get(id);if(product.variationSelectionRequired)continue;if(isSupplierProduct(product)){const q=supplierPolicy(product);if(quantity<q.minimum||(quantity-q.minimum)%q.step!==0)continue;}let line={id,quantity};
  if(isDoor(product)){try{const options=doorOptions(item.options??{},product);line={...line,options,key:doorLineKey(id,options)};}catch{continue;}}
  if(isCabinetFront(product)){try{const options=frontOptions(item.options??{});line={...line,options,key:frontLineKey(id,options)};}catch{continue;}}
  const key=cartLineKey(line),old=merged.get(key);line.quantity=Math.min(isDoor(product)||isCabinetFront(product)?10000:MAX_QUANTITY,(old?.quantity||0)+quantity);if(isSupplierProduct(product))line.quantity=supplierQuantity(line.quantity,product);merged.set(key,line);
 }
 return [...merged.values()];
}
function searchFold(value){return String(value??'').toLocaleLowerCase('tr-TR').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replaceAll('ı','i');}
export function categoryFamily(id,categories=[]){
 const result=new Set([String(id)]);
 let changed=true;
 while(changed){changed=false;for(const category of categories){if(category.parentId!=null&&result.has(String(category.parentId))&&!result.has(String(category.id))){result.add(String(category.id));changed=true;}}}
 return result;
}
export const productDisplayName=(p,locale='tr')=>localized(p.modelName||p.name,locale);
export function distinctModels(products){const seen=new Set();return products.filter(p=>{const key=p.modelId||p.id;if(seen.has(key))return false;seen.add(key);return true;});}
export function priceFilterMinor(value){
 if(typeof value!=='string'||!/^\d{1,9}(?:[.,]\d{1,2})?$/.test(value.trim()))return null;
 const [whole,fraction='']=value.trim().replace(',','.').split('.');
 return Number(whole)*100+Number(fraction.padEnd(2,'0'));
}
export function categoryNavigation(categories,active=''){
 const byId=new Map(categories.map(c=>[String(c.id),c])),lineage=new Set();let node=byId.get(String(active));
 while(node&&!lineage.has(String(node.id))){lineage.add(String(node.id));node=byId.get(String(node.parentId));}
 const output=[],seen=new Set();
 const visit=(category,depth)=>{const id=String(category.id);if(seen.has(id))return;seen.add(id);output.push({...category,depth});if(lineage.has(id))for(const child of categories.filter(c=>String(c.parentId)===id))visit(child,depth+1);};
 for(const root of categories.filter(c=>c.parentId==null||c.parentId===''))visit(root,0);
 return output;
}
export function filterProducts(products,{query='',locale='tr',category='',categories=[],favorites=null,sort='recommended',groupModels=false,minPriceMinor=null,maxPriceMinor=null,color='',maxWidth=null,maxHeight=null,maxDepth=null}={}){
 const family=category?categoryFamily(category,categories):null;
 let result=rankProductSearch(products,query,locale).filter(p=>(!family||(p.categoryIds||[]).some(id=>family.has(String(id))))&&(!favorites||favorites.has(String(p.id))));
 for(const [axis,maximum]of Object.entries({width:maxWidth,height:maxHeight,depth:maxDepth}))if(Number.isFinite(maximum)&&maximum>0)result=result.filter(p=>{const bounds=numericDimensions(p.specs)[axis];return bounds!==null&&bounds.max<=maximum;});
 if(color)result=result.filter(p=>!p.colorReviewPending&&localized(p.variantColor,'tr')===color);
 if(Number.isSafeInteger(minPriceMinor)||Number.isSafeInteger(maxPriceMinor))result=result.filter(p=>{const price=unitPriceMinor(p);return price!==null&&(!Number.isSafeInteger(minPriceMinor)||price>=minPriceMinor)&&(!Number.isSafeInteger(maxPriceMinor)||price<=maxPriceMinor);});
 if(sort==='name-asc'||sort==='name-desc'){const direction=sort==='name-asc'?1:-1;result=[...result].sort((a,b)=>direction*productDisplayName(a,locale).localeCompare(productDisplayName(b,locale),locale,{numeric:true}));}
 if(sort==='price-asc'||sort==='price-desc'){const direction=sort==='price-asc'?1:-1;result=[...result].sort((a,b)=>{const left=unitPriceMinor(a),right=unitPriceMinor(b);return left===null?(right===null?0:1):right===null?-1:direction*(left-right);});}
 return groupModels?distinctModels(result):result;
}
export function unitPriceMinor(product){
 const price=product?.salePriceMinor;
 // Account baskets contain at most 100 lines, each with at most 99 units.
 return product?.currency==='TRY'&&Number.isSafeInteger(price)&&price>0&&price<=Math.floor(Number.MAX_SAFE_INTEGER/(100*MAX_QUANTITY))?price:null;
}
export function discountInfo(product){
 const sale=unitPriceMinor(product),previous=unitPriceMinor({...product,salePriceMinor:product?.previousPriceMinor});
 if(sale===null||previous===null||previous<=sale)return null;
 // Derive the display from verified amounts, never from an unchecked badge.
 // Round down except when the next whole rate differs only by half a kurus
 // from the actual monetary rounding of a percentage discount.
 const numerator=BigInt(previous-sale)*100n,denominator=BigInt(previous);
 let rate=numerator/denominator;
 if(numerator%denominator!==0n&&(rate+1n)*denominator-numerator<=50n)rate++;
 return{previousPriceMinor:previous,salePriceMinor:sale,discountPercent:Math.min(99,Number(rate))};
}
export function formatDiscount(percent,locale='tr'){
 if(!Number.isSafeInteger(percent)||percent<1||percent>99)return null;
 const language=storeLocales.includes(locale)?locale:'tr';
 const rate=new Intl.NumberFormat(language,{style:'percent',maximumFractionDigits:0}).format(percent/100);
 return shopTranslate('discountPercent',language).replace('{percent}',rate);
}
export function formatMoney(minor,locale='tr'){
 if(!Number.isSafeInteger(minor)||minor<0)return null;
 const language=storeLocales.includes(locale)?locale:'tr';
 return displayMoney(minor,language);
}
const decimalMoney=minor=>minor===null?null:`${Math.trunc(minor/100)}.${String(minor%100).padStart(2,'0')}`;
export function cartPrices(cart,products){
 const byId=new Map(products.map(p=>[String(p.id),p]));
 const items=normalizeCart(cart,products).map(item=>{const p=byId.get(item.id);if(isCabinetFront(p))return {...item,...frontPrice(p,item.options,item.quantity)};const unit=isDoor(p)?doorPrice(p,item.options).unitPriceMinor:unitPriceMinor(p);return{...item,unitPriceMinor:unit,lineTotalMinor:unit===null?null:unit*item.quantity};});
 const priced=items.filter(item=>item.unitPriceMinor!==null);
 const subtotal=priced.reduce((sum,item)=>sum+item.lineTotalMinor,0);
 if(!Number.isSafeInteger(subtotal))throw new RangeError('Basket price exceeds exact integer range');
 return{items,currency:'TRY',subtotalMinor:priced.length?subtotal:null,pricedCount:priced.length,unpricedCount:items.length-priced.length,quantity:items.reduce((sum,item)=>sum+item.quantity,0)};
}
export function quoteData(cart,products,locale='tr'){
 const byId=new Map(products.map(p=>[String(p.id),p])),prices=cartPrices(cart,products);
 return{brand:'NODENO',language:locale,currency:'TRY',notice:shopTranslate('quoteDisclaimer',locale),items:prices.items.map(item=>{const p=byId.get(item.id),discount=discountInfo(p);return{id:item.id,code:p.code,name:productDisplayName(p,locale),...(p.variantColor?{color:localized(p.variantColor,locale)}:{}),quantity:item.quantity,currency:item.unitPriceMinor===null?null:'TRY',unitPriceMinor:item.unitPriceMinor,lineTotalMinor:item.lineTotalMinor,unitPrice:decimalMoney(item.unitPriceMinor),lineTotal:decimalMoney(item.lineTotalMinor),...(discount?{previousUnitPriceMinor:discount.previousPriceMinor,previousUnitPrice:decimalMoney(discount.previousPriceMinor),previousLineTotalMinor:discount.previousPriceMinor*item.quantity,previousLineTotal:decimalMoney(discount.previousPriceMinor*item.quantity),discountPercent:discount.discountPercent}:{})};}),subtotalMinor:prices.subtotalMinor,subtotal:decimalMoney(prices.subtotalMinor),subtotalType:prices.pricedCount===0?'unavailable':prices.unpricedCount?'partial':'complete',unpricedItemCount:prices.unpricedCount};
}
export function quoteText(cart,products,locale='tr'){
 const t=key=>shopTranslate(key,locale),data=quoteData(cart,products,locale);
 const lines=data.items.map((item,index)=>{const discountLabel=formatDiscount(item.discountPercent,locale),previous=item.previousUnitPriceMinor===undefined?'':`${t('previousUnitPrice')}: ${formatMoney(item.previousUnitPriceMinor,locale)}\n`;return`${index+1}. ${item.name}\n${item.color?t('productColor')+': '+item.color+'\n':''}${t('code')}: ${item.code}\n${t('quantity')}: ${item.quantity}\n${previous}${item.unitPriceMinor===null?t('notPriced'):`${t('unitPrice')}: ${formatMoney(item.unitPriceMinor,locale)}\n${t('lineTotal')}: ${formatMoney(item.lineTotalMinor,locale)}`}${discountLabel?'\n'+discountLabel:''}`;});
 const total=data.subtotalMinor===null?'':`\n\n${t(data.unpricedItemCount?'pricedSubtotal':'subtotal')}: ${formatMoney(data.subtotalMinor,locale)}`;
 const missing=data.unpricedItemCount?`\n${t('missingPriceNotice')}`:'';
 return`${t('quoteHeading')}\n${t('slogan')}\n\n${lines.join('\n\n')}${total}${missing}\n\n${t('quoteDisclaimer')}\n`;
}
export function contactLinks(value={}){
 const links=[];
 if(typeof value.contactEmail==='string'&&/^[^\s<>"'@]+@[^\s<>"'@]+\.[^\s<>"'@]+$/.test(value.contactEmail))links.push({kind:'email',label:value.contactEmail,href:`mailto:${value.contactEmail}`});
 if(typeof value.contactPhone==='string'&&typeof value.contactPhoneUri==='string'&&/^tel:\+[0-9]{8,15}$/.test(value.contactPhoneUri))links.push({kind:'phone',label:value.contactPhone,href:value.contactPhoneUri});
 const safeUrl=input=>{try{const url=new URL(input);return url.protocol==='https:'&&!url.username&&!url.password?url:null;}catch{return null;}};
 const site=safeUrl(value.website);
 if(site&&typeof value.domain==='string'&&site.hostname===value.domain)links.push({kind:'website',label:value.domain,href:site.href});
 if(Array.isArray(value.socials))for(const social of value.socials){const url=safeUrl(social?.url);if(url&&typeof social.label==='string'&&social.label)links.push({kind:'social',label:social.label,href:url.href});}
 return links;
}


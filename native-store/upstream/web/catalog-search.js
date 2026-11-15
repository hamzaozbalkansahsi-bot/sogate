import {localized} from './i18n.js?v=storefront-recovery-20261112-r1';

export function normalizeSearchText(value){return String(value??'').slice(0,240).toLocaleLowerCase('tr-TR').normalize('NFKD').replace(/[\u0300-\u036f\u064b-\u065f\u0670]/gu,'').replaceAll('ı','i').replace(/[أإآ]/gu,'ا').replaceAll('ى','ي').trim();}
const compact=value=>normalizeSearchText(value).replace(/[^\p{L}\p{N}]/gu,'');
const indexCache=new WeakMap();
function words(value){return normalizeSearchText(value).split(/[^\p{L}\p{N}]+/u).filter(Boolean);}
function oneEdit(a,b){
 if(a===b)return true;if(Math.abs(a.length-b.length)>1)return false;
 let i=0;while(i<a.length&&i<b.length&&a[i]===b[i])i++;
 if(a.length===b.length)return a.slice(i+1)===b.slice(i+1)||(a[i]===b[i+1]&&a[i+1]===b[i]&&a.slice(i+2)===b.slice(i+2));
 return a.length>b.length?a.slice(i+1)===b.slice(i):a.slice(i)===b.slice(i+1);
}
function index(products,locale){
 let languages=indexCache.get(products);if(!languages){languages=new Map();indexCache.set(products,languages);}if(languages.has(locale))return languages.get(locale);
 const result=products.map((product,position)=>{const name=normalizeSearchText(localized(product.modelName||product.name,locale)),body=normalizeSearchText([name,localized(product.name,locale),localized(product.variantColor,locale),localized(product.name,'tr'),localized(product.variantColor,'tr'),product.code,'NODENO'].join(' '));return{product,position,name,body,code:compact(product.code),words:words(body)};});languages.set(locale,result);return result;
}
export function rankProductSearch(products,query='',locale='tr'){
 if(!Array.isArray(products))return[];const input=typeof query==='string'?query.trim().slice(0,200):'';if(!input)return products.slice();
 if(/^(?:https?:\/\/|\/\?)/iu.test(input)){try{const url=new URL(input,'https://nodenohome.com');if(['nodenohome.com','www.nodenohome.com','nodenohome.com.tr','www.nodenohome.com.tr'].includes(url.hostname)&&!url.username&&!url.password&&url.searchParams.has('product'))return products.filter(p=>p.id===url.searchParams.get('product'));}catch{}return[];}
 const needle=normalizeSearchText(input),terms=words(input),code=compact(input);if(!terms.length)return[];
 const matches=[];
 for(const entry of index(products,locale)){
  const compactCode=code&&entry.code.includes(code)&&/\d/u.test(code);let score=compactCode?1200:0,matched=true;
  if(!compactCode)for(const term of terms){if(entry.body.includes(term)){score+=entry.words.some(word=>word.startsWith(term))?20:10;}else if(term.length>=4&&!/\d/u.test(term)&&entry.words.some(word=>word.length>=4&&oneEdit(term,word))){score+=2;}else{matched=false;break;}}
  if(!matched)continue;if(entry.name===needle)score+=500;else if(entry.name.startsWith(needle))score+=200;
  matches.push({...entry,score});
 }
 return matches.sort((a,b)=>b.score-a.score||a.position-b.position).map(entry=>entry.product);
}
export function searchCategoryMatches(categories,query='',locale='tr'){
 const terms=words(query);return terms.length?categories.filter(category=>{const body=normalizeSearchText(localized(category.name,locale)+' '+localized(category.name,'tr'));return terms.every(term=>body.includes(term));}).slice(0,4):[];
}
export function rememberSearch(history,query){
 const clean=(Array.isArray(history)?history:[]).filter(value=>typeof value==='string'&&value.trim()&&value.length<=120&&!/@|https?:\/\//iu.test(value)).slice(0,6);
 if(typeof query!=='string')return clean;const value=query.trim();if(!value||value.length>120||/@|https?:\/\//iu.test(value)||/^\+?[\d\s()-]{7,}$/u.test(value))return clean;
 return[value,...clean.filter(old=>normalizeSearchText(old)!==normalizeSearchText(value))].slice(0,6);
}

import {storeLocales,localizedValue} from './locale-runtime.js?v=storefront-recovery-20261112-r1';
const locales=new Set(storeLocales);
const roles=new Map([
 ['ürünölçüleri','dimensions'],['ürünölçüsü','dimensions'],['ölçüler','dimensions'],['ölçüleri','dimensions'],
 ['ürünrengi','color'],['renk','color'],
 ['kolibilgisi','packaging'],['ambalajbilgisi','packaging'],['paketbilgisi','packaging'],
 ['ürünözellikleri','features'],['ürünözellikler','features'],['özellikler','features'],
 ['ürünmalzemesi','materials'],['ürünmalezemesi','materials'],['malzeme','materials'],['materyal','materials'],
 ['ürünkurulumu','assembly'],['kurulum','assembly'],['montajbilgisi','assembly'],
 ['bakımvetemizlik','care'],['bakım','care'],['temizlik','care'],
]);

function text(value,locale='tr'){
 if(typeof value==='string')return value.trim();
 if(!value||typeof value!=='object')return '';
 const localized=localizedValue(value,locale);
 return typeof localized==='string'?localized.trim():'';
}
function role(spec){
 const label=text(spec?.label).normalize('NFC').toLocaleLowerCase('tr-TR').replace(/[\s:：]+/gu,'');
 return roles.get(label)||'other';
}
function short(value,limit){return Boolean(value)&&value.length<=limit&&!/[\r\n\u2028\u2029]/u.test(value);}

const quantity='\\d+(?:[.,]\\d+)?(?:\\s*[-–]\\s*\\d+(?:[.,]\\d+)?)?';
const axisOrder='(?:genişlik\\s*[x×]\\s*yükseklik\\s*[x×]\\s*derinlik|g\\s*[x×]\\s*y\\s*[x×]\\s*d)';
const dimensionPattern=new RegExp(`^(${quantity})\\s*[x×]\\s*(${quantity})\\s*[x×]\\s*(${quantity})\\s*cm\\s*\\(\\s*${axisOrder}\\s*\\)\\.?$`,'u');

function dimensions(value){
 const match=dimensionPattern.exec(value.normalize('NFC').toLocaleLowerCase('tr-TR'));
 if(!match)return null;
 const values=match.slice(1,4);
 // Position alone is not evidence of an axis. Both the explicit source order
 // and positive numeric endpoints are required before labelling dimensions.
 if(values.some(part=>part.split(/[-–]/u).some(endpoint=>!(Number(endpoint.trim().replace(',','.'))>0))))return null;
 return values.map(part=>part.replace(/\s+/gu,' ').trim()+' cm');
}

export function summarizeSpecs(specs,locale='tr'){
 if(!Array.isArray(specs))return [];
 const language=locales.has(locale)?locale:'tr',result=[];
 const dimensionRow=specs.find(spec=>role(spec)==='dimensions');
 if(dimensionRow){
  const parsed=dimensions(text(dimensionRow.value));
  if(parsed){
   const keys=['width','height','depth'],labels=['dimensionWidth','dimensionHeight','dimensionDepth'];
   parsed.forEach((value,index)=>result.push({key:keys[index],labelKey:labels[index],value}));
  }else{
   const value=text(dimensionRow.value,language),label=text(dimensionRow.label,language);
   if(short(value,120)&&label)result.push({key:'dimensions',label,value});
  }
 }
 for(const [target,key,labelKey,limit] of [
  ['color','color','productColor',120],
  ['materials','material','productMaterial',100],
  ['packaging','packaging','productPackaging',100],
 ]){
  const row=specs.find(spec=>role(spec)===target&&short(text(spec.value),limit)&&short(text(spec.value,language),limit));
  if(row)result.push({key,labelKey,value:text(row.value,language)});
 }
 return result.slice(0,6);
}

/** Only explicit source axis order is accepted; adjustable values retain both endpoints. */
export function numericDimensions(specs){
 const result={width:null,height:null,depth:null};
 for(const fact of summarizeSpecs(specs,'tr'))if(Object.hasOwn(result,fact.key)){
  const numbers=fact.value.replace(/\s*cm$/u,'').split(/[-–]/u).map(value=>Number(value.trim().replace(',','.')));
  if(numbers.length<=2&&numbers.every(value=>Number.isFinite(value)&&value>0))result[fact.key]={min:Math.min(...numbers),max:Math.max(...numbers)};
 }
 return result;
}

export function groupSpecs(specs){
 const groups={attributes:[],features:[],materials:[],assembly:[],care:[],other:[]};
 if(!Array.isArray(specs))return groups;
 for(const [index,spec] of specs.entries()){
  const type=role(spec);
  const bucket=['dimensions','color','packaging'].includes(type)?'attributes':type;
  groups[bucket].push({spec,index});
 }
 return groups;
}

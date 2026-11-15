export const isCabinetFront=p=>p?.productType==='cabinet-front';
export function frontOptions(input={}){
 if(!input||typeof input!=='object'||Array.isArray(input)||Object.keys(input).some(key=>!['widthMm','heightMm','application'].includes(key)))throw new TypeError('front_options_invalid');
 const value={widthMm:input.widthMm??0,heightMm:input.heightMm??0,application:input.application??'solid'};
 if(!Number.isInteger(value.widthMm)||value.widthMm<1||value.widthMm>5000||!Number.isInteger(value.heightMm)||value.heightMm<1||value.heightMm>5000||!['solid','glazed','drawer','long'].includes(value.application))throw new TypeError('front_measurements_required');
 return value;
}
export function frontLineKey(id,o){return id+'@'+o.widthMm+'x'+o.heightMm+'-'+o.application;}
export function frontPrice(p,input,quantity=1){
 const o=frontOptions(input);if(!Number.isSafeInteger(quantity)||quantity<1||quantity>10000)throw new TypeError('front_quantity_invalid');
 const area=o.widthMm*o.heightMm,areaMm2=area*quantity,rate=p.salePriceMinor;
 const quoted=!Number.isSafeInteger(rate)||rate<=0||o.application==='glazed'&&!p.front?.glazingPriceVerified;
 const cost=a=>Number((BigInt(rate)*BigInt(a)+500000n)/1000000n);
 return {areaMm2,unitAreaMm2:area,unitRateMinor:rate??null,unitPriceMinor:quoted?null:cost(area),lineTotalMinor:quoted?null:cost(areaMm2),requiresQuote:quoted};
}
export function frontCartStatus(items,products,country){
 if(!/^[A-Z]{2}$/.test(country||''))throw new TypeError('delivery_country_required');
 const byId=new Map(products.map(p=>[p.id,p]));let areaMm2=0,hasFronts=false,invalidMeasurements=false;
 for(const item of items){if(!isCabinetFront(byId.get(item.id))||byId.get(item.id).front?.minimumApplies===false)continue;hasFronts=true;try{areaMm2+=frontPrice(byId.get(item.id),item.options,item.quantity).areaMm2;}catch{invalidMeasurements=true;}}
 const minimumAreaMm2=(country==='TR'?5:10)*1000000,missingAreaMm2=hasFronts?Math.max(0,minimumAreaMm2-areaMm2):0;
 return {hasFronts,areaMm2,minimumAreaMm2,missingAreaMm2,eligible:!invalidMeasurements&&missingAreaMm2===0,invalidMeasurements};
}
export function areaText(areaMm2,locale='tr'){
 if(!Number.isSafeInteger(areaMm2)||areaMm2<0)return '';
 return new Intl.NumberFormat(locale,{maximumFractionDigits:6}).format(areaMm2/1000000)+' m²';
}

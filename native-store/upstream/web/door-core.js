const defaults=Object.freeze({frameDepth:15,height:207,architrave18:false,glazed:false,hardware:false,handle:false,openingWidthMm:0,handing:'unspecified'});
export const doorFrameWidths=Object.freeze([95,115,145,165,185,215]);
const measuredKeys=['heightMm','leafWidthMm','frameWidthMm','glassModelId'];
export const isDoor=product=>product?.productType==='door';
export function doorOptions(input={},product){
 if(input===null||typeof input!=='object'||Array.isArray(input)||Object.keys(input).some(key=>!Object.hasOwn(defaults,key)&&!measuredKeys.includes(key)))throw new TypeError('door_options_invalid');
 const value={...defaults,...input};
 const measured=measuredKeys.some(key=>Object.hasOwn(input,key));
 if(measured){
  if(!Number.isInteger(value.heightMm)||value.heightMm<1000||value.heightMm>3500||![770,870].includes(value.leafWidthMm)||!doorFrameWidths.includes(value.frameWidthMm))throw new TypeError('door_measurements_invalid');
  const frame=value.frameWidthMm<=145?15:value.frameWidthMm===165?17:value.frameWidthMm===185?19:21;
  if(Object.hasOwn(input,'height')&&input.height!==Math.ceil(value.heightMm/10)||Object.hasOwn(input,'frameDepth')&&input.frameDepth!==frame)throw new TypeError('door_measurements_conflict');
  value.height=Math.ceil(value.heightMm/10);value.frameDepth=frame;value.glassModelId=input.glassModelId??'';
  if(typeof value.glassModelId!=='string'||value.glassModelId.length>100||value.glassModelId&&!/^[a-z0-9-]+$/.test(value.glassModelId)||value.glassModelId&&!value.glazed)throw new TypeError('door_glass_model_invalid');
  if(value.glazed&&!value.glassModelId)throw new TypeError('door_glass_model_required');
 }
 if(![15,17,19,21].includes(value.frameDepth)||!Number.isInteger(value.height)||value.height<100||value.height>350||!Number.isInteger(value.openingWidthMm)||value.openingWidthMm<0||value.openingWidthMm>5000||!['unspecified','left','right'].includes(value.handing))throw new TypeError('door_options_invalid');
 for(const key of ['architrave18','glazed','hardware','handle'])if(typeof value[key]!=='boolean')throw new TypeError('door_options_invalid');
 if(value.glazed&&!product?.door?.glassAvailable&&product?.door?.kind!=='glazed')throw new TypeError('door_glazing_unavailable');
 return value;
}
export function doorLineKey(id,options){return id+'@'+[options.frameDepth,options.height,+options.architrave18,+options.glazed,+options.hardware,+options.handle,options.openingWidthMm,options.handing].join('-')+(options.heightMm?'-mm'+options.heightMm+'x'+options.leafWidthMm+'x'+options.frameWidthMm+'-'+(options.glassModelId||'solid'):'');}
export function validDoorGlass(product,options,products){
 if(!options.heightMm||!options.glazed)return true;
 const models=products.filter(p=>p.modelId===product.modelId&&p.productType==='door'&&p.door?.kind==='glazed');
 return models.length?models.some(p=>p.id===options.glassModelId):options.glassModelId==='standard';
}
export const cartLineKey=item=>item?.key||item?.id;
export function doorPrice(product,input={}){
 if(!isDoor(product))return {unitPriceMinor:product?.salePriceMinor??null,knownUnitMinor:product?.salePriceMinor??null,requiresQuote:!Number.isSafeInteger(product?.salePriceMinor),reasons:[]};
 const options=doorOptions(input,product),reasons=[],base=product.salePriceMinor,fees=product.door.charges||{};
 let known=Number.isSafeInteger(base)&&base>0?base:null;
 if(known===null)reasons.push('source_price_missing');
 const add=(amount,reason)=>{if(!Number.isSafeInteger(amount)||amount<0){reasons.push(reason);return;}if(known!==null)known+=amount;};
 if(options.frameDepth>17)add(fees.depth?.[options.frameDepth],'frame_price_missing');
 if(options.architrave18)add(fees.architrave18,'architrave_price_missing');
 if(options.glazed)add(fees.glazing,'glazing_price_missing');
 if(options.hardware)add(fees.hardware,'hardware_price_missing');
 if(options.height>207)reasons.push('special_height');
 if(options.openingWidthMm>0)reasons.push('opening_measurement');
 if(options.handle)reasons.push('handle_model');
 if(product.door.finishGroup==='veneer')reasons.push('veneer_paint');
 if(known!==null&&!Number.isSafeInteger(known))throw new RangeError('door_price_overflow');
 return {unitPriceMinor:reasons.length?null:known,knownUnitMinor:known,requiresQuote:reasons.length>0,reasons};
}
export function doorMinimum(country){if(typeof country!=='string'||!/^[A-Z]{2}$/.test(country))throw new TypeError('delivery_country_required');return country==='TR'?5:10;}
export function doorCartStatus(items,products,country){
 const byId=new Map(products.map(p=>[p.id,p]));let quantity=0;
 for(const item of items){if(!Number.isSafeInteger(item.quantity)||item.quantity<1)throw new TypeError('door_quantity_invalid');if(isDoor(byId.get(item.id)))quantity+=item.quantity;}
 const minimum=doorMinimum(country),missing=quantity?Math.max(0,minimum-quantity):0;
 return {quantity,minimum,missing,eligible:missing===0,country};
}
export function convertTryMinor(tryMinor,rate,exponent=2){
 if(!Number.isSafeInteger(tryMinor)||tryMinor<0||!Number.isSafeInteger(rate?.rateMicros)||rate.rateMicros<=0||!Number.isSafeInteger(rate?.unit)||rate.unit<1||rate.unit>10000||!Number.isInteger(exponent)||exponent<0||exponent>3)throw new TypeError('exchange_rate_invalid');
 const numerator=BigInt(tryMinor)*10n**BigInt(exponent)*1_000_000n*BigInt(rate.unit),denominator=100n*BigInt(rate.rateMicros);
 const result=Number((numerator+denominator/2n)/denominator);if(!Number.isSafeInteger(result))throw new RangeError('exchange_amount_overflow');return result;
}

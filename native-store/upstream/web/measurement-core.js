import {isDoor,doorOptions,doorLineKey,doorPrice,validDoorGlass} from './door-core.js?v=storefront-recovery-20261112-r1';
import {isCabinetFront,frontOptions,frontLineKey,frontPrice} from './cabinet-front-core.js?v=storefront-recovery-20261112-r1';

export function measurementLines(product,rows,products){
 if(!Array.isArray(rows)||!rows.length||rows.length>100||!isDoor(product)&&!isCabinetFront(product))throw new TypeError('measurement_rows_invalid');
 return rows.map(row=>{
  if(!row||!Number.isInteger(row.quantity)||row.quantity<1||row.quantity>10000)throw new TypeError('measurement_quantity_invalid');
  const options=isDoor(product)?doorOptions(row.options,product):frontOptions(row.options);
  if(isDoor(product)&&!validDoorGlass(product,options,products))throw new TypeError('door_glass_model_invalid');
  return {id:product.id,quantity:row.quantity,options,key:isDoor(product)?doorLineKey(product.id,options):frontLineKey(product.id,options)};
 });
}
export function mergeMeasurementCart(cart,lines){
 const next=cart.map(row=>({...row})),known=new Map(next.map(row=>[row.key||row.id,row]));
 for(const line of lines){const key=line.key||line.id,old=known.get(key);if(!Number.isInteger(line.quantity)||line.quantity<1||line.quantity>10000)throw new TypeError('measurement_quantity_invalid');
  const quantity=(old?.quantity||0)+line.quantity;if(quantity>10000)throw new RangeError('measurement_quantity_limit');
  if(old)old.quantity=quantity;else{const copy={...line};next.push(copy);known.set(key,copy);}
 }
 if(next.length>100)throw new RangeError('measurement_cart_limit');return next;
}
export function measurementSummary(lines,products){
 const byId=new Map(products.map(p=>[p.id,p]));let knownMinor=0,quantity=0,areaMm2=0,quoteLines=0;
 // The basket coalesces identical configurations. Price the same canonical
 // groups here so whole-line rounding cannot change the total on addition.
 for(const line of mergeMeasurementCart([],lines)){const p=byId.get(line.id);if(!p)throw new TypeError('product_unavailable');quantity+=line.quantity;
  if(isCabinetFront(p)){const price=frontPrice(p,line.options,line.quantity);areaMm2+=price.areaMm2;if(price.lineTotalMinor===null)quoteLines++;else knownMinor+=price.lineTotalMinor;}
  else{const price=doorPrice(p,line.options);if(price.unitPriceMinor===null)quoteLines++;else knownMinor+=price.unitPriceMinor*line.quantity;}
 }
 if(!Number.isSafeInteger(knownMinor))throw new RangeError('measurement_price_overflow');return {knownMinor,quantity,areaMm2,quoteLines,totalMinor:quoteLines?null:knownMinor};
}
export function demoRows(type){
 return type==='door'?[{quantity:2,options:{heightMm:2070,leafWidthMm:770,frameWidthMm:115}},{quantity:2,options:{heightMm:2070,leafWidthMm:870,frameWidthMm:145}},{quantity:1,options:{heightMm:2070,leafWidthMm:870,frameWidthMm:115,glazed:true,glassModelId:'standard'}}]:[{quantity:2,options:{heightMm:1975,widthMm:225,application:'solid'}},{quantity:2,options:{heightMm:1914,widthMm:255,application:'glazed'}},{quantity:3,options:{heightMm:247,widthMm:597,application:'drawer'}}];
}

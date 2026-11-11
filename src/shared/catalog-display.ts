/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/shared/catalog-display.ts
 * Açıklama   : Katalog kartında birlikte gösterilen varyant ve fiyatı tek kaynaktan seçer.
 */
import {projectedPrice,type Currency,type Variant} from './contracts';

export function selectCatalogDisplay(variants:readonly Variant[],currency:Currency):{variant:Variant|undefined;priceMinor:number|null}{
 let variant:Variant|undefined,priceMinor:number|null=null;
 for(const candidate of variants){
  const price=projectedPrice(candidate,currency);
  if(price===null||!Number.isSafeInteger(price)||price<=0||price>9_000_000_000_000)continue;
  // SQL matched_products.min(amount_minor) ile aynı eşleşen varyant kümesi.
  if(priceMinor===null||price<priceMinor){variant=candidate;priceMinor=price;}
 }
 return {variant:variant??variants[0],priceMinor};
}

/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/shared/product-seo.ts
 * Açıklama   : Ürünün gerçekten gösterilen fiyat ve varyantlarından yapılandırılmış veri üretir.
 */
import type {Product,Locale,Currency} from './contracts';
import {localizedProductPath} from './seo-rules';
export function productStructuredData(product:Product,locale:Locale,currency:Currency,base:string,settlementCurrency:Currency|null=currency){
 if(product.fixture)return null;
 const paths={tr:localizedProductPath('tr',product.localizedSlugs?.tr??product.slug),en:localizedProductPath('en',product.localizedSlugs?.en??product.slug)};
 const url=new URL(paths[locale],base).href,en=locale==='en',name=en?product.nameEn:product.name,description=en?product.descriptionEn:product.description;
 const variants=product.variants.map(variant=>{
  const amount=variant.displayCurrency===currency?variant.displayPriceMinor:variant.currency===currency?variant.priceMinor:null;
  const offer=currency===settlementCurrency&&amount!==null&&amount!==undefined&&Number.isSafeInteger(amount)&&amount>0?{'@type':'Offer',url,priceCurrency:currency,price:`${BigInt(amount)/100n}.${(BigInt(amount)%100n).toString().padStart(2,'0')}`,availability:variant.available>0?'https://schema.org/InStock':'https://schema.org/OutOfStock'}:undefined;
  return {'@type':'Product',name:`${name} — ${en?variant.nameEn||variant.name:variant.name}`,sku:variant.sku,image:new URL(product.image,base).href,...(product.brand?{brand:{'@type':'Brand',name:product.brand}}:{}),...(offer?{offers:offer}:{}),...(variant.color?{color:variant.color}:{}),...(variant.size?{size:variant.size}:{})};
 });
 if(!variants.length)return null;
 const variesBy=[...(product.variants.some(variant=>variant.color)?['https://schema.org/color']:[]),...(product.variants.some(variant=>variant.size)?['https://schema.org/size']:[])];
 const structured=variants.length>1?{'@context':'https://schema.org','@type':'ProductGroup',productGroupID:product.id,name,description,...(variesBy.length?{variesBy}:{}),hasVariant:variants}:{'@context':'https://schema.org',...variants[0],description};
 const breadcrumb={'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:[{'@type':'ListItem',position:1,name:en?'Home':'Ana sayfa',item:new URL(en?'/en':'/',base).href},{'@type':'ListItem',position:2,name:en?'Products':'Ürünler',item:new URL(en?'/en/urunler':'/urunler',base).href},{'@type':'ListItem',position:3,name,item:url}]};
 return [structured,breadcrumb];
}

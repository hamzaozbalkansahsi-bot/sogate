/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/product-seo.test.ts
 * Açıklama   : Yapılandırılmış verinin görünür fiyat, stok, dil ve gerçek kayıtla tutarlılığını sınar.
 */
import {expect,it} from 'vitest';
import type {Product} from '../../src/shared/contracts';
import {productStructuredData} from '../../src/shared/product-seo';
const product:Product={id:'local-test',slug:'urun',localizedSlugs:{tr:'ic-giyim',en:'intimate-wear'},name:'İç Giyim',nameEn:'Intimate wear',description:'Ölçü ve Özellikler',descriptionEn:'Measurements and details',category:'ic-giyim',brand:'',image:'/media/atelier-01.svg',material:'',status:'published',warnings:'',care:'',manufacturer:null,fixture:false,variants:[{id:'v',sku:'LOCAL-SEO',name:'Bordo',nameEn:'Burgundy',priceMinor:12345,currency:'TRY',available:0,displayPriceMinor:4999,displayCurrency:'EUR'}]};
it('seçili fiyat listesi ve gerçek stok aynı Offer içinde korunur',()=>{
 const data=productStructuredData(product,'en','EUR','https://example.test')!;const text=JSON.stringify(data);
 expect(text).toContain('"price":"49.99"');expect(text).toContain('"priceCurrency":"EUR"');expect(text).toContain('OutOfStock');expect(text).toContain('/en/urun/intimate-wear');expect(text).not.toContain('AggregateRating');expect(text).not.toContain('Review');
});
it('seçili para listesi eksikse başka para veya sıfır fiyatla Offer uydurmaz',()=>{
 const data=productStructuredData({...product,variants:[{...product.variants[0],displayPriceMinor:null,displayCurrency:'GBP'}]},'tr','GBP','https://example.test');expect(JSON.stringify(data)).not.toContain('"offers"');
});
it('yerel fixture için arama motoruna ürün veya teklif şeması üretmez',()=>{expect(productStructuredData({...product,fixture:true},'tr','TRY','https://example.test')).toBeNull();});
it('gösterim parası seçili ülkenin tahsilat parasından farklıysa satın alınabilir Offer iddiası üretmez',()=>{expect(JSON.stringify(productStructuredData(product,'tr','EUR','https://example.test','TRY'))).not.toContain('"offers"');});
it('birden fazla gerçek varyant ProductGroup olur; olmayan marka/GTIN/puan eklenmez',()=>{
 const data=productStructuredData({...product,variants:[product.variants[0],{...product.variants[0],id:'v2',sku:'LOCAL-SEO-2',color:'Krem'}]},'tr','EUR','https://example.test');const text=JSON.stringify(data);expect(text).toContain('ProductGroup');expect(text).toContain('hasVariant');expect(text).toContain('schema.org/color');expect(text).not.toContain('gtin');expect(text).not.toContain('"brand"');
});

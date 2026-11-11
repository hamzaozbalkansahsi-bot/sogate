/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/social-assets.test.ts
 * Açıklama   : Sosyal SVG şablonlarının ölçü, veri, kaçış ve görsel bütünlüğünü doğrular.
 */
import {describe,it,expect} from 'vitest';
import {createHash} from 'node:crypto';
import {parseSocialInput,renderSocialSVG,verifyMediaBytes,socialSizes,type SocialSnapshot} from '../../src/server/social-assets';
const base:SocialSnapshot={template:'product',theme:'light',locale:'tr',title:'Özgür & İpek <script>keşif</script>',subtitle:'Üreticinin mevcut ürün kaydı.',variantName:'Gül kurusu · Özel ölçü',sku:'GERÇEK-TR-1',priceMinor:12345,currency:'TRY',generatedAt:'2026-11-11T00:00:00.000Z',fixture:false,source:{kind:'product',id:'p',variantId:'v'}};
describe('Düzenlenebilir sosyal varlık',()=>{
 it('istemcinin fiyatı, resmi veya SVG kaynağını belirlemesine izin vermez',()=>{
  const input={template:'product',theme:'light',locale:'tr',currency:'TRY',productId:'p',variantId:'v'};expect(parseSocialInput(input)).toEqual(input);
  for(const extra of [{priceMinor:1},{image:'https://foreign.example/a.jpg'},{svg:'<svg/>'},{role:'admin'}])expect(()=>parseSocialInput({...input,...extra})).toThrow();
 });
 it('görsel byte uzunluğu ve SHA256 referansı gerçekten eşleşmelidir',()=>{const bytes=Buffer.from('RIFF0000WEBP');const sha256=createHash('sha256').update(bytes).digest('hex');expect(()=>verifyMediaBytes(bytes,{sizeBytes:bytes.length,sha256})).not.toThrow();expect(()=>verifyMediaBytes(bytes,{sizeBytes:bytes.length+1,sha256})).toThrow();expect(()=>verifyMediaBytes(bytes,{sizeBytes:bytes.length,sha256:'0'.repeat(64)})).toThrow();});
 it('renderer içinde dış adres ve bozuk XML karakteri de reddedilir',async()=>{await expect(renderSocialSVG({...base,image:{dataUri:'https://example.invalid/a.webp',sha256:'0'.repeat(64),rightsReference:'Kaynak',source:'/uploads/a.webp',raster:true}})).rejects.toThrow();await expect(renderSocialSVG({...base,title:'Bozuk\ud800'})).rejects.toThrow();});
 it.each(Object.keys(socialSizes))('açık ve koyu %s şablonu sabit ölçülü, lisanslı ve düzenlenebilir metindir',async template=>{for(const theme of ['light','dark'] as const){const svg=await renderSocialSVG({...base,template:template as SocialSnapshot['template'],theme});const {width,height}=socialSizes[template as keyof typeof socialSizes];expect(svg.includes(`width="${width}" height="${height}"`)).toBe(true);expect(svg.includes('<text')).toBe(true);expect(svg.includes('data:font/ttf;base64,')).toBe(true);expect(svg.includes('SIL OPEN FONT LICENSE')).toBe(true);expect(svg.includes('<script>')).toBe(false);expect(svg.includes('<foreignObject')).toBe(false);expect(svg.includes('href="http')).toBe(false);expect(svg.includes('®')).toBe(false);}});
 it('SKU, fiyat ve kaynak Türkçe metnini değiştirmez; XML olarak kaçırır',async()=>{const svg=await renderSocialSVG(base);expect(svg.includes('GERÇEK-TR-1')).toBe(true);expect(svg.includes('123,45')).toBe(true);expect(svg.includes('&lt;script&gt;')).toBe(true);expect(svg.includes('Özgür')).toBe(true);expect(svg.includes('Gül kurusu')).toBe(true);expect(svg.includes('"variantId":"v"'.replaceAll('"','&quot;'))).toBe(true);});
});

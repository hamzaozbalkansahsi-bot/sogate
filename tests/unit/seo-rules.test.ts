/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/seo-rules.test.ts
 * Açıklama   : Canonical ve yönlendirme kurallarının özel sayfa ve açık yönlendirme risklerini sınar.
 */
import {expect,it} from 'vitest';
import {safePublicPath,localizedProductPath,seoFields} from '../../src/shared/seo-rules';
it.each(['https://evil.test/x','//evil.test/x','/\\evil.test','/urun/../hesap','/urun/%2fhesap','/hesap','/en/odeme','/api/x','/yonetim','/urun/a?q=private','/urun/a#x'])('özel veya belirsiz yönlendirme yolunu reddeder: %s',value=>{
 expect(()=>safePublicPath(value)).toThrow();
});
it('dil bazlı ürün yolunu deterministik üretir',()=>{
 expect(localizedProductPath('tr','ic-giyim')).toBe('/urun/ic-giyim');
 expect(localizedProductPath('en','intimate-wear')).toBe('/en/urun/intimate-wear');
 expect(safePublicPath('/rehber/bakim')).toBe('/rehber/bakim');
});
it('SEO alanları Türkçe metni korur ve HTML komutu olarak değerlendirmez',()=>{
 expect(seoFields.parse({title:'İç Giyim — Ölçü ve Özellikler',description:'İstanbul, İzmir, Iğdır ve Çeşme için bakım bilgileri.',alt:'Bordo ürünün ön görünümü'}).title).toContain('İç Giyim');
 expect(()=>seoFields.parse({title:'<script>x</script>',description:'a'.repeat(50),alt:''})).toThrow();
});

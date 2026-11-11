/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/public-catalog.ts
 * Açıklama   : Canonical, sitemap ve yönlendirmeler için gerçekten açılabilen ürün koşullarını paylaşır.
 */
export const PUBLIC_PRODUCT_SQL="p.status='published' AND EXISTS(SELECT 1 FROM categories category WHERE category.slug=p.category AND category.active=true) AND EXISTS(SELECT 1 FROM variants variant WHERE variant.product_id=p.id AND variant.active=true)";
export const ENGLISH_PRODUCT_SQL="length(trim(p.name_en))>0 AND length(trim(p.description_en))>0";

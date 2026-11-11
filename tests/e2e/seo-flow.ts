/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/e2e/seo-flow.ts
 * Açıklama   : Gerçek SEO formundan canonical ve eski ürün yönlendirmesine uzanan tarayıcı akışını sınar.
 */
import {expect,type Page} from '@playwright/test';
import type pg from 'pg';
export async function verifySEO(page:Page,pool:pg.Pool,productId:string,suffix:string){
 await pool.query("UPDATE products SET status='published',fixture=true,description='Yerel SEO ürün açıklaması',description_en='Local SEO product description' WHERE id=$1",[productId]);
 await page.goto('/yonetim/seo');await page.getByLabel('SEO kayıtlarında ara',{exact:true}).fill('Yerel yönetim sınaması');await page.getByRole('button',{name:'Ara',exact:true}).click();
 const edit=page.getByRole('button',{name:'SEO alanlarını düzenle',exact:true});await expect(edit).toHaveCount(1);await edit.click();
 const modal=page.getByRole('dialog',{name:'Ürünün SEO alanları'}),slug=`seo-${suffix}`,title='İstanbul — Ölçü ve Özellikler';
 await modal.getByLabel('Bu dilde ürün bağlantısı',{exact:true}).fill(slug);await modal.getByLabel('Sayfa başlığı',{exact:true}).fill(title);await modal.getByLabel('Meta açıklaması',{exact:true}).fill('İzmir, Iğdır, Şişli ve Çeşme için ürün bakım açıklaması.');await modal.getByLabel('Görsel alt metni',{exact:true}).fill('Bordo maskenin ön görünümü');await modal.getByRole('button',{name:'Kaydet',exact:true}).click();await expect(modal).not.toBeVisible();
 expect((await pool.query("SELECT slug FROM product_routes WHERE product_id=$1 AND locale='tr'",[productId])).rows[0].slug).toBe(slug);
 const old=await page.request.get(`/urun/ui-${suffix}`,{maxRedirects:0});expect(old.status()).toBe(308);expect(old.headers().location).toContain(`/urun/${slug}`);
 const canonical=await page.request.get(`/urun/${slug}`);expect(canonical.status()).toBe(200);const html=await canonical.text();expect(html).toContain(title);expect(html).toContain(`rel="canonical" href="http://127.0.0.1:3000/urun/${slug}"`);expect(html).toContain('noindex');expect(html).not.toContain('application/ld+json');
 const disabled=await page.request.post('/api/admin/seo',{headers:{origin:'http://127.0.0.1:3000'},data:{action:'redirect',from:`/urun/ui-${suffix}`,to:`/urun/${slug}`,reason:'Eski adresi açık yönetici kararıyla devre dışı bırakma sınaması',active:false}});expect(disabled.ok()).toBeTruthy();
 expect((await page.request.get(`/urun/ui-${suffix}`,{maxRedirects:0})).status()).toBe(404);
 await page.getByRole('button',{name:'Yönlendirme ekle',exact:true}).click();const redirect=page.getByRole('dialog',{name:'Yeni yönlendirme'});
 await redirect.getByLabel('Eski site içi yol',{exact:true}).fill(`/brand-guide-${suffix}`);await redirect.getByLabel('Mevcut hedef sayfa',{exact:true}).fill('/rehber');await redirect.getByLabel('İlgili karşılık ve değişiklik gerekçesi',{exact:true}).fill('Aynı rehber alanının önceki genel bağlantısı');await redirect.getByRole('button',{name:'Kaydet',exact:true}).click();await expect(redirect).not.toBeVisible();
 const general=await page.request.get(`/brand-guide-${suffix}`,{maxRedirects:0});expect(general.status()).toBe(308);expect(general.headers().location).toContain('/rehber');
 await page.screenshot({path:'docs/screenshots/admin-seo-mobile.png',fullPage:true});
}

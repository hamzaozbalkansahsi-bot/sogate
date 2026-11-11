/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/source-headers.mjs
 * Açıklama   : Elle yazılmış kaynaklara dosya görevi ve proje kredi başlığını ekler.
 */
import {readFile,writeFile,readdir} from 'node:fs/promises';
import path from 'node:path';
const descriptions={
 'auth.ts':'Güvenli oturum, rol ve oturuma bağlı iki adımlı doğrulama.',
 'customer.ts':'Müşteri adresleri, sepet sahipliği ve izinli hesap işlemleri.',
 'security.ts':'İstek kökeni, gövde limiti ve dosya güvenlik sınırları.',
 'orders.ts':'Sipariş, rezervasyon ve doğrulanmış ödeme durum geçişleri.',
 'catalog.ts':'Sunucu katalog araması, varyant ve kalıcı sepet erişimi.',
 'admin.ts':'Yetkili yönetim işlemleri ve denetlenebilir operasyon akışları.',
 'db.ts':'PostgreSQL bağlantısı, parametreli sorgu ve işlem tekrarları.',
 'contracts.ts':'Modüller arasında paylaşılan veri sözleşmeleri.',
 'stripe.ts':'Resmî Stripe SDK ile güvenli ödeme sağlayıcı adaptörü.',
 'storage.ts':'Yerel ve S3 uyumlu özel dosya depolama adaptörleri.',
 'order-document.ts':'Saklanan sipariş ve sözleşme özetini mali olmayan PDF olarak üretir.',
 'proxy.ts':'Türkçe ve İngilizce URL yönlendirmesi ile sunucu dilini belirler.',
};
async function walk(root){const entries=await readdir(root,{withFileTypes:true});return(await Promise.all(entries.map(entry=>entry.isDirectory()?walk(path.join(root,entry.name)):Promise.resolve([path.join(root,entry.name)])))).flat();}
const candidates=[...(await Promise.all(['src','scripts','tests'].map(walk))).flat(),...'next.config.ts playwright.config.ts vitest.config.ts eslint.config.mjs postcss.config.mjs'.split(' ')];let changed=0;
for(const file of candidates){
 if(!/\.(tsx?|mjs|css)$/.test(file))continue;
 let source=await readFile(file,'utf8');if(source.includes('* Proje      : SEXSOGATE'))continue;
 source=source.replace(/^\/\/ Proje: SEXSOGATE[^\n]*\r?\n\/\/ Dosya:[^\n]*\r?\n/,'');
 const relative=file.replaceAll('\\','/');const base=path.basename(file);
 const description=descriptions[base]??(relative.startsWith('tests/')?'İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.':base==='route.ts'?'HTTP işlemini doğrulayıp yetkili veri akışına bağlar.':base==='page.tsx'?'İlgili müşteri veya yönetim sayfasını sunar.':base==='layout.tsx'?'Sayfa kabuğu, dil ve gezinme düzenini kurar.':relative.startsWith('src/components/')?'Erişilebilir müşteri veya yönetim etkileşimini sunar.':relative.startsWith('scripts/')?'Yerel kurulum, doğrulama veya operasyon komutunu yürütür.':'Uygulamanın ilgili yapılandırmasını ve işlevini tanımlar.');
 const header=`/**\n * Proje      : SEXSOGATE\n * Geliştirici: PTYS Technoligess LLC\n * Tasarım    : Hamza ÖZBALKAN\n * Dosya      : ${relative}\n * Açıklama   : ${description}\n */\n`;
 const prefix=source.match(/^(?:#![^\n]*\n)?(?:["']use (?:client|server)["'];?\r?\n)?/)?.[0]??'';
 await writeFile(file,prefix+header+source.slice(prefix.length),'utf8');changed++;
}
console.log(`Kaynak başlığı uygulanan dosya: ${changed}. JSON, üretilmiş dosya ve vendor korunuyor.`);

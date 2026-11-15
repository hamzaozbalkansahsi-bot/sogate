# Ürün SEO başlangıç denetimi — 10 Kasım 2026

Bu belge değişiklik öncesi canlı ölçümleri kaydeder. Son yayın kabulü yerine geçmez. Kaynak kod, yönetici verisi veya uzak servis durumu bu denetimde değiştirilmedi.

## Canlı durum

Kamu kataloğunda 3.602 kayıt, bunların içinde 2.581 Alka/Altın İş kaydı bulunuyor. Türkçe ürün haritası 3.602 URL ve 8.250 görsel referansı içeriyor; 2.745 referans yeni `/assets/suppliers/` görsellerine ait. Harita yaklaşık 1,75 MB ile protokol sınırlarının altında. `robots.txt`, kök haritayı ilan ediyor. Yeni görsellerin haritaya hiç alınmadığı yönündeki varsayım doğrulanmadı.

Örnek ürünün TR ve AR karşılıkları kendi canonical adreslerini ve TR/EN/RU/AR ile `x-default` bağlantılarını sunuyor. Sepet ve arama sonuçları `noindex,follow` ile işaretli. Kamu HTML'sinde Google, Bing veya Yandex sahiplik meta etiketi görülmedi; bu gözlem DNS üzerinden sahiplik doğrulaması bulunmadığını kanıtlamaz.

## Doğrulanan eksikler

1. Ahşap kategori sunucu HTML'si yalnız 24 farklı ürüne bağlantı veriyor. Sonraki sayfaya `<a href>` bağlantısı yok; `p=2` aynı ürünleri ve ilk sayfanın canonical adresini döndürüyor. Bu nedenle JS çalıştırmadan kategori üzerinden bütün koleksiyona ulaşmak mümkün değil. Google, ardışık sayfalara gerçek bağlantı ve her sayfaya kendi canonical adresini öneriyor. [Google sayfalama belgesi](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading).
2. `alka-family-30373` örneğinin seçenekleri ahşap türüne göre değişmesine rağmen `ProductGroup.variesBy` alanı `color`. Kayın/meşe seçenekleri aynı çam model başlığını tekrarlıyor. Ahşap türü `material`, fiziksel ölçü seçenekleri `size` olarak ifade edilmeli; ayrıntılı çap/genişlik değerleri ayrıca korunmalı. Google'ın desteklediği alanlar arasında `width` ve `height` doğrudan `variesBy` seçeneği değil. SKU adresleri mevcut ürünün doğru seçeneğini açmalı. [Google ürün varyasyonları belgesi](https://developers.google.com/search/docs/appearance/structured-data/product-variants).
3. Örnek çıtanın açıklaması genel satış/teslim şartlarıyla başlıyor. Ürüne özgü ad, gerçek malzeme, satış birimi ve ölçü özellikleri önce gelmeli. Kaynakta olmayan özellik, stok, değerlendirme veya teslimat sözü eklenmemeli.
4. Aynı örneğin fiyatı 102 TRY/metre ve minimumu üç metre iken yapılandırılmış veri fiyatı yalnız `102.00` olarak bildiriyor. Birim fiyat ile minimum alınabilir miktarın toplamı karıştırılmamalı. Google Merchant ürün verisi, minimum satın alınabilir miktarın toplam tutarını ister; birim bazlı fiyatlar için `UnitPriceSpecification.referenceQuantity` tanımı bulunur. Satış birimi bilinmeyen 72 fiyatlı kayıtta koşulsuz Offer oluşturmamak gerekir. İşletme fiyatı veya minimumu değiştirilmeden, görünür fiyat ile yapılandırılmış veri aynı anlaşılır miktarı tanımlamalı. [Google ürün verisi şartnamesi](https://support.google.com/merchants/answer/7052112?hl=en-GB), [Google birim fiyat ölçüsü](https://support.google.com/merchants/answer/6324455?hl=en).

## Arama motoruna bildirim

Mevcut yönetim adaptörü `/api/admin/indexnow` altında kimlik doğrulaması gerektiriyor; anonim denemede 401 döndü. Sahiplik anahtarı SQLite ayarından okunuyor; gerçek anahtar bu denetimde alınmadı veya yazdırılmadı. Ürün/kampanya yayınları kuyruğa girebiliyor, fakat içe aktarılan bütün kataloğun otomatik kuyruğa alındığına dair kanıt yok.

IndexNow bir istekte en fazla 10.000 URL kabul ediyor. Tüm 3.602 ürünün dört dil adresi 14.408 URL ettiğinden bir toplu bildirim en az iki isteğe bölünmeli; değişmeyen adresler tekrar tekrar gönderilmemeli. 200/202 sonucu yalnız isteğin alındığını gösterir. [IndexNow protokolü](https://www.indexnow.org/documentation), [IndexNow SSS](https://www.indexnow.org/faq).

Google için kök site haritası zaten robots üzerinden keşfedilebilir. Search Console raporu veya API üzerinden gönderim, doğrulanmış hesap/mülk erişimi gerektirir; hesap oturumu olmadan gönderilmiş gibi raporlanamaz. [Google site haritası oluşturma ve gönderme](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

Dört gerçek dil için karşılıklı tam adresli `hreflang` korunmalı. Almanca/Farsça çeviri yokken `de`/`fa` sayfası veya ülke bazında kopya kapı sayfaları oluşturulmamalı. [Google yerelleştirilmiş sürümler](https://developers.google.com/search/docs/specialty/international/localized-versions).

## Yayın bütünlüğü gözlemi

İlk ve sonraki denemelerde `/api/health` 503 döndü; ürün/kategori/harita uçları 200 döndü. Uzak sürüm işaretçisi `597729266e3c432327eb0abec94370e3e54e7cf22cd824787806e4ebf1761232`, yani `cpanel-release-suppliers-ready-20261110-r7`.

Kimlik doğrulanmış cPanel salt okunur kontrolleriyle 43 özel manifest dosyasının tamamı (50.047.061 byte) ve 71 raster dışı kamu dosyasının tamamı (1.314.393 byte) beklenen SHA-256 değerleriyle eşleşti. Özel önbellek dizini ve medya kasası `0700`, UID 2010. Kasada beklenen 4.882 farklı eski görselin tamamı mevcut ve byte boyutları doğru; r7 medya doğrulama makbuzu mevcut. Bu bulgular 503 nedenini tek başına belirlemiyor. İlgili çalışma, gerçek istisnayı ayrıca tanılamalı; bu denetim güvenlik geçidini kaldırmayı önermiyor.

## Kanıtlar

- `artifacts/seo-products/live-audit-before.json`
- `artifacts/seo-products/live-release-integrity.json`
- `artifacts/seo-products/private-release-integrity-download.json`
- `artifacts/seo-products/public-nonraster-integrity.json`
- `artifacts/seo-products/vault-stat-audit.json`

HTML/XML örnekleri aynı klasörde tutuluyor. Uzak parolalar, anahtarlar ve müşteri verileri rapora alınmadı. Arama sırası veya dizine eklenme garantisi üretilmedi.

## Aynı denetim sırasında sonraki durum

Diğer yayın çalışması `cpanel-release-legal-20261110-r3` sürümünü etkinleştirdi; sürüm hash değeri `380ad28635c005c3b6c6f680884e911fc84ea72843c473ad0e43bdfdb5107088`. Bundan sonra sağlık yanıtı 200 ve PHP sürümü 8.4.27 olarak gözlendi. Eski 503'ün kesin nedeni bu salt okunur denetimle belirlenmedi; iyileşme yeni yayınla aynı zamana denk geldi.

Yeni sürümün bütün 2.549 kamu raster dosyası, kimlik doğrulanmış cPanel indirme uç noktasından stream edilip SHA-256 ile karşılaştırıldı. Toplam 463.441.176 byte kontrol edildi; sıfır uyuşmazlık var. Yeni sürüm ve önceki r7'nin raster manifestleri aynı olduğundan bu dosya kimlikleri her iki sürüm için de geçerli. Özet `artifacts/seo-products/public-raster-integrity.json`, dosya bazlı sonuçlar `public-raster-stream.ndjson` içindedir. Bu işlem 470,08 saniye sürdü ve dosya yüklemedi/değiştirmedi.

Gerçek GET isteğinde hem kamu katalog API'sinin hem ürün HTML'sinin gzip sıkıştırması ve `Vary: Accept-Encoding` başlığı mevcut. API katalog ayrıca ETag ve `no-cache` başlıkları sunuyor. HEAD yanıtında sıkıştırma başlığının bulunmaması, gerçek GET gövdesinin sıkıştırılmadığı anlamına gelmiyor.

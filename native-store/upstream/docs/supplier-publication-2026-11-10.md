# Alka ve Altın İş katalog yayını

## 11 Kasım 2026 — yeniden paketleme düzeltmesi

Önceki teslimlerde açık kalan üç cPanel paketleme hatası giderildi. Sorun, eski mobilya görsellerini test rasterleriyle değiştiren düzenin yeni tedarikçi kayıtlarını katalogda tutmasına rağmen onların özel açıklama ve görsel onay dosyalarını pakete almamasıydı. Artık katalogda tedarikçi kaydı varsa gerçek onay projeksiyonu, açıklamalar ve onaylı görseller birlikte doğrulanıp paketlenir. `testOnly` paketler üretime yüklenemez; test kolaylığı için yayın kapısı açılmaz.

Üretim doğrulayıcısı yalnız eski mobilya kodlarını beklemek yerine eski mobilya, kapı, kapak ve tedarikçi kaynaklarından tam katalog sözleşmesini yeniden kurar. Fiyat, satış birimi, kimlik ve görsel eşitliği denetlenir. Onaylı fotoğrafsız AK74 kaydı korunur. Eksik, değiştirilmiş veya onaysız tedarikçi görseli derlemeyi durdurur; paket içindeki raster değişirse PHP sağlık kontrolü 503 verir.

Gerçek PHP ile 361 Node ve 215 Python testi sıfır hata ve sıfır atlamayla geçti. `npm run build`, `npm run validate` ve üretim cPanel paketi başarılıdır. Kanıtlar `artifacts/packaging-fix-20261111` altındadır. Güncel yayın ve tarayıcı kabulü için aynı dizindeki `acceptance.json` kaydına bakın. Önceki bölümlerdeki hashler o tarihli yayınların kaydıdır.

Ana sayfanın ilgili vitrini dört dilde kapak yenilemeye uygun metni kullanır; yalnız `dolap-kapaklari` kategorisini seçer. Kategori bulunmazsa başka bir ürün türünü aynı başlık altında göstermez. Türkçe başlık: “Kapaklarla evinizin görünümünü baştan sona yenileyin.”

10 Kasım 2026 çalışmasının kapsamı Alka ve Altın İş ürünlerinin indirilmesi, marka temizliği, kaynak fiyat üzerine %20 fiyatlandırma, gerçek seçenek grupları, dört dil ve Turhost yayınıdır. Orijinal kaynaklar ve tedarikçi bağlantıları özel yönetim verisinde korunur.

## Kapsam ve istisnalar

- Alka: 644 ana kayıt ve 148 gerçek varyasyon, toplam 792 kayıt.
- Altın İş: 1.789 müşteri ürünü. Kaynaktaki `test` adlı deneme kaydı vitrine alınmaz.
- Yeni toplam: 2.581 ürün/varyasyon kaydı; önceki 1.021 kayıt korunur. Birleşik toplam 3.602 kayıttır.
- 2.168 farklı görsel hash ile onaylıdır. Alka'nın 244 görselinde rötuş uygulanmıştır; kaynaklar değiştirilmemiştir. Ürünün üzerindeki gerçek APEL ambalajı korunur.
- AK74 Kulp 160 mm K-10 B ürününde kaynak site de gerçek ürün fotoğrafı sunmuyor. Bu tek kayıt fotoğraf yok açıklamasıyla gösterilir; başka bir ürünün fotoğrafı kullanılmaz, büyütme düğmesi açılmaz. Kaynak kanıtı `artifacts/supplier-expansion/publication/source-exceptions/AK74.json` dosyasındadır.

2.034 kayıtta doğrulanmış fiyat vardır. Kaynak fiyatın %20 üzeri kuruş düzeyinde hesaplanır; indirim veya stok oluşturulmaz. 47 ana kayıtta önce gerçek seçenek seçilir; 500 diğer kayıtta fiyat için teklif gerekir. Kaynağın sayısal fiyat verdiği fakat satış birimini belirtmediği 72 kayıtta birim teklifle teyit edilir; bunlara adet/metre/takım varsayımı atanmaz. Altın İş kaynak fiyatları KDV dahil; Alka'nın belirtilmemiş vergi temeli için KDV iddiası eklenmez.

## Ürün ve yönetim davranışı

Malzeme, çap, genişlik ve boy seçimleri kaynaktaki gerçek varyasyonlara bağlanır. Aynı fotoğrafı kullanan farklı ölçüler tek ürüne yanlışlıkla birleştirilmez. Metre, tam boy, adet, kg ve takım ayrımı korunur; kaynak minimum ve artış değerleri hem tarayıcıda hem PHP tarafında denetlenir. Örneğin üç metre katlarıyla satılan ürün bir veya dört metre olarak gönderilemez.

Yönetim adresi `/yonetim#suppliers`. Kaynak firma, kaynak SKU ve doğrudan kaynak ürün bağlantısı özel tedarikçi kataloğundadır. Gerçek alış maliyetleri satış fiyatından ayrı tutulur. Fiyat listesi karşılaştırması ve mevcut 15 günlük hatırlatıcı korunur.

Türkçe açıklamalar korunur; İngilizce, Rusça ve Arapça karşılıklarında model ve sayısal yer tutucular bağlanır. Ölçü dizilerinin sırası ayrıca denetlenir. Kaynak satıcı reklamları ve arama kelimesi yığınları müşteri açıklamasından çıkarılır. Tam açıklamalar özel indeksli dosyadan `/api/supplier-products/{id}` ile okunur; yalnız ürün kimliği, dört dil açıklaması ve hash döner. SSR aynı tam açıklamayı kullanır.

## Yayın ve tekrar derleme

`data/supplier-storefront.json` kalıcı üretim projeksiyonudur. `supplier-details.bin`, `supplier-details.json` ve `supplier-media-approved.json` özel sunucu dosyalarıdır. Normal üretim derlemesi onay projeksiyonu, fiyat bağları, görsel hashleri ve açıklama hashleri değiştiğinde durur.

PHP yayını görselleri doğrudan Turhost üzerinden sunar. Derleme amaçlı Worker, bu büyük görselleri JavaScript içine base64 olarak gömmez; yalnız onaylı NODENO URL'sini ve SHA-256 değerini tutar. Tedarikçi CDN'sine geri dönüş yoktur. cPanel paketi yerel onaylı gerçek rasterleri kopyalar.

Yayıncı güncel canlı sürüm hashini eşleştirir, yedek alır, yalnız onaylı hash adlı rasterleri yükler ve HTTPS üzerinden çıktı byte'larını tekrar doğrular. Kalıcı hesap ve ödeme ayarları değiştirilmez. Eşzamanlı ödeme yayını görüldüğü için ürün paketi güncel `cpanel-release-stripe-sandbox-20261110` tabanına taşınmıştır.

## Kanıt ve teslim

- Birim testleri: `artifacts/supplier-expansion/publication/final-regression.log`, `final-python-tests.log`.
- Tarayıcı: `artifacts/supplier-expansion/publication/browser/acceptance.json` ve `acceptance-webkit.json`.
- Görsel inceleme: `artifacts/supplier-expansion/publication/media-review`.
- Temiz müşteri kataloğu: `output/pdf/NODENO_Ahsap_Urun_Katalogu_2026_Temiz.pdf`, 647 sayfa. İlk, ikinci ve son sayfa ayrıca render edilip incelenmiştir.
- Özel fiyat/tedarikçi raporu: `output/supplier-catalog/NODENO_Fiyat_Kontrol_ve_Tedarikci_Eslesmeleri.csv`.

Canlı kabul tamamlandı. Son sürüm `597729266e3c432327eb0abec94370e3e54e7cf22cd824787806e4ebf1761232`. Son yedek `/home/nodenoho/nodeno-backups/20261110T193300Z-suppliers-7b23d200`. `.com`, `www.com` ve `.com.tr` HTTPS sağlık yanıtları aynı sürümü, 3.602 toplam kaydı, 2.581 tedarikçi kaydını ve 2.168 onaylı yeni görseli doğruladı. Yeni 2.034 fiyatın tamamında %20 hesap canlı API üzerinden tekrar kontrol edildi. Yeni kodlar birbirinden farklıdır ve önceki ürün kodlarıyla çakışmaz. Kaynak firma bağlantıları kamu API’sine sızmıyor. Üç örnek tam açıklama API’si dört dilde doğrulandı. Gerçek HTTPS mağazada Chromium masaüstü/TR ve WebKit mobil/AR kontrolleri geçti; ilgili ekran görüntüleri `browser/live-*` dosyalarıdır.

Kanıtlar: `cpanel-release-suppliers-ready-20261110-r6-deployment.json`, `cpanel-release-suppliers-ready-20261110-r7-deployment.json`, `final-live-health.json`, `live-catalog-acceptance.json`, `live-pricing-acceptance.json`, `browser/live-acceptance.json`. Yönetim görünürlük bayraklarının son yayını, tarayıcıda test edilen müşteri vitrininin dosyalarını byte düzeyinde değiştirmedi. Hesaplar, kalıcı siparişler ve mevcut ödeme ayarları korundu.

Canlı misafir sepeti de gerçek tarayıcıda doğrulandı: Altın İş ürününde 1 adet, Alka metre varyasyonunda 3 metre sepete eklendi. Gerçek sipariş veya tahsilat oluşturulmadı.

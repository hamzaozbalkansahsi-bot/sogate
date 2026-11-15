# Hedef ülke dilleri ve para birimleri

12 Kasım 2026 tarihinde yayımlandı. Canlı sürüm: `af4206253f7b99b51084f2c71d195186cfe2bfbae6850729cbd6311518a0a821`.

Dil kayıtlarının kaynağı `data/store-locales.json` dosyasıdır. Mevcut Türkçe, İngilizce, Rusça ve Arapçaya Almanca, Azerbaycanca, Kazakça, Türkmence, Özbekçe, Kırgızca ve Farsça eklenir. Arapça ve Farsça sağdan sola gösterilir. Üst menüde dil ve para birimi ayrı ayrı değiştirilebilir.

| Haritada seçilen ülke | Dil | Başlangıç para birimi |
| --- | --- | --- |
| Türkiye | Türkçe | TRY |
| Almanya | Almanca | EUR |
| Birleşik Krallık | İngilizce | GBP |
| Azerbaycan | Azerbaycanca | AZN |
| Kazakistan | Kazakça | KZT |
| Türkmenistan | Türkmence | USD |
| Özbekistan | Özbekçe | USD |
| Kırgızistan | Kırgızca | USD |
| İran | Farsça | USD |
| Irak, Suriye | Arapça | USD |

TCMB akışında bulunmayan yerel para birimleri için kur üretilmez. Dil değiştirmek dilin varsayılan parasını seçer; sonrasında elle yapılan para seçimi korunur. Örneğin haritada Birleşik Krallık seçimi GBP, yalnız İngilizce dil seçimi USD kullanır. Ülke ve dil farklı tercihlerdir; gerçek teslimat ülkesi adres veya teklif formunda ayrıca doğrulanır. Kur hesabında haftanın o ana kadarki en yüksek TCMB satış kuru korunur.

Geçerli bağlantı dili ve kullanıcının kaydettiği tercih, IP ülkesinin önerisinden önce gelir. Haritada ülkeye tıklamak açık bir seçimdir; dili, para birimini ve vitrin ülkesini birlikte değiştirir. Aynı Wi-Fi üzerindeki kullanıcılar ortak bir tercih kaydını paylaşmaz; tercihler ilgili tarayıcıda tutulur.

## İçerik ve bakım

Katalogdaki mevcut dört dil, ürün kodları, ölçüler, teknik bilgiler, fiyatlar ve görsel kayıtları korunur. Yeni dil sözlükleri doğrulanmış İngilizce kaynak metne bağlanır. Kaynakta bulunmayan sayı ekleyen, korunan teknik değeri değiştiren, eksilen veya bozulmuş çeviriler yayın kapsamından çıkarılır. Eksik çeviri yerine İngilizce metin gösterilmez; yayın derlemesi eksik kapsamda durur.

İlk açılışta arayüz ve kısa katalog metinleri yüklenir. Uzun ürün açıklamalarını içeren ikinci sözlük ürün sayfası gerektiğinde bir kez yüklenir. Her iki dosyanın aynı kaynak envanterine ait olması gerekir. Sunucu tarafındaki ürün içeriği, arama motoru açıklamaları ve yasal sayfalar da aynı dil kapsamını kullanır.

Yönetimde ürün adı, açıklama ve SEO alanları yeni diller için düzenlenebilir. Yeni İngilizce metnin sözlükte karşılığı yoksa ilgili hedef dil alanları da doldurulmadan yayın yapılamaz. Taslak ve mevcut yayın korunur. Fiyat gibi metinden bağımsız değişiklikler bu kontrole takılmaz.

Çeviri bakımı: `scripts/inventory-target-locales.mjs` ile kaynak envanterini güncelleyin; `data/localization` altındaki gözden geçirilmiş ifadeleri ve terimleri koruyun. Derlenmiş sözlükler `scripts/compile-target-locales.py` ile üretilir. `--partial` çıktısı yalnız yerel inceleme içindir. Üretim derlemesi tam kapsam, güncel kaynak özetleri ve katalog kapsamı denetimlerini geçmelidir. Model, ham çeviri önbelleği ve karantinaya alınmış metinler yayın paketine alınmaz.

Otomatik taslaklar sayı/ölçü korumasına ve yanlış dil denetimine tabidir; hatalı model çıktıları kullanılmaz. Gözden geçirilmiş arayüz, yasal metin ve mobilya terimleri otomatik taslaklardan önceliklidir. Hatalı İngilizce tedarikçi ifadeleri gerektiğinde özgün Türkçe açıklamayla karşılaştırılır; örneğin “Saled sofa” sallanır koltuk, “Session: Bucks” satırındaki malzeme Papel, “News oak” kaynak ürünü ise fıçı biçimli meşe ayaktır. Ürün kodları ve gerçek ölçüler değiştirilmez.

Bu dil/arayüz yayını mağazadaki katalog, fiyat, medya, müşteri verisi ve ödeme ayarlarını mevcut canlı sürümden korur. Kaynak derlemesi için tedarikçi fiyat kanıtlarının yeniden okunması ayrı kaydedilir; kaynakta saptanan değişiklikler bu yayında müşteri fiyatlarına uygulanmaz.

## Kabul kayıtları

`artifacts/target-locales-20261111` altında 8.113 kaynak metin için sıfır eksik, 205.450 katalog alanı ve her yeni dilde 977 arayüz alanı kontrolü bulunur. 379 Node ve 237 Python testi geçti. Tam yayın paketi üzerinde 14 Chromium/WebKit senaryosu; 11 ülkenin harita, dil ve para birimi geçişleri; gerçek fotoğraf yüklenmesi; tam tedarikçi açıklaması; yasal sayfalar; 320 piksel Farsça RTL ve mobil Türkçe kartlar doğrulandı.

Canlı kontrolde `.com`, `www.com`, `.com.tr`, `www.com.tr` alan adları; 11 dilin ürün ve yasal HTTP yanıtları; dil sözlüklerinin gerçek HTTPS içerikleri; site haritaları ve üç gerçek tarayıcı görünümü doğrulandı. Gerçek ödeme veya sipariş oluşturulmadı. Ödeme açık, sözleşme sürümü `2026-11-10.3`, hesap/ödeme depoları ve 5.129 görselin onayları korundu.

`deployment.json`, `browser-local.json`, `browser-live.json`, `coverage.json`, `language-audit.json` ve `code-review.json` kabul kanıtlarıdır. İlk aktarımda cPanel metin okuma API'sinin 1 MB sınırı güvenli geri dönüşü tetikledi. Büyük herkese açık sözlüklerde fiziksel dosya boyutu UAPI ile, içerik ise sınırlı boyutlu ve kimlik bilgisi taşımayan HTTPS okuyucusuyla doğrulanır. Bu yolun boyut/içerik bozulmasını reddetmesi ayrıca test edildi. Son yayın ve canlı kabul başarılıdır.

Kullanılmayan çeviri modelleri ve başarısız paket geçici dosyaları kullanıcı talimatıyla temizlendi; yaklaşık 8,36 GB alan açıldı. Hazır sözlükler, kaynak katalog/görseller, fiyat kanıtları ve test ortamları korundu.

12 Kasım 2026 ek düzeltmesi: ürün ayrıntısı yükleme/hata metinleri de 11 dilde tamamlandı; kaynak envanteri 8.115 oldu. Altı kısa etiketin önceden gözden geçirilmiş dil karşılıkları uygulandı. Güncel canlı sürüm `f9453eba124fed16cd7a10fef7e064d542bfe6fd257b9aa17e14feec9b9cfec2`; yeni kabul kayıtları `artifacts/storefront-followup-20261112` altındadır. 379 Node + 244 Python testi ve aynı 14 tarayıcı görünümü geçti. Üç canlı görünümde HTTP 503, geçersiz yanıt ve başarılı yeniden deneme ayrıca kontrol edildi; miktar ve para birimi korunuyor.

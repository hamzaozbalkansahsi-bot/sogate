# Takım seçimini koruma ve adet kontrolleri

Bu tur mevcut takım akışındaki sınırlı bir geliştirmedir. Yeni hesap, ödeme, fiyat veya stok sistemi kurulmaz. Kullanıcının geliştirmeyi sürdürme ve otomatik yayın yetkisi geçerlidir; yeniden tasarım/yayın izni istenmez. Başlangıç commit: `2eb50f0`.

## Müşteri davranışı

Yeni takım seçimleri aynı tarayıcı sekmesinde korunur. Müşteri başka koleksiyona veya ürün detayına gidip dönünce, dili değiştirince ya da sayfayı yenileyince seçtiği parça, renk, adet ve takım sayısını geri alır. Bu kayıt başka cihazlara aktarılmaz; sekme kapatıldığında tarayıcının sekme yaşam döngüsüne bağlı olarak sonlanır. Tarayıcı sekme geri yükleme özelliği kaydı koruyabilir.

Bireysel ve toplu alım seçimleri ayrıdır. Hesap kimliği eşleşmeyen taslak gösterilmez. Yalnız ürün kimliği, varyant ve miktarlar kaydedilir; iletişim, fiyat, parola ve onay bilgileri kaydedilmez. Tarayıcı kaydı kapalı veya doluysa normal takım seçimi çalışır.

Adet alanlarının yanında artırma/azaltma düğmeleri bulunur. Seçilmeyen parçanın miktar düğmeleri kapalıdır; alt/üst sınırdaki düğme devre dışı kalır. Kaynakta tek SKU olan hazır setlerin kapsamı korunur. Fiyatlar her seferinde güncel katalogdan hesaplanır.

“Seçimleri temizle” yalnız açık koleksiyon ve alım biçiminin taslağını siler. Sepete veya teklif listesine başarılı ekleme ilgili yeni takım taslağını temizler; yenilemede kendiliğinden tekrar ekleme yapılmaz. Teklif listesindeki mevcut içeriğin düzenlenmesi bu kayıt kapsamına alınmaz; mevcut teklif kayıtları ve gönderim kilidi korunur.

Taslak geri yüklenirken güncel koleksiyon üyeliği ve ürün görünürlüğü yeniden doğrulanır. Kalkmış ürünün yerine başka renk/model konmaz. Bazı parçalar çıkarılmışsa müşteriye açık mesaj gösterilir. Boş/geçersiz ara adet girişi son geçerli kaydı silmez.

## Görsel yön

NODENO Sans, mevcut koyu marka rengi `#172D38`, zemin ve beyaz ürün kartları korunur. Yeni sayfa/tema yoktur. İşlevsel SVG artırma/azaltma düğmeleri en az 44 CSS piksel dokunma alanına sahiptir; ürün fotoğrafı da ürün detayına bağlantıdır. Klavye odağı korunur; dört dil ve Arapça RTL aynı kapsamda doğrulanır.

## Kanıt ve durum

- Eski gerçek pakette koleksiyon değişimi sonrası iki komodin seçiminin bire düşmesi/işaretin kalkması yeniden üretildi: `artifacts/set-drafts/browser-red.log`.
- Kayıt sözleşmesi RED→GREEN: `tests/furniture-drafts.test.mjs`, 5 test. Kaldırılan parça bilgisinin eksikliği ayrıca RED→GREEN ile doğrulandı.
- İlk gerçek paket Chromium/Windows WebKit kontrolü geçti: koleksiyon/yenileme/ürün dönüşü, mod/hesap ayrımı, renk koruma, temizlik, miktar sınırları, engelli saklama, dört dil, 320 piksel genişlik. Son paket `a508cb791ee39fef029d04927aed21d30cd2c37fb5b90eedfb35bd38ea53214a` üzerinde aynı kontroller iki tarayıcıda geçti; sayfa hatası yok (`browser-final.log`, `browser-report.json`).
- İlgisiz mevcut medya/PDF çalışmaları değiştirilmez. Zorunlu medya denetimi ve yedekli Turhost yayını atlanmaz.

- Tam kaynak: 226/226, sıfır atlama/hata (`source-tests-final.log`). İlk kaynak çalışması derlemeyle çakışınca üç paket testi eski Worker varlığı gördü; derleme bittikten sonra sıralı çalıştırma sorunsuz geçti. Son paketin üretimi sırasında kaynak değiştirilmedi.
- Son kod incelemesi aynı yazar tarafından `code-review-expert` ile yapıldı. Adet girişindeki geçici boşluğun `selection()` filtresinde elenerek eski taslağı eksik kaydetmesi önemli bulguydu. Gerçek tarayıcıda `invalid-edit-red.log` ile yeniden üretildi; kayıt doğrulamasına tüm seçili miktarlar iletilerek düzeltildi. `browser-final.log` iki tarayıcıda GREEN; tam suite 226/226.
- Önceki takım regresyonu: `6e9cbbafb10a0ff09e00b75306e5ec84ca0ddf01e0b6cd929ff5169c1a6bd44e` paketinde misafir/üyelikli atomik sepet, 10 takımın bileşenleri, düzenleme, yönetim ve bekleyen istek/hesap değişimi iki tarayıcıda geçti (`regression.log`). Son değişiklik yalnız geçersiz taslak girdisinin kaydedilmesini önler; yeni son-paket kabulü onu ayrıca kapsar.
- Yayın ve canlı kabul tamamlandı. Fiziksel telefon testi, gerçek ödeme, sosyal sağlayıcı aktivasyonu ve canlı talep/müşteri oluşturma kapsam dışıdır.

- Son paket regresyonu da `a508cb791ee39fef029d04927aed21d30cd2c37fb5b90eedfb35bd38ea53214a` üzerinde Chromium ve WebKit ile geçti (`regression-final.log`). Misafir/üyelikli sepet, atomik sınır, 10 takım/20 komodin, yataksız içerik, yönetim kaydı ve gönderim/hesap değişimi kilidi doğrulandı. Açık kritik/önemli inceleme bulgusu yok.

- Dağıtım yardımcı testleri: 18/18 (`deploy-tests.log`). Marka/katalog doğrulaması 667 SKU, 104 kategori ve 15 orijinal marka varlığıyla başarılı (`validate.log`).

- Zorunlu medya denetimi geçti; `a508cb791ee39fef029d04927aed21d30cd2c37fb5b90eedfb35bd38ea53214a` yedekli yayımlandı. Kaynak `c1270c9`. `uploaded_verified_health=ok`; yedek `/home/nodenoho/nodeno-backups/20261101T180119Z-a508cb791ee3-036805`.
- Canlı kabul GREEN (`live-acceptance.json`, `live-acceptance.log`): dört alan adı/TLS/sürüm; dört dil SSR/hreflang/canonical; 24 özel erişim sınırı; dört harita ve 12 varlık özeti. Gerçek Chromium'da 17 grup, dört dil mobil/RTL, masaüstü, taslak yenileme/koleksiyon dönüşü, fotoğrafla ürün detayı dönüşü, miktar düğmeleri, boş adet sonrası son geçerli seçim, mod ayrımı ve ekleme sonrası temizlik geçti. 1 dolap + 2 komodin + 1 şifonyer anonim sepette doğru, yatak yok; sayfa hatası yok. Üretimde müşteri veya talep oluşturulmadı.
- Canlı mobil ve masaüstü görüntüleri ayrıca gözle incelendi (`live-selection-mobile.png`, `live-builder-desktop.png`). Bu sınırlı geliştirme tamamlandı; ödeme/sosyal sağlayıcı ayarları önceki durumda korunur.

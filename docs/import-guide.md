# Katalog içe aktarma

11 Kasım 2026. CSV/XLSX aktarımı katalog veya yönetici rolü ve doğrulanmış MFA oturumu gerektirir. Hem şablon indirme hem önizleme/onay aynı yetki sınırındadır. `npm run db:migrate` ile `019_catalog_import_fields.sql` uygulanmış olmalıdır. Dosya incelemesi ürün yayımlamaz, stok veya ülke uygunluğu oluşturmaz.

## Şablon ve gruplama

Yönetimde **Temel CSV/Excel** önceki yedi kolonlu dosyaları destekler. **Çoklu varyant CSV/Excel**, 38 desteklenen alanı taşır. Dört indirilebilir varlık `public/templates/product-import.csv`, `product-import.xlsx`, `product-import-extended.csv`, `product-import-extended.xlsx` altındadır. Hepsi yalnız başlık içerir; sahte ürün/üretici/barkod içermez.

- `productKey` boşsa her satır ayrı taslak ürün ve ayrı varyanttır; eski dosyanın davranışı korunur.
- Aynı, büyük/küçük harf duyarlı `productKey` bir ürün grubudur. Türkçe harfler kullanılabilir. Bu kod yeni dosyanın içindeki grubu tanımlar; mevcut ürüne varyant eklemez veya mevcut katalog kaydını güncellemez.
- Bir grupta birden fazla satır varsa her SKU için `variantName` ve `variantNameEn` zorunludur. Tek satırda da ad giriliyorsa iki dil birlikte verilmelidir; eksik İngilizce/Türkçe seçenek adı uydurulmaz. Bunlar seçenek adı olup ürün adından ayrıdır.
- Grubun ürün adı/çevirisi, kategori, malzeme, görsel, marka, üretici, menşe, tedarikçi, açıklama/bakım/uyarı ve garanti alanları bütün satırlarda aynı olmalıdır. Bir satırda boş, diğerinde dolu alan da çelişkidir. Sistem sessizce ilk satırı seçmez veya açıklamaları birleştirmez.
- SKU, barkod, beden/renk, ölçüler, fiyat/maliyet, pil/içerik ve belge referansı varyant başına değişebilir.

## Alanlar

| Alan | Kural |
|---|---|
| `sku` | Zorunlu; gerçek stok kodu, 1–80 ASCII harf/rakam/nokta/alt çizgi/tire; harf veya rakamla başlar. Dosya/DB'de harf duyarsız mükerrer kontrolü. |
| `name`, `nameEn` | Zorunlu; Türkçe/İngilizce ürün adı, 1–200 karakter. |
| `category` | Zorunlu; mevcut etkin kategori bağlantı adı; otomatik kategori oluşturulmaz. |
| `priceMinor` | Zorunlu TRY fiyatı, 0–9000000000000 arası tam sayı kuruş. |
| `material` | Zorunlu; beyan edilen gerçek malzeme, 1–200 karakter. Tıbbi/sertifika iddiası üretilmez. |
| `image` | İsteğe bağlı mevcut `/media/...` veya `/uploads/{uuid}.webp`; ağdan görsel indirilmez. Boş görsel taslakta kalır. |
| `productKey` | İsteğe bağlı grup kodu; 1–100 harf/rakam/nokta/alt çizgi/tire, Türkçe karakter destekli. |
| `variantName`, `variantNameEn` | Seçenek adları, 1–200 karakter; çok satırlı grupta ikisi zorunlu. Tek eski satırda varsayılan Standart / Standard. |
| `size`, `color` | Beden/renk, en fazla 100 karakter. |
| `weightGrams` | 0–10000000 arası tam sayı gram. |
| `packageDimensions` | Sadece `lengthCm`, `widthCm`, `heightCm` içeren JSON; her ölçü 0'dan büyük ve en fazla 10000 cm. Örnek biçim: `{"lengthCm":20,"widthCm":15,"heightCm":3}`. CSV içinde normal CSV tırnak kaçışı kullanılmalıdır. |
| `barcode` | Varsa gerçek barkod; 1–100 ASCII harf/rakam/nokta/alt çizgi/tire. Metin olarak korunur; baştaki sıfırlar kaybolmaz. Eksikse üretilmez; dosyada/DB'de tekrar reddedilir. |
| `brand` | Mevcut etkin markanın bağlantı adı; yeni marka veya sahte marka kaydı oluşturulmaz. Ürüne mevcut markanın adı yazılır. |
| `manufacturer`, `origin` | Dosyada açıkça beyan edilen üretici (en fazla 300 karakter) ve iki büyük harfli menşe ülke kodu. Sistem üretici bilgisi tahmin etmez veya tedarikçiden üretici çıkarmaz. |
| `supplierId` | Mevcut arşivlenmemiş tedarikçi kimliği; ürüne FK ile bağlanır. Tedarikçi stoğu alınmaz. |
| `costMinor` | Alış maliyeti, TRY kuruş olarak güvenli tam sayı; yoksa 0. Bilinmeyen maliyet kârlılık kanıtı değildir. |
| `priceEurMinor`, `priceUsdMinor`, `priceGbpMinor` | EUR/USD/GBP fiyat listesi, ilgili para biriminin alt biriminde aynı güvenli tam sayı sınırı. Boşsa fiyat oluşturulmaz; kur veya fiyat tahmin edilmez. |
| `description`, `descriptionEn` | TR/EN açıklamalar; hücre başına en fazla 2000 karakter. |
| `care`, `careEn`, `warnings`, `warningsEn` | TR/EN bakım ve uyarılar; en fazla 2000 karakter. İngilizce metinler çeviri alanında korunur. |
| `warranty` | Ürün düzeyinde beyan edilen garanti koşulları; attributes içinde tutulur. Garanti belgesi/onayı yerine geçmez. |
| `hygieneSealed`, `liquid` | Yalnız metin `true` veya `false`; Excel'de de metin hücresi kullanın. Hijyen/taşıma kabulü ayrı incelemedir. |
| `taxClass` | 1–100 karakter, boş değilse SKU vergi sınıfı. Yoksa açık ortak sınıf `*`. Özel sınıfta kural yoksa ödeme ortak sınıfa sessizce düşmez. |
| `batteryType`, `batteryCapacityMah` | Beyan edilen pil türü (100 karakter) ve varsa 1–1000000 arası tam sayı mAh. Taşıma belgesi/kabulü oluşturulmaz. |
| `ingredients`, `measurements` | Beyan edilen içerik ve varyant ölçüleri, en fazla 2000 karakter; sağlık/uygunluk iddiası türetilmez. |
| `documentRefs` | Var olan `product_documents` kimlikleri, `|` ile ayrılır; en fazla 20 benzersiz kimlik. URL, dış PDF veya yeni belge üretimi değildir. |

İsteğe bağlı alanın boş hücresi değer sağlamaz; hiçbir satırdaki bilinmeyen dolu kolon sessizce atılmaz. `stock`, tedarikçi stoğu, satış/yayın durumu, `lotTracking` ve `expiryRequired` bu importer'da desteklenmez; dolu değer satır hatasıdır. Lot takibi etkinleştirme/depo dengesi ayrı kontrollü operasyonla yapılır.

## Medya ve belge referansları

Bilinen `public/media` dosyaları güvenli kök ve gerçek dosya kontrolüyle okunur. `/uploads/...` için mevcut medya kaydı, WebP türü ve en az beş karakterlik kullanım hakkı referansı zorunludur. Yerel depoda nesne gerçekten var olmalı ve güvenli kök içinde kalmalıdır. S3 modunda yalnız daha önce kaydedilmiş özel nesne referansı kullanılır; URL ile ağdan dosya çekilmez. Medya hak kaynağı kaydı, lisansın hukuken doğrulandığı sertifikası değildir.

Belge belirli eski SKU/modelle ilişkiliyse yeni SKU aynı belge kapsamına otomatik girmez. İçe aktarma, `catalog_import_document_links` içinde yalnız **review_required** referans oluşturur. Kaynak belgeyi kopyalamaz, `reviewed=true` yapmaz, geçerlilik tarihini değiştirmez ve `product_eligibility` eklemez. Bu bağlantı inceleme girdisidir; SKU/model kapsamı ve ülke uygunluğu normal ürün belge sürecinde ayrıca doğrulanmalıdır. Bu sürümde importer ekranı belgeyi onaylayan bir işlem sunmaz.

## Önizleme ve onay

1. Dosyayı yükleyin; farklı başlıklar için alan → kaynak başlık eşlemesi yazın. Örnek: `{"sku":"Stok kodu","name":"Ürün adı","nameEn":"English name","category":"Kategori","priceMinor":"Fiyat kuruş","material":"Malzeme"}`.
2. Ürün/varyant sayılarını, her satırın grup/seçenek bilgisini ve **Aktarılacak bilgileri incele** bölümündeki bütün alanları okuyun. Hatalı dosyada kısmi kayıt yapılmaz. Satırlar 100 kayıtlık sayfalara ayrılır; önceki/sonraki düğmeleriyle bütün dosya incelenebilir. Hata ve toplamlar bütün dosyayı kapsar.
3. Hata varsa dosyayı düzeltip yeniden yükleyin. Yalnız aynı kişinin oluşturduğu, bir saatten eski olmayan ve hatasız önizleme onaylanabilir.
4. Onay tek transaction içinde ürünleri **draft**, varyantları ve açık fiyat listelerini oluşturur. Mevcut `main` depo için yalnız sıfır kullanılabilir/karantina/güvenlik payı bakiye satırı eklenir; böylece yeni SKU normal stok-giriş seçicisinde görünür. Fiziksel stok, mal kabul hareketi, lot, rezervasyon, yayın veya ülke uygunluğu oluşmaz. Ana depo yoksa önizleme kurulum hatası gösterir; yeni depo uydurulmaz. Normal mal kabulü ayrı yapılır.
5. Sonuç gerçek ürün ve varyant sayısını, batch ve audit kaydını verir. Aynı önizlemenin tekrar onayı ikinci ürün/varyant/batch oluşturmaz.

## Güvenlik ve sürümleme

Mevcut sınırlar korunmuştur: **2 MB dosya**, **1000 veri satırı**, **40 kolon**, **2000 karakter hücre**. Geniş şablon 38 kolondur; bu sınırı artırmaz. CSV UTF-8/BOM, virgül/noktalı virgül, tırnak kaçışı ve farklı satır sonlarını destekler. Formül önekleri (isteğe bağlı boşluk sonrası `= + - @`, tab/satır başı), geçersiz kontrol karakteri ve mükerrer başlıklar reddedilir. CSV çıktısında önekler apostrofla etkisizleştirilir.

XLSX MIME/ZIP imzası, 150 arşiv girdisi, 4 MB tek dosya, 16 MB toplam açılmış veri ve 100:1 oran sınırlarına tabidir. Gerçek açılmış baytlar ayrıca sayılır. Strict SAX önkontrolü DOCTYPE/XXE, formül, hyperlink/dış ilişki, işlem yönergesi, makro/gömülü içerik, symlink/yol kaçışı ve seyrek dev koordinatları ExcelJS yüklemesinden önce reddeder. Tek çalışma sayfasında yalnız metin/sayı hücreleri kabul edilir. Guardlar geniş alanlar için gevşetilmedi.

Önizleme **format_version=2**, kaynak ortam, aktör, normalize satırlar ve satır hatalarıyla saklanır. SHA-256 bu alanların tamamını kapsar; yalnız depodaki hata listesini temizlemek hatalı dosyayı onaylanabilir yapmaz. Ham dosya/istemci dosya adı saklanmaz. V1 veya bilinmeyen sürüm, farklı ortama taşınmış ya da değişmiş checksum'lu önizleme onaylanmaz; dosya yeni biçimle yeniden yüklenir. Eski yedi kolonlu dosyanın yeniden yüklenmesi desteklenir.

Onay `FOR UPDATE` ile önizlemeyi ve sınırlı süreli yazma kilidiyle varyant kataloğunu kilitler; SKU/barkod, kategori/marka/tedarikçi, belge/medya ve grup tutarlılığını tekrar doğrular. SQL parametrelidir; lock timeout 3 saniye, statement timeout 15 saniyedir. İşlemin bütünü başarısızsa tüm kayıtlar geri alınır. Üretim dışındaki yeni kayıtlar `fixture=true` kalır; ortam değiştirilerek production'a terfi edemez. Production, yerel atelier geliştirme illüstrasyonlarını reddeder.

XML/API tedarikçi fetch'i kapalıdır. Dosyadaki adres ağ erişimi yetkisi vermez. Uzak tedarikçi bağlantısı, SSRF izin listesi ve ürün inceleme akışı ayrıca tamamlanmadan gerçek entegrasyon sayılmaz.

## Sunucu sözleşmesi ve test kaydı

`previewImport(buffer,mime,filename,mapping,principal)` → `{previewId,rows,errors,valid,formatVersion,productCount,variantCount}`. `commitImport(previewId,principal)` → `{previewId,created,variants,alreadyCommitted}`; `created` ürün, `variants` varyant sayısıdır. `getImportTemplate(format='csv',mode='legacy')`; mode `extended` olabilir. `GET /api/admin/imports?format=xlsx&mode=extended`; POST multipart önizleme ve POST `{previewId}` onay aynı yetki sınırındadır.

Yeni testlerde önce desteklenmeyen grup/özel medya özellikleri için **3 RED**, mevcut 21 guard testi yeşil görüldü. DB testi eski 7 kontrolü geçtikten sonra eksik grup sayısı nedeniyle RED verdi. Hata listesinin bütünlüğü için ayrı regresyon da önce RED görüldü; checksum aktör/sürüm/ortam/satır/hataları kapsayacak şekilde düzeltildi. Sıfır bakiye satırının yokluğu ve tek dilde seçenek adı için de RED→GREEN gözlendi. Uygulama sonrası `npx vitest run tests/unit/imports.test.ts` **27/27**; `npx tsx --env-file=.env.local scripts/import-template-integration.ts` **14/14** geçti. Kapsam: eski güvenlik senaryoları, çoklu varyant/dört para listesi, Türkçe/gerçek XLSX, grup/çeviri çelişkisi, barkod ve referans hataları, format/ortam/hata bütünlüğü, ana depo/sıfır bakiye, mevcut belge kapsamının onaylanmaması ve gerçek geçici dosyayla özel medya hakkı kontrolü. DB kontrolleri benzersiz yerel `*_import_test` veritabanında yürütülür ve temizlenir.

Yeni `tests/e2e/imports.spec.ts`, resmi auth fixture + gerçek HTTP MFA ile CSV'yi arayüzden yükleyip bir ürün/iki varyant önizlemesini, gerçek taslak commit'ini ve sıfır stoklu SKU'nun stok API'sinde görünmesini doğruladı. Son kart düzenli hedef: `npx playwright test tests/e2e/imports.spec.ts --output=.local/imports-ui-final-cards --reporter=line` → **Chromium + WebKit 2/2, 23,7 saniye, retry 0**. 1440/390 ekran görüntüleri `docs/screenshots/import-preview-desktop.png`, `import-preview-mobile.png` ve WebKit eşleridir; iki ana görüntü açılıp incelendi. Yatay taşma yok; fiziksel cihaz testi değildir.

İlk UI koşusu eşzamanlı CMS JSX derleme hatası nedeniyle ekranı bulamadı; PASS sayılmadı. Daha sonra typecheck geçici dev tipleri/CMS/privacy sözleşme hatalarıyla durdu; bu başarısızlıklar gizlenmedi. Son kaynak durumunda ilgili altı dosya lint **0**, tam `npm run typecheck` **0**, `npm test` **16 dosya /114 test PASS** (11 Kasım 05:21). Son bütün E2E ve production build bu alt görevde çalıştırılmadı; kaynaklar dondurulduktan sonra ana doğrulama kaydında tamamlanır. Bu sürüm bütün e-ticaret kapsamının veya canlı satışın tamamlandığı beyanı değildir.

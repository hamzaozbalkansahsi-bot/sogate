# Beden/renk seçimi ve izin düğmesi

16 Kasım 2026. Kapsam yalnız PHP `/test` uygulaması; ana site ve korunmuş NODENO kaynak kopyası değiştirilmez.

## Davranış

Seçenekli üründe Sepete ekle, beden/renk penceresini açar. Hiçbir seçenek müşterinin yerine işaretlenmez. Gerekli seçimler tamamlanmadan ekleme yapılamaz. Gerçek kaynak varyant tablosu varsa yalnız aktif ve kayıtlı birleşimler kabul edilir. Kamu kaynağı bağımsız beden/renk alanları sunuyorsa bunlar bağımsız seçim olarak saklanır; bunlardan tedarikçi SKU’su, barkodu veya stok miktarı üretilmez.

Aynı ürünün farklı beden ve renkleri ayrı sepet anahtarları taşır. Aynı seçeneğe tekrar ekleme miktarı birleştirir; seçenek değiştirme yalnız ilgili satırı etkiler. Eski seçimsiz sepet, kullanıcıdan seçim bekleyen satır olarak görünür. Bu satırla sipariş özeti üretilemez. Sayfa yenileme, misafir sepeti ve hesap durumu seçimi korur. Favori/koleksiyondan toplu ekleme, her seçenekli ürünün seçimini sırayla bekler. Vazgeçilen ürün eklenmez ve işlem orada durur; daha önce onaylanan ürünler sepette kalır.

Sunucu istemcinin gönderdiği etiket, stok kodu veya fiyatı kabul etmez. İzin verilen seçenek kimliklerini ve birleşimi kendi kataloğuna karşı doğrular; sepet anahtarını yeniden hesaplar. Sipariş özeti `selectionSnapshot` içinde okunabilir beden/renk, mağaza ürün kodu ve varsa gerçek kaynak varyant/SKU referansını tutar. Sonraki katalog değişikliği bu kaydı değiştirmez. Yönetimde ödeme kaydının ürün satırında beden/renk açıkça gösterilir; ürün düzenleyicisinde “Sipariş için zorunlu seçenekler” okunabilir açıklaması bulunur.

`native-store/storefront/variants.php` sunucu doğrulamasıdır. `variants.js` tarayıcı sepet kurallarını, `variant-ui.js` erişilebilir seçim penceresini sağlar. `variant-apply.mjs` yalnız derlenen kopyaya kontrollü bağlantılar ekler. `variant-build.php` 2.194 ürünün yaklaşık 951 KB seçenek indeksini üretir; normal vitrin isteği için 30 MB özel kaynak çalışma dosyalarının taranması gerekmez. Yönetici beden/renk alanını değiştirdiğinde ilgili kaynak kaydıyla yeniden kontrol edilir.

Analiz izni penceresi ve gizlilik tercihleri dialogu `variant.css` ile krem/bordo kimliğe bağlanır. Birincil düğme `#5A0A20`, hover/aktif hali `#8E0F38`, yazı beyazdır. İkincil düğme açık zeminde bordo kalır; klavye odağı görünürdür. Beyaz metin kontrastı normal düğmede 14,01:1, hover yüzeyinde 9,23:1 ölçüldü; bu ölçüm tüm site için WCAG sertifikası değildir. İzin davranışı veya gerekli/isteğe bağlı izin ayrımı değiştirilmez.

## Veri ve doğrulama sınırı

Tam katalogda 1.173 ürün seçim gerektiriyor: 629 kaynak varyant matrisi, 544 bağımsız seçenek kaydı. Bir kaydın seçenekleri belirsiz olduğu için ekleme kapalıdır. Bu sayılar stok veya satışa uygunluk teyidi değildir. Aktif 468 katalog önizlemesinde seçim gerektiren 455 ürün vardır.

Gerçek tahsilat, ürün vergisi, tedarikçi sipariş API’si ve ülke kabulü bu değişiklikle açılmaz. `nodenoPaymentBegin` kalıcılık kontrolü yalnız izole SQLite testidir; Stripe çağrısı veya gerçek müşteri siparişi oluşturmaz. Liona bağımsız seçeneklerinde gerçek varyant SKU eşlemesi ayrıca bayi kaynağından doğrulanmalıdır. Seçenekler mevcut mağaza ürün fiyatıyla hesaplanır; ayrı beden/renk fiyat listesi veya fiziksel varyant stok defteri oluşturulmadı. Gerçek satış kabulü bu doğrulamaları da kapsar. Tarayıcı WebKit testi fiziksel iPhone testi değildir.

## Testler ve kanıt

Son paket `c4788429f85aec52b435c76e`, varlık `5f0a78ea46a0443b`; 480 paket kaydı / 70 JS modülü. ZIP SHA256: `f5b250a5985108b0c1649fd99fc13193bab0e9117920b9a1850b804f52961572`.

| Kontrol | Gerçek sonuç |
| --- | --- |
| `node --test scripts/test-native-public-read.mjs scripts/test-native-variants.mjs scripts/test-native-variant-artifact.mjs scripts/test-native-relocation.mjs` | 28/28 |
| `scripts/test-native-variants-php.php` · PHP SQLite uzantılarıyla | 23/23; tüm 2.194 kaynak şeması |
| `scripts/test-native-catalog-php.php` | 18/18 |
| `scripts/test-native-storefront-content.php` | 14/14 |
| `python scripts/test-native-installer.py` | 22/22; izole kurucu, zararlı ZIP reddi ve şifreli SQLite restore |
| `python scripts/test-native-public-read-browser.py` | Chromium/WebKit × yarım gövdeden kurtulma/iki süre aşımı = 4/4 |
| `python scripts/test-native-catalog-resilience.py` | Gerçek yerel vitrin, ilk bağlantı kesilir; iki motorda ikinci gerçek sorguyla katalog yüklenir |
| `python scripts/test-native-selection-admin.py` | İki motorda gerçek derlenmiş sipariş görünümünde XL/Siyah ve kaynak SKU, izole örnek |
| `python scripts/test-native-variants-browser.py` | Yerel ve uzak önizlemede iki motor × yedi bağımsız senaryo; 360/390/430/768/1440, İngilizce ve RTL |
| Genel yerel yayın dizisi | Yedi adım başarılı; tam yönetim 33 + müşteri 9 sayfa, katalog, arayüz, yaş, ilk HTML ve 11 dil |
| Genel uzak önizleme | Yedi adım başarılı; 11 bağımsız dil girişi ve aynı oturumda EN/DE/AR seçimi de geçti |

PHP komutlarında `.local/php-runtime/php.exe -d extension=pdo_sqlite -d extension=sqlite3` kullanılır. `scripts/test-native-core.py` korunmuş 34 test dosyasında 153 özgün kontrolü daha önce başarıyla çalıştırdı; aynı çekirdek manifest'i yeni derlemede 771 dosya / 768 aynı / mevcut üç güvenli fixture istisnasıyla doğrulandı. Bu eski çekirdek koşusu yeni sürümde tekrar çalıştırılmış gibi etiketlenmez.

Tüm normal kabul turlarında gerçek API cevapları kullanılır. Bağlantı kesme testi ayrı ve açıkça etiketli yerel hata enjeksiyonudur; başarı cevabı enjekte etmez. İzole sipariş görünümü testi veritabanı yazmaz; PHP ödeme kalıcılık testi yalnız izole SQLite kullanır, Stripe çağırmaz.

## Kullanım

1. Sepete ekle, gereken beden/renk penceresini açar. Başlangıçta seçim yoktur; tüm alanları seçmeden ekleme açılamaz.
2. Sepette seçenekleri değiştir bağlantısı yalnız ilgili satırı düzenler. Başka bir satırla aynı seçime dönüşürse miktar birleşir; 99 adet sınırı aşılmaz.
3. Eski seçimsiz sepet müşteri seçimi bekler; sistem müşterinin yerine beden seçmez.
4. Favori/koleksiyondan toplu ekleme her ürünü sırayla sorar. Vazgeçmek önce onaylananları kaldırmaz, kalan eklemeleri durdurur.
5. Yönetim ürün düzenleyicisinde “Sipariş için zorunlu seçenekler” okunabilir özeti vardır. Ödeme/sipariş kaydında seçim snapshot'ı gösterilir. Kaynak SKU bilinmiyorsa üretilmez; tedarikçi eşleme işi ayrıca tamamlanır.

## Yanıtsız katalog okuması

Uzak denemelerde aralıklı bağlantı sıfırlaması ve katalog/config beklemesi Chrome/WebKit'te görüldü. Bir doğrudan Python HTTPS ilk HTML okuması da 30 saniyeyi aştı. Kalıcı hosting veya ağ kök nedeni kanıtlanmadı. Eski sınırsız katalog okuması bağlantı yanıtsızken vitrini beklemede bırakabiliyordu.

`public-read.js` yalnız `/api/catalog` ve `/api/config` GET okumasını sınırlar: JSON gövdesi dahil her deneme en çok 20 saniye; ağ kopması/kendi süre aşımında tek tekrar. HTTP redleri ve geçersiz JSON tekrar edilmez. POST, ödeme ve harici adres kapsam dışıdır; fiyat, stok veya eski katalog cevabı üretilmez. Önce test RED verdi, uygulamadan sonra dokuz okuma testi geçti.

Uzak turlardaki başarısız denemeler PASS sayılmadı. Son c4788429 turunda bir WebKit favori sayfası DOM açılışı 60 saniyeyi aştı; kaynak değişmeden yeniden seçenek turu iki motorda tüm yedi senaryoyla geçti. Etkin sayfa hataları veya TLS/kritik istek kontrolleri filtrelenmedi. Senaryolar yeni tarayıcı bağlamında çalışır; gerçek yaş/gerekli çerez tercihi dışında kullanıcı durumu aktarılmaz. Üründen sepete gerçek vitrin bağlantısıyla geçilir; yenileme gerçek sayfa yenilemesidir.

WebKit'in belge değişimi sırasında iptal edilen sorguyu erişim hatası gibi sınıflandırabildiği [resmî kayıt](https://github.com/microsoft/playwright/issues/43120) incelendi; genel CORS hatası istisnası eklenmedi. Salt okunur [cPanel LVEInfo sorgusu](https://api.docs.cpanel.net/cpanel-api-2/cpanel-api-2-modules-lveinfo/cpanel-api-2-functions-lveinfo-getusage) kullanım sayacı yerine yardım metni döndürdü; CPU/bellek sınırı aşıldığı sonucu çıkarılmadı. Bu düzeltme uzak ağ sorununun kökünü çözmüş veya performans hedeflerini sağlamış sayılmaz.

## Yayın ve kaynak durumu

Son paket `https://sexogate.com/test` üzerinde etkin: `c4788429f85aec52b435c76e`. Sağlık kontrolü DB, 468 kamu ürünü / 2.194 kaynak kaydı ve tahsilatın kapalı olduğunu doğruladı; ana site aynı. Yerel/önizleme yedi kabul adımı yayın öncesinde geçti. Etkin adreste iki motor × yedi seçenek/izin senaryosu ve iki motorlu MFA/yönetim/blog dar kabulü geçti. Yeni sürümün şifreli DB yedeği yerelde 2 SQLite / 41 tablo / 10.114 satır ve geçerli yabancı anahtarlarla geri yüklendi; cron ve worker sağlıklı, diğer işler aynı. Medya restore testi bu kontrolün dışında.

Kaynak/test commit'leri `44c27e6`, `e107bc5`, `2d1ab4a`, `9a70120`, `7a49a08`, `36e93aa`, `83597d6`, `0d3a7e1`, `351883d`, `b40346d`, `f9f4528` normal push edildi. Son doğrulanan native CI `43781811340`, ana CI `43781811248`, GitHub hesap faturalama kilidi nedeniyle sıfır adımda durdu. Resmî API bildirimi doğrulandı; CI başarılı sayılmadı veya kapatılmadı.

Kanonik başarılı seçenek kanıtı `docs/native-variants-*-results.json`; görüntüler `docs/screenshots/native-store-variants-*/`. Etkin yayın kaydı `docs/native-deployment-report.json` ile `docs/progress.md` içinde tutulur. İlk testteki yanlış sağlık yolu ve yanlış odak/test seçicileri düzeltildi; çalıştırılmayan kontrol başarılı gösterilmedi.

İlk HTML testi 11 dilin ham sunucu cevabını doğrulamaya devam eder. JavaScript kapalı tarayıcı turunda bütün sayfanın genel `load` olayını beklemek yerine DOM, bütün stiller, fontlar ve dört kampanya görseli açıkça beklenir; 390/1440 boyut, 240 px altında kart yüksekliği, gerçek görsel ve yatay taşma şartları korunur. [Playwright gezinme dokümanı](https://playwright.dev/python/docs/navigations#when-is-the-page-loaded) incelendi. JavaScript kapalıyken rAF tabanlı bekleyicinin yerel zaman aşımı, Python tarafından DOM durumunu 30 saniye sınırıyla okuyarak düzeltildi. Son yerel ve uzak iki motorlu ilk HTML turu başarılı; gerçek HTTP/görsel doğrulaması kaldırılmadı.

Dil turunun başarısız misafir isteğinde hata kütüphanesi oturum başlıklarını özel araç çıktısına yazdı. `native_test_errors.py` Cookie/Set-Cookie/Authorization/CSRF başlıklarını sonraki hata çıktılarında maskeler; altı kontrol başarılı. Bu kayıt başlık değerlerini içermez. Testte yönetici girişi yoktu; tarayıcı bağlamı hata sonrası kapatıldı.

Dil testinin salt okunur meta GET'i için [resmî Playwright `max_retries`](https://playwright.dev/python/docs/api/class-apirequestcontext#api-request-context-get-option-max-retries) değeri 1 olarak kullanılır; yalnız `ECONNRESET` tekrar edilir, HTTP redleri tekrar edilmez. Başka turda yalnız isteğe bağlı `/api/exchange-rates` beklerken genel `networkidle` süresi doldu. Dil turu diğer kabul betikleriyle aynı `NativePageReadiness` bekleyicisine alındı: tüm kritik istekler ve görünür arayüz beklenir, tam kur ucu ayrıca gözlenir. Kritik isteği/yükleme durumunu yok saymadığını doğrulayan iki motorlu altı zamanlama fixture'ı geçti. Kur servisi başarılı sayılmaz; dil seçimi ve sunucu/istemci metaveri şartları korunur. Son yöntemle yerelde ve önizlemede 11 bağımsız dil girişi ve aynı oturumda EN/DE/AR gerçek seçimleri ilk denemede geçti. Tam bir 11-dil sert gezinti stres koşusu başarılı sayılmaz.

Son dil kontrolü her dili bağımsız tarayıcı bağlamında açar; gerçek dil değiştirme akışını ayrıca aynı oturumda doğrular. Her vaka sonrası sürüm, kaynak SHA256 ve tamamlanan adım kaydedilir. `--retry-failed` yalnız aynı URL/sürüm/betik kaynağında başarısız adımları tekrarlar; test yapılmamış satır üretmez. Yayın kapısı 11 girişin yanında üç istemci geçişini, kaynak hash'ini ve `finalized` sonucunu zorunlu tutar. Ürün sayısı aynı veritabanından hesaplanan küçük `/api/deployment-status` yanıtından taze okunur. Katalog denemesinin iki 20 saniyelik sınırına 5 saniye arayüz payı eklenerek dil bekleme bütçesi 45 saniyeye bağlandı; başarısız katalog arayüzü ayrıca reddedilir.

Etkin adresin ilk WebKit turunda kapalı ödeme durum okuması 60 saniyede bitmedi. Aynı değişmez sürümde ikinci tam iki motor turu bütün yedi senaryoyla geçti; önceki ağ hatası kayıtta tutulur. Etkin yönetim/blog dar turu her motorda 1 yönetim + 1 kamu sayfası ve MFA/güvenli çerez/5 genişlik içerir; önizlemedeki tam 33+9 gezintinin yerine sunulmaz.

`python scripts/test-native-language-checkpoint.py`: izole kanıt örneğinden yalnız eksik DE vakası gerçek yerel tarayıcıda tekrar çalıştı; kaynak hash değişikliği reddedildi, asıl dağıtım kanıtı değişmedi. Bu fixture üretim verisi veya ek 11-dil koşusu değildir. Ağ kök nedeni ve uzun ardışık sert gezinme yükü açık sınırlamadır; bağımsız girişler ve gerçek SPA dil seçimi kabulü ayrı kaydedilir.

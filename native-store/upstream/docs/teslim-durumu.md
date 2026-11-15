# Yönetim ve SEO teslim durumu

## 11 Kasım 2026 — mobil kartlar, dil/para birimi ve harita geçişi

Mobil hızlı inceleme katmanı kaldırıldı; ürün görseli ve başlığı ürün sayfasını açmaya devam eder. Yatay ürün sıralarında iki tam kart gösterilir. Para birimi üst menüde dil seçiminin yanındadır; 320 px Safari, 390 px mobil ve 1440 px masaüstü yerleşimleri doğrulandı. Dil değişimi varsayılan para birimini yeniler; ardından elle para birimi seçilebilir ve bu tercih yenilemede korunur. Eski Türkçe/KZT kaydı artık başlangıç dilini farklı bir para birimine kilitlemez. Ayrı önbellek sorgularıyla yüklenen döviz modülü durumları birleştirildi; seçim ve ürün fiyatları aynı para birimini kullanır.

Haritada üzerine gelme yalnız önizleme yapar; ülke veya ülke listesi tıklaması ve klavyede Enter/Space dil/para birimi seçimini uygular. TR/TRY, EN/EUR, RU/KZT geçişleri canlıda doğrulandı. Mevcut dil kapsamı TR/EN/RU/AR'dır; ek ülke dilleri için İngilizce, TCMB kapsamı dışındaki yerel para birimleri için USD kullanılır. Gerçek teslimat adresi ve sunucu ülke doğrulaması bu tercihlerden ayrıdır. [Tercih kuralları ve kullanım](visitor-market.md).

364 Node ve 215 Python testi sıfır hata/atlamayla geçti. Üretim derlemesi, katalog doğrulaması ve PHP paketi başarılıdır. Dört yerel ve dört canlı Chromium/WebKit senaryosu eski kayıt geçişini, dört dili, elle değişikliği, yenilemede korunmasını, harita geçişini, fiyat formatı ile seçicinin eşleşmesini ve yatay taşmayı kontrol etti. Dört alan adında yeni sürüm, medya bütünlüğü ve açık canlı ödeme doğrulandı. Fiyat verileri, katalog, özel medya, hesap/sipariş verisi ve ödeme ayarları korundu; gerçek tahsilat oluşturulmadı.

Güncel canlı sürüm `689f6e49f504c40493898e96d5a138e18ef030b2fd0bfe26e9decbb21708288d`; yedek `/home/nodenoho/nodeno-backups/20261111T094612Z-mobile-market-c214758d`. Kanıt ve ekranlar `artifacts/mobile-market-20261111`, birleşik sonuç `acceptance.json`. Fiziksel telefon testi yapılmadı.

## 11 Kasım 2026 — paketleme hataları, kapak vitrini ve görsel boşlukları

Önceki teslimlerde açık kalan üç tedarikçi/cPanel paketleme kontrolü düzeltildi. Eski mobilya test görselleri kullanılan katalogda yeni tedarikçi kayıtlarının açıklama ve onay dosyaları artık eksiksiz bulunur; gerçek onaylı rasterler hashleriyle paketlenir. Test paketleri `testOnly` kalır ve yayınlanamaz. Üretim doğrulayıcısı tüm katalog ailelerini gerçek kaynaklarına göre yeniden kurar; fiyat, birim, kimlik ve görsel farklılıklarını reddeder. Onaylı tek fotoğrafsız kayıt korunur. [İşletim ayrıntıları](supplier-publication-2026-11-10.md).

Ana sayfanın dolap kapağı vitrini “Kapaklarla evinizin görünümünü baştan sona yenileyin.” başlığını kullanır; İngilizce, Rusça ve Arapça karşılıkları tamamlandı. Kategori seçimi doğrudan dolap kapaklarına bağlıdır. Tüm ortak ürün kartlarında görsellerin etrafına mobilde en az 16 px üst/alt ve 12 px yan boşluk eklendi; geniş ekranda boşluk artar. Görseller `contain` ile tam gösterilir; hover büyümesi de çerçevenin içinde kalır. Kategori ve yaşam alanı fotoğrafları aynı kaldı.

361 Node ve 215 Python testi sıfır hata ve sıfır atlamayla geçti. Üretim derlemesi, tam katalog doğrulaması ve üretim PHP paketi başarılıdır. Gerçek PHP/HTTPS ile yerelde dört tarayıcı senaryosu; canlıda dört alan adı ve ayrıca dört dilde Chromium/WebKit masaüstü/mobil senaryoları geçti. Görünür görseller yüklenip boyandıktan sonra masaüstü ve Arapça mobil ekranları görsel olarak incelendi. Fiziksel telefon testi yapılmadı. İlk yerel WebKit denemesinde HTTP üzerinden Secure çerez gönderilmediği için test düzeneği HTTPS'e taşındı; uygulamanın CSRF veya çerez güvenliği gevşetilmedi.

Güncel canlı sürüm `d95c345cb80f8d4bd2abcc11639d2b175b28e98390ad4c43cf2d5e8405c9fd24`; tabanı Search Console sürümü `5bd99cc8404e2390d7268336f6826c1129bdc89124edbc8db9916feda5cc5d3c`. Yalnız kök HTML, uygulama, dört dil metinleri ve ortak stil değişti. Katalog, medya, fiyatlar, SEO yapılandırması, ödeme kodu ve yasal belge dosyaları tabanla bayt düzeyinde aynı kaldı. Kalıcı hesap/sipariş verisi, Stripe ayarları ve özel medya kasası korunur. Dört alan adında ödeme açık, gerçek modda; satış/iade sürümü `2026-11-10.3`. Gerçek kart tahsilatı veya test müşteri/sipariş kaydı oluşturulmadı.

Yedek `/home/nodenoho/nodeno-backups/20261111T084259Z-packaging-2e76d3ff`. Kanıtlar ve ekran görüntüleri `artifacts/packaging-fix-20261111`; birleşik kabul `acceptance.json`. Aşağıdaki önceki tarihli test/sürüm kayıtları tarihsel kayıttır; orada açık görünen paketleme hataları bu teslimle kapanmıştır. Önceki bölümde belirtilen resmî vergi/kayıt ve işletme bağımlılıkları bu teknik yayınla tamamlanmış sayılmaz.

## 10 Kasım 2026 — belge merkezi, aydınlatma ve sözleşme arşivi

Belge merkezi https://nodenohome.com/legal?lang=tr adresinde yayında. Ön bilgilendirme, mesafeli satış, iptal/cayma/iade, satıcı, KVKK, gizlilik, çerezler, üyelik, veri başvurusu ve uluslararası teklif koşulları dört dilde sunulur. İndirme/yazdırma, ilgili form bağlantıları ve tercihler eklendi. Satış/iade sürümü `2026-11-10.3`, ödeme ayarı sürümü 5; canlı tahsilat açık ve anahtarlar korunur. Yardım ekranlarındaki eski kapalı ödeme ve misafir verisi açıklamaları aynı politikalarla uyumlandırıldı.

Üyelik kabulü tam metin/dil/sürüm/özet/zaman kaydıyla atomiktir. Sipariş sözleşmesi gerçek ürün, ölçü/yön/aksesuar, adres, net/KDV/toplam ve koşullarla şifreli/değişmez arşivlenir. Testte başka misafir oturumu 403 aldı; gerçek Stripe test ödemesinden önce indirilen kopya ödeme sonrası değişmedi. Eski açık ödeme ekranı yeni belge akışını göndermediğinde sipariş/Stripe oturumu oluşturulmadan reddedilir. İzin olmadan otomatik arama/ürün geçmişi kalıcı tutulmaz; ret temizler. İzin/ret 90 gündür.

44 yerel belge sayfası, 40 canlı belge, dört alan adı ve dört canlı tarayıcı dili geçti. 46 ilgili kontrol, 5 çeviri/kısa metin kontrolü ve 207 Python testi başarılıdır. Genel kaynak Node kontrolü 342/345: ayrı tedarikçi çalışmasının onaysız kaynak rasterlerini reddeden üç cPanel paketleme kontrolü açık kalır; kapı atlanmadı. Bu yayın onaylı canlı katalog ve medya üzerinden yalnız belge/ödeme/aydınlatma farklarını taşır. Gerçek tahsilat veya canlı test kullanıcı/siparişi oluşturulmadı.

İlk yayın denemesi son inceleme sırasında durdurulduğunda dosya tutarsızlığı ve geçici bütünlük hatası oluştu; önceki sürüm ve aynı işin kilidi güvenle geri yüklendi. Sonraki yayın, kaynak kontrolleri ve canlı kabul başarılıdır. Güncel sürüm `02de01d5d5101c9c61332360bec16c3c5814a7e4d1f012a463f703817187838d`; son yedek `/home/nodenoho/nodeno-backups/20261110T201324Z-legal-a696db35`. Kanıt `artifacts/legal-20261110/acceptance.json`.

Bu teslim resmî kayıt, imza veya tam mevzuat uygunluk sertifikası değildir. PTYS Türkiye mükellefiyet/fatura/kayıt yolu, KVKK temsilcisi/VERBİS, gerçek aktarım güvenceleri ve gerekiyorsa ETBİS/İYS işletme işlemi bekliyor. Garanti/kullanım belgeleri için gerçek üretici evrakı gerekir; düzenlenmemiş şablon müşteri garantisi sayılmaz. Otomatik işlem e-postası bağlı değil; `served_at` dosyanın sunulduğunu, gerçekten saklandığını değil, gösterir. [Kullanım](legal-documents.md) ve [açık resmî işler](legal/compliance-register.md).


## 10 Kasım 2026 — gerçek Stripe test ortamı ve iade takibi

Stripe'ın canlı hesaptan ayrı geçici test ortamında beş senaryo geçti: başarılı kart, reddedilen kart, 3D Secure onayı, başarısız 3D Secure ve kısmi/tam iade. Gerçek barındırılan Checkout ve gerçek imzalı bildirimler, yayımlanan PHP kodunun yalıtılmış test deposuyla denendi. `rkcs_test_` anahtar desteği ve iade durumunun siparişe yansıması düzeltildi. Bekleyen/başarısız iade para iade edilmiş sayılmaz; tekrar veya gecikmiş bildirimler tutarı iki kez işlemez.

Canlı sürüm `737a01736b06e834e3f7c941e35bdb554c442efccb108a8f11c10ffd511b50e4`; birleştirme tabanı tedarikçi sürümü `91a7b8d93324f485d2fb3cd0b01e0e71523b261477db4a8a8e27eceb72a24d70`. Katalog ve medya baytları korunarak yalnız ödeme düzeltmeleri yayımlandı. 5.129 görselin güncel kaynak/çıktı hashleri doğrulandı. Canlı webhook'a `refund.created`, `refund.updated`, `refund.failed` eklendi; mevcut dört ödeme olayı ve imza anahtarı korundu. İade Stripe panelinde yetkili kişi tarafından başlatılır; mağazada otomatik para iadesi açılmadı.

Dört alan adında canlı ödeme, belge sürümü/özeti, TRY ve taşıma koşulu aynı kaldı; değişen modüller yayımlanan dosyalarla birebir eşleşti. Masaüstü/mobil üç canlı tarayıcı senaryosu ve dört dilde test iade ekranları geçti. 32 ödeme kontrolü ve 195 Python testi başarılıdır. Genel Node kontrolü 317/320: üç paketleme testi eski Worker varlığı nedeniyle başarısız; bağımsız tedarikçi çalışmasındaki onaylı `supplier-storefront.json` eksikliği kaynak üretim derlemesini durduruyor. Bu kapı atlanmadı; ödeme yayını zaten canlı ve doğrulanmış paket üzerinden hazırlandı. Genel kaynak derlemesi başarılı diye raporlanmaz.

Gerçek karttan çekim yapılmadı; test siparişleri ve test anahtarları canlı mağazaya aktarılmadı. Test süreçleri kapatıldı ve açık metin anahtar sızıntısı denetimi geçti. Yedek `/home/nodenoho/nodeno-backups/20261110T190155Z-stripe-refunds-221feb01`. Kanıtlar `artifacts/stripe-sandbox-20261110/acceptance.json`; kullanım [Stripe kılavuzunda](stripe-checkout.md#kısmi-ve-tam-iade-takibi).

## 10 Kasım 2026 — sahibi talimatıyla canlı kart tahsilatı açık

Firma sahibinin ABD'den PTYS faturası ve Türkiye'den teslimat kararıyla canlı kart tahsilatı etkinleştirildi. `.com`, `.com.tr` ve iki `www` alan adında `/api/payments/status.enabled=true`, canlı ortam ve `/api/config.checkoutEnabled=true` ayrı ayrı doğrulandı. Ayar sürümü 4; dört dildeki yayımlanan satış/iade sürümü `2026-11-10.2`. Kayıt ve kaynak metin özetleri eşleşir. İade adresi No:100/C'dir.

Önceki %10 mobilya, %20 kapı/kapak KDV hesabı ve alıcı ödemeli ilk taşıma kuralı korunur. ABD faturası gerekçesiyle KDV sıfırlanmadı. İşletme onayının kaynağı açık sahibi talimatıdır; resmî vergi tescili doğrulanmış gibi kaydedilmedi (`governmentTaxRegistrationVerified=false`). Fatura otomasyonu bağlı değildir; PTYS faturası ayrıca düzenlenir. Mevcut anahtarlar, imzalı webhook ve kalıcı veriler korundu. İlk gerçek tahsilat testi yapılmadı; kontroller karttan çekim veya sipariş oluşturmadı.

314 Node ve 194 Python testi geçti. Ortak çalışma ağacındaki yeni özel `supplier-products.php` paketi için eskimiş paket parmak izi beklentisi güncellendi; bu ödeme ayarı işlemi bir katalog/arayüz sürümü yayımlamadı. Geçici zamanlayıcı ve kurulum dosyası kaldırıldı. Canlı kabul: `artifacts/stripe-checkout-20261110/activation-live-acceptance.json`.

## 10 Kasım 2026 — satış ve iade taslakları yönetimde

`2026-11-10.1-draft` sürümü Türkçe, İngilizce, Rusça ve Arapça olarak canlı özel ödeme ayarlarına kaydedildi. Ön bilgilendirme/mesafeli satış koşulları, iptal-cayma-iade hükümleri ve isteğe bağlı cayma formu hazırdır. Firma sahibinin son teyidiyle iade adresi **Zafer Mah. Turgut Özal Cad. No:100/C, Buca/İzmir** olarak işlendi. Bu, 36/C depo adresini vergi/işyeri kaydı olarak değiştiren bir işlem değildir.

Kaynak ve sunucudaki sekiz metnin özeti birebir eşleşti. Canlı Stripe anahtarları ve hesap/webhook doğrulaması korundu; vergi onayı verilmedi ve tahsilat açılmadı. Dört alan adında taslak metinlerin halka açılmadığı ve canlı ortamda ödemenin kapalı kaldığı doğrulandı. 311 Node ve 190 Python testi geçti. Geçici kurulum dosyası ve zamanlayıcısı kaldırıldı. Kabul: `artifacts/stripe-checkout-20261110/sale-documents/acceptance.json`.

Vergi/fatura tarafındaki somut eksikler, gerçek satıcı/tedarik zinciri ve KolayBi veya uygun manuel fatura yolu [PTYS Türkiye fatura hazırlığında](ptys-turkiye-fatura-hazirlik.txt) açıklanmıştır; mali müşavire gönderilebilecek metin de hazırdır ve henüz gönderilmemiştir. Müşteri tahsilatı için bu bilgiler, son belge sürümü, kalıcı belge teslimi ve ödeme alınan sağlayıcı senaryoları tamamlanmalıdır.

## 10 Kasım 2026 — gerçek Stripe bağlantısı

Güncel canlı sürüm `32af0a885e447b77f0c800caaae1348a0e7365377270b222515163e24964bba2`. PTYS canlı hesabına sınırlı NODENO anahtarı ve imzalı webhook bağlandı; anahtarlar özel depoda şifrelidir. Dört alan adı aynı bağlantıyı kullanır. Gerçek TRY Checkout isteği oluşturulup hemen sona erdirildi; iki canlı bildirim HTTP 200 ile kabul edildi. Karttan ücret çekilmedi, mağazada sipariş oluşturulmadı. API sürümünün kart filtresi ve boolean kodlaması düzeltildi; kamusal varlıklar ve kalıcı müşteri verileri korunur.

**Müşteri tahsilatı kapalıdır:** PTYS'nin Türkiye satışlarında vergi/fatura düzeni, dört dilde satış/iade belgeleri ve ödeme alınan sağlayıcı senaryoları tamamlanmalıdır. Yönetici parolası mevcut sahip hesabı ve MFA korunarak kurtarıldı. Geçici bakım zamanlayıcısı ve düz metin kurulum dosyaları temizlendi. Güncel yerel derlemeden sonra 308 Node ve 185 Python testi geçti. Bağlantı kabulü: `artifacts/stripe-checkout-20261110/connection-final-verification.json`. [Ödeme kılavuzu](stripe-checkout.md).

## 10 Kasım 2026 — çoklu ölçü ve sipariş demosu yayını

Güncel canlı sürüm `fe19435ab04d6a56911daecc7b6ea69b2f5d99bedd718c8db258f393614d3874`; birleştirme tabanı `f2ece0ebe194b0fc997ff9a5db256605b948d18bf29694200f7f0b3f90c72109`. Kapak ve kapıda her satır kendi ölçü, adet ve uygulama seçimini taşır. Kapakta kapak/camlı kapak/çekmece klapası/boy kapak; kapıda 2070 mm örnek yükseklik, 770/870 mm kanat eni ve 95/115/145/165/185/215 mm kasa seçilir. Camlı seçimler ölçü alanlarından sonra, o kapı modelinin gerçek katalog referansıyla alınır. Sahibin 170 mm düzeltmesine göre 95/115/145/165 mm için fark yok; 185 mm +300 TL, 215 mm +455 TL. Eski cm tabanlı sepet seçenekleri okunur; yeni mm bilgisiyle çelişen değer reddedilir.

Tüm satırlar doğrulanıp tek işlemde sepete eklenir. Hata, miktar veya sepet sınırında kısmi ekleme yapılmaz. Aynı ölçü/uygulama birleşir; fiyat birleşmiş satır üzerinde bir kez yuvarlanır. Farklı ölçü, parça tipi ve cam modeli ayrı kalır. Liste toplamı ve mobil sabit fiyat birlikte güncellenir. Fiyatı kesinleşmeyen cam veya özel uygulama için teklif kuralı korunur.

İki ürün grubunun “Sipariş örneğini izle” düğmesi oynat/duraklat, ileri/geri ve kapatma kontrollü dört adımlı demo açar. Demo sepeti veya taslağı değiştirmez. “Örneği formda kullan” yalnız formu doldurur; sipariş veya talep oluşturmaz. Hareket azaltma, Escape, Safari dokunması sonrası odak geri dönüşü ve camlı sayfada yüzey değişiminden sonra fiyatların yenilenmesi denetlendi.

Başka sohbette yayımlanan tedarikçi, para birimi ve sepet hizalama çalışmaları son taban üzerinden korundu. `renderCheckout` fonksiyonu tabanla bayt düzeyinde aynıdır; canlı para birimi/adres/hizalama senaryosu ayrıca geçti. Orijinal kaynak belgeler, 1.021 SKU, banka/kur işi ve kalıcı hesap verisi korunur. Müşteri açıklamalarında 170 mm koşulu dört dilde güncellendi; kaynak PDF/manifest değiştirilmedi.

285 ilgili Node, 7 PHP ticaret, 3 PHP kur, 5 Python kur, 18 yayın ve 3 yayın kilidi testi geçti. Ayrı ve henüz bulunmayan ödeme modülüne ait 7 test bu arayüzün kapsamından ayrı kaydedildi; tahsilat bu yayınla açılmadı. Gerçek PHP ile yerelde 12 ve canlıda ayrıca 12 Chromium/WebKit masaüstü/mobil dil senaryosu geçti. Fiziksel telefon testi yapılmadı. 5.129 medya referansının tam denetimi ve son kaynak/çıktı hashleri doğrulandı; 375 yeni katalog görseli aynı kaldı. Yeni raster üretilmedi veya değiştirilmedi.

Yedek: `/home/nodenoho/nodeno-backups/20261110T145917Z-measurements-ec194c92`. Kanıt: `artifacts/measurement-orders/final-acceptance.json`. [Kullanım ve demo adımları](kapi-ve-kapak-ticareti.md).


## 10 Kasım 2026 — kapılar, lake/PVC kapaklar ve ölçülü teklif

Önceki canlı sürüm `f496d09e6c7d446044f7fd011203993fb90c3a234a53eb51230507b48f53dfb1`. 667 mevcut mobilya kaydı korunarak 95 kapı/profil ve 259 kapak/tamamlayıcı seçeneği eklendi; toplam 1.021 SKU var. Yeni kaynaklara ait 375 görsel, belge ve çıktı hashleriyle doğrulandı. Kaynak kataloglar değiştirilmedi. GK/GB/GT/GM önekleri ND oldu; kapak ile aynı numaralı tamamlayıcı parçalar ayrı model grubunda tutulur.

Kapı minimumu Türkiye'de 5, yurt dışında 10 takım. Doğrulanmış lake/PVC kapaklarda toplam alan Türkiye'de 5 m², yurt dışında 10 m². En/boy milimetre ve adetle girilir; farklı ölçüler ayrı sepet satırıdır. Gerçek teslimat ülkesi minimumu yeniden belirler. 171 yeni seçenek kaynak PDF'deki kesin bedelle fiyatlandı; 183 belirsiz fiyat seçeneği tahmin edilmeden teklif üzerinden sunulur. KDV, nakliye ve özel üretim kapsamı teklifte kesinleşir.

Dövizde pazartesi başlayan haftanın o ana kadarki en yüksek TCMB döviz satış kuru kullanılır. Turhost'taki özel Python cron işi resmî kaynağı doğrulanmış HTTPS ile beş dakikada bir yeniler; geçici taşıma hatalarında en fazla üç, 20 saniyelik deneme yapar. Yeni kod, sunucuda zorlanmış gerçek yenilemeyle doğrulandı; geçici kontrol cron'u kaldırıldı. PTYS Technologies LLC üst kuruluş ilişkisi eklendi. Banka/Stripe diğer sohbette kurulacağı için tahsilat kapalıdır.

270 Node, 3 PHP kur, 5 PHP proje ticareti, 5 Python kur, 18 yayın, 3 yayın kilidi ve 4 paketleyici testi geçti. Yerelde 12 ana + 2 ek; canlıda ayrıca 12 ana + 2 ek Chromium/WebKit senaryosu geçti. Türkçe, İngilizce, Rusça, Arapça/RTL; masaüstü ve mobil genişlikler denetlendi. Fiziksel telefon testi yapılmadı. Dört alan adında HTTPS/sağlık, gerçek görsel örnekleri, sunucu fiyatları, sitemap ve özel dosya sınırları doğrulandı. Mevcut 5.129 medya referansının tam piksel/yayın denetimi ilk proje yayınında geçti; son model grubu düzeltmesinde bütün medya ve kamusal dosya baytlarının aynı kaldığı yeniden doğrulandı. Kullanıcı verisi ve görsel kasası korunur.

Kabul kaydı: `artifacts/project-commerce/final-acceptance.json`. Kullanım ve ödeme entegrasyonu sözleşmesi: [Kapı ve kapak ticareti](kapi-ve-kapak-ticareti.md). Kapaklar: https://nodenohome.com/?page=catalog&category=dolap-kapaklari&lang=tr — Kapılar: https://nodenohome.com/?page=catalog&category=kapilar&lang=tr


## 3 Kasım 2026 — ülke seçimi ve karşılama tercihi

Önceki canlı sürüm `f72d422fc4c4b9b99e448374a840ac560c58381b5c45ab52cca27cec17828a5a`. Haritadaki her ülke ayrı seçilir: sınır şekli %9 büyür, lime yeşile döner, ülke adı açılır ve diğerleri soluklaşır. Gerçek seçim sınırları sabittir. Mobilde harita/ülke listesine dokunma, klavyede ok tuşları ve hareket azaltma desteklenir. Dört dil ve Arapça RTL korunur.

Poster yeni uygun sayfa yüklenişlerinde tekrar açılır; yalnız ziyaretçinin **Bir daha gösterme** seçimi aynı tarayıcıda sonraki açılışları engeller. Önceki otomatik görüldü kaydı yok sayılır. Tercih IP veya Wi-Fi ağına göre paylaşılmaz. Çarpı, Escape ve 30 saniye kapanma korunur. [Güncel davranış ve kullanım](welcome-poster.md).

Katalog, hesap kodu, kalıcı kullanıcı verisi ve medya sürümü korunan yedi dosyalık arayüz katmanı yayımlandı. Bütün medya denetimi ve standart yedek/kilit/geri alma/sağlık adımları geçti. Yedek `/home/nodenoho/nodeno-backups/20261103T141859Z-f72d422fc4c4-a68a72`. Özellik/komşu testleri 11/11, yayın testleri 21/21; gerçek PHP yerel kabulünde dört dil ve Chromium/Windows WebKit ile 16 görünüm geçti. Dört alan adında 32 gerçek HTTPS kontrolü ve iç tarayıcıda ülke seçimi doğrulandı. Ayrı canlı tarayıcı kabulündeki 16 görünüm, ülke vurgusu ve gerçek 30 saniye kapanma kontrolleri de geçti. Sonuçlar `artifacts/welcome-poster-v2/` altında tutulur. Fiziksel telefon testi yapılmadı.

## 3 Kasım 2026 — önceki uluslararası karşılama posteri

Önceki sürüm `c828f61dd4d92e909ea1cd1f4d1ec0604e2c81f47a7a981fa7efefbd8e11236d`. Onaylanan on ülke, İzmir merkezli harita, NODENO logosu/fontu/sloganı ve dört dil içeren karşılama posteri eklendi. Bu tarihsel sürümde otomatik tek gösterim ve haritanın bütününe uygulanan fare efekti vardı; yukarıdaki revizyon bu iki davranışı değiştirdi. Sağ üst çarpı ve 30 saniye kapanma yeni sürümde korunur.

Bu yayın, aşağıdaki doğrulanmış canlı sürüme yalnız karşılama arayüzünü ekleyen altı dosyalık bir katmandır. Katalog ve hesap kodu baytları, kampanya/kullanıcı deposu ve mevcut medya sürümü korunur. Standart yayın aracının tam görsel onay denetimi, yedek, yayın kilidi ve HTTPS sağlık kontrolü geçti. Dört alan adında 24 gerçek HTTPS dosya/HTML/sağlık doğrulaması ve iç tarayıcıda gerçek poster görünümü doğrulandı. Yerelde ve canlıda ayrı ayrı Chromium/Windows WebKit üzerinde dört dil ve 1440/390/320 genişliklerini kapsayan 16 görünüm; 30 saniye kapanma, çarpı/Escape, tekrar gizleme, klavye odağı ve fare/hareket azaltma kontrolleri geçti. Canlı süre kontrolünde gerçek 30 saniye kullanıldı. Ayrı canlı tarayıcı kabulü `artifacts/welcome-poster/live-acceptance.json` dosyasında tutulur; fiziksel telefon testi yapılmadı.

## 3 Kasım 2026 — yönetim, kampanya ve görsel teslimi

Önceki canlı sürüm `f08acdc8a42747af23ba302e9aa98b50a5174e84fdc92f99caadde8be4ffa248`. Yönetim menüsü arama ve günlük işlem bağlantılarıyla sadeleştirildi. Kampanyalarda fotoğraflı ürün seçimi, gerçek fiyat önizlemesi, açık taslak/yayın durumları ve tek işlemde **Kaydet ve yayınla** var. Parola göz düğmesi giriş, kurulum, davet ve yeniden doğrulama formlarında çalışır. [Güncel kullanım adımları](yonetim-kilavuzu.md).

Kullanıcının kayıtlı **Kasım_Kampanyası**, ürün `2395` için %25 oranla yayındadır; fiyat **₺7.559,21**. Önceden taslakta kaldığı doğrulandı. Başlık, ürün, oran ve tarihler korunarak mevcut yayın API’si üzerinden yayınlandı. Gerçek fiyat dört alan adında API/HTML ve dört dilde tarayıcıyla doğrulandı. İlk sahip hesabı kullanıcı tarafından tamamlanmıştır; kurulum kodu yeniden kullanılmaz.

Güncel 5.129 görsel referansında 570 temizlenmiş çıktı vardır. Kullanıcının Mira 708 örneği dahil marka etiketi/magnetinin gövdesi ve çevresi için dar, kaynak piksellerini koruyan onarımlar uygulandı. 519 değişen dosya için eski/yeni URL’lerde dört alan adından 4.152 gerçek HTTPS yanıtı ve 102 masaüstü/mobil galeri görünümü doğrulandı. Kaynak arşivi korundu. Bilinmeyen her görsel kusurunun otomatik yakalanacağı garantisi verilmez; kabul, kayıtlı tarama ve gerçekten incelenen görüntülere bağlıdır.

En son eşitlenmiş **168 sayfalık tam katalog** güncellendi: `output/pdf/NODENO_Mobilya_Katalogu_2026_Tam_Katalog.pdf`, SHA-256 `981a08f6b6f87c0fd618a46c1a223089f851517a776bd1a6093f583668d94bb0`. 709 kayıt, metin, ölçü, bağlantı ve sayfa özellikleri korundu; 200 yerel görsel nesnesi düzeltildi. Dört köken/kimlik metadata dosyası aynı doğrulanan işlemle güncellendi. Eski tam PDF ve 86 sayfalık paylaşım kaynağı korundu.

255 Node ve 151 Python testi geçti; ayrıca gerçek PHP/SQLite kampanya ve bakım temizliği testleri, birleşik yayın/geri alma senaryosu ve yerel yönetim tarayıcı kontrolleri geçti. Canlı yönetim girişinde dört kullanılabilir görünüm incelendi; giriş gönderilmedi. Kampanya yayınını doğrulayan özel geçici bakım görevi kaldırıldı. Tek bağımsız son inceleme onayı ve ayrıntılı kanıt: `artifacts/media-object-removal-20261102/final-acceptance.json`.

## Önceki teslim kayıtları

Çalışma dalı `codex/control-seo`; başlangıç `853aed8`, yayımlanan uygulama kaynağı `6403788`. Son dil seçici kanıtları `artifacts/language-picker`, seçim/adet kanıtları `artifacts/set-drafts`, önceki takım kanıtları `artifacts/furniture-sets` ve yönetim/SEO kanıtları `artifacts/control-seo` altında tutulur. Son sürüm 1 Kasım 2026 tarihinde canlıya alındı ve kabul kontrolleri geçti.

Mağaza: https://nodenohome.com/ — Yönetim: https://nodenohome.com/yonetim

- Doğrulanan canlı paket: `0ba468acc04cc378af916232ee6ba2fc3a4f5c0912ce1087cca204fd56bd4229`.
- Yayın öncesi yedek: `/home/nodenoho/nodeno-backups/20261101T183029Z-0ba468acc04c-3dd432`.
- 226/226 kaynak testi, 18/18 dağıtım testi. Son pakette Chromium ve Windows WebKit üzerinde dört dil, mobil/masaüstü, misafir ve üyelikli sepet, miktar sınırında atomik ret, renk seçimi, içerik düzenleme, 10 takımın 20 komodin açılımı ve özel yönetim kaydı geçti. Bekleyen gönderimde ürün sayfasına gidip dönme ve hesaptan çıkma doğrulandı. Yeni takım seçimlerinin koleksiyon/ürün dönüşü ve yenilemede korunması, mod/hesap ayrımı, renk/adet, geçersiz ara girişin son geçerli kaydı koruması, engelli saklama ve 320 piksel genişlik iki tarayıcıda geçti. Önceki 27 yönetim bölümü kabulü arşiv kanıtında korunur.
- Önceki seçim/adet sürümünün canlı kabulü: dört alan adında güvenilir HTTPS ve doğru sürüm kimliği; dört dilde takım/B2B SSR, canonical ve hreflang; 24 özel erişim sınırı; dört sayfa haritası ve 12 varlık özeti geçti. Gerçek canlı Chromium'da 17 oda grubu, dört dil mobil/RTL ve masaüstü, 1 dolap + 2 komodin + 1 şifonyer misafir sepeti doğrulandı; bazalı karyola eklenmedi. Canlı yenileme/koleksiyon/ürün dönüşü, fotoğraf bağlantısı, miktar düğmeleri, geçersiz ara giriş, mod ayrımı ve ekleme sonrası taslak temizliği geçti; sayfa hatası yok. `artifacts/set-drafts/live-acceptance.json` ve `live-*` görüntüleri kanıttır. Fiziksel telefon testi yapılmadı.
- Son dil seçici düzeltmesi: kaynakta 226/226 ve dağıtımda 18/18 geçti. Son pakette ve canlıda ayrı ayrı Chromium/Windows WebKit, dört dil, altı genişlik, ana sayfa/kategoriler toplam 96 senaryo başarılı. Metin açıklığı, dil değişimi, üst bilgi çakışması ve taşma kontrol edildi; fiziksel iPhone kabulü yapılmadı. [Kanıt](language-picker.md). Önceki takım/seçim canlı kabulü `artifacts/set-drafts` altında kendi sürümüyle arşivlenir.
- Katalog: 667 SKU, 392 model, 104 kategori ve 5.129 onaylı görsel referansı. Test amacıyla gerçek yönetici, müşteri veya sipariş oluşturulmadı.

İlk sahip e-postası `hamzaozbalkan@gmail.com`. Özel kurulum kodu yalnız yerel `artifacts/control-seo/NODENO_Yonetim_Ilk_Kurulum.txt` dosyasındadır; kullanıcı kendi parolasını ve doğrulama uygulamasını kurar. Kod sunucuda özet olarak saklanır ve yedi gün geçerlidir. Dosya Git'e veya siteye yayımlanmaz. Adımlar [yönetim kılavuzunda](yonetim-kilavuzu.md).

Teknik SEO yayımlandı; arama motorlarında birinci sıra garantisi verilmez. Hesaba bağlı Search Console/Webmaster doğrulaması, gerçek ülke hizmet koşulları ve aşağıdaki sağlayıcı bağlantıları ayrıca tamamlanmalıdır.

| Alan | Hazırlanan davranış | Dış bağlantı durumu |
|---|---|---|
| Yönetici girişi | Ayrı oturum, parola, TOTP, tek kullanımlık kurtarma ve personel rolleri | İlk sahibi kullanıcı kendi parolasıyla kurar |
| Katalog/fiyat | Kalıcı taslak, sürüm kontrolü, yayın, aynı API/HTML/JSON-LD fiyatı | Kaynak katalog ve 5.129 onaylı medya korunur |
| Kampanya/kupon | Tarihli kampanya ve hazırlık kupon kayıtları | Ödeme açılmadan kupon tahsilatı yok |
| Koleksiyon/vitrin | Onaylı tam görsel, ürün seçimi, metin ve sıralama | Marka varlıkları korunur |
| SEO | SSR, canonical, dört dil, yapılandırılmış veri, haritalar, doğrulama alanları | Search Console/Webmaster sahiplik hesabı kullanıcı adımı |
| Yurt dışı toplu alım | Adet ve takım bazlı teklif talebi, seçilebilir içerik/renk/adet, takım tekrar sayısı, misafir formu, özel yönetim ve değiştirilemez bileşen kaydı; dört dil B2B sayfası | Doğrulanmış toptan fiyat listesi yok; teklif talebiyle ilerlenir. Eski paket/palet kayıtları tarihsel olarak korunur. Üretime örnek ticari veri eklenmedi; otomatik ileti ve gerçek satış kapalı |
| Perakende takım kurucusu | PDF ile doğrulanan 17 oda grubu; opsiyonel parçalar, renk/adet, gerçek toplam ve ayrı SKU kalemleriyle atomik sepet | Güncel listede olmayan beş katalog kodu seçim dışında raporlandı; tek SKU hazır setler yapay olarak parçalanmadı. [Katalog eşleşmesi](furniture-sets.md) |
| Takım seçimi ve adet | Yeni seçimleri aynı sekmede koruma, bireysel/toplu ayrımı, hesap kimliği kontrolü, güncel üyelik denetimi, mobil artırma/azaltma ve ürün fotoğrafı bağlantısı | Cihazlar arası eşitleme yok; yalnız ürün/varyant/miktar kaydı. Tarayıcı saklaması kapalıyken alışveriş çalışır. [Kabul kaydı](set-drafts.md) |
| Ülkeler | Hedef pazar listesi ve ayrı koşul formları | Kargo/gümrük/iade gerçek koşulları girilmeli |
| Sipariş/kargo | Gerçek talepler, müşteri sipariş görünümü, kargo kuralları/sevkiyat hazırlığı | Gerçek ödeme, kargo etiketi satın alma ve tamamlama kapalı |
| Fatura | Proforma/paketleme, KolayBi şifreli ayarı, doğrulama, eşleştirme, taslak/durum/PDF adaptörü | API anahtarı/Channel girilmedi; gerçek bağlantı doğrulanmadı; GİB gönderimi kapalı |
| Mesaj/reklam | Gerçek destek formu, kayıtlar, şablon/ileti taslakları ve reklam planları | E-posta/SMS/reklam sağlayıcı adaptörleri seçilmedi; otomatik gönderim/harcama yok |
| Analiz/öneriler | Açık izin, geri alma/silme, gerçek olaylar, model tekilleştiren sıralama | İzinsiz analitik veya örnek başarı verisi yok |
| Google/Apple müşteri girişi | Önceki giriş/kayıt/hesap birleştirme arayüzü ve hazırlığı korunur | Sağlayıcı uygulama ayarları sonraki kullanıcı adımı |

Yeni ücretli/bilinmeyen eklenti yüklenmedi. Mevcut PHP/SQLite hosting, NODENO tasarım varlıkları ve kurulu geliştirme/doğrulama becerileri kullanıldı. Eksik sağlayıcı veya yasal ayar, “çalışıyor” diye taklit edilmedi.

Toplu alım: https://nodenohome.com/?lang=tr&page=wholesale — Talepler: https://nodenohome.com/yonetim#wholesaleRequests — Adet/takım fiyat ayarları: https://nodenohome.com/yonetim#wholesale

Takım seçimi: https://nodenohome.com/?lang=tr&page=sets — Örnek: https://nodenohome.com/?lang=tr&page=sets&set=bohera-bedroom

## 2 Kasım 2026 ülke ve dil yayını

Türkiye ziyaretçilerinde toplu alım tanıtımları ve takım kurucudaki toptan geçiş gizlendi. Doğrulanabilir yurt dışı IP ülkelerinde açılır. Desteklenen dört dil arasında ülkeye göre başlangıç dili, açık dil URL'si ve kalıcı manuel tercih önceliği eklendi; desteklenmeyen ülke dillerinde İngilizce kullanılır. Ayrıntılar [ziyaretçi ülkesi sözleşmesinde](visitor-market.md).

Yayın `fbc8ce7ec1c88aee065f5eccfbcd8ff44df224d46093d891ef1e4847d73cb267`; yedek `/home/nodenoho/nodeno-backups/20261102T074416Z-fbc8ce7ec1c8-e49f46`. Zorunlu güncel medya denetimi, 229 kaynak testi, 18 dağıtım testi, 33 yerel ülke/tarayıcı senaryosu ve 9 görsel senaryo geçti. Canlıda Chromium mobil/masaüstü ve WebKit mobilde 3 kontrol geçti; gerçek test bağlantısının ülkesi TR idi. Ülke/dil davranışı, gizlenen ihracat çağrıları ve kalan perakende takım işlevi doğrulandı. Başka ülkelerden fiziksel canlı bağlantı yapıldığı iddia edilmez. Kanıtlar `artifacts/visitor-market`.

Yeniden doğrulanan 666 fiyat aynı kaldı. `4639 / AGT-144EL-BB-1` için kaynak sayfada tam SKU doğrulanmadığından fiyatı gösterilmiyor; ürün silinmedi.

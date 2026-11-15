# Kapı ve dolap kapağı koleksiyonları

10 Kasım 2026 tarihli ekleme, NDECOR R4 kapı kataloğu/fiyat listesi ile Göktaş 2026 lake ve yatay kapak kataloglarını kullanır. Kapak fiyat kaynakları, masaüstündeki 10.09.2026 tarihli 2026-3 lake ve membran fiyat listeleridir. Kaynak PDF'ler değiştirilmez; belge ve görsellerin SHA-256 kayıtları `data/door-catalog.json` ve `data/cabinet-fronts.json` içinde tutulur.

## Mağazada kullanım

- Kapılar: `https://nodenohome.com/?page=catalog&category=kapilar&lang=tr`
- Dolap kapakları: `https://nodenohome.com/?page=catalog&category=dolap-kapaklari&lang=tr`
- Yönetim: `https://nodenohome.com/yonetim`

Kapı yüzeyi/modeli seçildikten sonra **Ölçü ve adet listesi** alanında her farklı ölçü için **Ölçü ekle** kullanılır. Boy mm, kanat eni 770/870 mm, kasa genişliği 95/115/145/165/185/215 mm ve adet her satırda ayrı belirlenir. Ölçülerden sonra o satırın camlı uygulaması ve katalogdaki gerçek cam modeli seçilir; pervaz, donanım, kol ve açılış yönü **Uygulama ve donanım** bölümündedir. Aynı kapının farklı ölçü ve cam seçimleri ayrı sepet satırlarıdır. 10 Kasım kullanıcı düzeltmesine göre 170 mm’ye kadar kasa farkı yoktur: 95/115/145/165 mm ücretsiz, 185 mm +300 TL ve 215 mm +455 TL. Farklar kapı takımı başına uygulanır. Önceki 15 cm açıklaması müşteri kataloğunda 17 cm olarak düzeltilmiştir; kaynak PDF ve orijinal manifest korunur. Türkiye teslimi için toplam 5, diğer ülkeler için 10 kapı takımı gerekir. Profil ve aksesuarlar bu sayıya katılmaz.

Dolap kapağında her satırda boy/en milimetreyle girilir; adet aynı ölçüdeki parça sayısıdır. Kapak, camlı kapak, çekmece klapası ve boy kapak ayrı satırlarda birleştirilebilir. Satır çoğaltma ve kaldırma düğmeleri vardır. Sepete ekleme bütün satırları önce doğrular: herhangi bir hatada veya sınır aşımında hiçbir satır kısmen eklenmez. Aynı ölçü ve uygulamalar birleşir; farklı olanlar ayrı kalır. Örneğin 500 × 1000 mm'den 10 adet toplam 5 m² eder. Lake/PVC kapak alanı farklı model ve ölçüler arasında birikir. Türkiye için 5 m², diğer ülkeler için 10 m² gerekir. Kapı takımı sayısı ile kapak alanı birbirinin minimumunu tamamlamaz. Akrilik, malzemesi kesinleşmeyen camlı modeller ve tamamlayıcılara kaynakta belirtilmeyen ticari koşullar uydurulmaz; teklif aşamasında doğrulanır.

Alıcı sepet özetinden teslimat ülkesini seçer. Misafir adres adımında ülke değişirse minimum yeniden kontrol edilir. Sonraki ödeme entegrasyonu da gerçek teslimat adresinin ISO ülke kodunu sunucu hesabına vermelidir.

## Sipariş örneği demosu

Her iki ürün sayfasındaki **Sipariş örneğini izle** düğmesi dört adımlı demo açar. Oynat/duraklat, geri/ileri ve kapatma kontrolleri vardır. Demo güncel ürünün gerçek birim bedelleriyle gösterilir; cam veya yüzey bedeli kesinleşmiyorsa kesin toplam uydurulmaz. Kullanıcının sepetini ve mevcut taslağını değiştirmez. **Örneği formda kullan** açıkça seçilirse örnekler yalnız forma aktarılır; sepete eklenmez ve sipariş oluşturulmaz. Hareket azaltma tercihinde demo otomatik başlamaz. Escape veya kapatma düğmesi odağı açan kontrole döndürür.

Kapak örneği: 1975 × 225 mm / 2 kapak; 1914 × 255 mm / 2 camlı kapak; 247 × 597 mm / 3 çekmece klapası. Toplam 2,307267 m² olduğu için Türkiye’deki 5 m² minimumunu tek başına karşılamaz. Örneğin ilk satır 9 adede çıkarılırsa toplam 5,417892 m² olur. Camlı satırın uygulama bedeli kesinleşene kadar o satır teklif gerektirir.

Kapı örneği: 2070 × 770 × 115 mm / 2 takım; 2070 × 870 × 145 mm / 2 takım; 2070 × 870 × 115 mm / 1 camlı takım. Boy × kanat eni × kasa genişliği sırasındadır. Cam modeli katalogda aynı kapı ailesinden seçilir. Cam çıtası farkı yüzeye göre mevcut liste üzerinden eklenir; gerçek cam bedeli dahil değildir. Kaynak camlı fotoğrafı tek başına yüzey fiyatı belirtmediğinde, sayfada yüzey/renk ayrıca seçilir.

Liste altındaki toplam ve mobil sabit satın alma alanı birlikte güncellenir. Eksik ölçü veya teklif gerektiren satır varken mobil alan kesin toplam göstermez. Üstteki kapı fiyatı **Başlangıç takım fiyatı**, satır fiyatları ise seçilen uygulamanın bedelidir. Mevcut 5/10 takım ve 5/10 m² minimumları bağımsız olarak sürer.

## Fiyatlar ve doğrulanmayan seçenekler

Yeni kapı ve kapaklar, mevcut mobilyalara uygulanan Adore fiyat politikasıyla karıştırılmaz. Kullanıcının kendi PDF fiyatları kullanılır; bu ürünlere ayrıca yüzde 40 eklenmez. Mevcut 667 mobilyanın fiyat, kampanya ve medya kayıtları korunur.

Kapaklarda seri veya RAL grubu tabanı ile modelin açıkça listelenmiş m² farkı toplanır. Listede bulunmayan model, ek kod, renk grubu, karışık yüzey ve cam uygulaması için tahmini fiyat üretilmez. Kapı kollarındaki “başlangıç” ve “ortalama” bedeller, seçilmiş kolun kesin fiyatı olarak eklenmez. Kaplama boyası, özel yükseklik ve belirsiz camlı yüzeyler teklif gerektirir.

Kapı ve kapak fiyatları KDV hariçtir. Kapılarda İzmir fabrika teslim esası gösterilir. Kaynak kapak listesindeki tedarikçi nakliye hükmü, müşteriye otomatik ücretsiz sevkiyat vaadine çevrilmez. Vergi, nakliye, montaj, cam ve aksesuar kapsamı teklif sırasında kesinleşir. Katalogdaki yangın dayanımı süreleri proje/belgelendirme gerektiren seçeneklerdir; doğrulanmamış sertifika veya stok iddiası yoktur.

Fiyatı doğrulanamayan seçeneklerin dökümü: `artifacts/project-commerce/fiyat-teyidi-gerekenler.csv`.

## Döviz kuralı

Ana tutarlar tamsayı TRY kuruş olarak saklanır. Döviz gösterimi, fiyatın pazartesi başlayan İstanbul haftasında o ana kadar yayımlanan **en yüksek TCMB döviz satış kuruna** bölünmesiyle hesaplanır. Her para biriminin birim katsayısı ayrı uygulanır; JPY'nin 100 birimlik bülteni doğru ölçeklenir. Yuvarlama, para biriminin alt birimine yarım yukarı yapılır.

Pazartesi 55 ve çarşamba 50 yayımlanırsa, aynı hafta 55 kullanılır. Yeni hafta önceki haftanın en yükseğini taşımadan yeniden başlar. Yeni haftada henüz bülten yoksa son yayımlanmış iş günü kullanılır. Bu hesaplama yöntemi müşteri ekranında açıklama olarak gösterilmez. Bu kaynak gün içi sürekli piyasa verisi değildir; TCMB'nin yayımladığı iş günü bültenidir.

Kaynak yalnız `https://www.tcmb.gov.tr/kurlar/YYYYMM/DDMMYYYY.xml` adresleridir. TLS doğrulaması açıktır, yönlendirme ve XML dış varlıkları kabul edilmez. Sunucuda özel veri klasöründe önbellek/yenileme kilidi vardır. Geçerli kur doğrulanamazsa yabancı para gösterimi yerine TRY ve açıklama kullanılır; eski kur “güncel” olarak sunulmaz.

Turhost'un PHP TLS bağlantısı TCMB'de zaman aşımına girdiği için resmî veri, aynı sunucunun Python HTTPS istemcisiyle alınır. `hosting/fx-refresh.py`, PHP üreticisiyle aynı haftalık seçim, para katsayıları ve revizyonu üretir; birebir eşitlik testi vardır. Kaynak kodu `/home/nodenoho/nodeno-jobs/fx-refresh.py`, veri ve kilit `/home/nodenoho/nodeno-data/` altındadır. HTTPS sertifika doğrulaması korunur; alternatif kur sağlayıcısı kullanılmaz.

Sunucu cron'u her dakika çalışır; normalde beş dakikada bir bülteni yeniler. İş günü 15:30 sonrasında o günün bülteni henüz yoksa yayımlanana kadar her dakika tekrar kontrol eder. Ön yüz kur kaydını 15 dakikada bir ve sayfa açılışında alır. Kaydın geçerliliği 30 dakikadır; başarısız indirme geçerliliği uzatmaz. TCMB bağlantısında her deneme en fazla 20 saniyedir; geçici ağ/sunucu hatalarında en fazla üç deneme yapılır. Henüz yayımlanmamış günün 404 yanıtı tekrar denenmez. Kaynak hata durumunda eski değer güncel sayılmaz. Kur işi dışında mevcut cron kayıtları korunmuştur.

Kur işi kurulumu ve dosya okuma doğrulaması `scripts/configure-fx-refresh.py`, canlı servis kanıtı `artifacts/project-commerce/fx-service.json` içindedir. Mevcut koddan farklı bir iş dosyası otomatik ezilmez. İncelenmiş taşıma düzeltmesi `scripts/update-fx-refresh.py` ile yalnız beklenen önceki hash üzerinden, özel klasörde yedeği alınarak kurulur; bu işlem cron veya kur geçerliliğini değiştirmez. Gelecekteki yayınlar bu özel klasörü, cron kaydını ve veri dosyalarını korumalıdır. Normal web yayını kur üreticisinin Python dosyasını web köküne kopyalamaz.

## Teklif ve yönetim

Sepetteki kapı/kapak seçimleri, iletişim bilgileri ve açık izinle teklif talebine dönüşür. Yönetimde **Kapı, kapak ve proje talepleri** bölümünde görünür. Durum, teklif koşulları ve iç not düzenlenebilir; alıcının orijinal seçimi ve fiyat anlık kaydı değiştirilmez.

Gönderim; aynı kaynak denetimi, HttpOnly/SameSite CSRF çerezi, hız sınırlaması ve tekrar gönderim anahtarı kullanır. Aynı anahtarla aynı istek aynı referansı döndürür. SQLite yazma kilidi alınmadan önce döviz kaydı hazırlanır. Bu işlem sipariş, tahsilat veya otomatik e-posta oluşturmaz.

## Diğer sohbetteki ödeme entegrasyonu için sözleşme

- `GET /api/commerce/status`: kullanılabilirlik, ülke kodları ve teklif CSRF belirteci.
- `GET /api/exchange-rates`: haftalık kur kaydı, kaynak bülten özetleri, revizyon ve geçerlilik zamanı.
- `POST /api/commerce/quote`: `items`, gerçek teslimat ülkesinin `country` kodu, `currency`, `priceRevision`, dövizde `exchangeRevision`.
- `POST /api/door-inquiries`: yukarıdakilere iletişim/izin/tekrar gönderim bilgilerini ekler.

Kapı satırı `id`, `quantity`, kanonik `options` ve `key` taşır. Yeni ölçüler `heightMm`, `leafWidthMm`, `frameWidthMm`; cam seçimi `glazed` ve `glassModelId` alanlarıdır. Sunucu, cam referansının aynı modelin gerçek camlı seçeneği olduğunu doğrular. Eski cm tabanlı `height`/`frameDepth` seçimleri geriye dönük okunur; yeni mm alanlarıyla çelişiyorsa istek reddedilir. Kesin mm ve cam modeli satır anahtarına katılır. Kaynakta yalnız genel cam uygulaması varsa `standard` kullanılır; katalogda gerçek cam modeli bulunuyorsa bu referans seçilmelidir. Kapak satırı seçenekleri `widthMm`, `heightMm`, `application` içerir. İstemci fiyat gönderemez. Sunucu satır ve toplam tutarı kendi katalog verisinden hesaplar. Kapakta her satırın alanı tam sayı mm² ile hesaplanır; tüm satır bir kez yuvarlanır. Yuvarlanmış parça fiyatını adetle çarpmak farklı sonuç verebileceği için `lineTotalMinor` esas alınır.

Yanıt; alan/miktar minimumlarını, TRY alt toplamını, döviz tutarını, katalog/kur revizyonunu ve teklif gerektiren satırları içerir. `checkoutEnabled:false` ve `taxAndFreightFinalized:false` korunur. Kullanıcının talimatıyla banka, Stripe ve tahsilat açılışı diğer sohbettedir. Ödeme adaptörü sunucu teklifini yeniden hesaplamalı; minimum, revizyon, vergi/nakliye ve teklif gereksinimi kesinleşmeden tahsilat yapmamalıdır.

Kapak satırında `quantity` parça adedidir; fatura veya ödeme entegrasyonu bu alanı doğrudan m² kabul etmemelidir. Fatura alan miktarı `areaMm2 / 1_000_000`, m² fiyatı `unitRateMinor` alanından alınır. Ödeme sağlayıcısına yuvarlanmış parça fiyatını adetle çarparak farklı toplam gönderilmez; doğrulanmış satır/toplam tutarı esas alınır. Kaynak m², parça adedi ve ölçüler açıklama/metaveride birlikte korunur.

PTYS Technologies LLC ilişkisi marka ayarında, altbilgide ve Organization verisinde parentOrganization olarak gösterilir. Bu ilişki, doğrulanmamış yasal satıcı/vergi/banka bilgileri üretmez.

## Yayın ve doğrulama

Yeni görseller PDF'nin ürün bölgelerinden alınır. Düzenlenebilir PDF yazıları ürün görseline dahil edilmez; orijinal fotoğraf geometrisi ve rengi korunur. GK/GB/GT/GM marka öneki ND olur; modelin sayısı ve son eki korunur. Katalogdaki marka başlıkları ve kaynak firma geçmişi yayımlanmaz.

`lib/owner_media_gate.py`, kaynak PDF, incelenmiş kontak sayfaları, OCR, resim boyutları ve dosya hashlerini doğrular. Mevcut 5.129 mobilya görsel referansının yayın kapısı ayrıca eksiksiz çalışır. Importer tekrar çalıştırılırsa yeni belge otomatik onaylanmaz; `publicationReady:false` ile yeniden inceleme ister.

15/11/2026 görsel düzeltmesi: yazısı kaldırılmış katalog etiketlerinin üst/alt gri çizgileri 33 kapak görselinden çıkarıldı. `lib/cabinet_front_decoration.py` yalnız belirlenmiş PDF çizgi stilini ve aynı sınırlar içindeki nötr gri raster kalıntılarını temizler. Orijinal PDF, ürün fotoğrafı ve alfa akışları korunur. Önceki yayımlanan dosyalar arşivlenir; yeni dosyalar yeni SHA-256 adları ve yeni `frontCatalogVersion` ile yayımlanır. Çizgi alanları dışındaki piksellerin birebir aynı olması, yeni koyu piksel oluşmaması ve tüm karşılaştırma sayfalarının incelenmesi zorunludur. Önceki OCR sonucu, yeni metin/çizim eklenmediği ispatına bağlı olarak aktarılır; yeniden OCR çalıştırılmış gibi gösterilmez. Kanıtlar `artifacts/front-image-integrity-20261115/` altındadır.

`scripts/build-project-release.py`, doğrulanmış f72d422 canlı paketindeki 667 mobilyayı aynen koruyarak yeni koleksiyonları ekler. Bu yöntem eski tedarikçi fiyatlarının tarihini yenilenmiş gibi göstermez. Normal tam kaynak derlemesindeki fiyat tazeliği kapısı değiştirilmemiştir. `scripts/build-test-project-worker.mjs` yalnız izole regresyon içindir ve üretim paketi olarak reddedilir.

Yerel kabul gerçek PHP ile Chromium masaüstü, Chromium mobil ve WebKit mobilde Türkçe, İngilizce, Rusça ve Arapçayı kapsar. Fiziksel telefon testi yapılmış sayılmaz. Yerel ve canlı kabul dosyaları `artifacts/project-commerce/` içinde ayrı tutulur. Kullanıcı verisi, oturumlar, OAuth bilgileri ve görsel kasası sürüm/web kökü dışında korunur.

## Para birimi seçimi ve adres kontrolü — 10 Kasım 2026

Üst gezinmede ayrı para birimi şeridi kullanılmaz. Ana sayfada ilk ürün vitrininin başlığında, ürün sayfasında fiyat bloğunda, sepet ve adres kontrolünde sepet özeti içinde seçim yapılır. Kur hesabının kaynağı ve haftalık politika teknik kayıtlarda kalır; müşteri ekranına TCMB açıklaması eklenmez. Geçerli kur alınamazsa TRY'ye dönüş bilgisi korunur.

Bilgileri kontrol et adımı iletişim, teslimat ve fatura kartlarından oluşur. Fatura adresi teslimatla aynıysa adres tekrarlanmaz. Seçilen ürünler fotoğraf, ürün adı, renk, adet ve satır tutarıyla listelenir; kaynak ürün kodu gösterilmez. Para birimi değişikliği veya bilgileri düzenleme iletişim/adres taslağını silmez. Ayrı fatura adresi ayrıca gösterilir. Ödeme öncesi hazırlık akışı sürer; bu arayüz değişikliği tahsilat veya gerçek sipariş açmaz.

Dört dil ve Arapça RTL için Chromium masaüstü/mobil ile Windows WebKit mobil kabulü `artifacts/checkout-currency/browser.json` içinde; canlı kontrol ayrı `live-browser.json` dosyasında tutulur. Yerel görsel test, onaylı görsel dosyalarının SHA-256 doğrulanmış özgün çıktılarını kullanır; canlı görsel kabulü gerçek HTTPS medya uçlarından yapılır.

Hizalama düzeltmesi: adım göstergesi iki sütunun dışına alınır; adres kartı ve sepet özeti aynı üst kenardan başlar. Başlık yükseklikleri ve iç boşluklar eşittir. İletişim alanları masaüstünde üç sabit sütun, mobilde tek sütundur. Ürün fotoğrafı, açıklama ve tutar satırları üstten hizalanır. Bu geometri masaüstünde kartların `y` farkı en fazla 2 CSS piksel olacak şekilde kontrol edilir. Son kabul dosyaları `artifacts/checkout-currency/alignment/` altındadır.

Genel çalışma alanında bu doğrulama sırasında `payments-core.test.mjs` içindeki yedi ödeme testi eksik sunucu ödeme sözleşmesi nedeniyle başarısızdı (285 başarılı / 7 başarısız). Bu ödeme dosyaları, katalog/özel hesap verileri ve tahsilat ayarları dar kapsamlı arayüz paketinde değiştirilmez. Ödeme için tam başarı veya açılış iddiasında bulunulmaz.


## Kargo dahil fiyat politikası — 12/11/2026

Türkiye içi tüm ürünlerde standart kargo ürün fiyatına dahildir. Mobilyanın mevcut fiyatı korunur; kapı, kapak ve bunların profil ürünlerinde net taban fiyatına %20 eklenir. Kapı kasa, cam ve donanım farkları aynı katsayıya tabidir. Önce artış, sonra KDV hesaplanır. Artış tam kuruşla yuvarlanır; aynı katalog ikinci kez işlenirse tekrar uygulanmaz. Fiyatı doğrulanmamış bir ürün veya cam seçeneği tahminî fiyat kazanmaz; teklif gerektirmeye devam eder.

Ham kaynak katalog ve yönetimde kaydedilen fiyatlar net tabandır. `shippingPolicyVersion=2026-11-12-included` sunucu projeksiyonunda satış ve varsa önceki fiyatı artırır; ürün sayfası, SEO ve ödeme aynı tutarı kullanır. Yönetici net tabanı değiştirirken mağazadaki %20 artışı hesaba katmalıdır. Kaynak fiyat üzerine ayrıca elle aynı artışı eklemek çift artışa yol açar. Geçmiş sipariş ve sözleşme tutarları değiştirilmez.

Türkiye için minimum 5 kapı takımı / 5 m² kapak, yurt dışı için 10 takım / 10 m² kuralları korunur. Uluslararası nakliye, gümrük ve teslim hizmetleri için teklif istenir; standart Türkiye kargosuna kata çıkarma veya montaj otomatik eklenmez. Döviz fiyatları mevcut haftanın o ana kadarki en yüksek TCMB satış kuru politikasıyla hesaplanır.

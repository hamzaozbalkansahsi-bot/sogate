# NODENO SEO sözleşmesi

## Yayınlanan teknik yapı

Ürün, kategori, ana sayfa, yardım ve teslimat sayfalarında ilk HTTP yanıtında gerçek içerik bulunur. Ürün adı, renk varyasyonları, teknik bilgiler, fiyat ve ürün/kategori bağlantıları JavaScript çalışmadan okunabilir. SPA gezinmesi aynı SEO politikasına göre title, açıklama, canonical, alternatif diller, sosyal paylaşım metası ve yapılandırılmış veriyi yeniler.

Canonical alan adı `https://nodenohome.com` olarak sabittir. `.com.tr` ve www ziyaretleri tarayıcıda girdikleri alan adını korur; içerikteki bağlantılar yerel köktendir. Canonical/OG/site haritaları tek ana alan adını kullanır. Sayfa içindeki fiyat yönetim panelinin yayın katmanıyla API, SSR ve JSON-LD için aynıdır.

Her gerçek dil sürümü Türkçe, İngilizce, Rusça, Arapça, Almanca, Azerbaycanca, Kazakça, Türkmence, Özbekçe, Kırgızca, Farsça ve x-default bağlantılarını karşılıklı içerir. Arapça ve Farsça RTL korunur. Ülke dil yerine kullanılmaz; aynı içeriği ülke adlarıyla çoğaltan kapı sayfaları üretilmez. Yeni dillerin gerçek arayüz, katalog ve belge sözlükleri sunucuda da kullanılır; yalnız dil kodunu değiştiren İngilizce sayfalar üretilmez.

Ziyaretçinin kaydettiği dil ve açık dil bağlantısı yoksa ilk sayfa IP ülkesinin desteklenen diliyle hazırlanır. Örneğin Almanya de, Azerbaycan az, Kazakistan kk ve İran fa kullanır. Destek dışındaki ülkelerde İngilizce kullanılabilir. Yönlendirme zorlanmaz. Açık `lang` adresleri ve karşılıklı hreflang bağlantıları korunur. Türkiye'de dil seçimi ihracat çağrısı açmaz. Ayrıntılar [ziyaretçi ülkesi sözleşmesinde](visitor-market.md).

Seçili ürün `Product` olarak işaretlenir. En az iki gerçek varyantı olan ailelerde ayrıca `ProductGroup` kullanılır; renk, malzeme ve ölçü eksenleri gerçek seçeneklere göre belirlenir. Görseller onaylı aynı alan adı medya yollarındadır. Fiyat, stok, puan, değerlendirme, teslimat ve satış sayısı uydurulmaz. Stok ancak açıkça biliniyorsa belirtilir. Geçersiz ürün/kategori 404 döner. Özel hesap/sepet/ödeme/favori sayfaları, arama/filtreler ve yönetim index dışıdır. Boş kategoriler index dışıdır.

## Haritalar ve doğrulama

- `https://nodenohome.com/robots.txt`
- `https://nodenohome.com/sitemap.xml`
- `https://nodenohome.com/sitemap-products-tr.xml` (ayrıca en, ru, ar, de, az, kk, tk, uz, ky, fa)
- `https://nodenohome.com/sitemap-pages-tr.xml` (aynı 11 dil)

Ürün haritaları gerçek canonical ürünleri ve onaylı görselleri; sayfa haritaları gerçek içerikli kategori ve yardımcı sayfaları içerir. Görsellerin taranması engellenmez. Yönetim ve özel API yollarının taraması engellidir; bu güvenlik yerine geçmez, API ayrıca oturum/yetki kontrolü yapar. Sayfayı oluşturmak için gereken kamu katalog, yapılandırma ve ürün ayrıntısı API'leri dar kapsamlı `Allow` kurallarıyla erişilebilir. Ham JSON yanıtları `X-Robots-Tag: noindex` taşır.

Yönetimden Google/Bing/Yandex doğrulama değerlerini yayınlayın. Search Console ve Webmaster hesaplarında mülk sahipliğini tamamlayıp site haritasını ekleyin. Bu hesap işlemleri kullanıcı oturumuna bağlıdır; sistem kurulmuş gibi göstermez.

IndexNow anahtarı panelden hazırlanır. Değişiklikler gerçek yayın işleminden sonra kuyruğa girer. Yalnız sabit resmi HTTPS endpointine ait alan adının canonical URL’leri gönderilir. Yanıt 200/202 ise “istek alındı” olarak kaydedilir; “dizine eklendi” denmez. Kuyruk, anahtar dosyası ve son gerçek yanıt panelde görünür. Geleceğe tarihli kampanyanın fiyatı sunucu saatine göre değişir; sınır zamanında yeniden bildirim/arama motoru taraması kendiliğinden kesinleşmiş sayılmaz.

## İçerik ve pazar geliştirme

Hedef ülkeler için ürün dilini, gerçek kargo anlaşmasını, iade yolunu, vergi/gümrük koşullarını ve iletişim kapasitesini ayrı doğrulayın. Dil desteği tek başına o ülkeye satış sözü değildir. Yerelleştirilmiş ülke sayfası ancak kendine ait gerçek içerik ve koşullarla eklenmelidir.

Ürün başlığına ölçü ve teknik kısaltmaları yığmayın; bu bilgiler teknik özelliklerde kalır. Model adları ve renk seçimi mevcut yapıda korunur. Özgün ve doğru ürün metni, açık navigasyon, ulaşılabilir sayfalar ve tutarlı fiyat esastır. Arama motorunun dizin ve sıralama kararı site dışındadır; ilk sıra garantisi verilmez.

## Doğrulama

`tests/seo.test.mjs` JS/PHP davranışını, doğru/kaçışlı meta, canonical/hreflang, ürün fiyatı, filtre/noindex ve haritaları kontrol eder. `tests/browser/seo.py` gerçek paket üzerinde Chromium/Windows WebKit, mobil/masaüstü, dört dil ve JavaScript kapalı sayfaları açar. `tests/browser/control-panel.py` panel yayınının API/SSR/JSON-LD fiyat eşitliğini ayrıca kanıtlar.

Resmî kaynaklar: [Google dil sürümleri](https://developers.google.com/search/docs/specialty/international/localized-versions), [ürün varyantları](https://developers.google.com/search/docs/appearance/structured-data/product-variants), [JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics), [IndexNow](https://www.indexnow.org/documentation).

## Uluslararası toptan mobilya SEO'su

`?page=wholesale&lang=tr|en|ru|ar` dört dilde ayrı, sunucuda oluşturulmuş başlık/açıklama ve gerçek katalog görselleriyle yayımlanır. İçerik adet/takım alımını, miktara göre teklifi ve sevkiyatın teyit edilmesini açıklar. Her dil sayfası kendi canonical adresini, karşılıklı hreflang bağlantılarını ve sayfa haritası kaydını taşır. Ürün sayfaları ile mağaza menüleri bu akışa bağlanır.

Sayfa için `Service` ve işletme alıcısı tanımı kullanılır. Bilinmeyen toptan fiyat için sıfır fiyatlı `Offer`, sahte stok veya teslimat garantisi üretilmez. Mevcut perakende ürün/renk `ProductGroup` fiyatı değişmez. Ürün ön seçimi (`item`) canonical'a eklenmez; arama/filtre kopyaları indekslenmez. Firma bilgileri ve teklif kalemleri yalnız özel yönetimde kalır.

Yeni ülke kopyaları veya mevcut olmayan dillerle kapı sayfaları oluşturulmaz. Almanya için Almanca veya İran için Farsça sayfa bu değişiklikle eklenmiş değildir. Arama motoru mülk doğrulaması ve site haritası gönderimi hesap sahibi adımlarıdır; içerik geliştirmek veya teklif almak sıralama garantisi vermez.

## Seçilebilir takım sayfaları

`?page=sets` ve17gerçek oda koleksiyonu `?page=sets&set=<id>` dört dilde SSR, kendi canonical adresi ve karşılıklı hreflang ile yayımlanır. Site haritasına gerçek koleksiyon adresleri eklenir. Yapılandırılmış veri CollectionPage olarak tanımlanır; müşterinin seçmediği bileşenler için sabit ürün/SKU, stok veya toplu Offer fiyatı oluşturulmaz. Toptan mod ve ürün ön seçimi aynı oda canonical adresine bağlanır.

## Kapı ve kapak koleksiyonları

Kapılar ve dolap kapakları, gerçek ürün/kategori kimlikleriyle dört dilin SSR, canonical, hreflang ve site haritalarına dahil edilir. Marka NODENO'dur. Organization kaydındaki parentOrganization, kullanıcının bildirdiği PTYS Technologies LLC ilişkisidir; yasal satıcı/vergi bilgisi türetilmez. m² veya yapılandırma gerektiren ürünlere koşulsuz tek parça perakende Offer verilmez; kaynak fiyatı olmayan modellere tutar, stok veya değerlendirme üretilmez. Kur dönüşümü mağaza görünümüdür; indekslenebilir kaynak para birimi TRY olarak kalır.


10 Kasım çoklu ölçü güncellemesinde ölçü/adet satırları ayrı URL üretmez; ürünün kanonik adresi korunur. Güncellenen 170 mm kasa koşulu müşteri kataloğunda dört dildeki ürün açıklamalarına uygulanır. Kaynak PDF/manifeste müdahale edilmez; özel ölçülü ürünlerde koşulsuz tek parça Offer üretilmez.

## 10 Kasım 2026 ürün SEO yayını

`cpanel-release-product-seo-20261110-r3` canlıya yayımlandı. Sürüm SHA-256 değeri `09dff6fe3ded11d568043a6f49a4c9f0172c08d2719f095ff80a75ee2357f4ce`. Mevcut hukuk/ödeme yayını taban alındı; müşteri verisi ve canlı ödeme ayarları korundu. Yayın ve canlı HTTP kanıtları `artifacts/seo-products/deployment.json` ile `live-http.json` dosyalarındadır.

Katalogdaki 3.602 ürün/varyant kaydı dört dilde 14.408 canonical ürün adresiyle haritalardadır. Ürün açıklaması, gerçek teknik özellikler ve seçili varyanta göre meta bilgiler oluşturulur. Yalnız koddan oluşan ürünlerin arama başlığında gerçek alt kategori adı kullanılır; ürün adı ve kodu değiştirilmez. Kaynakla doğrulanan kayın/meşe/çam seçeneklerinin ad/açıklama uyuşmazlıkları giderildi. Kaynak arşivleri, fiyatlar, birimler ve görseller korunur.

Katalog listeleri `pg=2`, `pg=3` biçiminde, sayfa başına 24 ürünle gerçek bağlantılar üzerinden gezilebilir. Her sayfanın kendi canonical adresi ve dört dil alternatifi vardır. JavaScript çalışmasa da ürünler ve sonraki sayfa bağlantıları ilk HTML'de bulunur. Sayfa haritaları katalog sayfalarını içerir. Geçersiz, boş veya aralık dışı sayfa numarası 404/noindex döndürür; ilk sayfanın kopyası olarak sunulmaz.

Seçilmemiş seçenek üst ürünlerine, satış birimi doğrulanmamış ürünlere ve birim fiyatının minimum alınabilir toplamı göstermediği ürünlere koşulsuz `Offer` eklenmez. Görünür birim fiyatı ve satın alma koşulları korunur; arama verisine yanıltıcı tek ürün fiyatı yazılmaz. Gerçek olmayan renk/puan/stok veya teslimat taahhüdü üretilmez.

Yayın öncesi 348 JavaScript ve 33 Python kontrolü geçti. Üretim derlemesi, medya bütünlük geçidi ve aynı paketteki 10 masaüstü/mobil tarayıcı kontrolü geçti. Canlı HTTP kabulünde dört dilde ürün ve ikinci katalog sayfası, haritalar, geçersiz sayfa ve özel yol sınırları doğrulandı. Yerel tarayıcı kanıtı `artifacts/seo-products/browser.json`, canlı HTTP kanıtı ayrı `live-http.json` dosyasındadır.

Canlı HTTPS tarayıcı kabulünde Chromium/1440 px/Türkçe ve WebKit/390 px/Arapça senaryoları da geçti. Gerçek bağlantıyla ikinci katalog sayfasından üçüncüye geçildi, her sayfada 24 farklı ürün gösterildi; canonical/hreflang ve seçili kayın ürünü başlığı doğrulandı. Yatay taşma ve JavaScript hatası görülmedi. Ekran görüntüleri incelendi; kanıt `live-browser.json` dosyasındadır. Dört `.com`/`.com.tr` ve www girişinde TLS doğrulaması geçti; ziyaretçinin alan adı korunurken aynı ana canonical adresi sunuldu (`domain-canonical-live.json`). Bağımsız son kod incelemesinde yayın engeli bulunmadı.

IndexNow sahiplik dosyası HTTPS üzerinden doğru içerikle erişilebilir. Toplam 16.504 güncellenmiş kamu adresinin bildirimi için `scripts/submit-product-indexnow.py` hazırlanmıştır; kabul edilmiş aynı sürüm grupları yeniden gönderilmez. Gerçek yanıt `artifacts/seo-products/indexnow-submission.json` içinde tutulur. Henüz 200/202 kabulü alınmadıkça bildirim tamamlandı veya dizine eklenme gerçekleşti denmez.

11 Kasım 2026 son IndexNow sonucu: Global resmî adrese, aynı anahtar ve sahiplik dosyasıyla gönderilen tek ana sayfa bildirimi saat 08:09:41 UTC'de `202 Accepted` aldı (`indexnow-single-url-20261111.json`). Bu yanıt adresin alındığını, anahtar doğrulamasının hâlâ beklediğini gösterir; doğrulamanın veya dizine eklemenin tamamlandığını göstermez. Beş dakikadan sonra global adrese yapılan toplu deneme saat 08:14:57 UTC'de yine `403 SiteVerificationNotCompleted` aldı; `Retry-After` başlığı yoktu. Resmî protokolün ayrıca desteklediği `https://www.bing.com/indexnow` kanalına saat 08:18:09 UTC'de aynı anahtar, sahiplik dosyası ve HTTPS doğrulamasıyla yalnız bir toplu deneme yapıldı; aynı 403 yanıtı alınınca duruldu. Bekleyen doğrulamaya yaklaşık 17 dakika süre tanındıktan sonra, saat 08:26:40 UTC'de yalnız ilk global kanala yapılan tek kontrollü deneme de `403 SiteVerificationNotCompleted` döndürdü; `Retry-After` başlığı yine yoktu. Her iki kanalda da ilk 10.000 adreslik grup kabul edilmedi; kalan 6.504 adres gönderilmedi. Sonuç: tek ana sayfa için bir 202 kabulü, toplu bildirimlerde sıfır kabul. Son denemenin öncesinde ve sonrasında gerçek canlı sürüm `5bd99cc8404e2390d7268336f6826c1129bdc89124edbc8db9916feda5cc5d3c` idi. Son global yanıt `artifacts/seo-products/indexnow-submission.json` içinde; önceki Bing yanıtı `indexnow-bing-submission-20261111.json` ve `indexnow-attempt-before-final-20261111T082638Z.json` içinde, önceki global yanıt da `indexnow-global-before-bing-20261111.json` içinde değişmeden korunur. Google Search Console doğrulaması bu ayrı servisin sahiplik kabulünü kanıtlamaz.

Sahiplik dosyasının tam bayt içeriği, yönlendirmesiz 200 yanıtı, dört normal/bot kullanıcı ajanıyla erişimi, DNS, TLS ve robots kuralları yeniden doğrulandı (`indexnow-diagnostics-20261111.json`). Erişilebilen geçmiş sunucu günlüklerinde doğrulayıcı isteği bulunmadı; bu sonuç güvenlik duvarı engeli olduğunu kanıtlamaz (`indexnow-ownership-accesslog-20261111.json`). Kalan engel, global ve Bing servislerinin tamamlanmadığını bildirdiği sahiplik doğrulamasıdır; sunucuda buna yol açan somut bir hata saptanmadı. Anahtar ve sahiplik dosyası değiştirilmedi, güvenlik kuralları gevşetilmedi, başka motor veya IP denenmedi. Aynı veriyi aralıksız göndermek yerine servis doğrulaması tamamlandıktan sonra gerçek canlı sürüm yeniden kontrol edilerek tek kontrollü deneme yapılmalıdır; 403 sürerse, mevcut yanıt zamanları ve erişim kanıtlarıyla servis/hosting desteğinde gerçek doğrulayıcı erişimi araştırılmalıdır. Site haritaları bu sonuçtan bağımsız olarak canlı ve robots.txt üzerinden keşfedilebilir. [Resmî IndexNow protokolü ve yanıt anlamları](https://www.indexnow.org/documentation), [resmî doğrulama ve katılımcı motor kanalları](https://www.indexnow.org/faq).

10 Kasım yayınında Google Search Console kullanıcı tarafından henüz kurulmamıştı. Google hesabıyla `https://search.google.com/search-console/` üzerinden `https://nodenohome.com/` URL öneki mülkü veya DNS ile alan adı mülkü eklenip doğrulanmalıdır. Ardından `https://nodenohome.com/sitemap.xml` gönderilebilir. Site haritası zaten robots.txt içinde ilan edilir; Search Console kurulumu organik taranmanın ön şartı değildir. Mülk doğrulaması ve Google'a hesap üzerinden gönderim, servis sonucu görülmeden tamamlanmış gibi raporlanmaz. [Google'ın kurulum adımları](https://support.google.com/webmasters/answer/34592?hl=tr).

## 11 Kasım 2026 Search Console kurulumu

Kullanıcının Search Console'dan verdiği Google sahiplik etiketi kanonik marka ayarındaki `seo.googleVerification` alanına kaydedildi. Derleme yalnız bu kamu doğrulama değerini yapılandırmaya aktarır; marka ayarlarındaki başka alanlar veya gizli bilgiler bu yolla açılmaz. Google şifresi, oturum çerezi veya OAuth anahtarı alınmadı.

Canlı taban sürüm korunarak yalnız `private/config.json` güncellenmiş değişmez paket yayımlandı. Sürüm SHA-256 değeri `5bd99cc8404e2390d7268336f6826c1129bdc89124edbc8db9916feda5cc5d3c`. Kamu dosyaları, ürün kataloğu, görseller, müşteri verisi ve ödeme ayarları değişmedi. Yayın makbuzu `artifacts/search-console-20261111/deployment.json` içindedir. Etiketin tek kez gerçek `<head>` içinde bulunduğu ve kamu yapılandırmasından okunduğu yayın sırasında doğrulandı; bu kontroller başarısız olsaydı önceki sürüme dönülecekti.

23 ilgili test, üretim derlemesi ve paket tarayıcı kontrolü geçti. Canlı dört dilin ham HTML'sinde tek etiket; Chromium masaüstü/Türkçe ve WebKit mobil/Arapça uygulama başladıktan sonra aynı etiket doğrulandı. Kanıtlar aynı klasördeki `browser.json` ve `live-verification.json` dosyalarındadır. Bu kontroller etiketin yayınını kanıtlar; Google'ın mülk sahipliğini kabul ettiği anlamına gelmez.

Kullanıcı 11 Kasım'da **HTML etiketi** yöntemiyle sahipliğin doğrulandığını bildirdi; `google-status.json` bu kullanıcı teyidini kaydeder. Önceki **HTML dosyası bulunamadı** hatası, hazırlanmış etiket yerine dosya yönteminin çalıştırılmasından kaynaklanıyordu. Google'a ait dosya veya başarısız bir dosya doğrulaması oluşturulmadı.

Search Console'un doğrulanmış `https://nodenohome.com/` mülkündeki **Site haritaları** ekranı açıldı. İç tarayıcı açılabilse de kontrol bağlantısı başlatılamadığından hesabın gönderme düğmesine otomatik basılamadı. `https://nodenohome.com/sitemap.xml` ve sekiz alt harita canlıda HTTP 200 ve geçerli XML olarak yeniden doğrulandı; ürün haritalarında 14.408 dil adresi var (`sitemap-live.json`). Kullanıcı **sitemap.xml → Gönder** işleminin **Gönderildi / Başarılı** sonucunu 11 Kasım'da teyit etti. Sahiplik ve site haritası gönderimi tamamlandı; kullanıcı teyidinin kaydı `google-status.json` içindedir. Bu sonuç bütün ürünlerin Google dizinine alındığını veya bir arama sırasına ulaştığını göstermez.

Google gönderiminin başarı teyidinden sonra, 11 Kasım saat 12:17 Türkiye saatiyle (09:17 UTC), son IndexNow toplu denemesinin üzerinden yaklaşık 50 dakika geçtiği için ilk 10.000 adreslik grup aynı resmî global kanalda bir kez daha denendi. Yanıt yine `403 SiteVerificationNotCompleted` oldu; duruldu, kalan 6.504 adres gönderilmedi. Canlı sürüm ve sahiplik dosyası korunur; son yanıt `artifacts/seo-products/indexnow-submission.json` içindedir. Google kurulumu tamamlanmış olsa da IndexNow toplu bildirim kabulü ayrı ve hâlâ bekleyen bir servis aşamasıdır.

Sahiplik etiketi kalıcıdır; doğrulamadan sonra kaldırılmamalıdır. Gelecekte yönetimde ilk **Arama motorları / SEO** kaydı oluşturulurken **Google doğrulama değeri** alanına aynı değer aktarılmalıdır. Mevcut yönetim formu boş yeni kaydı kaynak yapılandırmadan otomatik doldurmaz; boş bir SEO kaydının yayımlanması kaynak doğrulama değerini gizleyebilir. Ev başlığı veya açıklaması değiştirilirken bu alanı koruyun. [Google sahiplik doğrulaması](https://support.google.com/webmasters/answer/9008080?hl=tr).

11 Kasım 09:19–09:24 UTC IndexNow incelemesinde kök dosyasının standart keşfiyle (`keyLocation` belirtilmeden) tek URL POST isteği 202 aldı. Aynı yöntemle 10.000 URL ve ardından 1.000 gerçek ürün adresi yine 403 döndürdü. Dolayısıyla tek istekteki 202, toplu doğrulama sorununun giderildiği anlamına gelmiyor; istek parametresinin neden olduğu da kanıtlanmadı. `Stats/get_site_errors` ile .com ve .com.tr için erişilebilen güncel hata kayıtlarında ilgili hata bulunmadı; gerçek Microsoft doğrulayıcısının ağ/HTTP erişiminin başarılı olduğu bu sonuçtan çıkarılamaz. Türkçe Turhost ve İngilizce Bing destek talebi metinleri `artifacts/seo-products/indexnow-turhost-destek-talebi.txt` ve `indexnow-bing-support-request.txt` olarak hazırlandı. Dış destek ekibine mesaj gönderilmedi; açık kullanıcı yetkisi ve gerekli insan doğrulaması tamamlanmadan gönderim yapılmaz. Son durum `indexnow-resolution-status.json`: kabul edilmiş toplu adres sayısı sıfır.

Kullanıcının **Turhost ve Bing'e ilet** onayından sonra iki destek talebi de 11 Kasım'da gerçekten gönderildi. Turhost müşteri hesabına kullanıcı giriş yaptı; `nodenohome.com.tr` cPanel hizmeti için **BDC-161-38545** numaralı kayıt oluşturuldu (`https://panel.turhost.com/support/ticket/view/2271844`). Açık iletişim formundaki ticari ileti izni işaretlenmedi; kayıt mevcut müşteri panelinden açıldı. Bing'e mevcut Google hesabıyla standart profil/e-posta oturumu açılarak destek formu gönderildi; Search Console verilerini okuma veya bütün siteleri içe aktarma yetkisi verilmedi. Bing'in **Your request has been successfully submitted** ekranı görüldü ve Gmail'deki `bwtsupport@microsoft.com` teyidi **UCM000007564499** numarasını doğruladı. Gönderim kanıtları `artifacts/seo-products/support/receipts.json`, `turhost-submitted.png` ve `bing-submitted.png` içindedir. İki talebin gönderilmiş olması IndexNow'ın sahipliği veya toplu URL listesini kabul ettiği anlamına gelmez; toplu bildirim hâlâ destek incelemesi beklemektedir.

## 12 Kasım 2026 Turhost yanıtı ve kontrollü tekrar

Kullanıcının paylaştığı Turhost yanıtı 11 Kasım 13:44 Türkiye saatiyle tarihlidir. Turhost, Bingbot ve Yandexbot'un varsayılan engellemesini bildirmiş, paket için izin verildiğini belirtmiş ve 12 saat sonra kontrol önermiştir. Bu, destek ekibinin bildirimidir; gerçek Microsoft doğrulayıcısının başarılı erişim kaydı olarak değerlendirilmez. Bing destek yanıtı bu çalışmada kontrol edilmedi.

12 Kasım 21:56 Türkiye saatiyle yapılan kontrollü tekrar öncesinde sahiplik dosyası, yönlendirmesiz HTTP 200 ve tam bayt içeriğiyle doğrulandı. Canlıdaki 22 alt haritada 11 dil için 45.826 canonical adres bulundu. Resmî global IndexNow kanalına ilk 10.000 adres yalnız bir kez gönderildi; yanıt yine **403 SiteVerificationNotCompleted** oldu, `Retry-After` başlığı bulunmadı. Kabul edilen toplu adres sayısı sıfırdır; kalan 35.826 adres gönderilmedi. Anahtar ve sunucu ayarı değiştirilmedi. Önce/sonra canlı sürüm SHA-256 değeri `faa7951843c79715f0580e3878e5df77f7f5670f01911f0059820f1cced97a8c` olarak aynı kaldı. Ön kontrol, gerçek adres listesi ve makbuz `artifacts/indexnow-turhost-recheck-20261112/` içindedir. `scripts/recheck-indexnow-after-turhost.py` makbuz bulunan aynı çalışmayı tekrar göndermeyi engeller.

Bot ayarının gerçek menüsü cPanel uygulama listesinden salt okunur olarak doğrulandı: **cPanel → Güvenlik → Turhost Bot Engelleme Modülü**. cPanel aramasına **Bot** yazılabilir. Jupiter yolu `frontend/jupiter/BlockBot/index.live.php` olup normal **IP Engelleyici** aracından ayrıdır. [Turhost'un resmî açıklamasında](https://destek.turhost.com/yandex-bot-nasil-engellenir/) işaretli kutular engellenen botları gösterir; tarama izni için Bingbot/Yandexbot engelleme kutuları boş olmalıdır. Ayar ekranındaki mevcut değerler bu çalışmada değiştirilmedi. Uygulama keşif kaydı `bot-module-discovery.json` içindedir.

İlk kontrollü denemeden sonra kullanıcı botları açtığını bildirdi. Sunucudan yeniden getirilen modül formunda Google, Yandex, Bingbot ve diğer dokuz botun **12 engelleme kutusunun tamamının boş** olduğu 22:02 Türkiye saatiyle salt okunur olarak doğrulandı. Bu yeni dış durum değişikliğinden sonra 22:03:07 Türkiye saatiyle yalnız bir 10.000 adreslik istek daha gönderildi; yanıt yine **403 SiteVerificationNotCompleted** oldu. Kabul edilen adres sıfır, kalan gönderilmemiş adres 35.826'dır; ardışık yeniden deneme yapılmadı. Bu ikinci denemenin bot ayarı, ön kontrol ve gerçek yanıt kayıtları ayrı `artifacts/indexnow-after-user-bot-open-20261112T190218Z/` klasöründedir. Önceki makbuz korunur. Bot engelleme kutularının boş olması doğrulandı; bunun gerçek Microsoft doğrulayıcısının uçtan uca erişimini veya IndexNow sahiplik kabulünü kanıtladığı söylenemez.


### 12/11/2026 — IndexNow doğrulaması ve toplu bildirim tamamlandı

Saat 23:10–23:11 (Europe/Istanbul), aynı mevcut anahtar ve aynı HTTPS sahiplik dosyasıyla resmî `https://yandex.com/indexnow` kanalına güncel 46.882 canonical adres gönderildi. Beş grup (10.000 + 10.000 + 10.000 + 10.000 + 6.882) ayrı ayrı HTTP 200 ve `success:true` aldı. Sahiplik kabulü ve toplu bildirim bu kanalda tamamlandı; 202 yanıtı tamamlanma sayılmadı. Kaynak canlı sürüm `68b66c81829d4b0a0d676520d754c013bdcc30dfe1d24bffec1cb2a356d59a20`, ürün sayısı 3.725. Gerçek makbuz: `artifacts/indexnow-live-diagnosis-20261112/yandex-bulk.json`; adresler ve hashleri aynı klasörün `preflight/` altındadır.

Bu sonuç anahtarın/dosyanın geçerli olduğunu kanıtlar. Önceki global/Bing kanalının neden doğrulamayı tamamlamadığı servis içi kayıtlar olmadan kesinleştirilemez; Bing kanalının ayrıca düzeldiği iddia edilmez. Resmî alternatif katılımcı kanal üzerinden çözüm uygulanmıştır. IndexNow, bir katılımcıya gönderilen bildirimlerin diğer katılımcılarla paylaşılacağını belirtir; bu, dizine ekleme veya sıralama garantisi değildir. Kaynak: https://www.indexnow.org/faq

Operasyonel gönderim betiklerinin varsayılanı doğrulanmış Yandex kanalıdır; mevcut anahtar korunur. Yönetim panelinin eski global endpoint kodu bu görevde değiştirilmedi ve panel kuyruğunun bu makbuzla eşitlendiği iddia edilmez. Eski başarısız kayıtlar silinmez. Anahtar yenileme teşhisinde ek bir test dosyası oluşturuldu, fakat etkin anahtar değiştirilmedi ve yeni anahtarla toplu bildirim yapılmadı.


## Otomatik yeni içerik bildirimi

Ürün veya kampanya yayımı mevcut yönetim kuyruğuna eklenir. Turhost'taki özel CLI çalışanı katalog yayın sürümü değiştiğinde, yönetimden yayım geldiğinde ve en geç beş dakikada bir gerçek müşteri kataloğunun özetini karşılaştırır. Yeni, güncellenmiş ve kaldırılmış canonical adresler kaydedilir. Taslak ürünler, özel hesap/sepet sayfaları ve henüz yayımlanmamış blog yazıları bildirilmez. Blog yayınından sonra dört gerçek dil adresi ile blog liste sayfaları aynı çalışmada kuyruğa girer.

Kuyruk ve içerik özetleri müşteri verisini silmeden mevcut özel `control.sqlite` içinde saklanır. Çalışan her dakika sunucuda çağrılır; bilgisayarın açık kalması gerekmez. Gecikme ve yeniden deneme alanları, HTTP sonucu ve son çalışma kaydı yönetim SEO ekranındaki IndexNow alanından okunur. HTTP 200 onaydır. HTTP 202 doğrulama bekliyor olarak tutulur; başarıya çevrilmez. 403 daha seyrek yeniden denenir, 429 için Retry-After dikkate alınır; ağ kesintisi/5xx artan bekleme süresi kullanır. En fazla 20 denemeden sonra kayıt inceleme gerektiren durumda kalır. Kesilen bir işlem 10 dakikalık işlem kiralaması ardından geri alınır; eşzamanlı manuel ve otomatik gönderim ortak kilit kullanır.

İlk kurulum, daha önce gerçekten HTTP 200 ile kabul edilmiş 46.882 adresi başlangıç referansı kabul eder; hepsini yeniden göndermek yerine aradaki yeni adresleri ve sonraki gerçek değişiklikleri gönderir. Fiyat ve stok için gerçek müşteri katalog verisi kullanılır; inceleme gerektiren/henüz bilinmeyen stok uydurulmaz.

Resmî Yandex IndexNow katılımcı kanalı kullanılır. Google IndexNow katılımcısı değildir; Google için daha önce Search Console'a gönderilen ana site haritası yeni ürün ve blog alt haritalarını sunar. Sosyal ağ profilleri NODENO alan adındaki URL'ler olmadığı için IndexNow kuyruğuna sokulmaz. Yedi profil, ilk HTML yanıtında ve JavaScript çalıştıktan sonraki Organization verisinde `sameAs` olarak belirtilir; bu bir sosyal profilin dizine alındığı veya sıralandığı teyidi değildir.

Kurulum ve canlı kanıtların tek kaynağı `artifacts/search-automation-20261112/` altındaki `deployment.json`, `timer.json`, `heartbeat-live.json`, `worker-local.json`, `browser-live.json` ve `social-markup-live.json` dosyalarıdır. Bir dosya henüz yoksa ilgili canlı kabul tamamlanmamıştır. Tamamlanmış bir kuyruk kaydı dizine girme veya sıralama garantisi değildir.


### Canlı kabul sonucu — otomatik bildirim

Kurulum, ilk sunucu çalışması ve sonraki boş çalışma gerçekten doğrulandı. İlk çalışmada 250 rehber sıraya alındı, iki rehber yayımlandı, 248 rehber takvimde kaldı; 38 yeni/değişmiş adresin gönderimi HTTP 200 aldı. Sonraki dakika değişmeyen içerik yeniden gönderilmedi. Ana haritada blog dahil 23 alt harita vardır. Blog mobil/masaüstü ve dört dilde 26 canlı tarayıcı kontrolünden geçti; yedi sosyal profil JavaScript çalıştıktan sonra da Organization sameAs içinde doğrulandı. 47 davranış testi geçti. Kanıt: `artifacts/search-automation-20261112/acceptance.json`. Google keşfi mevcut Search Console haritası üzerindendir; Google'a ürün/blog için uygun olmayan Indexing API çağrısı yapılmaz.

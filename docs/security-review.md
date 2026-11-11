# Güvenlik incelemesi ve düzeltme kanıtı

Son kaynak kodu incelemesi: 11 Kasım 2026, yerel geliştirme. Kapsam: oturum ve MFA, roller, müşteri/sepet/teklif/sipariş sahipliği, eski istek yanıtları, istek sınırları, Stripe bildirimi/iade kurtarma, kalıcı işler, raster yükleme, özel medya/sipariş belgesi erişimi, önbellek politikaları ve yerel geri yükleme aracı. Bu belge canlı ortama sızma testi veya hukuki uygunluk belgesi değildir. Bu belgeleme geçişinde kod/test değiştirilmedi ve yeni test başlatılmadı; ana ajanın son koşusu ile mevcut çıktılar esas alındı. Önceki hedef koşular tarihsel kanıttır; güncel kaynak ve sonuç kaydı [progress.md](progress.md) ile [test-evidence.md](test-evidence.md) içindedir.

## Önceki dondurulmuş yerel kontrol noktası

319 dosyalık kaynak manifestinin SHA-256 değeri `b48946568ebd671eea767b647f660f6c90c3a5f733e8ca14ee2b6232affebd46` olarak kaydedildi. Bu tarihsel sürümde 223 birim, 224 PostgreSQL kontrolü ve 94 E2E (Chromium 47 + WebKit 47) geçti; lint, strict typecheck, optimize build, artefakt sınırı ve 33 tabloluk yerel restore da başarılıdır. Ardından sepet/checkout sahiplik denetiminde TOCTOU (P1) ve başarılı HTTP durum kodlu bozuk JSON'un başarı sayılması (P2) bulundu; kaynak düzeltmeler için yeniden açıldı. Yeni 320 dosyalık sürüm 09:19 İstanbul itibarıyla ayrıca 246 birim/232 DB/94 E2E ve build/artefakt/33 tablo restore ile geçti. Güncel sonuçlar kanonik dosyalardadır; önceki kabul yeni kaynağa, gerçek sağlayıcıya veya production ortamına aktarılmaz.

## Bulunan açıklar

| Öncelik | Bulgu | Düzeltme ve gerçek durum |
|---|---|---|
| P1 | Hesapta MFA açık olmasının tüm eski oturumları doğrulanmış sayması | `auth.ts` artık `session_mfa` ile oturum ve kullanıcıya bağlı, dört saatlik doğrulama arıyor. İşaret yalnız resmi TOTP/kurtarma kodu doğrulaması sonucunda yazılıyor; kurulum öncesi işaretsiz diğer oturumlar iptal ediliyor. Ana ajan iki gerçek tarayıcı oturumu regresyonunun geçtiğini bildirdi; kalıcı test `tests/e2e/security.spec.ts` içindedir. |
| P1 | Checkout'un mevcut sepetin kullanıcı sahipliğini yeniden doğrulamaması | Ortak sepet/checkout sınırında `resolveCartOwner` kullanılıyor. A kullanıcısına bağlı kabiliyet B veya misafir için yeni boş token'a dönüşüyor. Ayrı PostgreSQL veritabanında gerçek A/B/misafir regresyonu **PASS**. |
| P1 | Gövde sınırının yalnız `Content-Length` değerine güvenmesi | `readBodyLimited/readJsonLimited` akışı okurken gerçek bayt sayısına göre durduruyor; geçersiz UTF-8 reddediliyor. Başlıksız büyük gövde ve Türkçe JSON birim regresyonları **PASS**. |
| P1 | Yeni sepet çereziyle rezervasyon kotasının aşılabilmesi | Sepet kotasına ek bağımsız ağ kotası `abuse.ts` içinde HMAC anahtarıyla, atomik PostgreSQL upsert üzerinden uygulanıyor. Aynı ağdan farklı çerezli 11 eşzamanlı isteğin tam 10'u geçti, biri 429 aldı. IPv6 /64 ve IPv4 eşlenik IPv6 yazımı aynı kotayı paylaşıyor. Güvenilir production sınırı eksikse DB yazmadan 503. Ayrı veritabanı regresyonu **PASS**. Ana API'nin checkout isteğinde bu fonksiyonu çağırdığı kaynakta doğrulandı; gerçek ters vekil/firewall sınırı yerel domain testinin kapsamı dışındadır. |
| P2 | Yedek hazırlığında erken hata sonrası şifrelenmemiş `.dump` kalması | Ana ajan tüm dump/şifreleme/geri yükleme yaşam döngüsünü dış `finally` temizliğine aldı. Kod değişikliği görüldü; bu alt görevin kanıtı hata enjeksiyonu veya yeni geri yükleme çalıştırması içermez. Son doğrulama ana ajana aittir. |

Stripe mutabakatının yalnız işleyicisi bulunması ayrıca P1 olarak bildirildi. Daha sonra eklenen `scripts/scheduler.ts`, Stripe seçiliyken dakikalık tekil anahtarla kalıcı `payment.reconcile` işi oluşturuyor; bu nedenle “hiç sıraya alınmıyor” kod bulgusu giderildi. Gerçek sağlayıcı sorgusu ve kayıp webhook senaryosunun dış servis testi, kabul edilmiş Stripe hesabı/test erişimi olmadan doğrulanmış sayılmaz.

## Son incelemede bulunan ve kodda ele alınan noktalar

| Öncelik | Bulgu | Kaynakta görülen düzeltme | Kanıt sınırı |
|---|---|---|---|
| P1 | Set iadesinin bileşen yerine ana set SKU'suna stok eklemesi | `commerce/return-stock.ts`, siparişin değişmez `bundleComponents` snapshot'ını kullanır; miktarları çarpar, sıralı depo kilitleri altında bileşen karantina satırları oluşturur. QC yalnız bu kayıtları satışa döndürebilir. Doğrudan karantina boşaltma, incelemesiz iade miktarını tüketemez. | Son dondurulmuş sürümün operasyon/set regresyonları geçti; komut ve kapsam kanonik test kaydındadır. |
| P1 | Yayımdaki ürünün güvenlik/üretici alanlarını değiştirirken yayın onayının korunması | `commerce/admin.ts`, gerçek alan/çeviri değişikliğini kilitli ürün kaydıyla karşılaştırır; yayımdaki kaydı incelemeye çeker ve varyantların ülke uygunluk onayını kaldırır. Teknik varyant değişiklikleri de belge/taşıma onaylarını iptal eder. | Düzeltme kaynakta görüldü; son regresyon sonucu ana ilerleme kaydına aittir. |
| P1 | Sonucu bilinmeyen eski Stripe iadesinin yeniden POST edilerek ikinci iadeye yol açabilmesi | Worker, kayıtlı iade referansını sorgular; referans yoksa tahsilat iadelerinde `sexsogate_refund_key` arar. `assertRefundCreationWindow`, 23 saat veya daha eski belirsiz isteği yeni POST'a dönüştürmez. Scheduler referansı olmayan bekleyen iadeleri de mutabakat kapsamına alır. | `tests/unit/provider-retry.test.ts` bu sınırı kapsar; burada çalıştırılmadı. Gerçek Stripe API/zaman aşımı/kurtarma testi yapılmadı. Metadata araması ilk en fazla 100 iadeyle sınırlıdır; uzun geçmişte otomatik kurtarma tamamlanmış sayılmaz. |
| P2 | SDK hata mesajındaki anahtar veya müşteri ayrıntısının ortak API yanıtına taşınabilmesi | `security.ts` içindeki `publicFailure`, yalnız uygulamanın `HttpError` sınıfını açık mesajla döndürür. Diğer hatalar 500 ve genel `SERVICE_UNAVAILABLE` olur; SDK `statusCode/code/message` alanları kopyalanmaz. Ortak ticaret route'u bu işlevi kullanır. | `tests/unit/error-privacy.test.ts` son birim koşusunda geçti. Özel medya/upload/webhook uçlarının genel hata yanıtları ayrıca kaynakta incelendi. |

Stripe iadeleri önce `pending` ve kalıcı `refund.stripe` işi olarak kaydedilir. Doğrulanmış API sonucu gelmeden ödeme iade toplamı artırılmaz. `finalizeProviderRefund`, iade/ödeme satırlarını kilitler; sağlayıcı referansını ve toplam tutarı denetler, aynı başarılı sonucu ikinci kez toplama eklemez. Worker ve scheduler'ın gerçek dağıtımda sürekli çalışması gerekir. Bu kaynak incelemesi gerçek hesapta iade kabulü, itiraz yönetimi veya dış servis kesintisi kanıtı değildir.

İade sipariş/iade ekranından kalıcı kuyruğa ve sağlayıcı durum makinesine bağlanmıştır; “gerçek iade iş akışına bağlı değil” şeklindeki eski kapsam ifadesi geçerli değildir. Finans/yönetici isteği mevcut parolayı yeniden doğrular. Operations integration, sağlayıcıya gönderilecek iadenin doğrulanmış sonuçtan önce pending kalmasını, yanlış referansı ve tekrar finalize sonucunda ikinci toplam oluşmamasını kapsar. Son bağımsız operasyon koşusunda 14/14 kontrol geçti. Bu DB kanıtı gerçek Stripe API, sandbox iade veya ağ kesintisi deneyi değildir.

## Teklif snapshot'ı ve eski yanıtların sınırı

| Öncelik | Bulgu | Düzeltme ve doğrulama |
|---|---|---|
| P1 | Teklif sahipliğinin API'de snapshot dışında okunması | `quoteCheckout(token, input, callerUserId)`, `REPEATABLE READ READ ONLY` transaction'ında sepetin `user_id` değerini ve fiyatlamayı aynı snapshot'ta okur. API dışındaki eski SELECT kaldırıldı. Anonim kontrolün ardından üyeye bağlama/birleştirme ve snapshot kurulduktan sonraki birleştirme gerçek DB bariyerleriyle doğrulandı; yeni özel sepet satırları eski anonim isteğe dönmez. |
| P1 | Gecikmiş checkout yanıtının başka hesaba geçildikten sonra eski ödeme/takip bağlantısını açması | Hesap/ülke anahtarlı ekran, active ref, aynı AbortController, iptal ve başlangıç yolu kontrollerini başarı/hata yollarında uygular. Gerçek sunucu sonucu geciktirilip A çıkışı ve B girişi sonrasında bırakılan tarayıcı regresyonu iki motorda geçti. |
| P2 | Sandbox ödeme yanıtının kapatılan ekranı yeniden yönlendirmesi | TestPayment hesap/sipariş/token anahtarında ayrılır; sipariş GET ve ödeme POST iptal/eski yanıt kontrolleri kullanır. Gerçek test ödeme sonucu sonrası gecikmiş yanıt regresyonu iki motorda geçti. Test adaptörü production'da kapalı kalır. |
| P1 | Eski A oturum yanıtının yeni B oturumunu ekranda ezmesi | `store-context.tsx`, oturum ve sepet için ayrı artan istek nesli ve abort uygular; sahip değişiminde eski sepet isteğini ve sayacı geçersizleştirir. `.local/session-refresh-red.log` ilk RED'i korur; aynı test son Chromium/WebKit koşusunda GREEN oldu. |

409 ile değişmiş/süresi dolmuş teklif sonrası arayüz güncel sunucu özetini getirir; ikinci açık tık olmadan siparişi otomatik yeniden başlatmaz. Teklif DTO'sunda müşteri satır fiyatı/indirim/vergi/toplam vardır, maliyet veya tedarikçi alanı yoktur; özel değerlendirme izi HMAC ile bağlıdır. Teklif ve checkout aynı-origin/gövde sınırını korur; sepet ve HMAC ağ kotaları amaç bazında ayrıdır, yanıtlar `private, no-store` olur. İstemci fetch iptali sunucuda tamamlanmış ödeme/siparişi geri almaz. Kaynak ve yerel test kanıtı [test-evidence.md](test-evidence.md) içindedir; gerçek Stripe gecikmesi/kesintisi bu offline kabulün kapsamı değildir.

## Personel sipariş ayrıntısı ve miktar sınırı

`017_staff_fulfillment.sql`, kalıcı görev, görev satırı ve aktör/içerik bağlı komut kayıtlarını ekler. `GET/POST /api/admin/orders/{id}`, her istekte gerçek MFA oturumu ve rol denetimi yapar. Pazarlama/katalog/müşteri bu personel endpoint'ine erişemez. Depo yalnız doğrulanmış ödemeli siparişin SKU/adet/paketleri ile gerekli teslimat adı/adresi/telefonunu alır; e-posta, maliyet/kârlılık, fiyat/toplam, ödeme referansı veya geçmiş API yanıtına eklenmez. Finans yanıtında müşteri adresi/e-postası yoktur; destek rolü maliyet ve sağlayıcı ödeme referansını almaz.

Sipariş satırı kilidi altında kalan adet; sevk edilmiş miktar ve diğer aktif görevler düşülerek denetlenir. Toplama ve paketleme ayrı SKU/kayıtlı barkod doğrulaması gerektirir. Yanlış kod, fazla adet, paketlemeden sevk ve ödeme durumu değişikliği reddedilir. Aynı komut ikinci kez miktar artırmaz. Doğrulanmış paket, mevcut manuel sevk işlevine aynı transaction içinde bağlanır. Eski doğrudan manuel sevk yolu görev yokken korunur; aktif göreve ayrılmış adedi tüketemez ve barkod doğrulaması yapmış sayılmaz.

Tarihsel hedef kanıtı: `scripts/staff-orders-integration.ts` eksik modülle RED görüldükten sonra **11/11** geçti; aktör/rol/MFA ve veri küçültme, ödenmemiş sipariş, eşzamanlı miktar yarışı, yanlış kod/adet, iki aşama, tekrar, iptal/durum değişimi ve vergi sınıfı sınırları kapsandı. `tests/e2e/staff-orders.spec.ts` hedef koşusu **Chromium + WebKit 2/2, 9,9 saniye, retry 0**: gerçek oturum/MFA, minimal HTTP yanıtı, gerçek form akışı ve 390 px taşma kontrolü. Personel akışı son toplu E2E/build kabulünde de geçti. Fiziksel okuyucu/depo kabulü veya setin her bileşenini ayrı okutma kanıtı yoktur.

Vergi sınıfı, create/update/GET ve formlarda trim edilmiş 1–100 karakterle kaydedilir; varsayılan açık değer `*` olur. Sınıf değişimi teknik değişiklik sayılıp yayın/uygunluk onayını yeniden incelemeye çeker. Gerçek ülke/vergi/hukuk onayı yerine geçmez.

## SEO ve sayısal girdi incelemesi

Yeni SEO yönetim endpoint'i ve sunucu işlevleri yönetici/katalog/pazarlama rolü + gerçek MFA ister; mutasyon ayrıca same-origin ve sınırlı JSON gövdesi kullanır. Dil başına slug/metadata/alt değişiklikleri audit edilir. URL çakışmaları ve yönlendirmeler ortak advisory kilidi altında uygulanır. Yalnız güvenli site içi açık hedefler kabul edilir; özel hesap/API/sipariş yolları, dış adresler, döngü/zincir ve kapanmış hedefler reddedilir. Yönlendirme okunurken de hedefin hâlâ açık olduğu doğrulanır.

Son incelemedeki açık ürün kapsamı düzeltmesi; aktif kategori, aktif varyant ve gerektiğinde İngilizce içerik koşulunu canonical/sitemap/yönlendirme için ortaklaştırdı. Fixture ürünler production ve sitemap dışında kalır. Gösterim para birimi tahsilat para biriminden farklıysa o tutarla `Offer` yayımlanmaz; ürün açıklaması satın alınabilir tahsilat iddiasına çevrilmez. Bu kod, arama motoru schema/indeks kabulü değildir.

Sayfa girdisindeki `NaN`/`Infinity` değerlerini `|| 1` ile sessizce maskeleyen yol kaldırıldı. SEO raporu yalnız 1–100.000 arasında güvenli tam sayı kabul eder. Son izole SEO entegrasyonu 7/7 geçti; bozuk sayfa değerleri `NaN`, `Infinity`, `-1`, `0`, `1.2` ve `100001` kapsamda reddedildi. Katalog HTTP kontrolünde bozuk sayfa/fiyat için altı istek 400 verdi. Bu hedef sonuçlar son tam toplu koşunun yerine geçmez.

Favori gösterim tercihi doğrulaması da mutasyondan önce yapılır. HTTP regresyonunda geçersiz para birimi önce 400 yerine 200 verdi; düzeltme sonrası 400 ve sıfır favori yazımı iki motorda personel E2E'si içinde doğrulandı. Hatalı girdi, kısmen tamamlanmış bir mutasyon olarak bırakılmadı.

## Medya ve özel belge erişimi

`/api/admin/media` listeleme/yükleme için yönetici, katalog veya pazarlama rolü ve gerçek MFA oturumu ister. POST aynı origin kontrolünden geçer; akış gövde sınırı 9 MB, raster dosya sınırı 8 MB'dir. PNG/JPEG/WebP imzası kontrol edilir; Sharp 20 milyon piksel sınırı uygular, yönü düzeltip görseli en fazla 1800×1800 WebP olarak yeniden kodlar. SVG/HTML kabul edilmez. Dosya anahtarı istemci isminden türetilmez; UUID ile sunucuda üretilir. Hak kaynağı ve aktör audit kaydında tutulur.

`/uploads/{uuid}.webp`, DB'de kayıtlı nesneyi sunar. Yayımlanmış ürüne bağlı olmayan görsel yalnız yönetici/katalog/pazarlama rolü ve MFA ile erişilebilir; misafire 404 döner. Yayımlanmış katalog görseli müşteri için okunabilir, fakat nesne deposu özel kalır. Yanıt `private, no-store` ve `nosniff` taşır. S3 Put/Get güvenli nesne anahtarı kullanır; yerel depolama production'da reddedilir. Gerçek bucket policy ve tam medya yedeği henüz doğrulanmadı. `tests/e2e/admin.spec.ts` içindeki SVG reddi, gerçek PNG yükleme, yetkili okuma ve misafir 404 senaryoları son yerel toplu koşuda geçti.

`/api/orders/{id}/document`, önce `getOrder` üzerinden kayıt sahibi oturumunu veya güvenli misafir token'ını doğrular; yalnız sipariş numarası yetmez. Belge içeriği güncel hukuk kaydından yeniden üretilmez: siparişin `order_agreements` başlık/gövde/sürüm/hash/accepted_at snapshot'ı okunur. PDF ve JSON yanıtları `private, no-store` ve `noindex,nofollow` taşır. PDF resmî fatura değildir. Türkçe metin çıkarımı ve iki sayfa görsel kontrolü önceki ilerleme kaydındadır; gerçek müşteriye e-posta teslimatı kanıtlanmış değildir.

## Sunucu ve önbellek sınırı

`src/proxy.ts` içindeki `/en` yeniden yazımı yalnız dil/URL seçer; kimlik veya erişim izni vermez. API, medya ve özel sipariş belgesi kendi sunucu denetimini yapar. API yanıtları ile TR/EN hesap/sepet/ödeme/sipariş/yönetim/favori alanları özel önbellek ve indeksleme başlıklarına sahiptir. CSP, `nosniff`, `DENY` frame politikası ve `no-referrer` yapılandırılmıştır; bu başlıklar erişim denetiminin yerine geçmez.

`scripts/start.mjs`, standalone çıktıya public/static/PDF font varlıklarını kopyalar; açık `APP_ENV` ister ve varsayılan loopback adresine bağlanır. Development/test'te yerel origin/depolama yolu ayarlar; üretim sırlarını üretmez veya canlıyı etkinleştirmez. Bu helper, gerçek ters vekil/firewall, secret manager veya worker/scheduler kurulumunun doğrulandığı anlamına gelmez.

Geliştirme HMR incelemesinde, sekiz saniyelik dosya izlemede `.next` dışı kaynak değişimi 0 iken 150'den fazla yaklaşık 1 ms derleme ve trace'te 162 yeniden yükleme görüldü. Oturum/cart/market istekleri gezinmelerle iptal oluyordu; geliştirme derleyici döngüsü ayrı teşhis edildi. [Resmî Next CLI](https://nextjs.org/docs/app/api-reference/cli/next) tarafından desteklenen `next dev --webpack` kullanıldı. Dev `.next-local`, build `.next`; optimize `next build` varsayılan Turbopack olarak kaldı. Webpack üzerinde personel ve yeniden yüklenmeme hedefleri geçti. Son dondurulmuş sürümün optimize E2E/build kabulü de kayıtlıdır; test/TypeScript/güvenlik kontrolü kapatılmadı. HMR sorunu, ayrıca gerçek RED ile bulunan eski oturum yanıtı yarışını açıklayıp geçersiz kılmaz; o sorun ayrı istek nesli düzeltmesiyle kapatıldı.

## Ağ güven sınırı

Production ve staging checkout için tam alan adları:

- `APP_ENV=production` veya `staging`
- `TRUSTED_PROXY_ENABLED=true`
- `TRUSTED_CLIENT_IP_HEADER=x-real-ip`
- Sunucuya ait en az 32 karakterlik `BETTER_AUTH_SECRET`

`TRUSTED_PROXY_ENABLED` operatörün yapılandırma beyanıdır; istemcinin güvenilir olduğunu tek başına kanıtlamaz. Web uygulamasının origin portu yalnız ters vekilin erişebileceği özel ağda veya loopback üzerinde tutulmalı; güvenlik duvarı/doğrudan origin erişimi kapatılmalıdır. Ters vekil istemciden gelen `X-Real-IP` başlığını silip kendi doğruladığı bağlantı adresinden yeniden yazmalıdır. `X-Forwarded-For` zinciri uygulamada kimlik kaynağı kabul edilmez. Bu dağıtım sınırı gerçek ortamda doğrulanmadan satış açılmaz. Vekil erişim günlüklerinin ayrıca veri minimizasyonu gerektirdiği unutulmamalıdır.

Geçerli tek IP yoksa 503 döner. IPv4 adresi tek kota; IPv6 adresleri ilk 64 bite göre ortak kota; IPv4 eşlenik IPv6 aynı IPv4 kotasıdır. Veritabanında ham IP veya alt ağ tutulmaz: yalnız sunucu secret'ıyla alanı ayrılmış HMAC-SHA256 anahtarı ve kısa ömürlü sayaç vardır. Production/staging sınırı 10 checkout isteği/dakikadır. Development/test için yalnız yerel loopback uygulamasına yönelik ortak 100/dakika kotası kullanılır; bu mod dış ağa açık dağıtım ayarı değildir. Ayrı ağlardan dağıtılmış kötüye kullanıma sıfır risk garantisi verilmez.

## Önceki yerel alt görevde çalıştırılan kanıt

1. `npx vitest run tests/unit/abuse.test.ts`: önce modül bulunamadığı için **RED**, uygulama sonrasında **6/6 PASS**.
2. `npx tsx --env-file=.env.local scripts/security-boundary-integration.ts`: **4/4 PASS**. Rastgele adlandırılmış yerel `sexsogate_<rastgele>_boundary_test` veritabanı oluşturuldu, migration uygulandı ve sonunda kaldırıldı. Ana geliştirme/test veritabanı sıfırlanmadı.
3. `npx eslint src/server/abuse.ts tests/unit/abuse.test.ts scripts/security-boundary-integration.ts --max-warnings=0`: **PASS**, çıktı yok ve çıkış kodu 0.
4. `npx vitest run tests/unit/abuse.test.ts tests/unit/body-limit.test.ts tests/unit/security.test.ts`: **3 dosya, 12/12 PASS**; çıktı doğrudan okundu.

İzole entegrasyonun dört kontrolü: eşzamanlı ağ kotası, IPv6/IPv4 eşlenik kimlik, eksik production sınırı ve süresi dolmuş pencere, A/B/misafir sepet ayrımı. Her başarısız istekte tahsilat veya stok rezervasyonu oluşturulmadan sınırda durulması hedeflenir; ana API bu kontrolü checkout işleminden önce çağırmalıdır.

## İncelenen ve tamamlanmış sayılmayan noktalar

Stripe ham gövde imzası, ortam/tutar/para/sipariş ve oturum referansı denetimi; kalıcı webhook kaydı; iş tekrarı; sunucu rol/sahiplik denetimi; `private,no-store`; PAN/CVV saklamama incelendi. Bu incelemede imza aşımı veya kart verisi saklama yolu bulunmadı. Gerçek Stripe tahsilat/iade, taşıyıcı/fatura kabulü, gerçek cihaz, canlı ters vekil/firewall sınırı ve production geri yükleme testi yapılmış değildir. Yerel test iadesi gerçek sağlayıcı iadesi diye sunulmaz. Ayrı şirket ortamına veya başka projenin verisine bağlanılmadı.

`scripts/backup-verify.ts` yalnız localhost ve `_test` veritabanına izin verir. Şifreli dump'ı yeni izole DB'ye yükler; 33 kritik tablonun count/hash değerini karşılaştırır ve tek örnek marka medyasının şifreleme/çözme hash'ini denetler. Son rapor satın alma/kabul/lot ilişkilerini de içerir ve PASS'tir; boş tabloların gerçek sayıları raporda korunur. Geçici açık dump dış `finally` içinde temizlenir. Yerel PASS; üretim yedeği, bütün S3 medyası, saklama/erişim politikası veya staging'e geri yükleme tatbikatı anlamına gelmez.

Önceki dondurulmuş sürümün yerel lint/typecheck/birim/entegrasyon/E2E/build/artefakt sonuçları kayıtlıdır; sahiplik/JSON düzeltmeleri de yeni tam koşuda geçti; güncel kabul kanonik kayıttadır. Dağıtım için ayrıca kabul edilmiş sağlayıcı hesabında gerçek sandbox senaryoları, özel origin sınırı, üretim sır yönetimi ve şifreli DB/tam medya geri yükleme tatbikatı gerekir. Gerçek S3/SMTP/Stripe sandbox, staging ve remote CI çalıştırması henüz yoktur. Yeni kaynak değişikliği ilgili kabulü yenilemeyi gerektirir; kod düzeltmesi çalıştırılmamış testi geçmiş saydırmaz.

## 022–024 fazı inceleme bulguları

- Logical set üst SKU'suna stok/mal kabulü açığı RED ile doğrulandı. Ortak kilit sırası ve set üst koduna fiziksel stok yazma engeli, stok↔set dönüşümü yarışları ve işlem rollback kontrolleriyle kapatıldı. Geçmiş fiziksel satış/bileşen/iade kaydı olan SKU logical sete çevrilemez; yeni SKU gerekir. Geçmiş set siparişinin bileşen snapshot'ı korunur.
- Müşteri adresleri owner WHERE koşuluyla CRUD yapar, liste 50 kayıtla sınırlıdır. İlk GET veya başka mutasyonun gecikmesi için generation ve ortak işlem kilidi vardır; Account/Checkout oturum/ülke anahtarıyla özel taslağı sıfırlar. Profil içeriği değişmez sürümdür, kritik onay MFA+parola ister. Son tarayıcı kabulü ana kanıtta kaydedilir.
- Sosyal boş üçüncü sayfanın toplamı kaybetmesi tek SQL count/page snapshot'ıyla düzeltildi; 26 kaynak regresyonu dört türde geçti. Dosya okuması root/byte/timeout sınırındadır, dış URL çekimi veya kullanıcı SVG çalıştırması yoktur.
- Import'ta özel yerel dosya doğrulaması ortak sınırlı adaptöre taşındı; 8MiB üstü dosya önce kabul edilerek RED, düzeltme sonrası reddedilerek GREEN oldu. Next'in geniş dinamik filesystem trace'i derleme paketine docs/test raporları alıyordu. Bu yerel artefakt dışarı yayımlanmadı. Dar runtime okuması, açık trace dışlamaları ve bağımsız artefakt kontrolü eklendi; yeni optimize derlemenin gerçek sonucu kanonik test kaydına aittir.

Bunlar bağımsız sızma testi, gerçek işletme kabulü veya dış servis güvenlik denetimi değildir. Doğrulama komutları ve başarısız ilk koşular [test-evidence.md](test-evidence.md) içinde tutulur.

## Son inceleme: sepet sahipliği ve belirsiz kabul yanıtı

- Dış API sahiplik kontrolü ile gerçek sepet okuması/yazımı arasında anonim sepet üyeye bağlanabiliyordu. Eski kodda gerçek birleşme sonrası anonim okuma ve aynı tutarlı tekliften checkout ayrı `Missing expected rejection` RED verdi. `getCart` sahibi, satırları ve stok projeksiyonunu aynı read-only repeatable-read connection'ında okur. `setCartItem` ekleme/silme/yanıtını sepet satır kilidi ve sahiplik kontrolü altında yapar. Checkout aynı kilidi kullanır; verified principal kimliği HTTP oturumundan açık parametreyle gelir. JSON kimlik alanı kabul edilmez.
- Hesap birleşmesi eski sepeti anonimleştirdiğinde eski siparişin sahibi değişmez. Mevcut siparişin `user_id` denetimi idempotent tekrar dönüşünden önce ayrıca yapılır. Ayrılmış eski sepetten anonim/B tekrarının RED→GREEN regresyonu vardır; doğru A tekrarı ve ilk checkout'un değişmez sahipliği korunur. Boundary10 ve quote13 kontrolleri gerçek DB sıraları/kilit bariyerleriyle geçti.
- Başarılı HTTP durumu içindeki bozuk/boş JSON, eski istemci helper'ında hata nesnesi gibi çözülüyor ve mal kabulü başarı görünüyordu. Yeni `ApiResponseError` belirsizliği korur; kabul ekranı gerçek yeni-kayıt/idempotent-tekrar sonuç sözleşmesini ayrıca doğrular. Eksik/geçersiz sonuçta başarı gösterilmez; aynı açık önizlemede yeni UUID veya düzenleme açılmaz. Aynı gövde/anahtar yeniden denenir; eski `{id, duplicate: true}` yanıtı desteklenir. Native AbortError korunur, ham ağ/validator ayrıntıları kullanıcıya sızmaz. API helper'ının bütün genel yanıtlarına alan şeması eklenmiş değildir; bu katı sonuç doğrulaması mal kabulüne aittir.

Son kaynak statik incelemesinde ek somut kritik bulgu bulunmadı; bu bağımsız penetrasyon kabulü değildir. Yeni genel tarayıcı/build/restore sonucu, eski94 sonucundan ayrılarak [kanonik kanıtta](test-evidence.md) izlenir.

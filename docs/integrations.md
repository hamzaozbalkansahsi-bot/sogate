# Entegrasyonlar ve güvenli yapılandırma

Kaynak kodu kontrolü: 11 Kasım 2026. Adaptör kodunun bulunması işletme hesabının, ürün kategorisinin veya hedef ülkenin kabul edildiği anlamına gelmez. Canlı satış kapalıdır. Son doğrulanmış kaynak sürümü ve komut sonuçları [progress.md](progress.md) ile [test-evidence.md](test-evidence.md) içinde tutulur; yerel sonuçlar gerçek dış servis kabulüne dönüştürülmez.

| Bağlantı | Uygulanan işlem | Gerçek durum / açık iş |
|---|---|---|
| PostgreSQL 18.6 | Yerel native cluster, ayrı geliştirme/test DB, migration ve transaction | Yerelde çalışıyor; uzak/staging/production DB bağlantısı kurulmadı. |
| Better Auth 1.7.20 | Parola, oturum, TOTP, yedek kod, dört saatlik oturuma bağlı MFA, şifreli auth e-posta işi | Yerel gerçek oturum akışı var; SMTP teslimatı ve üretim güvenlik yapılandırması bekliyor. |
| Yerel test ödeme | İmzalı HMAC olay, replay, başarısızlık/süre sonu/geç başarı, test iade | Yalnız development/test. Production test adaptörünü reddeder; gerçek tahsilat değildir. |
| Sipariş toplamı teklifi | Aynı sunucu fiyat/vergi/kupon/kargo hesabı, yazmasız snapshot, sepete bağlı beş dakikalık HMAC, değişen koşulda yeniden inceleme | Yerel DB ve optimize tarayıcı akışı doğrulandı. Teklif stok/fiyat rezervasyonu veya gerçek ödeme değildir; sonraki sahiplik düzeltmesinin toplu kabulü kanonik test kaydında ayrıca izlenir. |
| Lotlu satın alma kabulü | PO kalanına atomik normal/lotlu mal kabulü, karantina, aktöre bağlı tekrar, lot-kabul-hareket kaynak zinciri | 025 yerel şemada uygulanmış; sunucu ve Chromium/WebKit yönetim akışı geçti. Gerçek irsaliye/üretici etiketi, fiziksel depo provası, barkod-lot paket eşleştirmesi ve tedarikçi API'si doğrulanmadı. |
| Stripe 23.1.0 resmî SDK | Hosted Checkout, kayıtlı oturumu sürdürme, ham webhook imzası, ortam/tutar/para/sipariş/oturum eşleme, durable inbox, ödeme mutabakatı, iade outbox ve sonuç mutabakatı | Kod ve yerel/offline senaryolar var. Gerçek API anahtarı/hesap erişimi, kategori ve hesap ülkesi kabulü yok. Gerçek sandbox Checkout/webhook/iade/kesinti testi yapılmadı. |
| Manuel kargo | Gerçek taşıyıcı/takip bilgisi, kısmi paket, miktar ve tekrar denetimi; ürün/ülke taşıma onayı | Yerel akış. Taşıyıcı API'si, etiket, gerçek tarife ve pil/sıvı kabulü bekliyor. |
| Personel sipariş/paket akışı | Rol başına küçültülmüş sipariş API'si, kalıcı toplama/paketleme görevi, iki SKU/barkod kontrolü ve mevcut manuel sevkle atomik bağlantı | 017 migration; izole DB 11/11 ve Chromium/WebKit hedefi 2/2 geçti. Gerçek okuyucu/depo provası ve taşıyıcı API'si yok. Eski doğrudan manuel yol görev yokken korunur; barkod kontrolü yapmış sayılmaz. |
| Fatura | InvoiceProvider sınırı, yetkili dış sistem belge referansı kaydı ve sipariş bağlantısı | Satıcı bilgisi ve gerçek sağlayıcı bağlantısı yok; e-Fatura/e-Arşiv düzenlenmez. Sipariş PDF'si resmî fatura değildir. |
| Yerel medya | Yetkili raster yükleme, hak kaynağı kaydı, WebP yeniden kodlama, DB/audit, yayın durumuna göre özel erişim | Yükleme ve özel erişim yerel uygulamada çalışıyor. Gerçek katalog görseli/hak doğrulaması operasyona aittir. Son toplu koşu sonucu progress.md içinde ayrıca izlenir. |
| S3 uyumlu depolama | Özel nesne Put/Get, güvenli nesne anahtarı, sınırlı byte/süre/akış okuması, AES256 şifreleme talebi | Gerçek bucket/hesap erişimi yok. Yerel filesystem adaptörü production'da reddedilir; bucket policy, şifreleme ve tam medya yedeği doğrulanmadı. |
| E-posta | Şifreli auth işleri, ürün adı içermeyen sipariş konusu, SMTP worker ve tekrar deneme | SMTP yok; başarısız iş gönderildi sayılmaz. Gerçek teslimat, SPF/DKIM/DMARC ve iletişim adresi doğrulanmadı. |
| Pazaryerleri | Kanal/SKU/fiyat/kota şeması ve kapalı adaptör sınırı | Trendyol/Hepsiburada/Amazon/eBay ürün ve API kabulü yok; publish, sipariş içe alma ve stok eşitleme aktif değil. |
| Tedarikçi XML/API | İnceleme/ithalat sınırı; CSV/XLSX için gerçek önizleme ve taslak commit | Dış fetch kapalı; aktif XML/API bağlantısı yok. Tedarikçi stoğu kendi depo stoğuna dönüşmez. |
| Arama/SEO/analitik | Sunucu katalog arama; dil başına SSR metadata, ürün slug/alt metin editörü, canonical/hreflang, güvenli 308 yönlendirme ve bölünmüş sitemap index | Yerel DB ve tarayıcı kontrolleri son başarılı kontrol noktasına dahil. Tam site crawler'ı, gerçek rich-results/indeks denetimi ve Search Console/Bing hesabı yok. Reklam analitiği ve session replay yüklenmez. |

## Yerel teklif, sepet ve mal kabulü

`POST /api/checkout/quote` mevcut sepeti aynı snapshot'ta doğrulanmış oturum sahibine göre okur; finansal kayıt oluşturmaz. Teklif ve yeni sipariş aynı hesaplayıcıyı kullanır. Checkout kilit altında yeniden hesaplar; fiyat, vergi, kupon, kargo, ürün metni veya bağlı koşullar değişince istemci yeni özeti açıkça incelemelidir. Teklif anahtarı idempotency iş girdisine katılmaz. Sepet okuması sahiplik ve satırları aynı snapshot'ta; sepet yazımı ve checkout ise hesap birleşmesiyle aynı satır kilidi altında denetler. Üyeden ayrılmış eski sepet, geçmiş siparişin sahibini değiştirmez veya anonim tekrar yetkisi üretmez. Son sahiplik regresyonları ve kaynak sürümü kanonik test kaydında izlenir. Ayrıntı: [checkout-guide.md](checkout-guide.md).

`POST /api/admin/purchases` üzerinden lotlu kabul bir dış servis bağlantısı değildir. PO kalan miktarı, normal/lot stokları, hareket, kaynak bağı ve kabul sayacı tek transaction'da güncellenir; tek hatalı satır karma kabulü geri alır. Aynı aktör/anahtar/içerik aynı kabulü döndürür; doğrudan lot kabulüyle aynı anahtar ikinci stok yazamaz. Kaynak paneli gerçek ilişkileri maliyetsiz whitelist ile gösterir; aynı üretici lotunun bütün kaynaklarını listeler, belirli bir satılmış adedi tek PO'ya atamaz. Kaynak referansı dış belgenin otomatik doğrulandığı anlamına gelmez. Tedarikçiye iade/mahsup, lotu bilinmeyen iade ve çok depolu transfer ayrıca açıktır. Ayrıntı: [purchase-lot-guide.md](purchase-lot-guide.md).

## Stripe ödeme ve iade sınırları

Checkout sağlayıcının güvenli sayfasına yönlenir; PAN/CVV uygulamaya alınmaz. Tarayıcı dönüşü ödeme kanıtı değildir. Ham gövdeden doğrulanan Stripe olayı önce kalıcı inbox'a, ardından worker işine kaydedilir; sipariş ve stok sonucu sunucudaki doğrulanmış olayla uygulanır. Scheduler, Stripe seçiliyken dakikalık tekil anahtarla `payment.reconcile` ve `refund.reconcile` işleri oluşturur. Worker ve scheduler web sürecinden ayrı çalışmalıdır.

Gerçek sağlayıcı için iade isteği DB'de `pending` ve outbox'ta `refund.stripe` olarak kalır; sağlayıcıdan doğrulanmış sonuç gelmeden tahsilatın iade toplamı artırılmaz. Worker:

1. Bilinen iade referansını API'den sorgular.
2. Yanıtı kaybolmuş bir işlem için tahsilatın iadelerinde `sexsogate_refund_key` metadata'sını arar; ilk en fazla 100 iade incelenir.
3. Uygun yeni isteği `refund:{id}` idempotency anahtarıyla gönderir. Sonucu bilinmeyen 23 saat veya daha eski kayıt yeniden POST edilmez; mutabakat/operatör incelemesi gerekir.
4. Tutar ve para birimini kontrol edip kilitli, tekrar güvenli sonuçlandırma işlevini çağırır. Başarısızlık/yeniden deneme iş kuyruğunda görünür.

Bu korumalar gerçek Stripe API uçtan uca kanıtı değildir. Webhook sırası, uzun kesinti, sağlayıcı hatası, sayfalama gerektiren iade geçmişi, itiraz/dispute iş akışı ve operatör kurtarma prosedürü kabul edilmiş hesapta ayrıca doğrulanmalıdır. Dispute/refund olayının kaydedilmesi tamamlanmış itiraz yönetimi sayılmaz.

İade, yönetimdeki sipariş/iade sürecine bağlıdır; “adaptör var ama iş akışına bağlanmadı” durumu geride kalmıştır. Finans/yönetici isteğinde parola yeniden doğrulanır, gerçek sağlayıcı sonucu gelene kadar **Para iadesi bekliyor** görünür. Yerel DB durum/geçiş/tekrar testleri gerçek API sonucunun alınmış olduğu anlamına gelmez.

[Stripe kısıtlı işletmeler politikası](https://stripe.com/legal/restricted-businesses), yetişkin ürünlerde ve ülkelere göre farklı kabul/yasaklar içerir; ilk inceleme 10 Kasım 2026. Bu kaynaktan SEXSOGATE'in belirli hukuki işletme/hesap/ürün/site/hedef ülke için kabul edildiği çıkarılamaz. Kimlik veya kategori değiştirilerek kısıt aşılmaz.

11 Kasım 2026 yeniden kontrolü: resmî sayfa son güncellemeyi 22 Eylül 2026 gösteriyor. Yetişkin içerik/hizmetler genel yasaklar altında; fiziksel cinsel aksesuar/oyuncaklar için ayrıca ülkeye özgü yasaklar listeleniyor. Bu ayrım, ABD LLC veya ABD hesap varsayımından otomatik kabul çıkarmaya izin vermez. SEXSOGATE için hesap ülkesi ve gerçek ürün/site kapsamı henüz verilmediğinden işletme/kategori kabulü **doğrulanmadı**. Ülkeye özgü politikayı ürün ithalatı veya tüketici hukuku onayı yerine kullanmıyoruz. Kaynak: [Stripe resmî güncel liste](https://stripe.com/legal/restricted-businesses).

Resmî teknik kaynaklar: [Checkout](https://docs.stripe.com/checkout/quickstart), [webhook](https://docs.stripe.com/webhooks), [idempotent istekler](https://docs.stripe.com/api/idempotent_requests) ve [iadeler](https://docs.stripe.com/refunds). Gerçek test için uygun hesaba ait sandbox anahtarları güvenli ortam dosyasına girilir; yetkili Stripe CLI bağlantısı `/api/payments/stripe` adresine yönlenir. Sohbete anahtar yapıştırılmaz. Yerel SDK imza üretme testi sağlayıcı sandbox tahsilatı değildir.

## Medya, dosya erişimi ve hata mahremiyeti

`/api/admin/media` yönetici/katalog/pazarlama rolü ve doğrulanmış MFA ister. Mutasyon aynı origin kontrolüyle çalışır. En fazla 8 MB PNG/JPEG/WebP, gerçek imza ve 20 milyon piksel sınırıyla işlenir; EXIF yönü uygulanıp en fazla 1800×1800 WebP olarak yeniden kodlanır. Kullanıcı SVG/HTML yükleyemez. Dosya ismi sunucuda UUID ile üretilir; kullanım hakkı referansı ve aktör audit kaydında tutulur.

`/uploads/{uuid}.webp`, yayımlanmış ürüne bağlı medyayı katalog için sunar. Yayımlanmamış medya yalnız ilgili yönetim rolleri ve MFA ile erişilir; misafire 404 döner. Bu erişim, özel bucket'ın kamuya açılmasıyla sağlanmaz. Yanıtlarda `private, no-store` ve `nosniff` vardır.

Ortak ticaret API'si `publicFailure` ile yalnız açıkça tanımlanmış `HttpError` mesajlarını döndürür. Bilinmeyen SDK/servis hataları, sağlayıcının ham mesajı veya anahtar ayrıntısı yerine genel `SERVICE_UNAVAILABLE` yanıtına çevrilir. Diğer özel uçlar kendi genel hata yanıtlarını kullanır; bütün üçüncü taraf hatalarının dış servisle test edildiği iddia edilmez.

## Personel, vergi sınıfı ve SEO sınırları

`/api/admin/orders/{id}` GET/POST, gerçek MFA ve her işlemde rol denetimi yapar. Depo yanıtından e-posta, maliyet/kâr, tahsilat toplamı/referansı ve geçmiş çıkarılmıştır; yalnız gerekli teslimat adresi/telefonu ve ödenmiş SKU/adet/paket döner. Finans, müşteri adres/e-postası olmadan finans alanlarını alır. Katalog/pazarlama bu endpoint'e erişemez. Toplama/paketleme, ödemede düşmüş stoğu ikinci kez düşürmez; siparişin kalan sevk miktarını ayırır. Ayrıntı `staff-order-guide.md` içindedir.

`variants.tax_class`, ürünün ilk varyantında ve varyant create/update/GET/formlarında bağlıdır. `*` açık ortak sınıftır; özel sınıfın ülke/yürürlük kuralı yoksa ortak kurala sessiz dönüş yapılmaz. Teknik sınıf değişikliği yayın/uygunluk incelemesini yeniler. Bu yapı, işletmenin gerçek vergi sınıflandırmasının onaylandığı anlamına gelmez.

SEO yönetimi MFA + yönetici/katalog/pazarlama rolüyle sınırlandırılır. Dil başına alias/metadata değişiklikleri ve yönlendirmeler audit kaydıyla tutulur. Hedef yalnız mevcut açık ürün/içerik olabilir; kapanmış kategori/aktif varyantı kalmamış ürün, özel hesap/API/sipariş yolu, dış URL, zincir ve döngü kabul edilmez. Canonical/sitemap/yönlendirme aynı açık katalog koşulunu kullanır. Gösterim para birimi tahsilat para biriminden farklıysa o gösterim tutarı için satın alınabilir `Offer` üretilmez. Geçersiz sayfa/sayısal arama girdileri 400 ile reddedilir. Bu sınırlar gerçek arama motoru kabulü veya bütün site crawler'ı değildir.

## Ortam alanları ve güvenli giriş

`.env.example` değer içermez. `npm run setup:local` yalnız yerel rastgele sırlar üretir. Development, test, staging ve production için farklı DB, secret ve bucket gerekir. Production/staging değerleri erişimi kısıtlı secret manager üzerinden verilmelidir; dosya veya sır sohbet/Git ile paylaşılmaz.

- `APP_ENV`, `APP_URL`, `APP_BIND_HOST`: ortam, güvenilir origin/canonical ve dinleme adresi. Varsayılan native başlangıç adresi `127.0.0.1`.
- `DATABASE_URL`, `TEST_DATABASE_URL`, `LOCAL_DB_PASSWORD`: runtime, izole test ve yalnız yerel kurulum. Production test DB'si değildir.
- `BETTER_AUTH_URL`, `BETTER_AUTH_SECRET`: oturum/MFA, auth job şifrelemesi ve amaç ayrımlı HMAC ile kısa ömürlü toplam teklifi/özel ekonomik izi. Rastgele en az 32 karakterlik secret gerekir; rotasyon mevcut oturum, bağlantı ve teklifleri etkiler.
- `PAYMENT_PROVIDER`, `PAYMENT_WEBHOOK_SECRET`: seçilen adaptör ve yerel test imzası. `PAYMENT_API_KEY`, `PAYMENT_MERCHANT_ID` aday sağlayıcı alanlarıdır; uygulanmış gerçek bağlantı anlamına gelmez.
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`: sunucu SDK/webhook ve gerekirse kamu anahtarı. Mevcut Hosted Checkout akışı publishable key gerektirmez.
- `STRIPE_BUSINESS_APPROVED`, `LIVE_SALES_ENABLED`: teknik kapılar; bayrağı açmak kabul belgesi, DB hazırlık kontrolleri veya gerçek operasyon kanıtının yerine geçmez.
- `TRUSTED_PROXY_ENABLED`, `TRUSTED_CLIENT_IP_HEADER`: üretimde yalnız denetlenen özel origin ve istemci başlığını silip yeniden yazan ters vekil ile kullanılır. Ağ sınırı doğrulanmadan checkout açılmaz.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`: worker'ın gerçek ileti bağlantısı. Eksikse iş başarısız olur/tekrar denenir.
- `STORAGE_PROVIDER`, `STORAGE_LOCAL_PATH`, `S3_ENDPOINT`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`: özel dosya deposu. Gerçek erişim politikası ve yedek ayrıca doğrulanır.
- `SHIPPING_PROVIDER`, `SHIPPING_API_KEY`, `INVOICE_PROVIDER`, `INVOICE_API_KEY`: aday bağlantı alanları; API entegrasyonu yapılmış sayılmaz.
- `BACKUP_ENCRYPTION_KEY`: 32 bayt hex AES256-GCM anahtarı; yedekten ayrı secret manager'da tutulur.
- `ADMIN_SETUP_EMAIL`, `ADMIN_SETUP_PASSWORD`: yalnız yerel bootstrap; `.local/admin-access.txt` Git dışıdır. Production bu helper'ı reddeder.
- `PG_BIN`: yerel yedekleme araçlarının dizini; native helper Windows binary yolunu kullanır.

## Başlatma ve dağıtım

`npm run dev`, `next dev --webpack --hostname 127.0.0.1` kullanır. Geliştirme `.next-local`, optimize derleme `.next` çıktısını kullanır. Production build komutu `next build` olarak korunur ve varsayılan Turbopack derlemesini kullanır; geliştirmede Webpack seçmek güvenlik veya tür kontrollerini kapatmaz. Desteklenen `--webpack` seçeneği [resmî Next CLI belgesinden](https://nextjs.org/docs/app/api-reference/cli/next) 11 Kasım 2026'da doğrulandı.

Yerel tanılama sırasında `.next` dışındaki kaynaklarda sekiz saniyelik izleme penceresinde sıfır değişiklik varken 150'den fazla yaklaşık 1 ms derleme ve trace'te 162 HMR yeniden yükleme görüldü. Bu Turbopack geliştirme döngüsü, tarayıcının oturum/katalog isteklerini sürekli iptal ediyordu. Webpack dev sunucusuna geçiş sonrası aynı personel akışı ve kendiliğinden yeniden yüklenmeme hedefi geçti. Bu tarihsel geliştirme tanısı güncel optimize build veya tam suite sonucu değildir; güncel kaynak ve komutlar [test-evidence.md](test-evidence.md) içinde ayrılır.

`npm run build` sonrasında `npm start -- --port 3000`, `scripts/start.mjs` üzerinden standalone sunucuyu başlatır. `APP_ENV` açıkça verilmelidir; script sır dosyasını kendiliğinden yüklemez. `public`, `.next/static` ve PDF fontlarını içeren `assets` dizinleri standalone çıktıya kopyalanır. Development/test için origin ve yerel medya yolu düzenlenir; diğer ortamlarda dış ortam yapılandırması korunur. Bu helper tek başına DB/worker/scheduler/secret manager kurmaz veya production yayını yapmaz.

Örnek yerel komut: `node --env-file=.env.local scripts/start.mjs --port 3000`. Gerçek dağıtım öncesi web, worker, scheduler, PostgreSQL ve özel nesne deposu birlikte doğrulanmalı; migration öncesi şifreli yedek/rollback planı bulunmalıdır. Kullanıcının açık talebiyle kaynaklar GitHub main dalına normal push ile aktarıldı; staging/production deploy, DNS işlemi veya gerçek tahsilat yapılmadı. GitHub aktarım kaydı [git-workflow.md](git-workflow.md) içindedir.

Gerçek S3, SMTP ve Stripe sandbox erişimi; staging geri yükleme ve remote CI çalıştırması henüz yoktur. Yerelde CI dosyalarının bulunması uzak pipeline'ın başarıyla çalıştığı anlamına gelmez.

## CI sürüm ve erişim durumu

`.github/workflows/ci.yml` içindeki resmî action sürümleri 11 Kasım 2026'da GitHub release API/etiketleri ve action manifestleriyle kontrol edildi; hareketli etikete değil tam commit SHA'larına sabitlendi:

| Action | Doğrulanan sürüm | Sabit commit |
|---|---|---|
| actions/checkout | [v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| actions/setup-node | [v7.1.0](https://github.com/actions/setup-node/releases/tag/v7.1.0) | `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| actions/upload-artifact | [v7.0.2](https://github.com/actions/upload-artifact/releases/tag/v7.0.2) | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |

Üçünün manifestinde Node 24 action runtime'ı görüldü: [checkout manifesti](https://raw.githubusercontent.com/actions/checkout/3d3c42e5aac5ba805825da76410c181273ba90b1/action.yml), [setup-node manifesti](https://raw.githubusercontent.com/actions/setup-node/949feb2413d6458794dcd2491c4babbbce0c15c1/action.yml), [upload-artifact manifesti](https://raw.githubusercontent.com/actions/upload-artifact/cf430e030ddbb5b0abf93d22962f4752f3646cd9/action.yml). Uygulama kurulumu ayrıca Node 24.12.0'a sabittir. Workflow yalnız `contents: read` ister; checkout `persist-credentials: false` kullanır. İzole personel ve SEO DB komutları da doğrulama sırasına eklendi.

Uzak push workflow'u tetiklendi; GitHub hesap/faturalandırma kilidi nedeniyle runner/test adımları başlayamadı ([42985339650](https://github.com/hamzaozbalkansahsi-bot/sogate/actions/runs/42985339650)). Remote CI PASS iddiası yoktur. Action manifesti/sürüm incelemesi runner, ağ, cache ve bütün komutların uzak çalıştırma kabulü değildir. Bu CI güncellemesi npm bağımlılıklarını değiştirmedi; exact lockfile korunur.

## Paket kararı

Bağımlılıklar exact kararlı sürüm ve lockfile ile sabittir. Next 16.4.6 + React 19.3.1, TypeScript 6.0.3, Kysely 0.29.8, pg 8.23.1 ve Better Auth 1.7.20 kurulumda npm registry/resmî dokümanlarla denetlendi. ESLint 10 denemesinde Next'in import/react/a11y eklenti peer aralığı 9 ile sınırlı olduğundan 9.39.5 kullanılır; EOL uyarısı araç zinciri borcudur. Kontroller kapatılmadı. `minimatch 11.0.1` ve ExcelJS altındaki `uuid 11.1.1` override'ları güvenlik danışma kayıtları için uygulandı. Son audit ve uyumluluk sonuçları yalnız `docs/progress.md` içinde güncel çalıştırma kanıtıyla raporlanır.

## Kayıttan sosyal çıktı ve sürümlü uygunluk — 022–024

Set editörü, SKU belge incelemesi, ürün teknik alanları ve ülke adres profilleri kendi PostgreSQL verisini kullanır; dış servis değildir. Her SKU'nun ülke uygunluğunda onay aktörü, gerekli belgede inceleyen kişi ve güncel kapsam zorunludur. Ürün yayınlama uygunluk onayı üretmez. Belge kaynağı/ref kaydı zararlı dosya tarama servisi veya resmî mevzuat kabulü değildir. Adres onayı ülke satış kapılarını açmaz.

Sosyal şablonlar aynı SKU/para/dilde gerçek katalog fiyatı ve yayımlanmış CMS içeriğinden düzenlenebilir SVG indirir. Platforma gönderi veya reklam yayını yapılmaz. Yedi ailenin açık/koyu sürümleri ve kaynak hak/hash kaydı vardır. Yüklenmiş görsel raster olarak gömülür; SVG içine gömülmüş fotoğraf vektör fotoğraf diye tanıtılmaz. Lisanslı fontlar ve logolar standalone trace listesine açıkça eklenir.

StorageProvider.get varsayılan 8MiB ve beş saniye sınırı taşır; yerelde confinement/dosya boyutu, S3'te Range ve gerçek stream/timeout denetlenir. S3 hesabı/politikası veya gerçek SMTP teslimatı bu yerel testlerden çıkarılamaz. İçe aktarma yerel özel görseli de bu sınırlı adaptörle doğrular. Son genel kabul kanıtı [progress.md](progress.md) ve [test-evidence.md](test-evidence.md) içinde tutulur.

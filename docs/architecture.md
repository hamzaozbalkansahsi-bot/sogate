# Mimari ve kararlar

## Temel
Next.js App Router + strict TypeScript + Tailwind, PostgreSQL, Kysely/pg, Better Auth, Zod, Vitest ve Playwright. Modüler monolit; web ve ayrı kalıcı worker. Kysely, Prisma'ya gerekçeli eşdeğerdir: tipli SQL erişimi, sürümlü SQL migration, PostgreSQL kilit ve koşullu güncellemelerinin açık denetlenmesi. SQL şema tek kaynaktır; migration kayıtları checksum ile korunur. Bağımlılıklar kurulumda npm stable ve resmî belgelerle doğrulanıp exact sürüme sabitlenir.

## Veri ve modüller
Katalog: product, variant, category, belge/ülke uygunluğu, lot bilgileri. Depo: warehouse/location, inventory balance + append-only movement + reservation. Ticaret: cart/item, order/item immutable snapshot, payment/event/refund, shipment/item, return/request/QC. İçerik: locale slug, draft/published sürümler. Yönetim: auth kullanıcı/oturum/MFA, rol, audit. Ayarlar: satıcı, ülke allowlist ve ayrı uygunluk kapıları, yürürlük tarihli vergi, fiyat listesi/kur, entegrasyon durumu. Operasyon: outbox/job claim/lease/retry/dead letter, mutabakat.

018–025 modülleri aynı monolit ve veritabanını genişletir; yeni servis/depo kaynakları kurulmadı. [Veri modeli](data-model.md), tablo ve alanların kanonik haritasıdır.

### Sunucu katalog, facet ve kart fiyatı

`commerce/catalog.ts` filtre doğrulamasının ve genel katalog sorgusunun tek kaynağıdır. Kategori/malzeme/fiyat/bulunabilirliğe marka, beden, renk, gerçek pil/güç türü ve mevcut sıvı/hijyen bayrakları eklenmiştir. Fiyat ve varyant filtreleri aynı SKU'da karşılanır; farklı seçeneklerin alanları birleşip hatalı eşleşme üretmez. Facetler gerçek açık kayıtlardan, ortam ve dil sınırlarıyla türetilir; boş değerler gizlenir ve özgün Türkçe saklanan metin değişmez. Bilinmeyen filtreler ve belirsiz tekil parametreler API'de reddedilir. Yazım hatası toleransı/fuzzy arama bu altyapıda yoktur.

Normal, lotlu ve set bulunabilirliği read-only CTE içinde hesaplanır; toplam, facet ve 24 ürünlük sayfa aynı PostgreSQL snapshot'ından gelir. Stok filtresi sayfalama öncesindedir. Katalog ve ortak kullanılabilirlik helper'ı checkout ile aynı `main` sevk deposunu kullanır; diğer depo stoğu sayılmaz. Ödeme/rezervasyon kendi kilitli denetimini tekrar yapar. `listProducts` dizi sözleşmesi korunur; `searchCatalog` ayrıca facet/toplam/sayfa döndürür. Yeni migration gerekmez.

`shared/catalog-display.ts` kartın fiyat/varyant temsilini seçer: sunucuda eşleşen varyantlar içinde seçili gösterim para biriminin en düşük geçerli pozitif fiyatı, SQL `min(amount_minor)` sıralamasıyla aynıdır. Fiyat ile seçenek adı aynı varyanta aittir. Eksik fiyat sıfır veya TRY'den varsayılan dönüşüm olmaz. SSR ve istemci ortak bilinen sorgu anahtarlarını iletir; filtre URL'si yenileme/sayfalama ile korunur. Mobil çekmece ortak Modal'ın odak/Escape davranışını kullanır; Chromium/WebKit yerel kabulü kanonik test kaydındadır. Rehber: [catalog-filter-guide.md](catalog-filter-guide.md).

### Set ülke ve belge sınırı

Setin üst SKU onayı fiziksel bileşenleri onaylamaz. Yayın ve checkout ortak `assertSkuCountryEligibility` ile üst SKU ve her bileşenin yönetici aktörü kayıtlı ülke onayını; zorunlu belge türünde aynı SKU/ülke/türde, referansı dolu, inceleyen aktörü kayıtlı ve tarihi geçerli belgeyi denetler. Bileşen etkin olmalıdır; production fixture bileşeni ve iç içe set reddedilir. Yalnız set içinde kullanılan fiziksel bileşenin ayrı ürün olarak yayında olması gerekmez. Bileşen/ürün satırları sabit sırada kilitlenir; stok atomikliği ve sipariş snapshot'ı korunur. 022 ile katalog/yönetici MFA oturumuna açık aramalı set editörü, yazmayan önizleme ve sürümlü kayıt eklendi. `bundle_components` stok tanımının kaynağıdır; `bundle_version` ile eski sürüm reddedilir, `bundle_changes` eski/yeni bileşen snapshot’ını, aktörü ve gerekçeyi tutar. Eski ve yeni fiziksel bileşenler kilitlenir; etkin rezervasyon veya üst kodda fiziksel/karantina stoğu varken değişiklik kapalıdır. Kayıt üst ürünü incelemeye alır, üst SKU onaylarını geçersizleştirir; fiyat, stok ve geçmiş sipariş değişmez. Rehber: [bundle-guide.md](bundle-guide.md).

Mantıksal set üst kodu fiziksel stok hedefi değildir. Doğrudan stok ayarı, satın alma kabulü ve iade kabulü/QC ortak `lockPhysicalStockTargets` denetimini kullanır. Tanım dönüşümü exclusive, fiziksel yazım shared aynı advisory kilidini; ardından ürün → SKU → bakiye sırasını izler. Eşzamanlı dönüşüm ile mal kabulü birlikte başarılı olamaz; karma satın almada tek uygunsuz satır bütün kabulü geri alır. Geçmişte normal ürün veya satılmış set bileşeni olan SKU üst set koduna dönüştürülemez; yeni SKU gerekir. Mevcut set tanımı değişse de geçmiş satış/iade snapshot’ı korunur. Eski tutarsız mantıksal üst kod iadesi sessiz stok yazımı yerine reddedilir ve operasyonel düzeltme gerektirir.

### Lot, FEFO ve geri çağırma — 018

`inventory_lot_balances`, toplam `inventory_balance` kaydının fiziksel lot ayrıntısıdır; ikinci bağımsız stok kaynağı değildir. SKU'nun `lot_tracking` ve `expiry_required` politikası yalnız bütün depolarda stok/karantina/aktif rezervasyon sıfırken açılır. Belgesiz geçmiş lot ataması yapılmaz. Genel stok artışı ve lotsuz satın alma kabulü takipli SKU'da kapalıdır.

Checkout toplam depo satırlarını ve uygun lotları sabit sırayla kilitler. FEFO tahsisi `reservation_lots` içinde kalır; doğrulanmış ödeme aynı tahsisi bir kez tüketir. Tarihi geçmiş/karantinadaki/geri çağrılmış lot satılamaz; arada uygunsuz olan tahsise geç başarılı ödeme otomatik sevk yerine istisna üretir. Recall kalan fiziksel stoğu karantinaya alır ve sevki engeller. Lotu bilinmeyen iade toplam iade karantinasında tutulur; lot veya satılabilir miktar tahminen artırılmaz.

Tek tahsis deposu `main` olarak kalır. Fiziksel lot barkodu/paket doğrulaması, bilinmeyen iadenin yeniden atfı/imhası ve çok depo/transfer açık işlerdir. Satın alma kalanına bağlı lotlu kabul 025 kapsamındadır. Rehber: [lot-guide.md](lot-guide.md).

### Satın almaya bağlı lot kabulü — 025

`purchase_receipt_lots`, satın alma kabul satırını aynı SKU'nun gerçek üretici lotuna ve tek stok hareketine bileşik FK'lerle bağlar. Satın alma/kalem, fiziksel SKU, ana depo ve lot kilitleri altında `receiveLotStock` çağıranın transaction'ını kullanır. Toplam depo, lot bakiyesi, kabul ayrıntısı, alınan miktar ve PO durumu birlikte commit edilir; lotlu satır için ikinci toplam stok artışı yazılmaz. Karma kabulde tek hatalı satır bütün işlemi geri alır. `quantity` karantina dahil fiziksel toplamdır; `quarantineQuantity` bunun alt kümesidir. Karantina kabulü PO kalanını azaltır, satılabilir stok oluşturmaz.

Yeni v2 hash aktörü, sıralanmış SKU/lot satırlarını ve kaynakları kapsar. Aynı aktör/içerik/anahtar önceki sonucu döndürür; içerik veya aktör değişimi reddedilir. Eski v1 kaydın aynı aktör ve eski içerikle tekrarı korunur; yeni kaynaksız v1 kabul açılamaz. Doğrudan lot girişi ve PO kabulü ortak kabul-anahtarı kilidini kullanır. Farklı anahtarlarla aynı fiziksel teslimatın elle iki kez girilmesini serbest belge metni kesin olarak tespit edemez; belge referansı global tekil değildir.

Kaynak zinciri lot → kabul ayrıntısı → mal kabulü → satın alma/tedarikçidir. Bir üretici lotu birden fazla PO'dan gelebilir; geçmiş bütün gerçek kaynakları gösterir, satılan belirli adedi tek PO'ya atfetmez. Teslimat başlığı referansı ile lot belge referansı ayrıdır. `lotSources` yalnız lot ve satın alma okuma yetkisi olan MFA oturumlarına maliyetsiz, aramalı/sayfalı DTO döndürür; doğrudan giriş ayrı etiketlenir. Kaynağı bağlanamayan eski kayıt için ilişki veya belge numarası üretilmez. Kaynak referansı dış belge doğrulaması değildir. Rehber: [purchase-lot-guide.md](purchase-lot-guide.md).

### Sürümlü gruplu import — 019

CSV/XLSX güvenli dosya sınırı aynı servistedir; dış XML/API fetch'i açılmadı. Eski yedi alanlı şablon ve 38 alanlı geniş şablon birlikte desteklenir. `productKey` dosya içinde yeni ürünü gruplar; ürün alanları tutarlı, SKU ve seçenekler ayrı olmalıdır. TRY/EUR/USD/GBP sabit listeleri açıkça verilirse saklanır; kur/fiyat/üretici/barkod tahmin edilmez.

Önizleme aktör, format 2, kaynak ortam, satırlar ve hataları kapsayan SHA-256 ile kaydedilir. Commit, önizleme ve varyant yazımı kilitleri altında kaynak/SKU/barkod/ref/medya denetimini tekrarlar. Hepsi tek transaction içinde draft ürün/varyant, açık fiyatlar ve mevcut ana depo için 0/0 bakiye üretir; fiziksel stok/hareket/lot/yayın/eligibility üretmez. Ana depo yoksa kurulum hatasıdır. Mevcut belge yalnız `review_required` FK referansıdır; eski SKU'nun kapsam/onayını kopyalamaz. Kaynaklar ve kanıt: [import-guide.md](import-guide.md).

### CMS, değişmez sürüm ve sunucu HTML'i — 020

Yapısal hero/navigation/footer/collection bölgeleri `cms_regions` ve değişmez `cms_region_revisions` kaynağındadır. Rehber/SSS mevcut `content_pages/content_revisions` üzerinde tür ve yayın alanlarıyla genişletilir; paralel ikinci içerik motoru yaratılmaz. Eski içerik yazıcısı aynı revision kaynağıyla uyumludur. Taslak, yayın ve arşiv ayrıdır; zamanlı yayın sunucunun okuma anında seçilir, açık tarayıcı veya kuyruk işi gerektirmez.

Ana kampanya/menü/footer aynı istek içindeki CMS snapshot'ından ilk HTML'ye girer. React.cache yalnız istek içi paylaşım sağlar. Yayın yokken mevcut marka bileşenleri güvenli varsayılandır; sahte sosyal kanıt eklenmez. Koleksiyon ürünleri yayın anında ve okumada dil/kategori/varyant uygunluğuyla filtrelenir. Taslak/gelecek/arşiv kayıtları özel kalır; bunların görsel referansı dosyayı anonim erişime açmaz.

CMS yetkisi yönetici/pazarlama + gerçek MFA'dır; mutasyonlar aynı origin, doğrulama ve audit ister. JSON/düz metin güvenli React bileşenleriyle gösterilir; zengin HTML/JS çalıştırılmaz. Hukuk onayı ayrı modüldedir. Serbest sayfa oluşturucu, otomatik çeviri ve çok aşamalı editör onayı tamamlanmadı. Katalog/CMS kaynaklı sosyal SVG üretimi ayrı yetkili modüldedir. Kanıt: [cms-guide.md](cms-guide.md).

### İlgili kişi başvuruları — 021

`privacy_controllers`, hukuki satıcıdan ayrı veri sorumlusunu sürümlü kaydeder. `privacy_policies` ülke, gün/takvim ayı, saat dilimi, kaynak/kanıt ve saklama notunu taşır. Hazır bir şirket veya hukuki süre varsayılmaz. Onaylı politika yokken başvuru alınır; süre boş kalır ve değerlendirme/yanıt kapalıdır. Yeni politika/yönlendirme mevcut son tarihi uzatmaz; politika geçmişi FK ile korunur.

Üye sahipliği veya hashlenmiş rastgele takip kabiliyetiyle erişilir. Misafir token'ı kimlik doğrulaması değildir ve yalnız sınırlı durum/tarih verisi döndürür. Kimlik incelemesi, değerlendirme ve kanıt referanslı yanıt ayrı geçişlerdir. Yönetici yapılandırır; yönetici/destek MFA ile işler. E-posta bildirimi şifreli kalıcı iş olarak sıraya alınır; gerçek SMTP teslimatı kanıtı yoktur.

Bu akış başvuru kaydı ve yanıtı yönetir; veri silme/anonimleştirme, tüm dış sistemlerde arama/taşınabilirlik ihracatı ve kanuni saklama kararını otomatik uygulamaz. Yerel DB ve tarayıcı akışları doğrulandı; son ortak kaynak sürümünün kanıtı [ilerleme](progress.md) ve [test kaydı](test-evidence.md) içindedir. Gerçek hukuk süreci ve SMTP teslimatı bu yerel sonuçla onaylanmaz. Rehber: [privacy-guide.md](privacy-guide.md).

### SKU belgeleri ve teknik bilgi — 023

`compliance.ts` belge metadata’sını, ayrı ülke uygunluğu kararını ve açık teknik veri projeksiyonunu yönetir. Katalog/yönetici belge ve teknik bilgiyi hazırlayabilir; belge incelemesi, ülke onayı ve işletme iletişimi onayı yalnız yönetici MFA kararıdır. Sürüm/idempotency, aktör, kaynak ve gerekçe olayları tutulur; eski aktörsüz boolean kaydı yeni onay sayılmaz. Normal yayın işlemi artık uygunluk üretmez. Teknik değişiklik ilgili SKU’yu ve etkilenen setleri yeniden incelemeye alır. Müşteriye yalnız izinli teknik alanlar ve onaylı gerçek işletme iletişimi döner; özel belge notu, maliyet ve tedarikçi dönmez. Raw PDF yükleme/önizleme/tarama veya dış belge doğrulaması bağlı değildir. Rehber: [compliance-guide.md](compliance-guide.md).

### Ülke adres profili ve hesap adresleri — 024

`address-profiles.ts` izinli yedi alanın TR/EN etiketi, zorunluluğu, uzunluğu ve sabit biçimini sürümler. Yönetici MFA ile taslak oluşturur; onay/arşiv ayrıca parola doğrulaması ister. Alan/kaynak/fixture içeriği SQL trigger ile değişmez; yeni onay önceki sürümü arşivler. Bu karar ülkeyi satışa açmaz. Kullanılabilir onaylı profil yoksa ülke market listesinden çıkar; checkout güncel profili transaction içinde kilitleyip yeniden doğrular, profil kimliği/sürümünü ve teslimat değerlerini siparişe kaydeder.

Adres defteri yalnız oturum sahibinin kayıtlarını getirir; oluşturma/güncelleme/kaldırma `user_id` ve sunucu alan doğrulamasına bağlıdır. Adres sekmesi açılınca yüklenir; kullanıcı değişimi bileşen state’ini ayırır. Checkout kayıtlı adresi form başlangıcı olarak kullanır, eski onay yerine geçirmez. Yeni profil eski adres/sipariş değerini yeniden yazmaz; adres defteri kaydını kaldırmak sipariş adresini silmez. Profil kuralları gerçek ülke adresleme mevzuatının kendiliğinden doğrulaması değildir. Rehber: [address-guide.md](address-guide.md).

### Katalog/CMS kaynaklı sosyal SVG

`social-assets.ts` yayımdaki ürünün gerçek varyant/fiyat listesi, koleksiyon veya rehber sürümünden açık/koyu düzenlenebilir SVG indirir. Yönetici/katalog/pazarlama MFA ile kullanır; kaynak/çıktı hash’i ve işlem izi tutulur. Görsel mevcut medya kaydının hak referansı, byte sınırı ve hash’iyle doğrulanır; storage okuması zaman ve boyutla sınırlıdır. Örnek görseller production’da kullanılmaz. İkinci katalog veya sosyal gönderi tablosu kurulmaz; sosyal hesaba yayın, reklam/feed kabulü veya gerçek S3 teslimatı iddiası yoktur. Rehber: [social-guide.md](social-guide.md).

## Tutarlılık
Rezervasyon transaction içinde variant ID sıralı satır kilidiyle; fiziksel satılabilirden aktif rezervasyon ve güvenlik payı düşülür. Kilit sırasında tekrar hesap; stok hareketi ve ödeme olayı unique key. Checkout idempotency anahtarı sepet sahibine bağlanır. Tamamlanan ödeme, snapshot'taki tutar/para ve doğrulanmış sağlayıcı olayıyla eşleşir. Expired→paid olayı payment_exception üretir; otomatik sevk yok. Deadlock/serialization sınırlı tekrar, sipariş başına kilit. Worker SKIP LOCKED ve lease ile kalıcı çalışır; e-posta başarısızlığı ödeme akışını geri çevirmez.

## Durum makineleri
Sipariş: awaiting_payment → confirmed → partially_shipped → shipped → completed; uygun durumdan cancelled; geç ödeme payment_exception. Ödeme: pending → succeeded/failed; succeeded → partially_refunded/refunded/disputed. Sevkiyat: pending → packed → shipped → delivered; her pakette miktar. İade: requested → reviewing → approved/rejected → received → inspected → refund_pending → refunded. İade stok kabulü quarantine; ayrı yetkili QC olmadan sellable değil.

Personel hazırlığı `picking → packing → packed → shipped` veya sevkten önce `cancelled`; shipment durumundan ayrı görevdir. CMS revision `draft → published/archived`; `publish_at` gelene kadar önceki uygun yayın korunur. Privacy başvurusu `received → in_review → responded/rejected`; kimlik `pending → verified` bağımsızdır. Bu model listesi her sağlayıcı/teslimat/itiraz geçişinin gerçek dış servisle tamamlandığını göstermez.

## Güvenlik
Better Auth güvenli oturumları, şifre sıfırlama/e-posta outbox ve TOTP MFA. Sunucu permission matrisi; admin API alanları role göre. Same-origin mutasyon, rate limit, parameterized SQL, Zod. Anonim cart ve guest tracking random32 token hash saklama; HttpOnly SameSite cookie. Özel API/sayfa private,no-store. CSP ve no-referrer; analitik/replay yok. Upload raster doğrulama + S3 adaptörü; SVG/HTML kullanıcıdan kabul edilmez. Dış fetch deny-by-default; özel ağ ve redirect reddi. Secret yalnız sunucu env.

İstemcide `store-context.tsx` oturum ve sepet yenilemelerini ayrı artan istek nesli ve AbortController ile sınırlar. Eski yanıt yeni kullanıcı state'ini ezemez; sahip değişiminde bekleyen sepet isteği geçersizleşir ve sayaç sıfırlanıp yeniden yüklenir. Cleanup iki akışı da iptal eder. Checkout/test ödeme ekranı hesap/sipariş kapsamını ayırır ve eski POST tamamlanmasının yeni ekrana yönlendirmesini engeller. Bu kontroller sunucu sahiplik denetiminin yerine geçmez; fetch iptali commit edilmiş işlemi geri almaz. Oturum yarışı ve gecikmiş ödeme yanıtı regresyonları iki motorlu yerel kabulde geçti; ayrıntı [kanonik test kaydındadır](test-evidence.md).

## Adaptörler ve ortamlar
PaymentProvider/ShippingProvider/InvoiceProvider/StorageProvider/MarketplaceProvider sınırları. Test ödeme yalnız APP_ENV development/test; NODE_ENV=production build ölçümü ile deployment ortamı farklıdır, APP_ENV production test adaptörünü reddeder. Production hazırlık kapıları ayrıca zorunlu. Gerçek entegrasyonlar erişim/kabul belgesi gelene kadar blocked. Docker Compose web/worker/PostgreSQL/MinIO ve ayrı scheduler; yerel credential üretici. Geliştirme/test/staging/production farklı DB/secret/bucket.

025 ve oturum değişikliklerini içeren önceki dondurulmuş kontrol noktasının yerel modül, toplu test, optimize build ve artefakt kabulü geçti. Ardından bulunan sepet/checkout sahiplik yarışı ve başarılı durum kodlu bozuk JSON yanıtı için kaynak yeniden açıldı; bu düzeltmeler önceki PASS'i devralmadı; yeni 320 dosyalık sürümün 246 birim/232 DB/94 E2E kontrolü ayrıca geçti. Kaynak kimliği ve güncel kabulün kanonik kaydı [progress.md](progress.md) ve [test-evidence.md](test-evidence.md) içindedir. Gerçek S3/SMTP/Stripe sandbox, uzak CI, staging restore ve fiziksel depo/cihaz kabulü bu sonuçların dışındadır.

## Para gösterimi ve yönetim listeleri

`shared/money.ts` içindeki `formatMinorAmount` alt birimleri BigInt ile korur; yapılandırılmış 0/2/3 basamak, negatif kesirli tutar ve Arapça rakam/ayırıcı düzeni için altyapı vardır. Arayüzün `money()` köprüsü mevcut TRY/EUR/USD/GBP para birimlerini iki basamakla gösterir. Bu generic helper yeni tahsilat para birimi, Arapça yayını veya kur servisi açmaz; kur kaynağı/tampon/yuvarlama operasyonu ayrı açık iştir.

Admin kategori/marka listeleri sunucu araması, 25 kayıtlık sayfa ve toplam ile çalışır; yeni/düzenle/arşiv işlemleri mevcut yetki/audit sınırındadır. Üründeki marka bugün metin etiketidir; marka listesi katı FK veya otomatik ürün adı dönüşümü sayılmaz. Liste/şema varlığı bütün operasyon kapsamının tamamlandığı anlamına gelmez.

## Kaynaklar
- https://nextjs.org/docs/app/getting-started/installation
- https://better-auth.com/docs/installation
- https://better-auth.com/docs/plugins/2fa
- https://kysely.dev/docs/intro
- https://node-postgres.com/features/transactions
- https://www.postgresql.org/docs/current/explicit-locking.html

Hukuki gereklilikler doğrulanmadan ülke açılmaz. PDF tedarik raporu hukuki, lisans veya ödeme kabul kanıtı değildir.

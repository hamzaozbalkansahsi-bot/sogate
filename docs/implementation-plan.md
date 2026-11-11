# SEXSOGATE uygulama planı ve yerel kontrol noktası

Güncelleme: 11 Kasım 2026. Amaç, kendi deposundan satış yapan tek işletmenin birbirine bağlı ticaret sistemidir. Kapsam docs/product-spec.md, mimari docs/architecture.md, gerçek komut sonuçları docs/progress.md, dış erişimler docs/integrations.md, canlı engeller docs/launch-checklist.md içindedir.

Bu plan kullanıcının sekiz aşamasını korur. [x] yalnız belirtilen yerel uygulama ve modül kanıtını gösterir; aşamanın bütün kapsamı veya canlı satış tamamlandı anlamına gelmez. Son değişikliklerden sonraki toplu doğrulama ayrıca ilerleme dosyasına kaydedilir. Tablo/adaptör bulunması çalışan uçtan uca akış yerine geçmez.

Onaylı çekirdek kontrol noktası [checkpoint-core.md](checkpoint-core.md) içindedir. 022–025, sosyal üretim, adres profili, ödeme öncesi toplam ve oturum yarış düzeltmesi dahil son toplu koşu 246 birim/232 DB/94 E2E ile geçti; bu, kalan tüm kapsamın veya canlı satışın kabulü değildir. Sonuçların tek kaynağı [progress.md](progress.md) ve [test-evidence.md](test-evidence.md) olarak korunur.

## Ortak kurallar

- Marka SEXSOGATE, slogan “Tutkunu Keşfet.”; açık alışveriş yüzeyleri, bordo vurgu. Tescil veya sahte sosyal kanıt kullanılmaz.
- Önce local geliştirme ve test; canlı satış kapalı. Başka işletmenin ortamına bağlanılmaz. Test verisi ve test ödeme production'da reddedilir; örnek ürünler üretim vitrini/sepetinden de dışlanır.
- Para, stok, rol, sahiplik ve ülke kuralları sunucudadır. Satıcı, vergi, katalog, belge ve sağlayıcı kabulü uydurulmaz. Sırlar Git'e veya çıktıya yazılmaz.
- Yeni davranışta başarısız regresyon → uygulama → başarılı doğrulama esastır. Dış servis simülasyonu gerçek sağlayıcı testi diye sunulmaz.

## Aşama 1 — Proje denetimi, kurallar, kimlik, veri modeli, tasarım sistemi

- [x] Boş proje denetlendi; bağımsız yerel Git, kısa AGENTS.md, exact bağımlılıklar ve lockfile kuruldu. PostgreSQL development/test ayrıldı; migration checksum ve advisory lock kullanıyor.
- [x] Karar, tasarım, veri modeli, güvenlik, hukuk ve devam belgeleri oluşturuldu. Marka görseli ve PDF incelendi; yeniden yorumlanmış SVG kimlik, küçük simgeler, sosyal şablonlar ve lisanslı fontlar üretildi.
- [ ] Gerçek katalog fotoğrafları/hakları, marka/alan adı sahipliği ve üretim varlıkları doğrulanacak. Raster yeniden çizimi özgün vektör kaynağı diye sunulmaz. Verilmemiş NDECOR başlığıyla biçim karşılaştırması açık; başka işletmenin deposu açılmadı.

Kanıt: migration komutları, marka inceleme belgeleri ve docs/progress.md. Bu aşama hukuki marka onayı tamamlandı sayılmaz.

## Aşama 2 — Katalog, yönetim paneli, depo, stok

- [x] Ürün/varyant, SKU, TR/EN içerik, kategori/marka, varyant ve sabit para birimi fiyat listesi yönetimi var. Kategori/marka UI'si sunucu araması ve 25 kayıtlık sayfalarla çalışır. Yayındaki ürün güvenlik içeriği veya teknik varyant değişince incelemeye döner; ilgili uygunluk/taşıyıcı/belge onayları iptal edilir. Yalnız fiyat değişikliği yayını korur ve kaydedilir.
- [x] Sunucu katalog araması ve kategori, malzeme, fiyat, marka, beden, renk, gerçek pil/güç türü, mevcut sıvı/hijyen bayrakları ve bulunabilirlik filtreleri uygulandı. Facetler gerçek açık kayıtlardan gelir; koşullar aynı SKU'ya uygulanır. Toplam/facet/sayfa tek snapshot'tadır; main deposu stok/lot/set filtresi LIMIT öncesindedir. Kartın en düşük geçerli gösterim fiyatı SQL min sıralamasıyla aynı varyanta aittir. Migration 014 özgün metni değiştirmeden Türkçe aramayı normalize eder; filtreler için yeni migration gerekmez.
- [x] Ana depoda hareketli stok girişi/ayarlama, karantina, tedarikçi, satın alma ve fazla kabulü engelleyen idempotent mal kabulü çalışıyor.
- [x] 019 ile eski yedi kolon ve 38 alanlı CSV/XLSX şablon/eşleme/önizleme desteklenir. productKey bir yeni ürünü gerçek ayrı SKU/varyantlarla gruplar; ürün alanı çelişkisi ve tek dil seçenek adı reddedilir. Teknik/maliyet/dört para/TR-EN metin/üretici/menşe/garanti ve mevcut referanslar kaydedilir; uydurma marka/üretici/barkod/belge oluşturulmaz.
- [x] Import hash'i aktör/format/ortam/satır/hataları bağlar; commit'te SKU/barkod ve kaynak denetimi kilit altında tekrarlanır. Fiziksel stok/hareket/lot/yayın/eligibility oluşmaz; mevcut main depoya yalnız sıfır bakiye eklenir. Belge FK bağlantısı review_required'dır. Eski 2 MB/1000 satır/40 kolon ve ZIP/XML/formül/SSRF sınırları korunur; tedarikçi stoğu veya lot açma kolonları reddedilir.
- [x] 018 lot takibi, belgeli doğrudan lot kabulü, tarih/karantina/recall, FEFO tahsisi ve ödeme tüketimi main depoda aynı stok kaynağına bağlıdır. Geç/uygunsuz lot ödemesi istisnaya alınır; genel stok/satın alma yolu lotsuz artış yapamaz. Geri çağırma ilişkileri ve lotu bilinmeyen iade karantinası yerel akışta var.
- [x] Rolüne göre az veri dönen personel sipariş ayrıntısı ve ödenmiş siparişten idempotent toplama/paketleme/sevk API'si var. SKU veya gerçek barkodla miktar doğrulaması, görev ayrımı ve aktif görevi doğrudan sevkle aşma engeli yerel entegrasyonda sınandı.
- [x] 022 set editörü: gerçek SKU araması/adet/önizleme, beklenen sürüm, eski-yeni tanım ve aktör geçmişi var. Stok/rezervasyon/lot/nested sınırları ve üst/bileşen uygunluğu ayrı denetlenir; son tarayıcı ve stok kabulü kanonik test kaydında geçti.
- [x] 023 SKU belge/uygunluk ve teknik bilgi UI/API'si var. Katalog metadata'yı sunar; yönetici belge inceleme/iptal, ülke kararı ve kaynaklı işletme iletişimini ayrı onaylar. Yayın/checkout aynı aktörlü SKU/ülke/exact belge kuralını kullanır. Public teknik DTO maliyet, tedarikçi ve özel referans içermez; raw PDF yükleme/malware taraması yoktur.
- [x] 025 lotlu satın alma kabulü kalan miktarı birden fazla üretici lotuna böler; karma normal/lotlu kabul, karantina, belge kaynağı ve aynı anahtarla belirsiz ağ yanıtı tekrarı atomiktir. Kaynak listesi yetkili/maliyetsiz ve sayfalıdır; gerçek tarayıcı/DB kabulü geçti.
- [ ] Fuzzy arama, fiziksel lot/paket eşleşmesi, bilinmeyen iadeyi yeniden atfetme/imha, çok depo/transfer ve gerçek depo kabulü açık. Mevcut katalog kaydını güncelleyen import veya tedarikçi XML/API kabulü bu teslim değildir.

Modül adımları/kanıt sınırları: [lot](lot-guide.md), [lotlu satın alma](purchase-lot-guide.md), [import](import-guide.md), [personel](staff-order-guide.md), [katalog](catalog-filter-guide.md), [set](bundle-guide.md), [belge/teknik bilgi](compliance-guide.md). Genel kabul yalnız kanonik test kaydından değerlendirilir.

## Aşama 3 — Ürün → sepet → rezervasyon → test ödeme → sipariş

- [x] Kalıcı sunucu sepeti, hashlenmiş token, üyeye birleştirme ve checkout'ta yeniden sahiplik denetimi çalışıyor. Başka hesaba ait veya çıkış sonrası kalan token eski hesaba sipariş oluşturamaz.
- [x] Ödeme öncesi yazmasız/sahiplikli sunucu teklifinde ürün/kupon/kargo/dahil vergi/teslimat koşulu gösterilir. Sepete bağlı beş dakikalık imza, kilit altında tekrar hesap ve değişince açık yeniden inceleme vardır; otomatik ikinci ödeme yok. Teklif idempotent iş parametresinden ayrıdır.
- [x] Sunucuda fiyat/kupon/vergi/kargo hesabı, snapshot ve sepet sahibine bağlı idempotency var. Son adet yarışı ana depo kilitleriyle; setler bileşenleri atomik rezerve ederek korunur.
- [x] Checkout set üst SKU'su ve her fiziksel bileşen için ülke uygunluğu ve gerekiyorsa aynı SKU/ülke/türde referansı dolu, incelenmiş, yürürlükte belge ister. Pasif/üretimde örnek bileşen ve iç içe set reddedilir; yalnız set içinde kullanılan bileşenin ayrıca vitrine yayımlanması zorunlu değildir. Bu uygulama gerçek belge veya hukuk onayı üretmez.
- [x] İmzalı yerel test ödeme, replay, yanlış imza/tutar/para reddi; başarısız ödeme/süre sonunda bırakma; geç başarı için otomatik sevk üretmeyen istisna doğrulandı.
- [x] Misafir siparişi, güvenli takip, üye siparişleri, sipariş anındaki TR/EN ürün ve hukuk snapshot'ları var. Dönüş URL'si tahsilat kanıtı değildir.
- [ ] Gerçek katalog, ülke/yaş gereksinimleri ve belgelerle üretim kabulü açık. Yerel akış gerçek tahsilat veya hedef ülke onayı değildir.

Kanıt: [checkout rehberi](checkout-guide.md), scripts/quote-integration.ts, scripts/integration.ts, scripts/operations-integration.ts, scripts/security-boundary-integration.ts ve müşteri/güvenlik E2E. Başka depo miktarı ana depo tahsisi yerine kullanılmaz.

## Aşama 4 — Stripe adaptörü, webhook, mutabakat, kargo, iade, fatura

- [x] Resmî Stripe SDK ile Hosted Checkout, ham imza, ortam/tutar/para/sipariş/oturum eşleme ve kalıcı olay/iş kaydı var. Scheduler ödeme/iade mutabakatı oluşturur. Sonucu bilinmeyen eski işlemlerde yeni tahsilat/iade POST'u sınırlandırılır.
- [x] Manuel taşıyıcı/takip, idempotent kısmi sevk ve miktar denetimi var. Pil/sıvı SKU'larında ülke/taşıyıcı kabulü doğrulanmadan checkout veya ilgili sevk reddedilir.
- [x] İade kararı, kabul, karantina ve açık QC ayrıdır. Migration 012 ile normal/set iadeleri satış snapshot'ından return_stock_lines üretir; güncel set tanımı geçmiş iadeyi değiştirmez. Genel stok ekranı bu karantinayı açamaz.
- [x] Test iadesi ve Stripe için bekleyen iade/outbox/sağlayıcı sonucu sonrası tekil kesinleştirme kodu var. Bekleyen iade başarı sayılmaz. Yetkili dış fatura referansı kaydı mali belge üretimi değildir.
- [ ] Uygun Stripe hesabı/sandbox ile gerçek API tahsilat/iade/zaman aşımı, taşıyıcı etiket/takip olayı, gerçek tarife ve e-Fatura sağlayıcısı doğrulanmadı. Dispute/chargeback ve tüm teslimat geçişleri tam operasyon değildir.

Kanıt: offline SDK imza/tekrar politikası; gerçek yerel DB kısmi sevk/iade/QC ve değişen set tanımı regresyonları. Callback simülasyonu gerçek para hareketi değildir.

## Aşama 5 — Ürün SEO, CMS, hukuk sürüm/onay ve ilgili kişi başvurusu

- [x] Ana sayfa/katalog/ürün sunucu çıktısı; TR/EN tekil ürün yolları, canonical/hreflang ve title/description/alt editörü var. Aynı ürünün eski slug'ı güvenli 308 ile son adrese gider; dış/özel hedef, çakışma, zincir ve döngü denetlenir. SEO değişikliği rol/MFA ve audit'e bağlıdır.
- [x] Sayfalı 25 kayıt SEO raporu yinelenen başlık/açıklama, eksik çeviri/alt, yerel kırık medya ve varyant/kategori uygunluğunu gösterir. Sitemap index ürünleri 1000 kayıtlık bölümlere ayırır; dil eşleri ve gerçek tarih kullanılır. Örnekler ve açılmayan ürünler dışlanır.
- [x] Gerçek Product/Offer/ProductGroup/Breadcrumb verisi seçili fiyat ve stoktan türetilir. Eksik fiyat veya gösterim/tahsilat parası farklılığında Offer iddiası üretilmez; özel sayfalar indekslenmez.
- [x] 020 ile kampanya/menü/footer/koleksiyon için yapısal TR/EN CMS bölgeleri ve değişmez sürümler, özel taslak önizlemesi ve zamanlı yayın var. Kampanya/menü/footer aynı istek snapshot'ıyla ilk sunucu HTML'ine girer. Koleksiyon seçimi gerçek ürünlerden, dil/kategori/varyant filtresi ve gerçek fiyat projection'ıyla çalışır; taslak/gelecek/arşiv medya anonim erişim sağlamaz.
- [x] Rehber/SSS mevcut content_pages/content_revisions kaynağında tür ve sürüm/zaman alanlarıyla yönetilir; eski yazıcı aynı kaynağa bağlıdır. Arşiv geçmişi silmez veya önceki yayını kendiliğinden açmaz. Hukuk taslak/onay/yürürlük/arşiv akışı ayrıdır; placeholder onaylanamaz, gerçek metin satıcı alanları olmadan yürürlüğe alınamaz.
- [x] Siparişe bağlı tam sözleşme/dil/sürüm/hash/kabul zamanı korunur. Yetkili PDF/JSON güncel hukuk metninden değil sipariş snapshot'ından üretilir; resmî fatura değildir.
- [x] 021 veri sorumlusu/süre politikası/ilgili kişi başvurusu/kimlik incelemesi/yanıt modülünün yerel rol/sahiplik/süre ve UI doğrulaması çekirdek kontrol noktasında kayıtlıdır. Veri sorumlusu satıcıdan türetilmez; kural yokken süre uydurulmaz ve değerlendirme/yanıt kapalıdır.
- [x] Gerçek SKU/dil/güncel fiyat/hak kaydı ve CMS sürümünden yedi düzenlenebilir sosyal SVG üreten özel yönetim akışı var; byte/hash/süre sınırları uygulanır. Sosyal hesaba gönderim veya reklam kabulü verilmez; tarayıcı kabulü kanonik test kaydında geçti.
- [ ] Hukuk ve veri sorumlusu/politika bilgileri yetkili onay bekler. Otomatik silme/anonimleştirme ve bütün dış sistemlerden taşınabilirlik, serbest sayfa oluşturucu, çok aşamalı editör onayı, otomatik çeviri, genel crawler/dış schema ve arama motoru hesabı kabulü tamamlanmadı.

Rehberler: [CMS](cms-guide.md), [privacy](privacy-guide.md), [sosyal](social-guide.md). Yerel kanıt, gerçek hukuk/SMTP/arama motoru kabulünün yerine geçmez; sonuçlar kanonik dosyalardadır.

## Aşama 6 — Ülke, dil, para, kanallar

- [x] Dil/ülke/gösterim parası ayrı; onaylı ülkenin tahsilat parası capability verisinden gelir. Gerçek sabit liste eksikse gösterim fiyatı/kur uydurulmaz. TR/EN arayüz ve sipariş içerikleri var; tamamlanmamış de/ru/ar yayını kapalı. Son market arayüzü tarayıcı kabulü genel sonuç kaydına aittir.
- [x] `formatMinorAmount` ile BigInt ve yapılandırılmış 0/2/3 alt birim basamağı, negatif tutar ve Arapça sayı biçimlendirmesi altyapısı var. Ticaret sözleşmesi yalnız TRY/EUR/USD/GBP'yi iki basamakla kullanır; generic biçimlendirici başka tahsilat parası veya Arapça vitrin açmaz.
- [x] Ülke allowlist ve ürün/yaş/ödeme/kargo/vergi/hukuk kapıları var. Eksik para birimine rastgele kur uygulanmaz; raporlar para birimlerini birleştirmez.
- [x] 024 ülke adres profilleri değişmez sürüm/kaynak ve yönetici MFA/yeniden parola onayıyla yönetilir. Checkout onaylı alanları doğrular; adres alanı/sürüm snapshot'ı geçmiş siparişte korunur. Üye adres oluştur/oku/güncelle/sil işlemleri sahiplik denetimlidir. Profil onayı ülkeyi açmaz; yeni UI kabulü [adres rehberi](address-guide.md) ve genel test kaydında izlenir.
- [x] Migration 015 ile her SKU sınıfı+ülke+yürürlük için tam bir ürün kuralı çözülür; eksik/çakışma reddedilir. Kupon önce satıra dağıtılır, her satır kendi oranıyla KDV dahil hesaplanır. Migration 013 kargo vergisi ayrıdır. Kural/sınıf/oran/kaynak/paylar snapshot'ta korunur; kısmi iade sonraki kurallardan etkilenmez.
- [ ] Gerçek ürün vergi sınıfı atamaları, oran/kaynak ve hedef ülke mevzuatı işletme/hukuk onayı bekler. Yerel karma sınıf hesabı vergi uygunluğu onayı değildir.
- [ ] Kur kaynağı/tampon/yuvarlama operasyonu, gerçek ülke mevzuatı ve güçlü yaş doğrulama bağlantısı tamamlanmadı. Kanal/SKU/fiyat/kota modeli ve engelli adaptörler var; gerçek pazaryeri sipariş/stok mutabakatı ve tedarikçi XML/API aktif değil.

Kanıt: ülke/belge/para engeli, EN snapshot, RTL ve para birimi ayrı rapor; scripts/shipping-tax-integration.ts 11 kontrol ve tests/unit/mixed-tax.test.ts 5 test. Hiçbir ülke veya kanal kendiliğinden uygun sayılmaz.

## Aşama 7 — Güvenlik, mobil, görsel, erişilebilirlik, performans

- [x] Sunucu rol/alan/sahiplik, oturuma bağlı MFA, aynı origin, akışta gövde limiti, özel önbellek ve kalıcı sepet/ağ kotası var. Ham IP yerine kısa ömürlü HMAC anahtarı tutulur.
- [x] İki oturum MFA, hesaplar arası erişim, stok/kupon yarışı, replay, karantina bypass, dosya/XML ve hata mahremiyeti regresyonları var. Reklam/session replay varsayılan yüklenmez.
- [x] Lot, import ve CMS yeni rol/MFA/fixture sınırları modül testlerinde doğrulandı. Taslak CMS önizlemesi gizli kalır; import satır hatasını silmek checksum'u geçerli yapmaz. Bu modül sonuçları privacy veya son bütün sürüm testini otomatik geçmiş saydırmaz.
- [x] 360/390/430/768/1440 düzen, klavye/modal, Chromium/WebKit, kontrast, axe ve RTL kontrolleri çalıştırıldı; başarısızlıklar ve tekrarları ilerleme dosyasında korunur.
- [x] Son 320 kaynak dosyalık sürümde lint/typecheck, 246 birim, 232 DB, 94 E2E, optimize build/artefakt ve ekran kaydı geçti. Oturum/sepet istek nesli, A→B sonrası gecikmiş session/checkout/test ödeme yanıtı regresyonları dahil. Sonuç yalnız manifestteki kaynak ve belirtilen yerel kapsam içindir.
- [ ] Gerçek cihaz, gerçek kullanıcı yüzde 75 saha performansı, kapsamlı bağımsız penetrasyon ve gerçek proxy/firewall sınırı doğrulanmadı. LCP/INP/CLS hedefleri ölçüm yerine geçmez.

Kanıt: docs/security-review.md ve son gerçek çıktıları kaydeden docs/progress.md. Güvenilir proxy bayrağı operatör beyanıdır; origin izolasyonu ve başlık temizleme ayrıca doğrulanır.

## Aşama 8 — Staging, yedek restore, canlı hazırlık

- [x] Yerel uygulama, worker/scheduler, migration, şifreli yedek/izole restore araçları; CI ve container kaynakları var. Yerel DB geri yükleme ve ayrı örnek medya hash kontrolü çalıştırıldı.
- [ ] Docker, uzak CI, gerçek staging/production dağıtımı çalıştırılmış değildir. Yapılandırma bulunması dağıtım başarısı sayılmaz.
- [ ] Üretim DB/medya yedekleme-saklama-erişim/restore, migration geri dönüş tatbikatı, gerçek SMTP/S3, izleme ve operasyon devri bekler.
- [ ] Satıcı/veri sorumlusu, gerçek katalog/stok, kategoriye uygun ödeme, taşıyıcı/tarife, vergi/fatura ve hukuk onayları olmadan canlı satış açılmaz. Remote push, production, gerçek tahsilat, DNS/alan adı işlemi yapılmaz.

## Sonraki çalışma ve kapanış

Önce docs/progress.md içindeki gerçek kontrol noktasını oku. Aynı test DB'sini sıfırlayan entegrasyonları paralel çalıştırma. Yeni migration'ları uygula, yalnız yerel örnekleri güncelle, tek test kaydıyla doğrula; hatayı kök neden/regresyonla düzelt. Sonuçları ve açık işleri güncellemeden aşamayı veya sistemi tamamlandı ilan etme.

Somut açık sıra: fiziksel lot/paket doğrulaması, bilinmeyen iade lotu atfı/imha ve çok depo; fuzzy arama, kalan CMS yönetişimi, genel crawler/kanal operasyonları; gerçek ürün/vergi/ülke belgeleri ve yetkili hesaplarla sağlayıcı/staging kabulü. Set, belge/teknik bilgi, sosyal üretim, adres profili ve privacy kodu yeniden sıfırdan yapılacak iş değildir; yerel kanıt ve gerçek dış/hukuki onay ayrı izlenir.

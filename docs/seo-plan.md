# Ürün SEO planı ve gerçek sınırlar

Kaynak uzlaştırma tarihi: 11 Kasım 2026. Hedef alan adı sexsogate.com; mülkiyet/DNS/marka tescili veya arama motoru hesabı doğrulanmış değildir. Bu belge mevcut kaynak davranışını ve açık kabul şartlarını anlatır. Son gerçek komut çıktısının sahibi docs/progress.md'dir; bu belge güncellemesi yeni uygulama/E2E testi çalıştırıldığı anlamına gelmez.

## Sunucu çıktısı ve dil yolları

Ana sayfa ve katalog sunucuda gerçek veriyi okuyup ilk ürünleri HTML'ye verir; ürün sayfası da sunucuda okunur. Katalog filtreleri ilk sunucu sorgusuna yansır. Sorgu parametreli katalog sayfası noindex/follow üretir; temel canonical ve dil eşleri page-metadata üzerinden belirlenir. Bu politika bütün olası faceted URL birleşimlerinin bağımsız crawler ile doğrulandığı anlamına gelmez.

Migration016 product_routes ile ürün+dil ve dil+slug tekilliği kurar. TR canonical /urun/{trSlug}, EN canonical /en/urun/{enSlug} olur. Aynı ürünün iki dilde farklı slug'ı olabilir. Proxy /en ve /en/* isteklerini aynı uygulamaya yeniden yazar ve sunucu dilini belirler; HTML lang da buna göre seçilir. Dil yalnız çerezden çıkarılmaz. İngilizce ad/açıklama yoksa İngilizce ürün açılmaz ve EN alternatifi üretilmez.

Ürün metadata'sı önce seçilen dilin kayıtlı SEO başlık/açıklamasını, yoksa ürünün gerçek ad/açıklamasını kullanır. Canonical, tr-TR/en/x-default ve Open Graph URL/görsel/alt bilgileri dil yolundan üretilir. Görsel için kayıtlı SEO alt metni ve ürün adı fallback'i desteklenir. APP_URL tabandır; gerçek üretim domain doğrulaması ayrıca bekler.

## SEO editörü ve güvenli yönlendirme

/api/admin/seo yönetici/katalog/pazarlama rolü ve doğrulanmış MFA oturumu ister. Mutasyon aynı origin ve sınırlı gövdeyle alınır. Editör TR/EN slug, title, description ve alt kaydını yönetir; başlık/açıklama uzunlukları, düz metin ve slug biçimi denetlenir. Yinelenen başlık/açıklamalar raporda görünür; her tekrar kaydı engelleyen bir kural olduğu iddia edilmez. Değişiklik audit'e yazılır.

Slug değişikliği eski eşdeğer ürün yolunu 308 ile yeni canonical adrese taşır. Bir ürün tekrar adlandırıldığında kendi eski yolları son hedefe düzleşir; eski sluga geri dönmek döngü oluşturmaz. Aynı dilde başka ürünün slug'ı devralınamaz.

Genel public_redirects kaydı güvenli site içi kaynak/hedef, mevcut açık hedef ve gerekçe ister. Dış/protokol göreli URL, özel hesap/sepet/ödeme/sipariş/admin/API yolu, kendine yönlendirme, zincir ve döngü reddedilir. Aktif ürün yolu ayrı ürün SEO işleminden değiştirilir. Route işlemleri ortak transaction/advisory lock kullanır. Runtime hedefin hâlâ açılabilir olduğunu yeniden kontrol eder; kapatılmış hedefe yönlendirme yapmaz. Proxy hariç tutmaları segment sınırındadır; /brand/* varlığı hariçken /branding gibi genel eski sayfa da yönlendirmeden geçebilir. Manuel hedefin anlamsal eşdeğerliği işletmenin içerik incelemesidir.

## Sayfalı ürün raporu

Rapor 25 kayıtlık, dil ve Türkçe normalize arama destekleyen sayfalarda çalışır. Başlık ve açıklama tekrarları seçili dilin tüm arşivlenmemiş kayıtları üzerinde belirlenir; gösterilen bulgu sayısı geçerli sayfaya aittir. Denetimler:

- Seçili dil açıklaması, EN çeviri, özel SEO başlık/açıklaması ve görsel alt metni.
- Yinelenen başlık/meta açıklaması.
- Yerel public görseli veya /uploads/* medya kaydı ve yerel depolama dosyası. Gerçek S3 nesne varlığı, erişim olmadan doğrulanmış gösterilmez.
- Aktif varyant ve temel fiyat/para biçimi; örnek/yayın durumu.
- Gerçek kamuya açıklık: yayımlanmış ürün, aktif kategori ve en az bir aktif varyant; EN için gerekli metin. Son varyantı/kategorisi kapatılmış ürün sitemap'e uygun sayılmaz.

Bu ürün içerik raporudur; genel site crawler'ı, dış Google schema doğrulayıcısı, tüm bağlantıların HTTP taraması veya indeks/sıralama puanı değildir.

## Yapılandırılmış veri ve fiyat doğruluğu

Gerçek ürünlerde Product veya çok varyantlı kayıtta ProductGroup/hasVariant ile BreadcrumbList JSON-LD üretilir. Teklif seçili gerçek fiyat listesini, para birimini ve stok durumunu kullanır. Varyant rengi/bedeni varsa eklenir. Kayıtsız marka, GTIN, değerlendirme veya puan uydurulmaz.

Gösterim parası ülkenin tahsilat parasından farklıysa satın alınabilir Offer eklenmez. Seçili gerçek fiyat eksik veya geçersizse başka para birimi, rastgele kur veya sıfır fiyatla Offer üretilmez. Ürün bilgisi fiyat teklifinden ayrı kalabilir. Müşterideki gösterim projeksiyonu ve sunucu schema üreticisi aynı seçimi kullanmalıdır; son market arayüzü kabulü genel E2E kaydında ayrıca doğrulanır.

fixture=true ürünlerde ürün/teklif JSON-LD çıkarılmaz ve ürün metadata'sı noindex olur. Production dışındaki ortam kök metadata/robots ile indeks dışında tutulur. Örnek veri gerçek katalog veya fiyat onayı değildir.

## Sitemap ve özel sayfalar

Production /sitemap.xml bir sitemap index'tir. İçerik bölümü ve her biri 1000 gerçek ürün kaydı içeren products-{n} bölümleri üretilir. Ürün başına TR ve hazır EN URL'si, karşılıklı hreflang/x-default ve gerçek updated_at kullanılır. Ürün sayısı, aktif kategori/aktif varyant koşuluyla aynı public predicate'ten hesaplanır.

Taslak, arşiv, örnek ve açılmayan ürünler dışlanır; stokta olmayan ama açık gerçek ürün OutOfStock olarak kalabilir. Production dışında sitemap içeriği boş kalır. İçerik bölümü temel sayfaları ve yayımlanmış TR/EN rehber kayıtlarını kapsar; tüm koleksiyon/kategori varyasyonları ve sınırsız içerik ölçeklemesi tamamlandı sayılmaz.

Hesap, sepet, ödeme, sipariş, yönetim, favori ve özel API alanlarında indeks/önbellek politikaları uygulanır; API'ler private/no-store taşır. Robots/noindex yetkilendirme yerine geçmez. Özel sipariş ve belge erişimi ayrıca sahiplik veya güvenli token ile denetlenir.

## Kanıt durumu

Mevcut katman testleri ve ana ajanın son bildirdiği kapsam:

| Katman | Kanıt/kapsam |
|---|---|
| İzole SEO PostgreSQL | scripts/seo-integration.ts, 7 kontrol: dil metadata/slug, çakışma ve rol/MFA, aynı ürün 308 düzleşmesi, dış/özel/zincir engeli, sayfalı rapor, dil sitemap'i ve son varyant/kategori arşivi |
| SEO metin/yol kuralları | tests/unit/seo-rules.test.ts, 13 kontrol |
| Proxy yol sınırları | tests/unit/proxy-paths.test.ts, 10 kontrol; genel önekli eski yollar ile özel/varlık segmentleri ayrılır |
| Product schema | tests/unit/product-seo.test.ts, 5 kontrol; gerçek seçili fiyat, eksik fiyat, fixture, gösterim/tahsilat ayrımı ve varyant grubu |
| Admin tarayıcı kabulü | TR SEO formu kaydı ve 308 takip senaryosu tests/e2e/admin.spec.ts/seo-flow.ts içinde; son94testlik genel koşuda Chromium/WebKit admin akışı2/2PASS, kanıt test-evidence.md içinde |

Bu tablo yeni genel test PASS iddiası değildir. Son komutlar, sürümden sonra tekrar gereken kontroller, başarısızlıklar ve sonuçlar docs/progress.md içinde tutulur.

## Açık işler ve canlı kabul

1. Genel dahili site crawler'ı; gerçek katalogda kırık link/görsel, tüm yönlendirme ve faceted URL kombinasyonlarının HTTP taraması. Mevcut ürün raporu bunları kapsamaz.
2. Dış Google Rich Results/schema doğrulayıcısı ve gerçek production URL incelemesi. Yerel JSON-LD birim testi dış doğrulama değildir.
3. Search Console/Bing işletme hesabı ve site sahipliği, canlı sitemap gönderimi ve gerçek tarama/indeks/saha organik performansı. Sıralama veya indekslenme garantisi verilmez.
4. Bütün ürün dışı sayfaların uluslararası metadata/canonical/hreflang kapsamı ve gerçek çevrilmiş katalog; de/ru/ar yayını tamamlanmadan açılmaz. RTL altyapısı Arapça içerik onayı değildir.
5. Gerçek yayımlanacak ülke/SKU belgeleri, üretici/güvenlik bilgileri, görsel hakları, hukuk ve ödeme/taşıyıcı kabulü. Teknik SEO bu ticari veya hukuki kapıları geçersiz kılmaz.
6. Tam içerik/koleksiyon/sosyal şablon ve ülke/ürün feed operasyonları. Kategori politikası doğrulanmadan reklam veya mağaza feed'i açılmaz.

## Yetişkin içerik ve kanal politikası

Gerçek katalog explicit/SafeSearch ve ilgili kanal politikalarıyla ayrıca değerlendirilir. hasAdultConsideration gibi uygulanabilir işaretlerin otomatik tamamlandığı iddia edilmez. Yaş giriş bildirimi marka politikasıdır; her ülkede hukuki yaş doğrulaması sayılmaz. Botlara farklı katalog gösterilmez; yanlış kategoriyle politika aşılmaz. Genel ürünler için anında indekslenme sağlayan bir servis kurulmadı.

Resmî inceleme bağlantıları; ilk kaynak incelemesi 10 Kasım 2026, bu belge güncellemesinde yeniden web doğrulaması yapılmadı:

- [Google explicit içerik yönergeleri](https://developers.google.com/search/docs/specialty/explicit/guidelines)
- [Google Product yapılandırılmış veri](https://developers.google.com/search/docs/appearance/structured-data/product)
- [Google dil ve bölge sürümleri](https://developers.google.com/search/docs/specialty/international/localized-versions)
- [Google Merchant yetişkin ürün alanı](https://support.google.com/merchants/answer/6324508?hl=en)
- [Bing Webmaster yönergeleri](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)

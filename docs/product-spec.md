# SEXSOGATE ürün sözleşmesi

10 Kasım 2026. Kullanıcının son gönderdiği 29 bölümlük talimat kapsam ve kabul kaynağıdır; önceki 23 bölüm bu sürümle genişletildi. Tek hukuki işletme, Türkiye'deki kendi stokları, fiziksel ürün, yurt içi ve yalnız onaylı ülkelere satış. Dropshipping ve çok satıcılı model yoktur.

Geliştirici gösterimi kullanıcının verdiği yazımla PTYS Technoligess LLC; tasarım Hamza ÖZBALKAN. Bu roller hukuki satıcı ve veri sorumlusundan ayrıdır. Resmî unvan belgeye dayanmadan mali/hukuki alana yazılmaz. NDECOR başlık standardı bu projeye verilmedi; başka işletmenin deposu açılmadı. Kullanıcının verdiği başlangıç bloğu esas alınır, NDECOR biçim karşılaştırması açıktır.

Son sürüm ekleri: Stripe öncelikli resmî SDK adaptörü, ürün bazlı SSR/SEO kontrol ekranı, sürümlü taslak/onaylı/yürürlükte/arşiv hukuk dokümanları ve siparişe bağlı içerik hash'i; Türkçe karakterlerin API, arama, içe aktarma, e-posta ve çıktıda korunması. Yeni belgeler data-model, security-and-privacy, seo-plan, legal-requirements ayrı sorumluluklarla tutulur.

## Sonuç ve sınırlar
Müşteri vitrini, Türkçe yönetim, katalog/varyant, depo hareketleri, sunucu sepeti, süreli rezervasyon, ödeme, sipariş, sevkiyat, iade, içerik ve raporlar aynı PostgreSQL verisini kullanır. Önce tamamen yerel geliştirme ve test; production satışı varsayılan kapalı. Ödeme/kargo/fatura/kanal erişimi veya hukuk onayı bulunmayan modül gerçek entegrasyon diye sunulmaz.

## Ürün kapsamı
Yetişkin oyuncakları, fantezi iç giyim, aksesuarlar, çift ürünleri, bakım ve hediye setleri. Ürün ve varyant ayrı; SKU tekil, barkod/üretici/sertifika uydurulmaz. Taslak, incelemede, yayında, satışa kapalı yaşam döngüsü. Yerel örnekler yalnız APP_ENV=development/test ve ayrı veritabanı kimliğiyle yüklenebilir. Gerçek katalog görselleri ve belgeleri gelene kadar üretime yayın yok.

## Müşteri kapsamı
Ana sayfa, kategori ve sunucu filtreleri, ürün, koleksiyon, favori, sepet, adres/teslimat/ödeme özeti, misafir sipariş, güvenli takip, hesap/adres/sipariş/iade, rehber, SSS, iletişim ve hukuk sayfaları. Türkçe ve İngilizce metin kaynakları; Almanca/Rusça/Arapça yayın kapalı çeviri altyapısı, Arapça gerçek dir=rtl. Dil, ülke ve para ayrı tercihler. Giriş bildirimi hukuki yaş doğrulaması değildir. Ticari ileti ve analitik izinleri zorunlu işlemden ayrıdır.

## Operasyon kapsamı
Roller: yönetici, katalog, depo/sevkiyat, müşteri hizmetleri, finans, pazarlama. Sunucuda rol, alan ve sahiplik denetimi; admin MFA. Katalog, stok girişi/sayım/karantina, satın alma, sipariş/ödeme, manuel gerçek takipli sevk, kısmi sevk/iade, içerik, ülke/para/vergi ayarı, rapor, işlem kaydı, iş kuyruğu ve canlı hazırlık. CSV/XLSX inceleme/önizleme/onay, SKU kontrolü, güvenli ihracat; XML/API önce inceleme kuyruğu.

## Kritik kabul
- Son adet iki eşzamanlı checkout'ta bir kez rezerve olur; ödeme olayı tekrarında ikinci stok düşmez.
- Fiyatlar sunucuda alt birimlerle hesaplanır; sipariş snapshot'ı değişmez. Vergi, ülke, belge eksikse checkout durur.
- İmza/tutar/para uyuşmazlığı reddedilir. Süresi geçen başarılı ödeme istisnaya alınır, negatif stok veya otomatik sevk olmaz.
- Sepet token'ı hash olarak saklanır; takip yalnız güvenli token veya kayıt sahibi oturumuyla. Sayfalar private/no-store.
- Üretimde test adaptörü ve örnek veri teknik olarak reddedilir. Gerçek satıcı/vergi/ödeme/kargo/hukuk/MFA/yedek/ürün kanıtı olmadan canlı kapalı.
- Otomatik birim, gerçek PostgreSQL entegrasyon, Chromium/WebKit E2E; 360/390/430/768/1440 ve RTL; lint, strict typecheck, production build. Gerçek cihaz ve saha performansı ayrıca bekler.

## Dış önkoşullar
Hukuki satıcı, vergi numarası, adres/banka/destek, gerçek SKU/stok/görsel hakları, ödeme sağlayıcısının bu kategori için yazılı kabulü, taşıyıcı ve batarya/sıvı kabulü, tarife, e-Fatura sağlayıcısı, ülkeye göre mevzuat ve hukuk metni onayı, alan adı/DNS sahipliği henüz verilmedi. Admin kurulum alanları boş kalır. Her önkoşul docs/launch-checklist.md içinde izlenir.

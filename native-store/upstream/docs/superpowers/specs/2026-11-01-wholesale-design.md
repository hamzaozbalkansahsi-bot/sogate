# NODENO yurt dışı toptan satış

Amaç: Türkiye dışındaki alıcılar aynı katalogdan renk/SKU seçerek paket veya palet miktarıyla birden fazla ürün için teklif talebi iletir. Talep satış/ödeme onayı değildir. Türkiye perakende akışı korunur. Mevcut yönetim, özel SQLite, marka, dört dil ve Turhost yayını genişletilir.

## Akış ve gerçek bilgiler

- `?page=wholesale&lang=tr|en|ru|ar`: gerçek ürün fotoğraflarıyla toptan mobilya sayfası, ürün/renk arama, paket/palet seçimi, çok kalemli teklif listesi, firma/e-posta/telefon/ülke/şehir ve teslimat notu. Üyelik gerekmez. İletişim bilgileri localStorage'a yazılmaz.
- Ürün sayfasında yurt dışı toplu alım bağlantısı; üst yardımcı menü ve alt menüden erişim. Sayfa gerçek ticari teklif sürecini anlatır; taşıma/vergi/teslim süresi garantisi vermez.
- Paket ticari satış ambalajıdır; bir mobilyanın montaj kolilerinin sayısı değildir. Palet kapasitesi ürün ölçüsünden tahmin edilmez. Veri yokken miktar paket/palet olarak kaydedilir, adet/toplam fiyat uydurulmaz.
- Yönetim `wholesale` kaydı her SKU için tek: productId, enabled, unitsPerPack, packsPerPallet, minimumPacks, minimumPallets, currency, üç adet eşiği ve birim fiyatı, doğrulanmış hazırlık günleri. Kademeler artan eşik/azalan birim fiyat; para birimi açık; hiçbir perakende fiyat otomatik toptan fiyata dönüşmez. Taslak/yayın ve sürüm/rol denetimi mevcut sistemden gelir.
- Yönetim `wholesaleRequests`: özel müşteri talepleri, kalemlerin değiştirilemez sunucu anlık kaydı, open/in_progress/quoted/closed/cancelled, iç not ve teklif koşulları. Teklif hazırlanması otomatik gönderim, sipariş/fatura veya ödeme oluşturmaz. Adet ve fiyat talep anında dondurulur; farklı para birimleri toplanmaz.
- Sunucu POST: aynı origin, JSON, 32KB sınırı, açık veri işleme onayı, honeypot, gizlilik koruyan hız limiti, tarayıcıya bağlı idempotency; aynı tekrar aynı referans, farklı içerikle aynı anahtar 409. En fazla 50 benzersiz SKU, sayısal tam miktar 1..10000, Türkiye talebine izin yok. Yayın revizyonu değişmişse 409; fiyat/adet/gönderim toplamları istemciden kabul edilmez. Public GET/ID sorgusuyla müşteri talebi okunamaz.

## SEO ve arayüz

NODENO Sans ve kanonik lacivert/krem/limon renkleri; başlık yanında tam ürün fotoğrafı, altında kompakt ürün kartları ve masaüstünde yan teklif listesi; mobilde tek sütun/44px dokunma/taşmayan formlar. Arapça RTL. İletişim formu yeniden çizimlerde korunur.

Dört dilde toptan mobilya, paket/palet alımı ve teklif içeriği SSR; canonical, karşılıklı hreflang ve sitemap. Ayrı ülke kopya sayfaları veya sahte dil/teslimat vaadi yok. B2B sayfası Service/WebPage + gerçek ürün bağlantıları; teklif fiyatı bilinmiyorsa sıfır Offer/AggregateOffer yok. Perakende ProductGroup fiyatı aynı kalır. Teklif kişisel verisi URL/JSON-LD/analitik içine konmaz.

## Teslim ve doğrulama

PHP gerçek kayıt/rol/sürüm/anlık görüntü testleri; JS/PHP SEO eşliği; Chromium ve Windows WebKit mobil/masaüstü/RTL gerçek form ve hata testleri. Tam kaynak ve dağıtım suite, fiziksel medya kapısı, yayın yedeği, canlı HTTPS/hash/SSR kabulü. Gerçek üretim QA müşteri talebi oluşturmaz. Yönetim/mağaza/SEO kılavuzları aynı kapsamda güncellenir.

Yetki kararı: Kullanıcı bu sistemin geliştirilmesini ve otomatik yayını zaten istedi. Yeniden spec/plan izin döngüsü başlatılmaz; mevcut dalda native uygulanır. Paket/palet/fiyat listesi ayrıca soruldu; yanıt yoksa sayılar boş, teklif akışı etkin kalır.

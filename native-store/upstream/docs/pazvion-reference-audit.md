# Pazvion referans ve kaynak incelemesi

31 Ekim 2026. İnceleme, kullanıcının verdiği [herkese açık mağazada](https://pazvion-store.web.app/) ve açıkça gösterdiği yerel Pazvion kaynak klasöründe salt okunur yapıldı. NODENO dışındaki hiçbir dosya değiştirilmedi. Hesap açılmadı, oturum açılmadı, e-posta/mesaj gönderilmedi, sipariş veya ödeme oluşturulmadı. Tarayıcıdaki POST/PUT/PATCH/DELETE istekleri engellenecek biçimde çalıştırıldı; incelenen akışlar hiçbir engellenen isteğe ihtiyaç duymadı.

## Doğrulanmış güncel durum

- Adresin ilk HTML başlığı Pazvion olsa da yüklenen mağazanın adı **NMakeup**. Halka açık API `slug=pazvion` için **20 ürün** döndürüyor; 20 ürünün tamamı demo olarak işaretli. Para birimi TRY. Kategori düzeninde bir üst bölüm ve 165 kategori düğümü var.
- [Halka açık ödeme durumu](https://pazvion-api.onrender.com/v1/storefront/pazvion/payments) HTTP 200, `enabled:false`, `shipping_cents:0` döndürdü. Bu mağazada gerçek tahsilat açık değildir.
- Google giriş istemcisi tanımlı. Sadece giriş penceresi gözlendi; mevcut hesabın erişimi veya gerçek giriş kabulü bu incelemede yapılmadı. SMTP teslimi doğrulanmadı.
- Masaüstünde 1440 × 1000, mobilde 390 × 844 tarayıcı çerçevesinde 16 ekran/durum kaydedildi. Kaydedilen her durumda belge genişliği ekran genişliğine eşit; yatay sayfa taşması yok. JavaScript sayfa hatası yok. Fiziksel telefon/klavye testi değildir.
- Ana sayfa, ürün, sepet ve mobil görselleri yüklenmesi beklenerek tekrar yakalandı. İlk ham HTML'de yalnız yükleniyor ekranı bulunması, istemci tarafındaki API yüklemesinden kaynaklanıyor.

Kanıtlar: `artifacts/reference-pazvion/flow-report.json`, `public-status.json`, `initial-network.json`. Bunlar mevcut gözlemi kanıtlar; eski teslim belgelerindeki bütün kabul iddialarını yeniden test etmez.

## Ekran ve etkileşim haritası

| Alan | Gözlenen davranış | NODENO'ya aktarılabilecek düzen |
|---|---|---|
| Üst başlık | Logo; geniş arama; giriş, favori ve sayaçlı sepet. Mobilde arama ikinci satıra iner, işlemler simge olur. | NODENO logosu/renkleriyle aynı işlev sırası; dört dil seçimi ve ürün koduyla arama korunur. |
| Kategori menüsü | Perde üzerinde açılan mega menü. Solda ana bölüm; sağda alt kategori grupları ve Daha fazla gör. Kapat, dışarı tıklama, Escape ve odak geri dönüşü kaynakta var. | Mevcut 104 NODENO kategorisiyle gerçek ağaç; mobilde kaydırılabilir iki alan. Trendyol kozmetik ağacı taşınmaz. |
| Kategori vitrinleri | Yuvarlak görseller ve kısa adlar; mobilde yatay kaydırma. | Mobilya odaları/ürün grupları için gerçek kategori görselleri. |
| Katalog | Masaüstünde altı, mobilde iki ürün sütunu. Kalp, fotoğraf, kategori, ad, fiyat, stok bilgisi ve eylem. Sonuç sayısı ve sıralama üstte. | Mobilya fotoğrafına uygun oran; gerçek fiyat yoksa fiyat talebi. NODENO ürün kodu ve renk bilgileri korunur. |
| Filtreler | Açılır filtre paneli; kategori, marka, stok; toplu temizle. İsim ve artan/azalan fiyat sıralaması. | Marka yerine mevcut mobilya verisine dayanan ölçü/renk/malzeme filtreleri; bilinmeyen stok ve fiyat için doğrulanmış gibi etiket gösterilmez. |
| Ürün sayfası | Ayrı URL durumu; breadcrumb; solda büyük fotoğraf/küçük resimler; sağda ad, fiyat, adet, hızlı satın alma, favori, adres. Altında özellikler, açıklama, teslimat/iade, benzerler, yorum ve sorular. | Modal yerine geniş ürün görünümü; ölçü, malzeme, montaj ve gerçek teknik veriler. Ürün koduyla paylaşım korunur. |
| Fotoğraf | Küçük resim seçimi ve native dialog içinde büyük fotoğraf. | Mevcut NODENO galeri verileriyle aynı davranış; ekran görüntüsü ve paylaşım izinli kalır. |
| Mobil ürün | Fotoğraf üstte, bilgiler altta; ekran altına sabit Şimdi al/Sepete ekle/favori çubuğu. | Yapışkan işlem çubuğu; ödeme etkin değilken uygun teklif/sepet eylemi. Arapça RTL ve güvenli alt boşluk birlikte ele alınır. |
| Birlikte al | Aynı kategoriden ikinci ürün; iki normal fiyatın toplamı. İndirim iddiası yok. | İlgili mobilya önerileri kullanılabilir. Uyumlu takım/ölçü verisi olmadan takım veya indirim iddiası üretilmez. |
| Sepet | Ayrı ekran, fotoğraf/ad/adet/kaldır; masaüstünde yan özet, mobilde altta özet. Devam et adres bölümüne kaydırır. | Mevcut kalıcı NODENO sepeti, teklif çıktısı ve gerçek fiyat bulunmadığında tutarsız toplam üretmeme kuralı korunur. |
| Favoriler/geçmiş | Favoriler, Önceden Gezdiklerim, önceden sepete eklenenler ve yeniden satın alma alanları. Misafir listeleri yerel; hesap favorileri API ile ayrıdır. | Yerel favori/son gezilenler hazır aktarım adayı. Cihazlar arası eşitleme ayrıca hesap/API gerektirir. |
| Giriş/hesap | Google veya e-posta kodu; oturumdan sonra sipariş, değerlendirme, soru/bildirim, profil ve adres defteri sayfaları. | Görsel kalıp ve bileşenler var; NODENO'ya gerçek servis bağlanmadan çalışan üyelik iddiası veya sahte sipariş geçmişi gösterilmez. |
| Footer | Mağaza, bilgilendirme ve iletişim sütunları; içerikler dialog açar. | NODENO'nun doğrulanmış alan adı, e-posta, telefon ve sosyal hesapları. Demo satıcı/hukuk metinleri aktarılmaz. |

Sepete ekleme sonrasında mevcut Pazvion bir **Tamam** düğmeli başarı dialog'u açıyor. Bu her eklemede akışı kesiyor; NODENO için sepet sayacını güncelleyen, erişilebilir kısa bildirim ve isteğe bağlı Sepete git bağlantısı daha akıcı olur.

## Herkese açık rota ve veri örüntüleri

| İşlev | Mevcut adres/durum |
|---|---|
| Ana katalog | `https://pazvion-store.web.app/` |
| Mağaza seçimi | `?magaza=<slug>`; varsayılan `pazvion` |
| Ürün | `?urun=<UUID>`; incelenen ürün [Amber demo](https://pazvion-store.web.app/?urun=6e0061e0-fb32-4ff0-884e-ffe721163fac) |
| Sepet | `#basket`; adres bölümü `#checkout-area` |
| Listeler | `#favorites`, `#recent`, `#flash`, `#best` |
| Hesap | `#account/profile`, `#account/orders`, `#account/reviews`, `#account/questions`, `#account/addresses`, `#account/help` |
| Ürün alt bölümleri | `#product-information`, `#product-delivery`, `#related-products`, `#product-feedback`, `#product-questions` |
| Katalog okuma | `GET https://pazvion-api.onrender.com/v1/storefront/pazvion?offset=0` |
| Yorum/soru okuma | `GET /v1/storefront/{shop}/products/{id}/feedback?offset=0` |

Kategori ve arama filtrelerinin durumu URL'de saklanmıyor; hash çoğunlukla katalog bölümüne kaydırıyor. NODENO mevcut paylaşım adreslerini korumalı; kategori/arama/sıralama için geri/ileri ve yeniden açılabilir URL durumu eklenebilir.

## Yerel kaynak mevcut

Kanonik kaynak:

`C:/Users/Hamza ÖZBALKAN/Desktop/PTYS E-ticaret Yönetimi, Araştırma ve Otomasyon Platformu/Pazvion`

Pazvion `AGENTS.md`, altyapı kararı, güncel teslim durumu ve mağaza alışverişi/üyeliği/ödeme belgeleri incelendi. Kaynak ayrı projeler kullanıyor; NODENO işi mevcut Pazvion otomasyonlarının duraklatma kararını değiştirmez. Kaynakta değişiklik yapılmadı; mevcut altı izlenmeyen kanıt görseline dokunulmadı.

### Doğrudan uyarlama adayları

| Kaynak dosyası | Hazır davranış | Bağımlılık/uyarlama |
|---|---|---|
| `storefront/app/CategoryNavigation.tsx:8` | Gruplu mega menü, genişletme, Escape, dış perde, mobil düzen | `category-layout.ts` verisini NODENO ağacına bağla. |
| `storefront/app/ProductDetail.tsx:10` | Galeri, adet, hızlı eylem, özellik listesi, benzer ürünler, mobil alt çubuk | `StoreProduct` kozmetik odaklı; ölçü/malzeme/renk/montaj modeline ve i18n'e uyarlanır. |
| `storefront/app/Basket.tsx:5` | Ayrı sepet ekranı, adet/kaldır ve özet | Şu an TRY tutarı zorunlu; NODENO fiyat/teklif sözleşmesiyle uyarlanır. |
| `storefront/app/ShoppingLists.tsx:10` | Son gezilenler, yerel listeler, favori kalbi, koleksiyon ekranları | Yerel anahtarlar ve adlar NODENO'ya ayrılır; 100 öğe sınırı bilinçli seçilir. |
| `storefront/app/Favorites.tsx` | Hesap favorileri, hata/yeniden deneme ve eski hesap yanıtını ayırma | Pazvion müşteri API'sine bağlı; yalnız UI kopyası gerçek eşitleme sağlamaz. |
| `storefront/app/CustomerAccount.tsx:21`, `AccountView.tsx:14`, `AddressChoice.tsx` | Giriş dialog'u, hesap bölümleri, adres seçimi/defteri | Google origin/SMTP/oturum backend'i gerekir. Mevcut kullanıcı tokenları taşınmaz. |
| `storefront/app/ProductFeedback.tsx` | Puan dağılımı, yorum/soru listeleri ve form durumları | Sunucuda satın alma doğrulaması ve moderasyon gerekir; örnek puan/yorum üretilemez. |
| `storefront/app/Checkout.tsx:9`, `ProductPayment.tsx` | Ödeme uygunluğu, adres/onay, sağlayıcı iframe'i ve durum | Ticari hesap, anahtar, fiyat/stok ve satıcı koşulları tanımlanmadan açılmaz. |
| `storefront/app/DemoCheckout.tsx:3` | Sadece tarayıcıda adres → özet → tamamlandı denemesi | Gerçek sipariş altyapısı değildir; NODENO satışa hazırmış gibi sunulmaz. |
| `storefront/app/StoreFooter.tsx`, `shared/feedback.ts`, `shared/feedback.css` | Bilgi dialog'ları, sosyal bağlantılar, ortak işlem bildirimi | NODENO marka/dil/veri sözleşmesiyle uyarlanır; örnek hukuk içerikleri aktarılmaz. |

Kaynak mağaza **Next.js 16.3.8 / React 19.3.0 / TypeScript 7**; `next.config.mjs` statik export kullanıyor. Yönetim paneli ayrı React/Vite; API FastAPI; veri/kimlik/Storage ayrı Supabase; yayın Firebase/Render. Bu bilgi mevcut `package.json`, `next.config.mjs`, backend router'ları ve canlı ağ gözleminden elde edildi. Eski README'deki “mağaza henüz uygulanmadı” cümlesi mevcut kaynak ve canlıyla uyuşmuyor.

### Gerçek backend ile demo ayrımı

- `backend/app/main.py` katalog, müşteri, e-posta, geri bildirim, ürün görseli ve ödeme router'larını gerçekten bağlıyor. `storefront.py` katalog okumasını `storefront_catalog` RPC'sine gönderiyor; 31 Ekim canlı GET yanıtı bunu çalışan veri kaynağı olarak doğruluyor.
- `store_customers.py` mağaza kapsamında müşteri, doğrulama, adres ve hesap yolları içeriyor. Kaynakta olması NODENO'da kurulmuş olduğu anlamına gelmez. Mevcut hesaplar kullanılmadı.
- `checkout.py` fiyat/stok/oturum ve PayTR callback akışı içeriyor. `docs/ODEME_ALTYAPISI.md` gerçek sağlayıcı/banka kabulünün yapılmadığını, ilk sürümün TRY/tek çekim/0 TL kargoyla sınırlı olduğunu belirtiyor. `return_url` Pazvion alan adına sabit; NODENO'ya aynen kopyalanamaz.
- Güncel demo ürünleri `isDemoProduct` tarafından ayrılıyor; `DemoCheckout` gerçek ödeme/sipariş/stok kaydı oluşturmuyor. Ekranda sepet ve adres olması ödeme hazır demek değildir.
- Teslim kayıtlarına göre Pazvion worker ve otomatik görevleri kullanıcı kararıyla kapalı. Bu inceleme onları yeniden başlatmadı. Sağlayıcıların uyandırılma/gecikme davranışı ve gerçek e-posta teslimi ayrıca doğrulanmalı.

## Aktarımda korunacak sınırlar

1. **NODENO marka kimliği korunur:** mevcut logo, renkler, “İyi tasarım. Kolay yaşam.” ve “Good design. Easy living.” kullanılır. NMakeup/Pazvion markası, kozmetik görselleri ve demo tutarlar taşınmaz.
2. **667 ürün ve dört dil korunur:** Pazvion 200 kayıt sayfalıyor; arama ve filtre yalnız yüklenen kayıtları kapsıyor. NODENO aktarımı bütün katalogda doğru sonuç vermeli. Türkçe sabit metinler çeviri anahtarlarına, fiziksel sol/sağ CSS kuralları RTL uyumlu mantıksal kurallara çevrilir.
3. **Ürün modeli uyarlanır:** hacim/konsantrasyon yerine mevcut gerçek ölçüler, malzeme, renk, montaj, paket/teknik veri kullanılır. Bilinmeyen fiyat ve stok tamamlanmış gibi gösterilmez.
4. **Hesap ve ödeme ayrıdır:** UI modülleri şimdi uyarlanabilir; NODENO için yeni servis/origin/SMTP/ödeme yapılandırması ve gerçek kabul gerekir. Pazvion sırları, oturumları, `.env` dosyaları, `.local` veya `.firebase` hesap kayıtları okunmadı/kopyalanmadı.
5. **Mevcut paylaşım davranışı korunur:** ürün kodu ve bağlantı paylaşımı, ekran görüntüsü izni ve mevcut görsel koruma davranışları kaybolmaz. Pazvion ürün ekranında doğrudan paylaş düğmesi gözlenmedi; NODENO'nun mevcut özelliği ayrıca sürdürülür.

## Ekran kanıtları

Dosyalar `artifacts/reference-pazvion/` altında:

- `home-desktop-viewport.png`, `home-mobile-viewport.png`
- `categories-desktop.png`, `categories-mobile.png`
- `filters-desktop.png`, `filters-mobile.png`, `search-desktop.png`
- `product-desktop.png`, `product-mobile.png`, `product-desktop-full.png`, `product-mobile-full.png`
- `gallery-desktop.png`, `add-confirmation-desktop.png`
- `basket-desktop.png`, `basket-mobile.png`, tam sayfa sepet görselleri
- `favorites-desktop.png`, `login-desktop.png`, `delivery-mobile.png`

`audit-flows.mjs` yalnız gözlem ve yerel sepet/favori işlemlerini yeniden üretir; `public-status.mjs` halka açık üç GET yanıtının özetini alır. Başarısız ilk çekimdeki `failure.*` dosyaları, sepete ekleme dialog'unun devam etmeden kapatılması gerektiğini gösterir; son rapor başarılı yeniden çekimin sonucudur. Uygulama kaynağına değişiklik veya uygulama testi yapılmadı; bu teslim bir referans/kaynak incelemesidir.

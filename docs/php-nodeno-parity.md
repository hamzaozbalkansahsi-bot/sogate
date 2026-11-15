# NODENO müşteri deneyiminin PHP uyarlaması

## 15 Kasım2026 — yeni PHP müşteri katmanı ve kaynak katalog incelemesi

Bu bölüm aşağıdaki tarihsel açık maddelerin güncel karşılığıdır; yayın kanıtı son `docs/progress.md` kaydıyla değerlendirilir. PHP027–029: sunucu misafir/hesap favorileri, sahiplikli/sürümlü özel listeler,4 ürün karşılaştırması, mevcut sepet adedini koruyan toplu ekleme ve açık cihaz→hesap aktarımı uygulanmıştır. Türkçe tek-hata arama/SKU sıralaması, klavyeli öneriler, kategori ağacı/mega menü, hesap menüsü, ayrı dil/gösterim para birimi/teslimat tercihi, hero+iki yan alan/kategori halkası/ürün rafı/gerçek CMS rehberleri eklenmiştir. Stok filtresi artık toplu CTE kullanır. PDP gerçek galeri/seçenek bağlantısı, hızlı incelemede seçili fiyat, footer KVKK `privacy` türü ve ayrı gizlilik politikası bağlanmıştır. Sosyal bağlantılarda görünür yazı/ok/tooltip yoktur; yalnız ikon ve erişilebilir ad vardır.

Katalog/kategori ve izinli medya yönetimi, gerçek kaynak kayıtlarından kontrollü taslak ve xShopum/Liona/Sistina **2.194 ürün +170 kategori** özel incelemesi vardır. Bu sayılar mağazada yayımlanan ürün veya fiziksel depo stoğu değildir. Son kaynaklar için [rapor](php-source-catalog-report.json), [erişim/kullanım durumu](php-supplier-research.md) ve [kullanım rehberi](php-shopping-guide.md) kanoniktir.

Açık farklar korunur: NODENO'nun opsiyonel gezinme geçmişi burada varsayılan kapalıdır ve etkinleştirilmemiştir; bütün öneri algoritmaları, tam ürün/varyant editörü, bütün admin listelerinde gelişmiş sayfalama, S3/medya geri yükleme ve ülke/kur editörleri eksiksiz port edilmedi. Bayi XML/authoritative stok, gerçek SKU fotoğrafı ve hakları, gerçek ödeme/taşıma/hukuk/ülke kabulü bekler. Bu sürüme “bütün sistem birebir tamamlandı” denmez.


14 Kasım 2026 son kullanıcı talebi: menü, kategori, ürün, sepet, blog ve önerilenler için NODENO davranışını bütün olarak uygula; tek tek özellik talebi bekleme. SEXOGATE marka kimliği ve yalnız `/test` yayın sınırı korunur. Kaynak `C:/Users/Hamza ÖZBALKAN/Desktop/Nodeno`, salt okunur; şirket, müşteri, ürün, görsel, anahtar ve kabul bilgileri aktarılmaz. Önceki Node hedefli uyarlama belgelerinin yerini PHP müşteri katmanı için bu kabul matrisi alır.

Kaynaklar: `web/app.js` kategori/mega menü/ürün/sepet render'ları; `shopping-core.js`, `shopping-ui.js`, `catalog-search.js`, `product-presentation.js`, `checkout-draft.js`, `guest-checkout.js`, `blog-entry.js`, `blog-tools.js`; `docs/commerce-experience.md`, `docs/product-page-and-sharing.md`, `docs/superpowers/specs/2026-11-01-shopping-experience-design.md`. NODENO'nun mobilyaya özel ölçü/boya araçları yetişkin ürünleri için sahte özellik üretmeye dönüştürülmez.

| Yolculuk | Kabul davranışı | PHP durumu |
| --- | --- | --- |
| Footer / sayfa geçişi | Sosyal, mail, site haritası ve ayrı hukuk hedefleri; belge sonunda boş akış yok; geri dönüş konumu korunur | Yerel ve uzak10 footer senaryosu,42 sayfalık axe/klavye kontrolü ve gerçek hedefler geçti; fiziksel iPhone boşluk kabulü açık |
| Menü / kategori | Masaüstü kategori bağlantısı, mobil tam görselli kategori sayfası ve beş doğrudan alt menü bağlantısı | Son kullanıcı reddi sonrası düz kategori dialogu kaldırıldı; iki sütun görsel/ad/sayı, toplam barı ve Ana sayfa/Kategoriler/Favorilerim/Sepetim/Hesabım sırası yerelde ve uzakta10 senaryoda geçti. Ana sayfa raf düzeni ve tam hiyerarşi açık |
| Arama / liste | Türkçe çok kelime/kod araması, URL filtreleri, sıralama, fiyat/renk/malzeme/stok, filtre çekmecesi ve sayfalama | Fiyat/renk/beden/malzeme/marka/gerçek stok ve sıralama/URL/mobil çekmece var; tek harf toleransı ve klavye öneri kutusu açık. Stok filtresi kanonik Inventory ile sunucuda en çok5000 aday kontrol eder; büyük katalog için toplu sorgu optimizasyonu açık. |
| Ürün | Gerçek varyant/galeri/zoom, miktar, paylaşım, hızlı inceleme, mobil satın alma; gerçek kategori benzerleri | Hızlı inceleme/ekleme, adet, zoom, paylaşım ve kategori benzerleri var; çoklu gerçek görsel/renk eşlemesi ve tam NODENO galeri verisi açık. |
| Önerilenler | Kategori ve gerçek stok/katalog temelli ilgili ürünler; sahte kişisel profil veya satış iddiası yok | Kategoriye bağlı gerçek benzer ürünler ve taslak hariç tutma testi geçti; kişisel geçmiş tutulmaz |
| Sepet | Artır/azalt, seçili satırlar, varyant birleştirme, seçilenleri kaldır/boşalt,8 saniye geri alma; stale durum geri yazılmaz | PHP26 atomik ekle/artır/azalt, seçili satır, aynı ürün varyant birleştirme, kaldır/boşalt/8sn tek kullanımlık undo, stale ret ve99 üzeri hesap merge rollback bağlandı; birim+iki motor gerçek kabul var. |
| Favoriler / özel listeler | Mevcut adedi artırmadan toplu sepete ekleme; sahiplik ve sürüm koruması | Üye favorisi var; toplu/özel liste farkları açık |
| Checkout | İletişim/adres, teslimat ve son inceleme adımları; sunucu teklifi/sözleşme/rezervasyon aynı kalır | Adres/teslimat/son kontrol, sözleşme dialogları, ayrı fatura adresi sunucu doğrulaması/snapshot ve20dk sahip/sepet bağlı sekme taslağı var; tek onaylı TR teslimat seçeneği kullanılır. |
| Blog | Liste, arama/kategori, yazı içindekiler, okuma görünümü, ilgili yazı ve gerçek ürün bağlantıları; CMS taslak/yayın | Sürümlü CMS liste/arama/konu/sayfalama, içindekiler, paylaşım, ilgili yazı/gerçek ürün bağlantısı var. Üç özgün rehber TR/EN6 kayıtla test CMS’ine yayımlandı. NODENO mobilya/boya araçları kopyalanmadı. |
| Hesap / gizlilik | Oturum/sahiplik, adres ve sipariş/iade; açık talep olmadan yetişkin gezinme profili yok | Temel akışlar test edildi; NODENO tam eşdeğerliği iddia edilmez |

Sıra: footer/kaydırma regresyonu → menü/kategori/arama → ürün/ilgili ürün/hızlı inceleme → atomik sepet/geri alma → blog ve checkout/liste araçları → tam yerel kabul → yedekli yalnız `/test` yayın ve aynı uzak kabul. Her satır kendi kanıtıyla güncellenir. Eksik hukuki satıcı, gerçek ürün fotoğrafı/katalog ve dış ödeme/taşıma kabulü uydurulmaz. Kullanıcının son iletişim tercihi: şimdilik yalnız e-posta.


## Yayın kanıtı ve açık farklar

PHP26 paket `111ec4c16b042f337dce6af5`, SHA256 `26ef752c696dd112326c27bce44161d4cf43e653001733e92609d95094217632`,3262 dosya. Yalnız `/test` yayımlandı; ana kök değişmedi, kurucu kaldırıldı, özel kaynaklar kapalı. Tam suite122/474 PASS (07:28.631); yeni logo sonrası HTTP10/91, son erişilebilir bağlantı düzeltmesi sonrası ilgili6/51 PASS. Kamu gezinmesi aynı belge içinde iki motorda geçti; özel sepet/hesap/ödeme/yönetim normal güvenli yüklemeyi korur. Yeni kaynaklar yazılırken eski JSX/Next kaynaklarına veya NODENO deposuna yazılmadı.

Orijinal iPhone ekranındaki uzun boşluk başlangıçta sabit ve iPhone13 benzetiminde yeniden üretilemedi. Normal belge akışı, kökte yumuşak kaydırmanın kaldırılması, sınırda sabit/clipped live region, kapalı dialogların gizlenmesi, viewport/geri konumu ve mobil16px kontrollerle sertleştirme yapıldı. Testlerde belge yüksekliği footer sonunda biter; gerçek iPhone klavye aç/kapat ve toolbar testi yapılmadı. Başlangıçta olmayan kusur yeniden üretilmiş gibi sunulmaz.

Son logo talebi: S simgesi yazının üstünde ortalı. `scripts/build-php-stacked-logo.py` mevcut onaylı path geometrisiyle açık/koyu SVG üretir; ölçülen merkez farkı0.000031px. Yatay kaynaklar ve diğer sohbetlerin marka dosyaları değiştirilmedi. Header/footer/yaş ekranında yeni app/ varlıkları kullanılır; ekstra slogan eklenmez.

Kalan eşdeğerlik: NODENO ana sayfa raf/kategori kompozisyonu ve tam kategori hiyerarşisi; header dil/ülke/para seçimi ve hesap menüsü; guest favorileri, mevcut adedi artırmadan toplu ekleme; karşılaştırma; sahiplikli/sürümlü özel listeler ve açık aktarım; arama önerileri/yazım toleransı; zengin gerçek görsel/varyant galerisi ve medya yönetimi. Kanonik gerçek katalog/görsel/işletme ve dış sağlayıcı onayları ayrıca bekler. Bunlar tamamlandı veya bütün NODENO sistemi birebir taşındı denmez. Başlangıç komutu mevcut yayın için `python scripts/publish-php-test.py --verify`; yeni geliştirmede önce bu matristeki açık satıra regresyon yaz.


Son logo/menü düzeltmesi: [kategori ve footer yayın kaydı](php-category-footer-release.md). Güncel yayın `10396efcfb5b01e868f6f8cc`,123/482 test PASS; ana kök değişmedi. Kategori/logo/ikonlar iki motor ×5 boyutta uzakta da geçti. Tedarikçi kapsamı ve gerçek erişim engelleri: [xShopum / Liona / Sistina](php-supplier-research.md). Eski PHP26 paketinin mobil kategori dialogu kabul edilmedi; güncel kabul tam sayfadır.

Sonraki teknik kontroller: hızlı incelemenin üst fiyatı seçilen varyantla birlikte güncellenmeli (sunucu tahsilat fiyatı zaten varyanttan hesaplanır); footer KVKK belge türü `privacy-notice` ile yönetimdeki `privacy` seçeneği aynı onaylı belge sözleşmesine bağlanmalı, gizlilik politikası ayrı kalmalı. Stok filtresinin aday başına Inventory sorgusu büyük gerçek katalog öncesi toplu sorguya çevrilmelidir. Bu açık işler hukuk/ürün onayı veya tam NODENO eşdeğerliği varmış gibi kapatılmaz.

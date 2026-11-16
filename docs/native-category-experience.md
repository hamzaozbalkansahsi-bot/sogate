# Kategori gezintisi ve ürün filtreleri

16 Kasım 2026 kullanıcı görsellerine göre SEXOGATE için hazırlanır. Tek mağaza yapısı korunur. Satıcı mağazası, hızlı satıcı, sponsorlu satıcı şeridi, uydurma puan/yorum, geri sayım veya indirim etiketi eklenmez.

## Kullanım

- Alt menüde Kategoriler, gerçek ürün fotoğraflı iki sütunlu kısa kartları açar. Yalnız vitrinde ürünü bulunan kökler gösterilir; kaynak katalog silinmez.
- Kök seçildiğinde üstte yatay kök sekmeleri, solda alt kategori menüsü, sağda görselli alt kategoriler açılır. Tümünü gör doğrudan ilgili ürün listesine gider. Soldaki alt kategori seçimi o bölümün ürünlerini gösterir.
- Kategori ve bölüm URL ile paylaşılır. Geri düğmesi seçili bölüme döner. Mobil arama üstte kalır. İlk kategori HTML’si de aynı kart/gezinti düzenini içerir.
- Ürün listesinde sıralama ve filtreler yatay şerittedir. Marka, renk, beden ve yalnız kısa açık malzeme bilgisi olan kayıtlar için malzeme; ayrıca fiyat ve kategori sunulur. Desteklenmeyen kalıp/hızlı teslimat/kupon filtreleri gösterilmez.
- Her alan tek seçimlidir; Tümü o alanı temizler. Filtrele/Uygula ile URL güncellenir. Etkin alan adedi ve kaldırılabilir seçimler görünür. Temizle, kategori/arama/koleksiyon bağlamını korur. Fiyat alt sınırı üst sınırdan büyük olamaz.
- Beden ve renk, kaynakta kayıtlı varyant eksenlerinden alınır. Matris modunda yalnız aktif birleşimler eşleşir. Kamu bulunabilirliği depo stoğuna dönüştürülmez. Filtrede XL seçmek sepette XL seçilmiş sayılmaz; sepete ekle adımında ürünün bütün gerekli seçenekleri yine doğrulanır.
- Sıralama, filtreleri korur; sayfa yenileme ve derin bağlantı aynı sonucu açar. Mevcut sayfalama ve favoriler korunur. Filtre sayıları model bazlıdır, stok adedi değildir.

## Mimari

`native-store/storefront/category-core.js` saf seçenek/filtre kuralları; `category-renderers.js` erişilebilir HTML; `category-ui.js` arama ve çekmece odağı; `category.css` marka görünümü; `categories.php` ilk kategori yanıtı; `category-copy.json` 11 mevcut dil için metinlerdir. `category-build.mjs`, TypeScript AST ile yalnız türetilmiş yayına bağlar. `native-store/upstream` değiştirilmez. Sunucuda Node kullanılmaz.

Mevcut native katalog istemciye güvenli kamu projeksiyonu olarak gelir; filtre/sıralama bu projeksiyonda çalışır. Bu değişiklik sunucuda katalog sorgu motoru veya yeni ticari stok entegrasyonu değildir. Yeni marka/beden/malzeme/bölüm parametreleri sunucu ve istemci SEO’sunda noindex,follow kullanır; canonical temel kategoriye döner. Diğer ürün liste SEO kuralları kaynak motorundadır; sıralama garantisi verilmez.

## Doğrulama ve yayın

Durum: yerel kabul tamamlandı; sunucu önizlemesi kuruldu, uzak kabul sürüyor. Etkin `/test` henüz değiştirilmedi. Paket `b1dc3d43d52fecf813c301a9`, SHA256 `17d8a96a25d7529fabcd7726af3d9c46bd5bae12bc2cf4376c45667633b4fc91`. Yerel kanıt `docs/native-category-local-results.json`: 39 Node, 23 PHP varyant, 18 katalog, 14 içerik; iki motor / 33 yönetim + 9 müşteri rotası; 11 dil + 3 oturum içi geçiş. Yeni kategori kabulü yayın kapısına eklenmiştir; eski sürümün kanıtı kullanılamaz.

Komutlar:

```powershell
node --test scripts/test-native-categories.mjs
python scripts/test-native-category-browser.py
python scripts/build-native-stage.py
```

Tarayıcı testi Chromium ve WebKit’te 360/390/430/768/1440 genişlik, gerçek fotoğraf, bölüm/geri dönüş, beden/renk/marka, sıralama, geçersiz fiyat, seçenek seçmeden eklememe, arama, RTL, klavye çekmecesi ve JavaScript kapalı ilk kategori HTML’sini sınar. Fiziksel cihaz ve tüm WCAG sertifikasyonu değildir. Genel platformun ödeme/ülke/işletme/hukuk kabulü ayrı açık işlerdir; tahsilat kapalı kalır.

# Yerel görsel doğrulama — 11 Kasım 2026

## Son kaynak sürümünün yeni ekranları — 09:19 İstanbul

320 kaynak dosyalık manifestteki optimize uygulama 127.0.0.1:3000 üzerinde 94/94 Chromium/WebKit E2E ile doğrulandı. Yeni ekranlar gerçek sunucu/DB akışından gelir; benzersiz yerel ürün/kupon/personel fixture'ları kullanılır ve production'a taşınmaz. Tüm test sonucu [test-evidence.md](test-evidence.md) içindedir.

| Ekran | Masaüstü | Mobil |
| --- | --- | --- |
| Ödeme öncesi gerçek toplam | [Chromium](screenshots/checkout-quote-chromium-desktop.png), [WebKit](screenshots/checkout-quote-webkit-desktop.png) | [Chromium](screenshots/checkout-quote-chromium-mobile.png), [WebKit](screenshots/checkout-quote-webkit-mobile.png) |
| Lotlu satın alma önizlemesi | [Chromium](screenshots/purchase-lot-preview-chromium-desktop.png), [WebKit](screenshots/purchase-lot-preview-webkit-desktop.png) | [Chromium](screenshots/purchase-lot-preview-chromium-mobile.png), [WebKit](screenshots/purchase-lot-preview-webkit-mobile.png) |
| Lotun satın alma/belge kaynakları | [Chromium](screenshots/purchase-lot-sources-chromium-desktop.png), [WebKit](screenshots/purchase-lot-sources-webkit-desktop.png) | [Chromium](screenshots/purchase-lot-sources-chromium-mobile.png), [WebKit](screenshots/purchase-lot-sources-webkit-mobile.png) |
| Ülke adres profili | [Chromium](screenshots/address-profile-chromium-desktop.png), [WebKit](screenshots/address-profile-webkit-desktop.png) | [Chromium](screenshots/address-profile-chromium-mobile.png), [WebKit](screenshots/address-profile-webkit-mobile.png) |

CSS görünüm alanları 1440×1000 ve 390×844'tür. Chromium DPR1, WebKit DPR2: modal PNG'leri sırasıyla 1440×1000/390×844 ve 2880×2000/780×1688. Ödeme tam sayfa PNG'si Chromium1440×1957/390×3338, WebKit2880×3914/780×6676; yüksek dosya ölçüsü daha geniş CSS ekran testi anlamına gelmez. Ölçüler Sharp metadata ile okundu.

Son kaynakta Chromium mobil ödeme görüntüsü yeniden açılıp incelendi; daha önce ödeme WebKit masaüstü/mobil, lotlu kabul mobil ve lot kaynakları mobil görüntüleri açılıp incelendi. Açık krem alışveriş yüzeyi, beyaz toplam kartı ve bordo birincil düğme korundu; ürün/indirim/kargo/toplam/dahil vergi ayrı okunuyor. Örnek test hesabı 123,45−12,35+69,00=180,10 TRY; dahil vergi18,52 toplam üzerine yeniden eklenmiyor. Bu rakamlar gerçek kampanya veya canlı vergi onayı değildir. Lot önizlemesinde SKU/lot, kalan miktar, belge ve karantina ayrımı görünür; uzun kaynak kimlikleri satıra yayılır. Modal gerektiğinde dikey kaydırılır, kapatma odağı görünürdür.

Yeni formların otomatik Axe ve yatay taşma kontrolleri geçti; ana sayfa 360/390/430/768/1440 px kapsamı genel koşudadır. Adres profilindeki checkbox genişlik taşması uygulama CSS'sinde düzeltildi; içerik kırpma veya testi gevşetme kullanılmadı. Bazı ödeme PNG'lerinde klavye odağındaki “İçeriğe geç” bağlantısı görünür; bu bağlantı yalnız odakta açılır ve görseli güzelleştirmek için gizlenmez.

Bu kontroller tam manuel WCAG/ekran okuyucu veya gerçek iOS cihazı kabulü değildir. Önceki ana sayfa/logo karşılaştırması aşağıda tarihsel kapsamıyla korunur. Yerel illüstrasyonlar gerçek katalog fotoğrafı, SVG yeniden yorum da onaylı kaynak vektör değildir.

## Önceki ana sayfa çekiminin ortamı ve yöntemi

Çalışan standalone sürüm `http://127.0.0.1:3004` üzerinde headless Chromium ile incelendi. Bu adres yereldir; canlı yayın veya üretim satış onayı değildir. HTTP ana sayfa yanıtı 200 olarak görüldü.

Görüntülerde daha önce kabul edilmiş giriş durumunu göstermek için yalnız tarayıcıya `sexsogate_adult=yes` çerezi verildi. Sayfa `networkidle` ve `document.fonts.ready` sonrasında yakalandı. Yaş bildirimi uygulamadan kaldırılmadı; bu görsel çekim, ayrı yaş/klavye testinin yerine geçmez. Kaynak kodu, ürün, stok, fiyat veya sipariş verisi değiştirilmedi.

## Önceki ana sayfa ekran görüntüleri

| Dosya | Tarayıcı görünümü | Gerçek PNG ölçüsü |
| --- | --- | --- |
| [Masaüstü ana sayfa](screenshots/home-desktop.png) | 1440×1000, tam sayfa | 1440×3378 |
| [Mobil ana sayfa](screenshots/home-mobile.png) | 390×844, tam sayfa | 390×4791 |
| [Masaüstü ilk görünüm](screenshots/preview-desktop.png) | 1440×1000, yalnız görünüm alanı | 1440×1000 |

Üç PNG dosyası üretildikten sonra görsel olarak açılıp incelendi. Bu dosyalar önceki geliştirme sunucusu görüntülerinin yerine güncel standalone çıktılarıdır. Yeni görüntülerde geliştirme rozeti veya hata katmanı görülmedi. Tarayıcının `pageerror` olay listesi bu çekimde boştu.

## Ana sayfa taşma kontrolü

| Görünüm genişliği | Belge genişliği | Yatay belge taşması | Ekran dışında kalan görünür düğme/bağlantı düğmesi/form kontrolü |
| --- | --- | --- | --- |
| 360 px | 360 px | Yok | 0 |
| 390 px | 390 px | Yok | 0 |
| 430 px | 430 px | Yok | 0 |
| 768 px | 768 px | Yok | 0 |
| 1440 px | 1440 px | Yok | 0 |

Kontrol `document.documentElement.scrollWidth` ile `window.innerWidth` karşılaştırmasını ve görünür kontrollerin ekran sınırlarını ölçtü. Bu tablo yalnız ana sayfanın bu Chromium çekimini kapsar; tüm ödeme, yönetim, RTL veya gerçek telefon sayfalarının eksiksiz testi olarak sunulmaz.

## Yerel katalog ve nesne eşleşmesi

`GET /api/catalog` yanıtında altı ürünün tamamı `fixture=true` idi. Ekran görüntülerindeki ürün adları güncel kayıtlarla eşleşiyor. Eski kurdele/kimono/seyahat çantası adlarının yerine nesne türüyle uyumlu güncel kayıtlar görülüyor.

| Güncel fixture adı | Görsel | İncelenen nesne |
| --- | --- | --- |
| Yakınlık Aksesuar Halkaları | `/media/atelier-05.svg` | Birbirine bağlı halka çifti |
| Bordo Duyusal Maske | `/media/atelier-01.svg` | Göz maskesi |
| Kadife Saklama Kesesi | `/media/atelier-04.svg` | Saklama kesesi |
| Krem Bakım Şişesi | `/media/atelier-06.svg` | Bakım ambalajı / şişe |
| Atelier Saten Gecelik | `/media/atelier-02.svg` | Gecelik silueti |
| Yakınlık Hediye Kutusu | `/media/atelier-03.svg` | Hediye kutusu |

Ana sayfadaki seçili dört kart API sırasındaki ilk dört kaydı gösteriyor. Altı kaydın dosya eşleşmesi katalog yanıtından kontrol edildi. İllüstrasyonların nesne türü uyumu; malzeme, üretici, ambalaj içeriği veya gerçek ürün fotoğrafı doğrulaması değildir. “Saten” ve “kadife” gibi fixture metinleri ticari ürün kanıtı sayılmaz. Gerçek SKU fotoğrafları ve kullanım hakları hâlâ gereklidir.

## Referans kimliğiyle görsel karşılaştırma

- Marka adı **SEXSOGATE** ve slogan **Tutkunu Keşfet.** korunmuş. Header ve footer wordmark'ı kırpılmıyor veya eğilmiyor.
- Serif başlıklar, açık krem alışveriş yüzeyleri, bordo kampanya/footer ve sınırlı gül metalik simge kullanımı referansın yazılı yönünü izliyor. Sayfanın tamamı koyu yüzeye çevrilmemiş. Alan yüzdeleri için mekanik piksel kotası ölçülmedi.
- Kemer içindeki S, küçük boynuzlar ve kuyruk açıkça görülebiliyor. Metalik efekt formlara veya alışveriş metnine taşınmamış.
- 390 px görünümde hero metni ile simge üst üste binmiyor; kategori kartları tek, ürün kartları iki sütuna düşüyor. Fiyatlarda kesilme görülmedi.
- Model fotoğrafı, sahte yorum/puan/takipçi, doğrulama rozeti ve tescil simgesi taşınmamış. Referanstaki kişinin fotoğrafını kullanma hakkı verilmediğinden soyut kumaş/kemer görseli kullanılması bilinçli farktır.

## Küçük simge kanıtı

`public/brand/favicon-16.png`, `favicon-32.png` ve `profile-48.png` dosyaları yeniden oluşturulmadı. Mevcut PNG'lerin gerçek ölçüleri Sharp metadata okumasıyla sırasıyla **16×16**, **32×32** ve **48×48** olarak doğrulandı. Mevcut ölçek kontrol görseli ve gerçek 16/48 px PNG'ler yeniden açılıp incelendi; dağıtıma yakın kanıt için kontrol görseli [buraya](screenshots/icon-scale-check.png) kopyalandı. Dosyanın büyütülmüş gösterimi yeni yüksek çözünürlüklü simge teslimi değildir.

32 px ve 48 px kullanımda S, boynuz ve kuyruk ilişkisi seçilebiliyor. 16 px kullanımda S silueti ve boynuzlar korunurken iç kemer çizgileri kaynaşıyor; bu sürümde küçük geometri sadeleştirilmiş. Gerçek işletim sistemi sekmesi, tarayıcı kısayolu ve telefon ana ekranı üzerinde cihaz testi yapılmadı.

## Açık görsel ve ürünleştirme işleri

- Raster referanstan yapılan logo yeniden yorumu, kaynak vektörün birebir teslimi veya tasarımcının son sadakat onayı değildir. İnce kıvrımlar ve metalik ışık dağılımı kaynakla aynı değildir; özgün düzenlenebilir logo kaynağı ve son marka kontrolü açık kalır.
- Ürünler hâlâ yerel illüstrasyon ve fixture kayıtlardır. Gerçek fotoğraf, üretici belgesi ve SKU bazlı görsel onayı olmadan canlı katalog tamamlanmış sayılmaz.
- “Çiftlere özel” koleksiyon kartında genel kese silueti kullanılıyor. Gerçek çift ürünleri geldiğinde koleksiyon çağrışımını daha doğrudan anlatan hakları doğrulanmış görsel seçilmelidir.
- Bu önceki çekim ana sayfaya aittir. Yeni ödeme/adres/satın alma görüntüleri üst bölümde ayrı izlenir; hiçbir çekim tüm tasarımın eksiksiz onayı değildir.
- Gerçek iPhone/iPad, Android cihaz, iOS Safari dokunma/klavye davranışı ve kullanıcıların yüzde 75'lik saha performansı ölçülmedi. Chromium ekran boyutu emülasyonu gerçek cihaz kontrolü olarak adlandırılamaz.

Bu rapor yalnız mevcut yerel görüntüyü ve ölçülen sınırları doğrular; canlıya hazırlık, hukuk, ödeme kabulü veya gerçek katalog onayı vermez.

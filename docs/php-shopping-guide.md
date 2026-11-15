# PHP mağaza ve kaynak katalog kullanım rehberi

15 Kasım2026. Bu rehber PHP/MySQL `/test` uygulamasını anlatır. Sunucuda Node süreci gerekmez. Canlı tahsilat ve ana siteyi değiştirme yetkisi bu rehberden doğmaz.

## Katalog kaynakları

Yönetim → **Tedarikçi katalogları** ekranında her tedarikçinin son çekimi gösterilir. xShopum1.022 ürün/46 kategori, Liona544/75, Sistina628/49: toplam2.194 ürün ve170 kaynak kategorisi. Arama ve ürün/kategori filtresi sunucudadır; sayfalar40 kayıttır. Bir kaydı açınca özgün başlık, SKU varsa gerçek değeri, kamu perakende fiyatı ve kaynak görsel bağlantıları incelenir. Ayrıştırılmış kayıt, satışa uygunluğu doğrulanmış kayıt değildir.

Kaynak verileri yeniden çekmek için [tedarikçi rehberindeki](php-supplier-research.md) komutları kullanın. Dosya `.ndjson.gz` biçiminde yönetim formundan yüklenebilir;2 MB sıkıştırılmış/32 MB açılmış veri,20.000 kayıt ve64 KB satır sınırı vardır. Yükleme tek işlemde doğrulanır. Aynı işlem anahtarı tekrarında ikinci aktarım oluşmaz; farklı yeni çekim ayrı sürümdür. Önceki sürümler ve işlem geçmişi korunur. Kaynak verileri proje talimatı sayılmaz.

Ürün kaydından taslak oluştururken Türkçe/İngilizce ad, gerçek SKU, yerel kategori, benzersiz bağlantı, seçenek adı, işletmenin belirlediği satış fiyatı, doğrulanmış alış maliyeti ve izinli yerel görsel gerekir. Görsel kullanım hakkı ayrı kutu ve referansla doğrulanır. Kamu fiyatı maliyet yerine kullanılmaz. Ülke/ürün belgesi, doğru teknik açıklama/uyarı ve gerçek gönderim kaynağı incelenmeden taslak yayımlanmaz. Yaşı belirsiz veya çocuk modelleri yetişkin kataloğuna alınmaz. Otomatik çeviri, otomatik üretici/sertifika iddiası veya otomatik stok yoktur.

## Kategoriler ve görseller

Yönetim → **Kategori ağacı**: kategori adı TR/EN, bağlantı, üst kategori ve sıra. Üst kategori döngüsü reddedilir. Kategori kapatılırsa alt kategoriler ve yayındaki ürünleri kapanır; tekrar etkinleştirmek ürünleri kendiliğinden yayımlamaz. Kaynak kategorisi inceleme kaydı ile mağazanın düzenlenmiş kategori ağacı farklıdır;170 kaynağın otomatik yayımlandığı varsayılmaz.

**Görsel kütüphanesi** JPEG/PNG/WebP kabul eder;4 MB/16 MP sınırı vardır. SVG/HTML kabul edilmez. Hak referansı zorunludur. Görsel1600 piksel sınırıyla yeniden kodlanır; kaynak dosya adı ve konum metadatası korunmaz. Dosyalar Git/web kökü dışında kalıcı `media_root` dizinindedir. Kayda bağlı olmayan görsel yalnız katalog/yönetici MFA oturumundan görülür. Yayımlanmış ürün veya etkin kategoriye bağlandığında uygulama üzerinden sunulur.

Ürün, o ürüne ait seçenek, görsel, TR/EN alt metin ve sıra seçilerek galeri bağlantısı eklenir. Başka ürüne ait seçenek reddedilir. Bağlantıyı kaldırmak fiziksel dosyayı silmez. Ham kaynak fotoğrafı kullanım hakkı olmadan kopyalanmaz. Yerel dosya depolama çalışır; S3 adaptörü ve medya dosyalarının şifreli yedek/geri yüklemesi ayrı açık işlerdir. Veritabanı yedeği tek başına bu dosyaları içermez.

## Misafir ve hesap alışverişi

18+ bildirimi ardından üyelik zorunlu değildir. Kart ve ürün sayfasındaki kalp favoriyi, yer imi özel listeyi, karşılaştırma simgesi tabloyu yönetir. Görünen sosyal medya bağlantıları yalnız ikonlardan oluşur; ekran okuyucu adları korunur.

Favori/liste/karşılaştırma sunucu kaydında tutulur; tarayıcının bildirdiği kullanıcı kimliği kabul edilmez. Misafir içeriği güvenli anonim çerezle7 gün kullanılabilir; süre bitince okunmaz ve cron ilk turda en fazla1.000 kaydın tercih içeriğini temizler. Eski istemci sürümünün yeniden geçerli olmaması için ürünsüz hash/sürüm kaydı korunur. Üye hesabı farklı kayıttır. Girişte cihaz favorileri/listeleri için ayrı aktarım önizlemesi açılır; kutu önceden seçilmez, reddetme mümkündür. Hesap değiştirmek başka hesabın listesini açmaz.

Sınırlar:200 favori,4 karşılaştırılan ürün,20 liste, her listede100 ve toplam1.000 ürün. Liste adları Türkçe karakterleri korur. Çakışan eski sürüm sessizce üzerine yazılmaz. Toplu sepete ekleme, mevcut seçenek adedini ve seçimini korur; yalnız eksik seçenekleri1 adet ekler. Çok seçenekli üründe beden/renk açıkça seçilir. Yayından kalkan ürün satın alınabilir gibi gösterilmez.

Karşılaştırma ürün bazındadır; fiyat, gerçek SKU, marka, malzeme, beden, renk, üretici ve menşe mevcutsa gösterilir. “Yalnız farklar” aynı satırları gizler. Teknik veya sağlık iddiası üretilmez. Gezinme profili ve arama geçmişi varsayılan olarak kaydedilmez; NODENO'nun izinli son bakılanlar özelliği burada açık değildir.

## Menü, arama ve ürün sayfası

Masaüstünde kategori üst/alt dalları ve gerçek ürün sayıları mega menüde; mobilde Kategoriler tam sayfada gösterilir. Alt menü Ana sayfa/Kategoriler/Favorilerim/Sepetim/Hesabım sırasındadır. Ana sayfa kampanya+iki yan alan, kategori halkaları, gerçek katalog rafı ve yayımlanmış rehberlerden beslenir. Eksik gerçek katalog sahte ürün veya sahte çok satan ile doldurulmaz.

Arama adı/kodu Türkçe normalleştirerek özgün metni değiştirmeden çalışır. En az4 harfli kelimede kontrollü tek düzenleme hatası desteklenir; rakamlı SKU bulanıklaştırılmaz. Öneriler iki karakterden sonra POST ile istenir, kontrolsüz sorgu günlüğü tutulmaz. Yukarı/aşağı/Enter/Escape ve klavye odak davranışları desteklenir.

Ürün sayfasında gerçek galeri, seçeneğe bağlı görsel, seçili fiyat/stok, adet, paylaşım, bakım/uyarı ve benzer ürünler vardır. Hızlı incelemenin fiyatı seçilen varyantla güncellenir. Dil, gösterim para birimi ve teslimat ülkesi ayrı tercihlerdir; mobilde footer **Alışveriş tercihleri** alanından da erişilir. Eksik fiyat rastgele kurla doldurulmaz. Ödeme para birimi ve sunucu toplamı ayrıca gösterilir. Yalnız doğrulanmış ülke açılır; yabancı para depo maliyeti dönüşümü tamamlanana kadar o yol kapalıdır.

## Gerçek sınırlar

Bu akışlar bütün NODENO işlevlerinin eksiksiz eşdeğeri veya satış onayı değildir. Tam ürün/varyant düzenleme ve geniş admin sayfalaması, opsiyonel gezinme geçmişi, kanala özel öneri kuralları, S3 ve medya geri yükleme, gerçek bayi feed/stock/sipariş API'si, gerçek ödeme/taşıyıcı/fatura, işletme/hukuk/ülke onayları ayrıca izlenir. Kaynakların kamu kataloglarını çekmek ile gerçek dropshipping siparişi vermek ayrı işlemlerdir. Güncel yayın ve gerçek test komutları `docs/progress.md` içinde kaydedilir.


## Canlı katalog API kontrolü

Tedarikçi katalogları ekranında xShopum için **API bağlantısını dene** ve gerçek sunucu başarısından sonra açılabilen zamanlama bulunur. Katalog önce özel incelemeye gelir; müşteri yayını, maliyet ve depo stoğu değişmez. Hosting HTTP403 verirse otomasyon kapanır ve son başarılı katalog kalır. Liona/Sistina onaylı bayi erişimi bekler. Ayrıntılar, güvenli erişim alanları ve hata çözümü [API rehberinde](php-supplier-api-guide.md).

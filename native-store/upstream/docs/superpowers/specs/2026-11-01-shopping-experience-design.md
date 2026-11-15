# NODENO alışveriş deneyimi

Kullanıcı, yalnız görsel bir yenileme yerine Trendyol'un mobilya alışverişinde yararlı akışlarının NODENO'da gerçekten çalışmasını istedi. Masaüstü ve mobil, dört dil ve RTL aynı kapsamda ele alınır. Marka renkleri/fontları/logoları ve onaylı gerçek ürün verileri korunur.

## Uygulanacak akışlar

1. Klavye ve dokunmayla çalışan ürün/kategori araması; ürün kodu normalizasyonu, kontrollü yazım hatası toleransı, temizlenebilir son aramalar ve anlaşılır boş sonuçlar.
2. Kaynaktaki açık Genişlik/Yükseklik/Derinlik sırasına dayanan ölçü filtreleri ve ürünün girilen alana uygunluk kontrolü. Eksik ölçü tahmin edilmez; ayarlanabilir aralıklar kesin uyum gibi sunulmaz.
3. En fazla dört gerçek varyantı fiyat, renk, ölçü, malzeme ve kapsamıyla karşılaştırma; yalnız farklar, kaldırma, ürün bağlantısı ve seçimi taşıyan URL. Tek ürün/fark yok/eksik veri durumları tasarlanır.
4. Hızlı ürün inceleme, aynı modelin gerçek rengini seçme, miktarla sepete ekleme ve tam ürün sayfasına geçme.
5. Adlandırılabilir özel koleksiyonlar: oluşturma, yeniden adlandırma, ürünü ekleme/çıkarma, sepete aktarma ve açık silme onayı. Konuk koleksiyonları cihazda, üyelerin koleksiyonları kendi sunucu hesabında tutulur. Konuk listelerini aktarmak ayrı, açık kullanıcı eylemidir.
6. Sepette renk değiştirme, birleştirilen satırlarda adet sınırının korunması ve kaldırılan/boşaltılan sepeti kısa sürede geri alma. Favorileri topluca sepete eklemek mevcut adetleri artırmaz.
7. Gerçek son gezilenler, favori/koleksiyon gezinmesi, daha dengeli ana sayfa ve tekrar eden model sayısı azaltılmış ürün vitrinleri.

## Veri ve hesap sözleşmesi

Yeni koleksiyon API'si mevcut sepet/favori DTO'sunu değiştirmez. Ayrı kullanıcıya bağlı SQLite kaydı ve sürüm numarası kullanır. Güncel olmayan kayıt 409 ile reddedilir; başka cihazdaki liste sessizce ezilmez. En fazla 20 koleksiyon, koleksiyon başına 100, toplam 1000 ürün kaydı; ad 1–60 Unicode karakter. IDs 32 hex, ürünler güncel kataloğa bağlıdır. Same-origin, CSRF, oturum, kalıcı hız sınırı ve hesap silme kuralları uygulanır. Sosyal hesap birleştirmede koleksiyonlar da aynı atomik işlem içinde korunur; sınır aşımı bütün birleştirmeyi geri alır.

Ölçü ve karşılaştırma sayıları yalnız doğrulanmış ürün özelliklerinden gelir. Fiyatlar değişmez. Değerlendirme, satış adedi, indirim, teslimat tarihi, ücretsiz kargo veya stok uydurulmaz. Tek markalı mağazaya ilgisiz çok satıcılı pazar yeri programları eklenmez. Ödeme, gerçek sipariş ve Google/Apple sağlayıcı aktivasyonu önceki kullanıcı talimatına göre kurulum beklemeye devam eder.

## Görünüm

NODENO Sans ve kanonik lacivert/kırık beyaz/lime korunur. İlk ekranda ürünlere daha erken ulaşılır; yardımcı karar araçları ayrı ve kısa bir bölümde yer alır. Kartlarda fotoğraf ve fiyat önceliklidir; ikincil eylemler tutarlı boyutta ve erişilebilir adlarla sunulur. Mobilde araçlar alt gezinme, satın alma çubuğu veya klavye üzerine binmez. Karşılaştırma tablosu kendi içinde kayar; sayfayı yatay büyütmez. Native dialog, Escape, görünür odak ve hareket azaltma desteği kullanılır.

## Kabul

Saf arama/ölçü/karşılaştırma/sepet sınır testleri; gerçek PHP/SQLite ile koleksiyon sahipliği, CSRF, sürüm çatışması, sınır ve hesap birleştirme rollback testleri; dört dilde Chromium ve Windows WebKit, 320/390/768/1024/1440/1920 genişlikleri; gerçek dokunma/klavye, kaydırma ve odak kontrolleri. Yerel test ve canlı kabul ayrı kaydedilir. Kaynak katalog, fiyat ve medya sürümü mevcut canlı tabanla karşılaştırılır. Normal yayın aracı ve `publicationReady` kilidi korunur; canlıya alma ancak aynı paketin testleriyle yapılır.

## Araştırma sınırı ve kaynaklar

Anonim Trendyol ana sayfası, mobilya listesi, erişilebilen ürün sayfaları ve resmî yardım rehberi incelenir. Kişisel hesap, gerçek ödeme veya sipariş yapılmaz; kapalı akışlar canlıda denenmiş gibi raporlanmaz. Kullanıcının daha önce verdiği uygulama ekranları da referanstır. NODENO'ya ait olmayan ürün fotoğrafı, kullanıcı yorumu, puan veya kampanya aktarılmaz.

- https://www.trendyol.com/
- https://www.trendyol.com/mobilya-x-c1119
- https://www.trendyol.com/yardim/islem-rehberi
- https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines
- https://github.com/anthropics/skills/tree/main/skills/webapp-testing

Kurulumlar kullanıcı tarafından açıkça istendi. İncelenen beceri dosyaları sabit Git revizyonlarından kuruldu ve SHA-256 ile eşleştirildi; marka/dil/erişim kuralları bu becerilerden üstündür. Yerel araştırma kanıtı `artifacts/commerce-research/` dizinindedir.

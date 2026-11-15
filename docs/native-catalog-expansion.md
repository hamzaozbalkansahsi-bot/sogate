# Vitrin kapsamının genişletilmesi — 15 Kasım 2026

<!-- BEGIN NATIVE_FIRST_PAINT_DELIVERY_20261115 -->
## Gerçek yayın sonucu

554e78f543311a4d7e250b89 yalnız `/test` üzerinde etkin. Yönetimde 2.194 kaynak, vitrinde 468 ürün; 1.726 taslak, 50 kategori tanımı ve 18 dolu alt kategori doğrulandı. Önizleme ve yayın sonrası gerçek yönetici oturumunda %30 fiyat, 11 dil alanı/SEO, 12 orijinal medya SHA256 örneği, tekrar güvenliği, CSRF ve özel taslak erişimi geçti. Aynı yüklemenin tekrarı ikinci ürün/fiyat/sürüm üretmedi; 450 yeni onay ve önceki18 ile toplam468 korunuyor.

Katalog büyümesi ve ilk HTML düzeltmesi aynı güncel test sürümündedir. Yeni ilk görünüm `native-first-paint.md`, tam kabul ve açık engeller `native-deployment-report.json` içindedir. Bunlar bütün galerilerin, üretici belgelerinin, insan çevirisinin veya gerçek satışın onayı değildir.
<!-- END NATIVE_FIRST_PAINT_DELIVERY_20261115 -->

Vitrinin küçük görünmesinin nedeni veri kaybı değildi: yönetimdeki 2.194 kaydın yalnız 18 kapak fotoğrafı incelenip yayımlanmış,172 kaynak kategori altı ana gruba indirgenmişti. Bu görev, mevcut izinli kaynak verisinden ürün görünürlüğünü ve alt kategori ağacını genişletir. Kaynak kamu fiyatı +%30 kuralı korunur; fiyatı bulunmayan43 ürün ücretsiz sayılmaz. Üretici/barkod/belge/maliyet veya fiziksel stok uydurulmaz.

`scripts/expand-native-catalog-review.py`, kaynakta bulunabilir gözlenmiş ve fiyatı olan 1.399 adayın orijinal kapaklarını özel inceleme paftalarına indeksledi. Özgün dosyalar değişmedi. İlk 640 adayın00–09 paftaları incelendi; 454 aday seçildi, 186 aday bu partide seçilmedi. Önceden onaylananlarla toplam 468 farklı ürün kapağı vardır. 759 aday henüz incelenmedi; geri kalan kaynak kayıtları fiyat, bulunabilirlik, görüntü veya ürün incelemesi bakımından ayrı kalır. Yalnız kapak onayı, bütün galerinin veya satışın onayı değildir. Özel karar dosyası `review/expansion/decision.json`; dosya hash'leri `review/approved.json` içinde tutulur. Müşteriye kaynak sansür rozetini başka yöntemle kaldırma/dönüştürme yapılmadı.

`scripts/native_catalog_taxonomy.py`, değişmez ürün kimliklerini koruyarak 50 düğümlü kategori ağacı üretir. Altı ana grup korunur; gece kıyafeti, jartiyer, body, sütyen, külot/tanga, pijama, sabahlık, korse, çorap, büyük beden ve ilgili oyuncak/bakım türleri alt kategoridir. Liona'nın ürün adını tekrar eden breadcrumb öğeleri ayrı kategori olmaz.172 kaynak kategori özel kaynak incelemesinde kalır;50 mağaza kategorisiyle aynı şey değildir. İlk 468 görünür ürün 18 alt kategoriyi dolduruyor; kalan tanımlı alt kategoriler incelenen ürün geldikçe görünür olur, boş kategori vitrinde çoğaltılmaz. Mevcut 11 dil için kategori adları sağlanır; bu çalışma ürün metinlerinin insan çeviri onayı değildir.

Yönetimde **Ürünler → Ürünleri yükle** yeni veri sürümünü 40'lı işlemlerle işler. Yeni kapak incelemesi yalnız ilk aktarımından beri değiştirilmemiş, yayımlanmamış, sürüm 1 taslağı yükseltebilir. Verinin geri kalanı önceki ilk aktarım ile aynı olmalıdır. Elle değiştirilmiş fiyat/metin veya gizlenmiş ürün ve geçmişte yayımlanmış kayıt korunur. Normal yetki, güncel MFA, CSRF, sürüm ve idempotency kontrolleri sürer. Para veya stok onayı arayüzden alınmaz.

Yerel kabulün ardından yalnız `sexogate.com/test` için önizleme ve yayın yapılır. Ana site korunur. Tahsilat kapalıdır. Yerel/uzak test sonuçları ve gerçek yayımlanmış sayılar `docs/progress.md` içinde kaydedilecektir; bu paragraf dağıtımın tamamlandığı anlamına gelmez.

Görsel aracıyla Liora'ya iç giyim giydirme denemesi ayrı bir iştir: `docs/liora-product-catalog-study.md` içinde araç reddi kayıtlıdır, çıktı oluşmadı. Görsel üretim reddi katalog yüklemesinin teknik engeli değildir. [OpenAI görsel belgesi](https://developers.openai.com/api/docs/guides/image-generation), isteklerin içerik filtresinden geçtiğini açıklar; belirli denememizde hangi ayrıntının tetiklediği doğrulanmış değildir. 15 Kasım 2026 kontrolü.

Yerel pafta aracı mevcut **Pillow 12.3.0** ile çalıştırıldı; sunucu çalışma bağımlılığı değildir. Fotoğraf paftaları özel D: alanında tutulur, Git veya herkese açık mağaza dosyası değildir. Önizleme ve aktif `/test` aynı test veritabanını kullanır; yönetimden ürün yayımlama, uygulama giriş dosyasının atomik geçişinden ayrı bir veri işlemidir. Dosya rollback'i ürün kayıtlarını geri çevirmez. Eski şifreli veritabanı yedeği ayrıca korunur.

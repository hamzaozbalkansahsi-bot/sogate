# Ürün özellikleri görünümü

Satın alma alanındaki eski üç sütun kaldırıldı. Ölçü, renk ve uzun özellik metni aynı yüksekliğe zorlanmaz. Adet ve sepete ekleme önce gelir; ardından en fazla dört kısa bilgi ve **Tüm özellikleri gör** bağlantısı bulunur.

Ölçüler yalnız kaynakta genişlik/yükseklik/derinlik sırası açıkça yazıyorsa ayrı alanlara bölünür. Aralıklar ve ondalık değerler korunur. Belirsiz sırada özgün ölçü metni kullanılır. Malzeme, adet veya özellik tahmin edilmez. Teknik verisi bulunmayan `3312` ve `4006` için ölçü üretilmez.

Tam teknik bölümde ölçü, renk ve paket bilgileri okunabilir alanlara ayrılır. Diğer satırlar özellikler, malzeme/yapı, kurulum, bakım/temizlik ve diğer bilgiler olarak gruplanır. Kısa gerçek özellik listeleri madde halinde; uzun veya başlıklı anlatımlar tek sütun metin olarak sunulur. Her kaynak teknik satır ve değeri tam bölümde bir kez korunur. Yer kazanmak için bilgi kırpılmaz.

Yalnız gövde, kapak veya üst modül olarak satılan on üründe mevcut doğrulanmış dört dilli kapsam notu ayrıca satın alma düğmesinden önce gösterilir. API'deki isteğe bağlı `scopeNote` alanı doğrudan kanonik kimlik notunun kopyasıdır. Bu ek alan dışındaki 667 ürünün adı, kodu, fiyatı, açıklaması, teknik satırları ve görsel bağları aynı kalır.

Ürün içi bağlantılar galeriyi, adedi veya açılmış bölümleri yeniden oluşturmaz. Bölüm hedefi gerçek sabit başlığın yüksekliğine göre konumlanır ve klavye odağı hedefe gider. Aynı ürün içindeki geri gezinme DOM'u korur. Doğrudan bölüm bağlantısı ve sayfa yenilemesi, katalog/oturum yüklenmesi tamamlanınca hedefe ulaşır. Ctrl/Meta ile bağlantı açma tarayıcının normal davranışını kullanır.

Türkçe, İngilizce, Rusça ve Arapça ile RTL aynı kapsamda uygulanır. Teknik değerlerdeki HTML karakterleri güvenli biçimde kodlanır; yeni alanların HTML olarak çalıştırılmasına izin verilmez. Yerel enjeksiyon kontrolü gerçek ürün verisine veya canlı sisteme yazmaz.

İncelenen bilgi hiyerarşisi örnekleri: [Hepsiburada ürün bilgileri](https://www.hepsiburada.com/adore-mobilya-country-4-cekmeceli-sifonyer-mat-lake-beyaz-90x89x45-cm-gxyxd-pm-HBC00004FU99I), [Trendyol öne çıkan özellikler](https://www.trendyol.com/adore-mobilya/white-genc-odasi-tek-kisilik-karyola-beyaz-99x103x195-cm-p-833273087). Resmî sayfa içerikleri kısa özellik/tam açıklama ayrımını doğruladı. Bu sitelerin Chromium erişimi 403 verdi; engel aşılmadı ve rakip mobil piksel görünümünün doğrulandığı iddia edilmez. NODENO görünümü kendi gerçek yayın paketiyle ayrıca kontrol edilir.

Kaynaklar: `web/product-specs.js`, `web/app.js`, `web/styles.css`, `lib/catalog.mjs`. Veri ve birim kontrolleri `tests/product-specs.test.mjs` ile kimlik testlerindedir. Gerçek paket kabulü `artifacts/product-specs/` altında, tam yayın kabulü `artifacts/qa/production-release.json` ve teslim kaydında tutulur. Çizili fiyat için yeni indirim oranı seçilmedi; mevcut +%40 fiyatları ve kapalı tahsilat korunur. 42 eski PDF kaydının siteye eklenmesi de değerlendirmede kalır.

# Masaüstü mağaza ve ortak alışveriş akışları

Durum: **Canlıya alındı ve gerçek HTTPS üzerinden doğrulandı.** Sürüm `15f6d6545fba84ea36da775d434f738a2a17bef301ff3d1ac7392ddf3376d9a8`, doğrulama 2026-11-01T03:27:39.501691+00:00. Ana kayıt: `artifacts/desktop-storefront/delivery-record.json`.

## Görünüm ve kullanım

- Masaüstü ana sayfada gerçek ürün fotoğraflarıyla kampanya alanı, oda kısayolları, altılı ürün rafları ve yatak/çalışma/salon vitrinleri bulunur. Vitrin sayıları varyant adedi yerine gerçek model sayısından hesaplanır.
- Listelerde kategori ağacı seçili dalı açar. Görselli alt kategori kısayolları ve kaldırılabilir seçili filtreler gösterilir. Fiyat aralığı, renk ve sıralama arama/kategori seçimiyle birlikte çalışır; bağlantıda ve tarayıcı geçmişinde korunur.
- Fiyat sıralaması doğrulanmış kuruş tutarlarını kullanır; fiyatı bilinmeyenler iki yönde de sona gelir. Etkin fiyat aralığı fiyatı bilinmeyen ürünü içermez. Renk filtresi aynı modelin seçilen gerçek varyantını bulduktan sonra modelleri gruplar.
- Hesap oturumu arka planda yüklenirken henüz uygulanmamış fiyat/renk filtreleri ve odak kaybolmaz. Taslak yalnız mevcut formda tutulur; hesap veya parola alanları bu işlemde kopyalanmaz.
- Geniş ürün sayfasında dikey küçük fotoğraflar, büyük galeri, fiyat/renk/adet/satın alma alanı ve NODENO teslimat/destek sütunu vardır. Özellik sekmeleri masaüstünde sabit kalır; hedef başlık menünün altında gizlenmez.
- Mobil galeri, fotoğraf büyütme, sabit satın alma alanı ve alt gezinme devam eder. Aynı gerçek filtreler mobil Filtrele penceresinden uygulanır.
- Sepette kompakt ürün satırları, sağ tarafta ara toplam ve Devam et alanı, ayrıca gerçekten ilişkili ürünler bulunur. JSON/TXT indirme, yazdırma ve Görsel kullanımı açıklaması kaldırılmıştır.
- Üyelik, adres, yardım ve diğer sayfalarda aynı masaüstü ölçüleri, paneller ve gezinme kullanılır. Google/Apple arayüzleri hazırdır; sağlayıcı yapılandırması tamamlanmadan açılmaz. Misafir adımları ödeme öncesine kadar çalışır; ödeme/sipariş oluşturma kapalı kalır.

## Doğrulama

Kaynak: 162/162 test, 0 atlama. Dağıtım: 18/18 Python testi. Normal derleme ve paket doğrulaması geçti. Gerçek PHP yayın paketi, Chromium ve Windows WebKit üzerinde dört dilde 20 mağaza senaryosu, 40 ürün sayfası ve 32 galeri kontrolünden geçti. Kaydırma senaryoları gerçek Chromium dokunma girdisi, dikey sayfa hareketi, büyütülmüş pencere eşlemesi, klavye ve yeniden boyutlandırmayı da içerir. Bunlar fiziksel iPhone testi değildir.

Yenilenen kaynak arayüzünde sosyal giriş seçenekleri 48 görünüm ve 8 hesap akışında doğrulandı. Kimlik tamamlama/parola oluşturma/bağlantı kaldırma için yalnız geçici test veritabanına eklenen doğrulanmış kimlik fikstürü kullanıldı. Gerçek Google/Apple sağlayıcı kabulü değildir.

Windows WebKit, mevcut canlı sürümün arama formu satırında da bir inline-style CSP tanısı veriyor; yerelde JavaScript kapalıyken aynı tanı görüldü. Playwright ekran görüntüsü hazırlığı ayrıca inline `body{}` stili ekliyor. Bu tanılar ayrı kaydedildi; üretim CSP’si gevşetilmedi. Yeni kategori girintileri inline CSS yerine veri öznitelikleri ve harici stil dosyasıyla çalışır. Uygulama çalışma zamanı hatası ve sayfa taşması denetimleri ayrıdır.

Yerel kanıtlar: `artifacts/desktop-storefront/local-report.json`, `review.json`, `csp-baseline.json`, `before-live.json`; ürün/galeri raporları `artifacts/product-page/local-report.json` ve `artifacts/inline-gallery/local-report.json`. Canlı kabul aynı paket özetiyle ayrıca kaydedilir.

Yayın öncesi karşılaştırmada canlı taban `02efc3db7efcdc592c1e887900b6dbfcf3470a741ae026bc7179dfd9e48f4e70` ile 667 ürünün tamamı, 104 kategori, fiyatlar ve medya sürümü eşit bulundu. Medya sürümü `557e3ba73d5bf21426518dd2be426a613a97767d742a1f7f248e9ec8b109260a` korunur. Diğer sohbette temizlenen görseller eski sürüme döndürülmez; kalıcı hesap ve medya kökleri korunur.

Canlı kabulde aynı 20 mağaza senaryosu, 40 ürün sayfası ve 32 galeri kontrolü geçti. Dört alan adının güvenilir HTTPS erişimi, 30 varlık SHA-256 değeri, 13 özel yolun kapalı kalması ve 15 medya örneği doğrulandı. Google/Apple durum API’si iki sağlayıcı için de hazır/bağlı=false döndürdü; dış sağlayıcı kurulumu yapılmadı. Yedek: `/home/nodenoho/nodeno-backups/20261101T032140Z-15f6d6545fba-1a081c`.

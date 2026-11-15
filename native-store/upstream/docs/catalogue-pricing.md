# NODENO ürün fiyatlandırması

10 Kasım 2026 talimatı: Adore için koşulsuz güncel satıcı fiyatı üzerine **%30**, Alka Ahşap ve Altın İş Ağaç için **%20** ilave edilir. Eski NODENO satış fiyatı yeniden çarpılmaz.

Hesap tam sayı kuruşla, yarım yukarı yuvarlamayla yapılır. Adore 8.099,25 TL → 10.529,03 TL; diğer iki tedarikçide 85,00 TL → 102,00 TL. Havale indirimi gibi koşullu tutarlar ve çizili liste fiyatı esas alınmaz. Adore tam SKU, ürün kimliği, görünür fiyat, Product/Offer, güncellik ve belge hash doğrulaması korunur. Son taramada 667 kaydın 665 fiyatı doğrulandı; GRD-1330-BB-2 ve AGT-144EL-BB-1 için fiyat atanmadı.

Alka Store API ve görünen sayfa fiyatları ayrı doğrulanır. Varyantlı ürünün başlangıç fiyatı bütün seçeneklere verilmez; 148 varyant ayrıca kendi teklifinden alınır. Açık sayfa “Fiyat İçin Bize Ulaşın” diyorsa sıfır satış fiyatı kullanılmaz. Altın İş'te teknik açıklamaya eklenmiş pazarlama SKU'su yerine görünür Stok Kodu korunur. Görünür KDV dahil tutar yapılandırılmış teklifle karşılaştırılır. Kaynakta fiyat yoksa ürün korunur, fiyat boş kalır.

Fiyat yenilemesiyle eski tarihli yönetim fiyat istisnaları yeni baz fiyatın önüne geçmez; başlıklar, stok notları ve diğer düzenlemeler korunur. Yenilemeden sonra yetkili yönetici yeni özel fiyat yayınlayabilir. Geçerli kampanyalar yeni baz fiyata uygulanmaya devam eder. Kanıtlanmamış önceki fiyat veya indirim iddiası oluşturulmaz. Geçmiş sipariş ve alışlar yeniden fiyatlandırılmaz.

Kur prensibi değişmedi: haftanın TCMB döviz satış kurları arasındaki en yüksek oran kullanılır. Tedarikçi stoğu NODENO stoğu sayılmaz. Ödeme ve sipariş oluşturma bu çalışma nedeniyle açılmaz.

Kanıtlar data/catalog-prices.json, artifacts/catalog-expansion/price-pages ve artifacts/supplier-expansion altındadır. Yeni HTML arşivleri kayıpsız gzip sıkıştırılmış olabilir; read_archive bunları açar, asıl yanıt SHA-256 özeti korunur. Orijinal görseller korunur. Müşteri vitrini için medya, dil ve birim incelemesi ayrıca gerekir.

Tedarikçiler ve alışlar ekranı gerçekleşen alışları perakende fiyatlardan ayrı tutar. Yeni fiyat listesi CSV olarak yüklenir, önceki onaylı listeyle karşılaştırılır ve açıkça onaylanır. Göktaş gibi listeyle çalışan firmalar için 15 günlük hatırlatma vardır. Adımlar [yönetim kılavuzundadır](yonetim-kilavuzu.md).

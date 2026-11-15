# Ürün sayfası ve paylaşım

Ürün sayfası, kullanıcının verdiği mobil mağaza örneklerine göre NODENO kimliğiyle düzenlenir. Ana fotoğraf mobilde daha geniştir; kırpılmadan gösterilir ve büyütmeden kaydırılır. Fotoğraf üzerindeki favori düğmesi, fotoğraf noktaları, masaüstü önizlemeleri ve büyütülmüş galeri aynı seçimi izler. Üst başlıkta bilinen renk eki ayrılır; teknik kaynak ve SKU değişmez.

Sabit satın alma alanı gerçek fiyatı, Şimdi al ve Sepete ekle düğmelerini içerir. Miktar seçimi ürünün asgari sipariş ve artış kuralına uyar; standart adet seçiminde üst sınır 99’dur. Şimdi al, seçili ürünün seçili rengini ve miktarını sepete yazar, diğer ürünleri silmeden yalnız bu ürünü seçip teslimat ve fatura bilgileri akışına geçirir. Sepete ekle mevcut miktara ekler. Şimdi al düğmesi tek başına karttan tahsilat yapmaz; ödeme, son kontrol ve sözleşme onayından sonra Stripe üzerinden tamamlanır. Ödeme durumu sunucuda doğrulanır.

Ürün hakkında bölümünde tekrarlanan ad/ölçü/renk/kod cümlesi gösterilmez. Gerçek kaynak açıklamaları ve bileşen kapsam notları korunur. Kaynak özelliklerinin kısa maddeleri öne çıkarılır; renk ve ürün kodu ayrı bilgi satırlarında yer alır. Teknik bilgilerin tamamı mevcut gruplu özellik alanında kalır.

Tedarikçi ürünlerinde uzun açıklama ayrıca yüklenir. Bağlantı sürerken kısa bir yükleme durumu görünür. Sunucu hatası, geçersiz yanıt veya 20 saniyeyi aşan açıklama isteğinde mevcut ürün özeti korunur ve “Yeniden dene” düğmesi gösterilir. Miktar ve seçili görsel sıfırlanmaz. Para birimini değiştirmek veya sayfayı yeniden çizmek otomatik tekrar isteği başlatmaz; kullanıcı düğmeye basarak yeniden dener. Uyarı, yükleme ve düğme metinleri mağazanın 11 dilinde gösterilir; Arapça ve Farsça sağdan sola yerleşir.

12 Kasım 2026 düzeltmesinin hata/yeniden deneme kontrolleri `tests/browser/supplier_details_recovery.py` üzerinden çalışır; tam sürüm kabulü `tests/browser/native_locales.py` içindedir. Kontrol, önce HTTP 503, ardından geçersiz içerik ve sonrasında gerçek açıklamayı kullanır; miktarın korunmasını ve kendiliğinden tekrar istek gönderilmemesini de doğrular. Kanıtlar `artifacts/storefront-followup-20261112` altındadır. Bu testler gerçek sipariş veya tahsilat oluşturmaz.

Bu düzeltmenin canlı sürümü `f9453eba124fed16cd7a10fef7e064d542bfe6fd257b9aa17e14feec9b9cfec2`: 379 Node + 244 Python testi, 14 yerel tarayıcı senaryosu ve üç canlı tarayıcı senaryosu geçti. Dört alan adı ve 11 dilin HTTP/yasal sayfaları doğrulandı; mobil Türkçe, masaüstü Almanca ve 320 piksel Farsça görünümü gerçekten incelendi.

Teknik bilgilerin altında ürün koduyla destek sorusu gönderme bağlantıları, doğrulanmış değerlendirme durumu, seçim rehberi, ürünün kaynak kurulum/bakım/paket bilgilerini kullanan sık sorulan sorular, favori işlemi, benzer ürünler, gerçek kategori koleksiyonları, aynı alan için diğer ürünler ve varsa son gezilenler bulunur. Koleksiyonlar katalog kategorilerine açılır. Ortak modelin renkleri öneri raflarında yinelenmez. Birlikte satın alma, yıldız, yorum sayısı, satıcı puanı, stok aciliyeti, kampanya veya kesin teslimat tarihi üretilmez.

Paylaş düğmesi mobilde alt panel, masaüstünde diyalog açar. Son kullanıcı talimatına göre panelde yalnızca Bu ürünü paylaş başlığı ve WhatsApp, Facebook, X, e-posta, SMS, kopyala ile destekleyen cihazlarda diğer paylaşım seçeneklerinin ikonları vardır. Açıklama, ürün özeti, görünür bağlantı/metin kutusu, dosya seçimi ve fotoğraf indirme bulunmaz. Normal durumda durum metni de boş kalır; yalnız kullanıcı işleminin sonucu veya hatası kısaca bildirilir.

Türkçe paylaşım metni “Görmeni istediğim bir ürün var; [ürün bağlantısı]” biçimindedir. İngilizce, Rusça ve Arapça karşılıkları da vardır. Başka renk seçilirse o rengin SKU bağlantısı kullanılır. WhatsApp, X, e-posta ve SMS bağlantıları metni ilgili uygulamanın desteklediği URI parametresine ekler. Facebook kendi paylaşım penceresini ürün bağlantısıyla açar; gönderi açıklamasını zorla doldurduğumuz iddia edilmez. Kopyala metni ve bağlantıyı kopyalar. Diğer ikonu mevcutsa cihazın yerel paylaşım menüsüne metin ve bağlantıyı gönderir. Açılır panel metni ekranda göstermez.

Native ekran görüntüsü algılama ve ekran görüntüsü dosyası ekleme, kullanıcının son düzeltmesiyle bu web yayınının kapsamından çıkarılmıştır. Tarayıcıya hayali screenshot olayı veya fotoğraf erişimi eklenmez. Fotoğrafın bağlantı önizlemesinde görünmesi Open Graph verisiyle sağlanır; gerçek görüntülemeyi ve önbelleği hedef uygulama yönetir.

Ürün bağlantısının ilk HTML yanıtında ürün adı, kapak fotoğrafı ve kanonik NODENO URL’si için Open Graph bilgileri yer alır; botların JavaScript çalıştırması gerekmez. HTML değerleri kaçışlanır; istemcinin gönderdiği Host, dış alan adı veya sorgu parametreleri paylaşım başlığına taşınmaz. Önizleme önbelleği ve son görünüm hedef paylaşım platformuna bağlıdır.

Tekrar çalıştırılabilir kontroller `tests/product-presentation.test.mjs`, `tests/browser/product-page.mjs` ve `tests/browser/product-gallery.mjs` dosyalarındadır. Yerel paket ve canlı kabul ayrı `artifacts/product-page/` raporlarına yazılır. İkonlar, seçili SKU bağlantısı, görünür metin kutusu olmaması, hata ve iptal sınanır. İşletim sistemi aktarımının test köprüsü ayrıca açıkça etiketlenir; gerçek WhatsApp/Facebook gönderimi veya fiziksel iPhone testi yapılmış gibi sunulmaz.

Google/Apple giriş hazırlığı ayrı sonraki aşamadır. Bu ürün sayfası yayını, sağlayıcı girişlerini aktif hale getirmez.

Paylaşım marka ikonlarının path verisi [Simple Icons](https://github.com/simple-icons/simple-icons) projesinden alınır; yerelde script, harici referans veya font içermeyen SVG olarak tutulur. CC0 lisansı `docs/licenses/simple-icons.txt` dosyasındadır.

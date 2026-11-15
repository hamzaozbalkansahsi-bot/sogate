# NODENO mağaza akışları uygulama planı

Kapsam: kullanıcının 31.10.2026 tarihli Hepsiburada masaüstü/mobil akışları ve önceki PAZVION çalışmasını temel alma talebi. Çalışma yalnız Nodeno klasöründe yapılır; PAZVION kaynağı salt okunur incelenir. Canlı marka/katalog başlangıç kaydı `47ded76`, Turhost PHP sürümü `a0cc1a0f3db5c098b59ad12157a884705e1a0d5145a4d94832003225ee621767`.

1. Hepsiburada'nın erişilebilir resmî sayfaları ile PAZVION'un canlı ve yerel kaynağını incele. Gözlemlenen davranışı, erişilemeyen özel hesap ekranlarını ve demo verilerini ayrı kaydet.
2. NODENO kimliğiyle yoğun mağaza başlığı, arama önerileri, çok seviyeli kategoriler, vitrin/ürün sıraları ve mobil alt gezinmeyi uygula. Gerçek olmayan puan, satış, indirim, fiyat veya teslimat vaadi ekleme.
3. Ürün listesi/filtreleri, detay/galeri, sepet ve favorileri ayrı bağlantılı sayfalar olarak tamamla. Misafir verisini koru; oturum açınca hesaba birleştir ve cihazlar arası kalıcı olarak sakla.
4. Gerçek sunucu oturumlarıyla kayıt/giriş/çıkış, profil/parola, kullanıcıya ait adresler, siparişler ve kargo görünümünü uygula. Parolaları yalnız güvenli özet olarak sakla; CSRF, sahiplik ve deneme sınırlarını doğrula. Kullanıcı verisi sürüm dizininin ve tüm web köklerinin dışında kalır.
5. Dört dil, Arapça RTL, yardım/iletişim, mobil menü/filtreler, klavye ve boş/hata durumlarını doğrula. Eksik fiyat/ödeme/yasal işletme bilgisi nedeniyle sipariş oluşturma/tahsilat açılmaz; sahte sipariş veya kargo kaydı üretilmez. E-posta teslimatı yapılandırılmadan parola sıfırlama gönderildiği söylenmez.
6. Gerçek PHP üzerinde iki kullanıcı, oturum, CSRF, veri sahipliği ve kalıcılık testlerini; 1366/768/390 tarayıcı akışlarını çalıştır. Paket bütünlüğü ve gizli bilgi taramasından sonra yedekli Turhost yayını yap. Gerçek HTTPS üzerinde sürümü, hesap akışlarını, .com bağlantılarını ve mobil görünümü doğrula.

Yayın hedefi aynı Turhost hesabıdır. Yeni bir Sites/Firebase yayını oluşturulmaz. Mevcut 667 ürün, 104 kategori, 5.129 kaynak görsel bağlantısı ve orijinal marka/font dosyaları korunur. Kullanıcı Google Drive aşamasını erteledi; bütün onaylı görseller doğrudan Turhost'un özel kasasına yüklenir.

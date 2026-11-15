# Ana sayfanın ilk görünümü

15 Kasım 2026 kullanıcı ekran görüntüsü: sayfa ilk açılırken büyük, yeşil arka planlı eski kampanya gösteriliyor; katalog isteği tamamlanınca küçük resimli kartlara geçiyordu. Korunmuş motorun sunucu tarafı SEO şablonu eski ana sayfayı üretiyor, yeni istemci bileşeni daha sonra onu değiştiriyordu. Önceki görsel testler sayfa yüklendikten sonraki durumu sınadığı için ilk HTML uyuşmazlığını kaçırmıştı.

`native-store/storefront/home.php`, ilk HTML'yi gerçek yayımlanmış katalogdan küçük resimli kategori kısayolları, dört kampanya kartı ve seçili ürün rafıyla üretir. İstemcinin kullandığı aynı CSS sınıfları uygulanır. Ana sayfa başlığı, etkin kampanya tercihi ve 11 dil, mevcut kaynaklardan okunur. Arayüz etiketleri derleme sırasında mevcut dil sözlüklerinden alınır; ikinci bir çeviri listesi oluşturulmaz. Fiyat ve görünürlük sunucudaki yayımlanmış kayıttan gelir. Yeni fotoğraf, stok, yorum veya üretici bilgisi üretilmez.

Ana sayfa gövdesi gizlenmez, yapay yükleme ekranı eklenmez. NODENO snapshot'ı değiştirilmez; derlenmiş sunucu SEO sayfasına yalnız SEXOGATE sunum bağlantısı eklenir. Sunucuda Node gerekmez.

`scripts/test-native-first-paint.py`, eski62d adayında `FIRST_HTML_USES_LEGACY_HOMEPAGE` ile RED verdi. Yeni554e78f543311a4d7e250b89 adayında gerçek HTTP HTML'si ve JavaScript kapalı Chromium/WebKit,390/1440px görüntüleri dört küçük resimli kartı doğruladı.11 dilin HTML/başlık/RTL kontrolleri ayrıca çalıştırılır. Dağıtım aracı aynı sürüme bağlı yerel ve önizleme ilk görünüm kanıtını zorunlu tutar.

Yeni adayın yerel kabulü tamamlandı: Chromium ve WebKit'te 33 yönetim ve 9 müşteri rotası, 5 genişlik, MFA/oturum, görsel düzen, yaş bildirimi, katalog ve 11 dil geçti. Kurucunun 22 güvenlik/geri yükleme kontrolü de geçti. Bu sonuçlar `.local/native-*-local.json` kanıtlarında aynı sürüme bağlıdır; komut çıktıları `D:/sexogate-local-artifacts-20261114/native-paint-local-*.log` altında korunur.

Yeni aday henüz sunucuda etkin değil. Önizleme ve yayın sonrası kabul sonuçları `docs/progress.md` içine kaydedilir. Önceki önizlemedeki aralıklı SSL/ağ bekleme hataları bu tasarım hatasından ayrıdır; ilk HTML düzeltmesi bu hataların giderildiği iddiası değildir.

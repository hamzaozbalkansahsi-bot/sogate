# PHP25 test yayını — 14 Kasım 2026

Adres: https://sexogate.com/test/. Etkin paket `7f9c90294d9c9e6b64b9cf64`; SHA256 `5282db97eafc8045c7e3081ee81f5a5f5e3d4325e2f52d6336ae80dfadf4f355`. Kaynak checkpoint'i `044bd5c`. Ana hazırlanıyor sitesi, DNS ve diğer sohbetlerin Next/TypeScript kaynakları korunur. Gerçek tahsilat kapalıdır.

## Kullanıcının son isteği

- Görünür geliştirici/tasarımcı kredisi kaldırıldı; kaynak dosya başlıkları korundu.
- İlk girişte Liora portresi, bordo kemer ve krem yüzeyle yetişkin giriş ekranı hazırlandı. Onay sonrası içerik hesapsız açılır; misafir alışverişi korunur.
- Ana kampanya aynı görsel dille yenilendi. Ürün/sepet/bilgi yüzeyleri açık kalır.
- Normal/maskeli uygulama ikonları, favicon, Apple Touch Icon ve `/test/` kapsamlı manifest eklendi. Gerçek telefon kurulumu henüz test edilmedi. Önceden eklenen ikonsuz kısayol için kaldırıp `/test/` üzerinden yeniden ekleme gerekebilir.
- Yönetim erişim kapısı, oturum, rol ve MFA korumaları devam eder. Yaş beyanı hukuki güçlü doğrulama yerine geçmez.

## Gerçek kabul kanıtları

| Kontrol | Sonuç |
| --- | --- |
| PHP tam test koşusu |104 test /387 assertion PASS,06:11.704 |
| PHP syntax, JS syntax, Composer strict validate/audit | PASS; bilinen güvenlik bildirimi0 |
| Yerel paket kurulumu ve güvenlik sınırları | Manifest,25 migration, aktivasyon, tek kullanımlık token ve ZIP traversal PASS |
| Uzak genel deneyim | Chromium/WebKit ×360/390/430/768/1440,10 senaryo PASS |
| Uzak erişilebilirlik/mahremiyet |18 sayfa, açık yaş ekranı, axe AA etiketleri, klavye/odak/çıkış/taşma ve izleme isteği kontrolü PASS |
| Uzak operasyon | İki motor,15 admin sayfası ve ürün→stok→misafir test sipariş→kısmi sevk→karantina/iade/para iadesi; CSV ve tedarikçi kaydı PASS |
| Yayın sınırı | Ana site aynı; özel dosyalar kapalı, kurucu kaldırılmış |
| Worker | Gerçek PHP8.3.36 cron heartbeat ok=true |
| Yedek geri yükleme | Yayın öncesi23→25; yayın sonrası82 tablo/546 satır/91 FK, hash ve checksum PASS |

Tarayıcı testi gerçek iPhone/Android kurulumu veya bütün manuel WCAG ölçütleri değildir. Laboratuvar kontrolü saha performansı iddiası değildir. Stripe SDK testleri gerçek hesap/kategori kabulü değildir. Gerçek taşıyıcı veya mali fatura entegrasyonu test edilmedi.

## Ekran görüntüleri

- [Mobil yaş ekranı](screenshots/php-public-remote/chromium-age-390.png)
- [Masaüstü yaş ekranı](screenshots/php-public-remote/chromium-age-1440.png)
- [Mobil vitrin](screenshots/php-public-remote/chromium-home-390.png)
- [Masaüstü vitrin](screenshots/php-public-remote/chromium-home-1440.png)

## Açık kapsam

Ülke/fiyat/vergi ve SKU/model/taşıyıcı uygunluğunun temel servis/HTTP/admin akışları vardır; kur/adres editörleri ve uluslararası müşteri seçimleri tamamlanmadı. Depo maliyetinin yabancı para snapshot dönüşümü tamamlanana kadar bu checkout yolu kapalıdır. Gizlilik başvuruları/saklama, tam katalog/varyant düzenleme, medya/S3 ve diğer kapsamlı yönetim özellikleri sürer.

Gerçek satıcı ve katalog, ürün belgeleri, ödeme işletme/kategori kabulü ve anahtarlar, kargo/fatura/SMTP, onaylı hukuk/ülke/vergi kuralları işletme veya dış erişim bekler. Bütün sistem tamamlandı ya da gerçek satışa hazır değildir. Kurulum/yayın/geri dönüş için [hosting rehberi](php-hosting-guide.md), kullanım için [operasyon rehberi](php-operations-guide.md), sıradaki iş için [ilerleme kaydı](progress.md) esas alınır. Gizli değerler bu belgelere veya Git'e eklenmez.

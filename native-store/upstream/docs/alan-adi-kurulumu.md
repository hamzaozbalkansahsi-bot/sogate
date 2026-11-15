# nodenohome.com Turhost yayını

Kullanıcı alan adını Turhost’tan aldığını ve yayının nodenohome.com.tr’ye bağlı hosting hesabından yapılmasını istediğini doğruladı. cPanel sunucusu HTTPS üzerinden doğrulandı.

- Hosting hesabının ana alanı: nodenohome.com.tr
- Ortak web dizini: /home/nodenoho/public_html
- Web IP adresi: 94.199.205.78
- Ziyaretçi alan adları: nodenohome.com ve www.nodenohome.com
- DNS: CPNS1.TURHOST.COM ve CPNS2.TURHOST.COM

.com, aynı document root’u paylaşan alias olarak eklendi. .com’dan .com.tr’ye HTTP yönlendirmesi yapılmaz; göreli ürün, API, görsel ve varlık bağlantıları ziyaretçinin geldiği .com alan adını korur. Yerel dosyalar yalnız C:/Users/Hamza ÖZBALKAN/Desktop/Nodeno altında yönetilir.

| Tür | Ad | Değer |
| --- | --- | --- |
| A | nodenohome.com | 94.199.205.78 |
| CNAME | www.nodenohome.com | nodenohome.com |

Bu kayıtlar alias eklenirken Turhost’un DNS kümesinde oluştu. Her iki yetkili DNS sunucusu ve Google/Cloudflare çözümleyicileri doğrulandı. Mevcut .com.tr DNS alanı, MX, SPF, DKIM ve DMARC kayıtları değiştirilmedi. Kayıtları varsayılana döndürmek veya başka hizmetlerin kayıtlarını silmek gerekmez.

Önceki Sites özel alan adı planı, kullanıcının Turhost hosting talimatıyla yürürlükten kaldırıldı ve bekleyen Sites bağlamaları kaldırıldı. Eski A/TXT/CNAME değerleri uygulanmaz. Sites geçici adresi tarihsel sürüm olarak kalır; bu alan adlarının hedefi Turhost hosting hesabıdır.

31.10.2026 tarihinde bildirilen alan adı uyuşmazlığı giderildi. nodenohome.com, www.nodenohome.com, nodenohome.com.tr ve www.nodenohome.com.tr aynı dört alan adlı Let's Encrypt sertifikasıyla gerçek TLS doğrulamasından geçti ve HTTPS 200 döndürdü. Ziyaretçinin alan adı korunur. Sertifika SHA-256 değeri `732e090762e2c8642e1e12d2c6dca23a893d50f4c2ae12d2bbaf0256c9092fa1`, bitişi 29.01.2027 17:51:18 Türkiye saatidir. Kanıt `artifacts/ssl-status.json` dosyasındadır. AutoSSL özelliği hesapta kapalıdır; ücretli sertifika satın alınmadı. Yenileme yardımcısı elle çalıştırılır; zamanlanmış yenileme kurulmamıştır.

Mağaza, gerçek üyelik ve onaylı yerel görseller ortak web dizininden yayımlanır. Mobil/misafir düzeninin güncel canlı PHP sürümü `d53b68f4a8f278f7590e9f68aca9072a3c004fc9289848db3ceee3399faef2b2`, canlı kabul zamanı `2026-10-31T22:37:22.944Z` oldu. Gerçek HTTPS kontrolünde dört alan adı, 23 genel varlığın SHA-256 eşleşmesi, 13 kapalı özel yol ve 15 gerçek görsel yanıtı doğrulandı. Tüm 5.129 görsel referansının kasadaki baytları sağlık kabulünden geçti. Kanıt `artifacts/qa/live-report.json` içindedir.

Önceki mağaza yayınının tarayıcı kontrolleri dört dilde ve 1366/768/390 genişliklerinde geçti. Misafir katalog/sepet/favori akışları, 156 sayfa düzeni ve gerçek kayıt/giriş/adres/sunucu seçimleri doğrulandı; geçici hesap silindi. Tarihsel raporlar `artifacts/qa/shop-report.json`, `artifacts/qa/shop-layout-report.json` ve `artifacts/qa/shop-account-report.json` dosyalarındadır. Son katalog güncellemesi ayrıca dört dilde 1366/390 genişliklerinde, 381 kod/1.524 ad ve sepet/favori/arama/çıktı akışlarıyla gerçek canlı tarayıcıdan doğrulandı: `artifacts/catalog-pdf-audit/browser-live-report.json`.

Son yayın öncesi yedek `/home/nodenoho/nodeno-backups/20261031T223342Z-d53b68f4a8f2-8f59ef` konumundadır. Kalıcı hesap verisi ve medya kasası bu arayüz yayınıyla değiştirilmedi.

Panel erişim bilgileri yalnız Git'e ve yayın paketine alınmayan .env.local içinde tutulur. E-posta teslimatı ayrıca doğrulanmalıdır. İndirilen liste, sipariş veya gönderilmiş e-posta değildir; ödeme ve sipariş kaydı kapalıdır.

Resmî kaynaklar: [Turhost panel erişimi](https://destek.turhost.com/cpanel-whm-plesk-panel-girisi/), [cPanel ortak document root](https://docs.cpanel.net/cpanel/domains/domains/create-a-new-domain/).

Önceki tam katalog ve fiyat güncellemesinin 667 fiyat canlı kanıtı `artifacts/catalog-expansion/pricing-live-browser-report.json` içindedir. Önceki ürün özellikleri yayını dört dilde 84 canlı görünüm, 16 bölüm bağlantısı, 20 gezinme senaryosu ve 156 sayfa yerleşimiyle doğrulandı. Kanıtlar `artifacts/product-specs/live-browser-report.json`, `artifacts/product-specs/live-navigation-probe-report.json` ve `artifacts/qa/shop-layout-report.json` içindedir. Mevcut 667 fiyat korundu; çizili fiyat bileşeni gerçek indirim seçilmediğinden etkin değildir. 42 PDF kaydı kullanıcı değerlendirmesi için siteye eklenmeden bekler.

Önceki mobil kategori ekranı dört dilde 24 canlı görünüm ve 156 sayfa yerleşimiyle doğrulandı: `artifacts/mobile-categories/live-report.json`.

Önceki büyütülmüş galerinin dört dilde 14 canlı kabul kanıtı: `artifacts/photo-swipe/live-report.json`.

Önceki renk seçimi dört dilde 16 varyant görünümü ve 156 sayfa yerleşimiyle doğrulandı: `artifacts/color-variants/live-report.json`. 667 satış kaydı, mağazada 392 modeldir.

Güncel WebKit/Chromium mobil/misafir kabulü: `artifacts/mobile-guest/live-report.json` (216 ekran, sekiz akış); 156 genel yerleşim ve dört alan adlı HTTPS ayrıca doğrulandı. Tahsilat/sipariş kapalıdır.

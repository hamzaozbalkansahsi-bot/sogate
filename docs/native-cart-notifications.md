# Ürün düğmeleri, sepet ve stok bildirimleri

Güncel `/test` paketi `b1dc3d43d52fecf813c301a9`; kategori deneyimi eklendi. Buton/sepet/API davranışı aynı pakette yerel, önizleme ve etkin adreste iki motorda yeniden geçti. Yeni kanıt [kategori rehberi](native-category-experience.md) ve [yayın raporunda](native-deployment-report.json); aşağıdaki 324b855 kaynak/test sonuçları önceki teslimin tarihsel kanıtıdır. Gerçek cihaz push teslimi hâlâ doğrulanmadı.

16 Kasım 2026 kullanıcı kapsamı: ürün eylemleri düzgün hizalanır; sepet, verilen mobil örnekteki ürün seçimi/adet/toplam/öneri düzenini SEXOGATE kimliğiyle kullanır; favori stok değişiminde cihaz bildirimi hazırlanır. Ana site ve gerçek tahsilat kapsam dışıdır.

## Uygulama

- Korunan `native-store/upstream` değişmez. Ürün eylemlerinde boş kalan üçlü grid yerine genişleyen bordo sepete ekle ve 52 px favori düğmesi kullanılır. Adet, karşılaştırma ve koleksiyon kontrolleri en az 44 px hedefe sahiptir. `/test` ürün paylaşımının URL doğrulaması da düzeltilir.
- Sepette gerçek seçili satırların ara toplamı, miktar ve beden/renk korunur. Ürün favorilere taşınabilir veya kaldırılabilir. Mobil alt toplam şeridi görünür alt navigasyon yüksekliğini izler; özeti erişilebilir dialog içinde açar. Öneriler yatay raf kullanır. Tahsilat kapalı olduğunda onay düğmesi kapalıdır. Yapılandırılmamış taksit, kargo bedava, teslimat tarihi veya kupon başarısı gösterilmez; bu iş bunların entegrasyonunu tamamlamaz.
- Footer'daki **Bildirim tercihleri** cihaz için açık izin alır. İlk sayfa yüklemesi bildirim izni istemez. Kullanıcı tüm favorilerinin stok takibini açmayı seçer; sonraki favori değişiklikleri aynı cihazın kayıtlarını günceller. Gerekli/analiz çerez izninden ayrıdır. İzin aynı pencereden geri alınır.
- PHP `sg_notify_*` tabloları mevcut özel kontrol SQLite veritabanındadır. Cihazın HttpOnly/Secure/SameSite=Strict rastgele çerezi hash ile sahiplik sağlar. Kayıtlar API seviyesinde cihazla sınırlanır. Origin/CSRF, IP ve cihaz hız sınırı, 100 favori sınırı uygulanır. Uç adresleri ve VAPID anahtarları AES-GCM ile özel state alanında şifrelenir; `.bin` dosyası mevcut şifreli yedek akışına girer. Abonelik/takip 90 günle sınırlanır.
- İşçi yalnız `stockKnown=true` ve doğrulanmış tamsayı `stockQuantity` ile stok dışı → stokta geçişini kuyruklar. İlk tarama, bilinmeyen stok veya kamu tedarikçi bulunabilirliği bildirim üretmez. Mevcut katalog fiziksel stok doğrulanmış sayılmadığından bugün gerçek stok olayı oluşturulmaz. Varyant bazlı tedarikçi stok eşlemesi ayrıca gerekir.
- Kalıcı işler kiralama, benzersiz olay, kontrollü tekrar deneme ve 404/410 abonelik iptali kullanır. Aynı olayın bildirim etiketi cihazda da aynıdır. Ağ kesintisinde kusursuz tek teslim garantisi verilmez. Gövde/ikon ürün adı, model fotoğrafı veya sipariş içeriği taşımaz; ayrıntı uygulamadaki ürüne açılır. Bu akış sipariş/kargo push olaylarının tamamlandığı anlamına gelmez.
- Service worker yalnız push/click dinler; hesap, sepet veya başka HTTP cevaplarını önbelleğe almaz. Yalnız aynı uygulama kapsamındaki bağlantı açılır. Sunucu yalnız bilinen Google/Mozilla/Apple Web Push uçlarına, doğrulanmış TLS, genel IPv4 DNS sabitlemesi ve sonlu süre ile gider; yönlendirme takip edilmez.

## Kullanım

1. Takip edilecek ürünleri favorilere ekleyin.
2. Footer → Bildirim tercihleri → Stok bildirimlerini aç.
3. Cihazın izin penceresinde izin verin. iPhone'da önce Safari paylaş menüsünden ana ekrana ekleyin.
4. Aynı tercih penceresinden Bildirimleri kapat ile sunucu kaydını ve cihaz aboneliğini kaldırın.

İzin verilmediğinde veya destek bulunmadığında başarı mesajı gösterilmez. Kilit ekranı tasarımını işletim sistemi belirler; web sitesi iOS izin penceresinin görünümünü kopyalayamaz.

## Kaynak ve bağımlılık

16 Kasım 2026 resmi kaynak kontrolü: [WebKit Web Push](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/), [Apple ActivityKit](https://developer.apple.com/documentation/activitykit), [Web Push PHP](https://github.com/web-push-libs/web-push-php), [Composer](https://getcomposer.org/download/). iOS Canlı Etkinlik biçimi ActivityKit/WidgetKit kullanan native iOS uygulaması gerektirir; bu PHP/PWA değişikliğiyle sağlandı denmez.

`native-store/notifications/composer.lock` tam bağımlılık çözümünü sabitler; `minishlink/web-push` 11.0.0 (MIT) kullanılır. Guzzle PSR-18 taşıyıcıdır. Vendor dosyaları değiştirilmez veya kaynak Git'e eklenmez; yerelde `php .local/composer.phar install --working-dir=native-store/notifications --no-dev --no-plugins --no-scripts` ile kurulur. Build sürüm kilidi ile kurulu paketleri karşılaştırır ve vendor'ı özel pakete kopyalar. Composer sağlayıcı SHA256 değeri doğrulanarak yalnız yerel araç olarak edinildi. Anahtarlar sohbet, ortam örneği veya kaynak koda yazılmaz.

## Mahremiyet ve açık kabuller

Google/Mozilla/Apple push servisi abonelik ucu ve aktarım metaverisini işler; içerik Web Push standardıyla şifrelenir. İşletmenin gerçek hizmet/veri aktarımı değerlendirmesi, saklama ve hukuk metni onayı canlı ticaret öncesinde tamamlanmalıdır. İşletim sistemi izni hukuki incelemenin yerine geçmez. Gerçek iPhone/Android teslimi, native Canlı Etkinlik, e-posta/SMS ve sipariş bildirimlerinin uçtan uca kabulü henüz yapılmadı.

## Gerçek test durumu

- İlk regresyon mevcut sürümde 360 px'de iki satır/92 px/pembe sepete ekle ile başarısız oldu; kaynağı eski üçlü sütundu.
- Ara yerel paket `64c4a09212a5b3fee6da36b7`: Chromium/WebKit, 360/390/430/768/1440, tek satır CTA, miktar/favori/karşılaştırma, zorunlu seçenek, paylaş ve RTL geçti. Bu ara paket yayımlanmadı.
- `php ... scripts/test-native-notifications.php`: 26 doğrulama geçti. Gerçek SDK şifreleme/VAPID üretimi yapıldı, teslim taşıyıcısı izole sahte istemciydi; dış cihaza teslim kanıtı değildir. Windows'ta paketle gelen OpenSSL yapılandırması yerel PHP işlemine sağlanır.
- `node --test scripts/test-native-notification-worker.mjs`: 4/4 geçti; mahrem gövde, kapsam dışı URL reddi, güvenli açılış, HTTP cache bulunmaması.
- `composer audit`: açık güvenlik tavsiyesi yok. Bu sonuç tam güvenlik sertifikası değildir.
- Sepet tarayıcı turu özetin geçici ödeme yükleme yazısını kopyaladığını saptadı. Kapalı ödeme için sepet özeti bu geçici hedefi kullanmayacak şekilde düzeltildi; nihai tekrar ve yayın kaydı aşağıda güncellenecek.

Aşağıdaki son kabul ve yayın kaydı bu ara durumun yerini alır.

Önceki sepet/bildirim tesliminin yerel paketi: `324b855ec1f632a73b3221a4`, varlık sürümü `1aba96a6cd66cd2e`, ZIP SHA256 `7320bcd3d17bda125e8829416caea1dad7f4856fd3b5821031b9d348ba220a17`. 1.300 dosya, 72 JS modülü; yayın satış kapalı. Kaynak ve paket PHP bildirim kontrolleri 26/26, ilgili Node kontrolleri 32/32 geçti. Kurucunun 22 izole kontrolü, aynı 1.300 dosyalı ön paket üzerinde güncel kurucu kaynağıyla geçti.

Kurucu testinin ilk 20 saniyelik istemci sınırı aşıldı; logda PHP'nin 30 saniyelik yürütme sınırı da doğrulandı. Yalnız kimliği doğrulanmış geçici bakım isteğine sonlu 90 saniye, test istemcisine 60 saniye ayrıldı. Dosya sayısı/boyutu, hash, sahiplik, token, ZIP yol/symlink kontrolleri korunur. Kötü ZIP reddi ve tutarlı şifreli SQLite yedeği 22 kontrol içinde gerçek çalıştı. Genel hosting veya güvenlik denetimleri kapatılmadı.

## Son kabul ve yayın — 16 Kasım

**Önceki sepet/bildirim tesliminde etkin sürüm: `324b855ec1f632a73b3221a4`.** Ana site aynı; gerçek tahsilat kapalı. Uygulama kaynağı `f52f18d` normal push edildi. Kanonik ayrıntı `native-deployment-report.json`; güvenli kısa sonuçlar `native-cart-local-results.json`, `native-cart-preview-results.json`, `native-cart-remote-results.json`.

Yerel ve özel önizleme aynı paket üzerinde dokuz kabul grubundan geçti: ürün eylemleri, sepet/bildirim API, varyant/bulk ekleme, tam yönetim 33 + müşteri 9 gezinme, gerçek katalog/SEO/içe aktarma, yaş/gizlilik, görsel düzen, JS kapalı ilk HTML ve 11 dil + üç gerçek istemci dil geçişi. Yayın sonrası ürün eylemleri ve sepet/bildirim API iki motorda, 360/390/430/768/1440 px'de tekrar geçti. Farklı cihazın aboneliğini okuma/değiştirme, Origin/CSRF, zararlı hedef ve geçersiz ürün engelleri gerçek HTTP ile doğrulandı. İzin isteme metodu gözlendi; kendiliğinden çağrılmadı.

Önceki 324b855 tesliminin sonuçları: Node 32/32; PHP bildirim 26/26, varyant/sipariş snapshot 23/23, katalog 18/18, içerik 14/14. Kurucu 22 kontrolü aynı yapıdaki ön paketle güncel kurucu kaynağında geçti; nihai paket ayrıca sunucuya hash doğrulamasıyla kuruldu. Gerçek yeni DB yedeği staging alanına geri yüklendi: 2 SQLite / 44 tablo / 10.147 satır, geçerli FK; SHA256 `45c5279b3ffcc94a903924a4c71478c8711a8b96327c9abb92bb25df5eb1856f`. Worker sağlıklı, bildirim sayacı 0; cron tek, diğer işler aynı. Medya geri yüklemesi yapılmadı.

İlk başarısız font/görsel/katalog denemeleri başarı sayılmadı. Görsel testteki 30 sn'lik ön bekleme, uygulamanın iki 20 sn okuma sınırından kısaydı: tüm kritik istekler beklenip ardından gerçek ürün bölümü doğrulanacak sıraya alındı. Yerel ve uzak tam görsel tekrar geçti. Yönetim yenilemesinde de kritik istek hazır olma kontrolü eklendi. Son bildirim API GET'inde ECONNRESET görüldü; Playwright'ın yalnız bu ağ hatasını bir kez tekrarlayan `max_retries=1` seçeneği kullanıldı. HTTP redleri, yazmalar, TLS ve sayfa hatası kontrolleri kaldırılmadı. Tam iki motorlu tekrar geçti. Sunucudaki aralıklı katalog yükleme/bağlantı hatalarının kökü ve saha performansı hâlâ açık risktir; fonksiyonel kabul performans garantisi değildir.

### Gerçek push denemesi ve açık sınırlar

Üç izole gerçek Chrome profiliyle deneme yapıldı. İzin `granted`, service worker `activated` iken native `PushManager.subscribe` `AbortError: Registration failed - permission denied` döndürdü; abonelik oluşmadı ve sunucuya POST aşamasına geçilmedi. Test cihazı kayıtları iptal edildi. **Gerçek bir cihazın bildirim teslimi doğrulanmadı.** İşletim sistemi/tarayıcı izni atlatılmadı. `scripts/test-native-real-web-push.py` negatif sonucu `.local/native-real-push-result.json` içinde tutar. Hazır abonelik oluşmadığı için tek kullanımlık bakım göndericisi çalıştırılmadı; Python/PHP sözdizimi kontrolleri yapıldı, gerçek gönderim başarısı iddia edilmez.

Tercih ekranı TR/EN; bu yinelemede push gövdesi/eylem metni Türkçedir. Doğrulanmış fiziksel veya uygun tedarikçi SKU stoğu bağlantısı olmadan kamu bulunabilirliğinden bildirim gönderilmez. iOS Canlı Etkinlik, native uygulama gerektiren ayrı açık iştir. Taksit/kupon/ücretsiz kargo alanları gerçek kurallara bağlı olmadığı için uydurma teklif olarak eklenmedi. GitHub native CI `43829847295` ve ana CI `43829847251`, hesap faturalama kilidiyle sıfır adımda durdu; başarılı gösterilmedi.

| Modül | Gerçek durum |
| --- | --- |
| Ürün düğmeleri ve mobil sepet | Test sitesinde çalışıyor ve test edildi |
| Bildirim izni/API, şifreleme, kuyruk, service worker | Yalnız test ortamında doğrulandı |
| Gerçek Web Push teslimi | Gerçek cihaz/tarayıcı izni ve doğrulanmış stok bağlantısı bekliyor |
| iOS Canlı Etkinlik | Tamamlanmadı; native uygulama gerektirir |
| Gerçek tahsilat | İşletme/ödeme kabulü bekliyor; teknik olarak kapalı |
| Tam medya felaket kurtarma | Tamamlanmadı |

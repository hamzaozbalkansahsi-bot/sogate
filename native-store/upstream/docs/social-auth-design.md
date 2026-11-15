# Google ve Apple giriş hazırlığı

Kullanıcı, ürün sayfası ve paylaşım değişikliklerinin önce yayımlanmasını; ardından giriş, kayıt ve hesap bağlama/birleştirme kodunun ve düğmelerinin hazırlanmasını istedi. Google Cloud ve Apple Developer ayarları sonraki kullanıcı adımıdır. Apple Developer üyeliği var, NODENO Sign in with Apple uygulaması henüz yok. Önceden Drive için bulunan Google istemcisi kendiliğinden giriş istemcisi olarak etkinleştirilmez.

Mevcut PHP/SQLite hesapları, sepetler, favoriler, adresler ve siparişler korunur. Parola girişi devam eder. Google ve Apple kimlikleri sağlayıcı ve kalıcı `sub` ile eşlenir. E-posta eşitliği otomatik hesap bağlantısı veya birleşme yetkisi değildir. Eski hesap varsa önce mevcut hesaba giriş, ardından sağlayıcı kimlik doğrulaması gerekir.

Kod akışı yetkilendirme kodu, tek kullanımlık state, nonce, Google PKCE, sabit sağlayıcı uçları, HTTPS ve imzası doğrulanan ID token kullanır. RS256 ID token ve Apple ES256 istemci sırrı için sabitlenmiş php-jwt sürümü kullanılır. Google/Apple erişim veya yenileme tokenları saklanmaz. Yapılandırma ve Apple özel anahtarı public/release klasörlerinin dışında kalır; paket ve Git’e yalnız boş örnekler girer.

Apple `form_post` dönüşünde normal SameSite=Lax hesap çerezi zayıflatılmaz. Ayrı Secure/HttpOnly/SameSite=None işlem çerezi, private SQLite akış kaydı ve tek kullanımlık state kontrol edilir. Kod değişimi sonucunda doğrulanan kimlik kısa süreli kayda alınır; 303 GET tamamlamasında asıl hesap oturumu tekrar okunur, başlangıç oturumuyla ve işlem çereziyle eşleştirilir. Oturum değişmişse giriş/bağlantı reddedilir. Başarıda hesap oturumu döndürülür.

Bağlama giriş yapılan NODENO hesabına yapılır. Sağlayıcı kimliği başka NODENO hesabına bağlıysa iki hesap sahipliği kanıtı ve ayrıca açık birleştirme işlemi gerekir. Birleştirme işleminde sepet/favoriler, adresler, sipariş sahipliği ve sağlayıcı kimlikleri korunur; adet 99, sepet 100 satır veya adres 20 sınırı aşılırsa sessiz veri kaybı yerine işlem reddedilir. Güncel hesabın e-posta/parolası ana hesap olarak kalır; diğer oturumlar geçersizleşir. Tek giriş yöntemini kaldırmak engellenir.

Sosyal kayıtla açılan hesap için rastgele kullanılamayan parola özeti tutulur ve parola kurulmadığı ayrıca işaretlenir. Yakın tarihli sağlayıcı doğrulamasından sonra müşteri kendi parolasını oluşturabilir. Doğrulanmamış e-posta ile kayıt yapılmaz; Apple özel aktarma adresi kabul edilir. Parola doğrulaması gereken ayarlar sosyal hesapları çözümsüz bir forma yönlendirmez.

Giriş/kayıt ekranları ve Hesabım bağlantı yönetimi dört dilde ve RTL ile hazırlanır. Sağlayıcı yapılandırması eksikken düğmeler görünür fakat devre dışıdır; kurulum durumunu anlatan tek kısa açıklama vardır. Sağlayıcı durumu ayrı oturum korumalı API’den okunur. Ödeme ve gerçek sipariş açılmaz.

Kabul: gerçek PHP/SQLite ayrık test verisi, yerel RSA/EC anahtarlı imza testleri, yanlış issuer/audience/nonce/imza/süre ve replay denemeleri; birleştirme sınırında rollback; sahiplik/CSRF/origin kontrolleri; dört dil mobil/masaüstü düğme ve form davranışı. Sahte test sağlayıcısı/OS köprüsü açıkça etiketlenir. Sağlayıcı tarafı tamamlanmadan gerçek Google/Apple uçtan uca girişinin çalıştığı söylenmez.

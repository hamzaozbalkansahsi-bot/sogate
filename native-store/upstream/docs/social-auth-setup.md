# Google ve Apple giriş ayarları

Kullanıcının talimatı gereği sağlayıcı hesap ayarları sonraki aşamaya bırakıldı. Kod, veri modeli, giriş/kayıt düğmeleri ve Hesabım bağlantı yönetimi hazırlanmıştır. Gerçek Google/Apple girişi çalışıyor olarak değerlendirilmez; düğmeler gerekli yapılandırma gelmeden açılmaz. Mevcut e-posta/parola hesabı ve ödeme öncesi misafir akışı devam eder.

## Özel sunucu dosyaları

`hosting/social-auth.example.json` yalnız boş bir şablondur. Gerçek değerlerin yeri kalıcı özel dizindeki `/home/nodenoho/nodeno-data/social-auth.json` dosyasıdır. Apple P-256 `.p8` anahtarı `/home/nodenoho/nodeno-data/apple-signin.p8` adıyla tutulur. İki dosya da `0600`, üst dizin `0700` olmalıdır. Web köküne, Git’e veya sürüm paketine eklenmezler.

Google için yeni giriş istemcisinin Client ID ve Client Secret bilgileri gerekir. Apple için Services ID (`clientId`), Team ID, Key ID ve indirilen özel anahtar gerekir. Değerleri sohbete yazmak yerine yerel özel dosyada tutun. `.env.example` içine yalnız boş alanlar eklendi; gerçek değerler `.env.local` içinde kalmalıdır. Önceki Google Drive istemcisi/yenileme anahtarı giriş için kendiliğinden kullanılmaz. Bu kod `.env.local` dosyasını web üzerinden okumaz; sunucu yapılandırması özel JSON dosyasıdır.

Şablonda iki `enabled` değeri de `false` kalır. Sağlayıcı portalı, dönüş adresleri ve gerçek kullanıcıyla kabul tamamlanınca ilgili sağlayıcı açılır. Eksik/bozuk Apple anahtarı, eksik kimlik bilgisi, desteklenmeyen alan adı veya kayıtlı olmayan yerel dönüş adresi düğmeyi açmaz. Yalnız anahtarların yerelde tamamlanmış olması, portal kurulumunun doğrulandığı anlamına gelmez.

## Portalda kaydedilecek dönüş adresleri

| Alan adı | Google dönüşü | Apple dönüşü |
|---|---|---|
| nodenohome.com | `https://nodenohome.com/api/account/oauth/google/callback` | `https://nodenohome.com/api/account/oauth/apple/callback` |
| www.nodenohome.com | `https://www.nodenohome.com/api/account/oauth/google/callback` | `https://www.nodenohome.com/api/account/oauth/apple/callback` |
| nodenohome.com.tr | `https://nodenohome.com.tr/api/account/oauth/google/callback` | `https://nodenohome.com.tr/api/account/oauth/apple/callback` |
| www.nodenohome.com.tr | `https://www.nodenohome.com.tr/api/account/oauth/google/callback` | `https://www.nodenohome.com.tr/api/account/oauth/apple/callback` |

Ziyaret edilen alan adı korunur. Bir alan adı portal ve özel yapılandırmada tamamlanmadıysa o alanda ilgili giriş seçeneği kapalı kalır. `/api/account/oauth/complete` tarayıcının aynı sitede tamamladığı iç adımdır; sağlayıcı portalına dönüş adresi olarak yazılmaz. Serbest dönüş adresi veya dış siteye yönlendirme kabul edilmez.

## Google

Google Cloud’da NODENO için web uygulaması türünde OAuth istemcisi, uygulama adı/iletişim/domain bilgileri ve izin ekranı hazırlanır. Yukarıdaki tam dönüş adresleri eklenir. İstenen kapsamlar yalnız `openid email profile` alanlarıdır; Drive yetkisi veya yenileme tokenı istenmez. Test modunda kalırsa yalnız izin verilen test kullanıcılarının giriş yapabileceği kontrol edilir. Gerçek kullanıcı testi bitmeden genel kullanıma açık olduğu söylenmez. [Google OpenID Connect kurulumu](https://developers.google.com/identity/openid-connect/openid-connect), [düğme yönergeleri](https://developers.google.com/identity/branding-guidelines).

## Apple

Aktif Developer üyeliği mevcut; NODENO giriş uygulaması henüz tanımlı değil. Sign in with Apple yeteneği açık bir birincil App ID, ona bağlı Services ID ve Sign in with Apple anahtarı hazırlanır. Services ID web ayarlarına dört alan adı ve Apple dönüş adresleri eklenir. Services ID sunucuda `clientId` olur; App ID ile karıştırılmaz. Gerekirse özel e-posta aktarma adreslerine gönderim için Apple relay ayarları ayrıca tamamlanır; burada e-posta gönderimi açılmaz. Apple domain kaydında sunucuya hayali bir doğrulama dosyası eklenmez. [Apple web yapılandırması](https://developer.apple.com/help/account/capabilities/configure-sign-in-with-apple-for-the-web/), [özel anahtar](https://developer.apple.com/help/account/capabilities/create-a-sign-in-with-apple-private-key/).

## Hesap davranışı

İlk sosyal girişte doğrulanmış kimlik yeni hesaba bağlanır. Aynı e-posta ile yerel hesap varsa otomatik birleştirme yapılmaz; kişi önce mevcut parolasıyla giriş yapıp Hesabım içinden hesabını bağlar. Mevcut Google/Apple kimliği farklı NODENO hesabına bağlıysa iki sahiplik kanıtından sonra ayrıca birleştirme onayı istenir. Sepet/favoriler, adresler, siparişler ve sağlayıcı kimlikleri taşınır. Geçerli NODENO hesabı ana hesap olarak kalır; diğer hesabın ayrı e-posta/parola girişi sona erer. Limit aşımında işlem tamamen geri alınır.

Sosyal hesabın ilk başta kullanılabilir bir parolası yoktur. Yakın tarihli sağlayıcı doğrulamasıyla kişi kendi parolasını oluşturabilir. Hesabı silmek için önce bu parola hazırlanır ve mevcut silme onayı kullanılır. Son giriş yöntemini kaldırmak reddedilir. Bağlama/kaldırma güncel parolayı veya yakın tarihli sosyal doğrulamayı gerektirir. Diğer oturumlar parola değişiminde, birleştirmede ve bağlantı kaldırmada geçersizleşir.

## Doğrulama ve yayın durumu

`PHP_BINARY` ile gerçek PDO SQLite içeren PHP seçilip `node --test tests/account-runtime.test.mjs tests/social-auth.test.mjs` çalıştırılır. Yerel RSA/EC anahtarlı imza, nonce/state/audience/issuer/süre, PKCE, Apple POST dönüşü, tek kullanımlık ispat, gerçek HTTP oturum yenilemesi, parola yaşam döngüsü, son giriş yöntemi koruması ve açık onayla veri birleştirmesi sınanır. HTTP tamamlaması için kullanılan doğrulanmış kimlik fikstürü yalnız geçici test veritabanına yazılır; üretim kodunda sahte sağlayıcı veya test kapısı bulunmaz.

Tarayıcı kontrolü `tests/browser/social-auth.mjs` dosyasıdır. Döngü adresindeki bağımsız HTTPS test sunucusu gerçek kaynak arayüzü ve PHP hesabını çalıştırır; Google/Apple çağrısı yapmaz, fiziksel iPhone veya gerçek sağlayıcı kabulü sayılmaz. `tests/browser/social-router.php` ve HTTPS vekili yalnız loopback test içindir, yayın paketine alınmaz. Raporlar `artifacts/social-auth/` dizinindedir.

Hazırlık kontrolünde 24 PHP/hesap testi, 18 dağıtım testi, Chromium ve Windows WebKit üzerinde dört dilde 48 görünüm kontrolü ve 8 hesap akışı geçti. Tarayıcı hesap akışları kayıt/parola girişi yanında, yalnız geçici test veritabanına eklenmiş doğrulanmış kimlikle parola oluşturmayı ve bağlantıyı kaldırmayı da kapsar. Bu kimlik fikstürü gerçek sağlayıcı doğrulamasının yerine kabul edilmez.

İlk hazırlıktaki 158 kontrolün üçü, o sırada kapalı olan görsel yayın onayı nedeniyle eski paketi doğrulayamamıştı. Görsel onayı tamamlandıktan sonraki masaüstü yenilemesinde normal derleme, paket doğrulaması ve 162/162 kaynak testi geçti; atlanan test yoktur. Güncel görünümle 48 sosyal üyelik görünümü ve 8 geçici hesap akışı da yeniden doğrulandı. Sağlayıcı portalı ayarları ve gerçek Google/Apple kabulü hâlâ sonraki aşamadır.

Normal derleme/yayın, güncel görsel denetiminde `publicationReady=true` gerektirir. Üyelik testleri bu kilidi gevşetmez ve sağlayıcı ayarlarını kendiliğinden açmaz. Güncel paket ve canlı kabul durumu [masaüstü mağaza kaydında](desktop-storefront.md) tutulur; arayüzün yayınlanması sağlayıcıların etkin olduğu anlamına gelmez.

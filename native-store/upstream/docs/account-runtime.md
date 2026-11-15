# NODENO üyelik ve kişisel alanı

Üyelik modülü gerçek e-posta/parola hesabı, oturum, profil, sepet, favoriler ve adres defteri sunar. Kullanıcılar kendi verilerini görür. Sepet ve adresler PHP yeniden başlatıldığında veya yeni site sürümü yayımlandığında korunur. Satın alma ve e-posta hizmetleri bağlı değildir: sistem sipariş oluşturmaz, ödeme almaz, e-posta doğrulama veya parola sıfırlama iletisi göndermez.

## Kurulum ve kalıcı depolama

`hosting/account.php`, mevcut PHP giriş noktası tarafından `require_once` ile yüklenir. Yönlendirici, genel GET/HEAD kısıtından **önce** şu çağrıyı yapar ve `true` dönerse isteği sonlandırır:

```php
if (nodenoHandleAccountRequest($path, $method, $catalog, '/home/nodenoho/nodeno-data')) {
    return;
}
```

`$catalog`, güncel `products` listesini içeren katalog dizisidir. Depolama yolu güvenilir sunucu yapılandırmasından gelmelidir; HTTP parametresinden alınmaz. Üretim yolu `/home/nodenoho/nodeno-data` olarak sabittir. Testler bağımsız geçici dizin kullanır. Yalnız son dizin oluşturulur; üst dizinin önceden var olması gerekir.

Gerekli PHP yetenekleri: PDO, `pdo_sqlite`, JSON, session, güvenli rastgele sayı üretimi ve `password_hash`/`password_verify`. SQLite'ın `ON CONFLICT DO UPDATE` ve kısmi indeks desteği gerekir; SQLite 3.24 veya üstünü kullanın. Taşınabilir yerel PHP çalışma ortamında PDO SQLite ayrıca açılmıştır; bu klasör yayımlama paketine eklenmez.

Veriler `accounts.sqlite`, SQLite WAL/SHM yardımcı dosyaları ve `sessions/` içinde saklanır. Depolama ve oturum dizinleri `0700`, veritabanı `0600` izinleriyle hazırlanır. Yol, gerçek dosya yollarına göre etkin `DOCUMENT_ROOT`, `CONTEXT_DOCUMENT_ROOT` ve modülün sürüm/depo kökü altında olamaz. Standart `public_html`, `public_ftp`, `www`, `htdocs`, `httpdocs`, `nodeno-releases` ve `.nodeno-releases` ağaçları da reddedilir. Depolama, veritabanı ve oturum dizinine doğrudan sembolik bağlantı kabul edilmez. Web sunucusunun başka bir alias ile bu dizini yayımlamaması sunucu kurulumunun bir parçasıdır.

Sürüm paketleri bu dizini içermez ve yeniden yayım bu dizini silmez. Yedekleme için SQLite'ın tutarlı çevrimiçi yedekleme mekanizmasını kullanın; etkin WAL varken yalnız `accounts.sqlite` dosyasını kopyalamak yeterli değildir. Geri yükleme sırasında yazan PHP süreçlerini durdurun; hesap verisi ve oturum dosyaları herkese açık dizine taşınmamalıdır. Modül parola, e-posta, fiziksel adres veya SQL/path hata ayrıntısını günlüklere yazmaz.

## Kullanıcı akışı

1. İstemci `GET /api/account` ile misafir oturumunu ve CSRF değerini alır.
2. Kayıt veya giriş formunu JSON olarak, `X-CSRF-Token` başlığıyla gönderir. Tarayıcı çerezi otomatik taşır. Sunucu aynı kaynaktan gelen `Origin` başlığını zorunlu tutar.
3. Başarılı kayıt/giriş sonrası dönen yeni `csrfToken` kullanılır. Profil, adres, sepet/favoriler ve sipariş geçmişi hesaba bağlıdır.
4. İstemci misafir sepetini/favorilerini hesap verileriyle birleştirirse birleşik ve doğrulanmış sonucu `PUT /api/account/state` ile kaydeder. Bu uç nokta tüm durumu değiştirir; sunucu misafir verisini örtük olarak birleştirmez.
5. Çıkış veya parola değişimi oturum kimliğini ve CSRF değerini döndürür. Parola değişimi diğer cihazlardaki mevcut oturumları da geçersiz kılar. Oturumlar 30 dakika hareketsizlik veya 12 saat toplam süreden sonra sona erer.
6. Kullanıcı hesabını silmeyi açıkça seçip mevcut parolasını doğrularsa `DELETE /api/account` yalnız o hesabı, adreslerini ve sepet/favori verisini siler. Gerçek sipariş geçmişi varsa `409 account_has_orders` ile silme reddedilir. Başarılı silme anonim oturum ve yeni CSRF döndürür; başka kullanıcıların verisi korunur.

Oturum çerezi `NODENOSESSID`, `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/` özelliklerini taşır; kalıcı giriş çerezi değildir. Üretim HTTPS üzerinden çalışmalıdır. API yanıtları `Cache-Control: no-store` ve `Vary: Cookie` kullanır.

## API sözleşmesi

Tüm hata yanıtları `{ "error": "kod" }` biçimindedir. Tüm değiştirme istekleri aynı kaynak `Origin`, `Content-Type: application/json` ve güncel `X-CSRF-Token` gerektirir. Gövdesiz çıkış ve silme işlemlerinde de `{}` gönderin. JSON gövdesi, beyan edilen boyut ve gerçek okunan veri üzerinden 32.768 baytla sınırlanır. GET/HEAD dışındaki desteklenmeyen metotlar `405`, bilinmeyen hesap yolu `404` döndürür.

| Yol | Metot | Gövde ve sonuç |
| --- | --- | --- |
| `/api/account` | GET / HEAD | `{user, csrfToken, capabilities}`; misafirde `user:null`. |
| `/api/account` | DELETE | `{password}`; mevcut parola ile kendi hesabını siler, `200` ve anonim hesap zarfı döner. Sipariş varsa `409 account_has_orders`. |
| `/api/account/register` | POST | `{name,email,password}`; `201` ve hesap zarfı. E-posta tekildir ve küçük harfe dönüştürülür. |
| `/api/account/login` | POST | `{email,password}`; `200` ve hesap zarfı. |
| `/api/account/logout` | POST | `{}`; `200`, `user:null` ve yeni CSRF. |
| `/api/account/profile` | PATCH | `{name}`; `200` ve güncel hesap zarfı. |
| `/api/account/password` | POST | `{currentPassword,password}`; `200` ve yeni oturum/CSRF ile hesap zarfı. |
| `/api/account/password-reset` | POST | `503 email_delivery_unavailable`; e-posta gönderildiğini söylemez. |
| `/api/account/state` | GET / HEAD / PUT | `{cart:[{id,quantity}],favorites:[id]}`. PUT bütünü değiştirir. |
| `/api/account/addresses` | GET / HEAD | `{addresses:[...]}`. |
| `/api/account/addresses` | POST | Adres gövdesi; `201 {address:{...}}`. |
| `/api/account/addresses/{id}` | PATCH | Değişen adres alanları; `200 {address:{...}}`. |
| `/api/account/addresses/{id}` | DELETE | `{}`; `200 {addresses:[...]}`. |
| `/api/account/orders` | GET / HEAD | `{orders:[...]}`; veritabanında kayıt yoksa boş liste. Her sipariş kendi `shipments` listesini içerir. |
| `/api/account/orders` | POST | `409 commerce_not_configured`; veritabanına sipariş veya gönderi yazmaz. |

Kayıt, giriş, çıkış, profil ve parola yanıtlarındaki hesap zarfı:

```json
{
  "user": {"id":"sunucunun-ürettiği-kimlik", "email":"user@example.com", "name":"Ad Soyad", "emailVerified":false},
  "csrfToken":"64-onaltılık-karakter",
  "capabilities":{"registration":true,"passwordReset":false,"checkout":false}
}
```

Kayıt adı 2–100 Unicode karakterdir. Parola en az **12 Unicode karakter** içermelidir; alt sınır `preg_match_all('/./us')` ile kod noktaları üzerinden sayılır ve `mbstring` gerektirmez. NUL içeren veya bcrypt güvenlik sınırı olan 72 UTF-8 baytını aşan parola kırpılmadan `422 invalid_password` ile reddedilir. Parolalar `PASSWORD_DEFAULT` ile tuzlanmış tek yönlü özet olarak saklanır. Müşteri arayüzünde alt sınır “En az 12 karakter kullanın”, üst sınır ise parolayı kısaltmayı isteyen doğal bir mesajla anlatılır.

Sepet yalnız güncel katalogdaki ürün kimliklerini metin olarak kabul eder. Miktar 1–99 tam sayıdır; en fazla 100 farklı ürün satırı ve 667 favori kabul edilir. Bilinmeyen ürün `422 invalid_product`, geçersiz miktar veya durum `422 invalid_state` döndürür. Favori tekrarları tekilleştirilir; yinelenen sepet satırları reddedilir. Sonraki katalogda kaldırılmış ürünler GET sonucundan çıkarılır.

Adres alanları: `id` (sunucu üretir), `label`, `name`, `phone`, `country`, `city`, `district`, `postalCode`, `line1`, `line2`, `isDefault`. `postalCode` ve `line2` boş bırakılabilir. Telefon 7–15 rakam içermeli; `+`, boşluk, parantez, nokta ve kısa çizgi kullanılabilir. `line1` 5–250 karakterdir. En fazla 20 adres tutulur. İlk adres varsayılan olur; yeni bir adres varsayılan seçilince önceki kaldırılır. Varsayılan adres silinirse kalan ilk adres varsayılan yapılır. Başkasının adres kimliği `404 address_not_found` döndürür.

Korunan okuma ve yazma işlemleri misafire `401 authentication_required`, yanlış parola `401 invalid_credentials`, yinelenen kayıt `409 email_already_registered` döndürür. Aynı IP için değiştirme sınırı 10 dakikada 120, kayıt sınırı saatte 5, giriş sınırı 15 dakikada 30'dur. Aynı IP/e-posta birleşimi için giriş sınırı 15 dakikada 8; parola değişimi ve hesap silme ayrı ayrı aynı IP/hesap için 15 dakikada 8 denemedir. Sayaçlar veritabanında gizli anahtarlı HMAC ile tutulur; düz IP/e-posta sayaç anahtarına yazılmaz. Sınır aşımında `429 rate_limited` ve `Retry-After` döner. Eksik depolama/SQLite/oturum yeteneği `503 account_unavailable` döndürür.

## Doğrulama

`PHP_BINARY` değişkenini PDO SQLite içeren PHP CLI yoluna ayarlayıp `node --test tests/account-runtime.test.mjs` çalıştırın. Testler gerçek PHP HTTP sunucusu ve bağımsız SQLite veritabanıyla kullanıcı ayrımı, CSRF/kaynak, Secure çerez, oturum sabitleme, 12 Unicode karakter/72 bayt/NUL sınırları, gövde boyutu, adres sahipliği, varsayılan adres geçişi, durum kalıcılığı, oturum iptali, reddedilen sipariş, sipariş/gönderi sahipliği, doğrulanmış hesap silme ve yeniden başlatma sonrasında giriş sınırını kontrol eder. Yalnız geçici test veritabanına yazılan sipariş/gönderi fikstürü okuma ve silme engelini sınar; uygulama sipariş üretmez. Geçici dosyalar test sonunda temizlenir; üretim hesabı veya gerçek müşteri verisi kullanılmaz.

Parola ve oturum davranışı PHP'nin [password_hash](https://www.php.net/manual/en/function.password-hash.php) ve [güvenli oturum ayarları](https://www.php.net/manual/en/session.security.ini.php) belgeleriyle, WAL kullanımı [SQLite journal_mode](https://www.sqlite.org/pragma.html#pragma_journal_mode) belgesiyle uyumludur.

## Üyelik gerektirmeyen ödeme öncesi taslak

`?page=checkout` artık misafiri hesap oluşturmaya zorlamaz. İletişim/teslimat/ayrı fatura ve bilgi kontrolü yalnız sayfa belleğinde yürür. Form normal akışta sunucuya gönderilmez, hesap adreslerine kaydolmaz. Sahip ve dil anahtarı DOM korumasını sınırlar; giriş/çıkış veya sahip değişimi taslağı temizler. Gerçek sipariş/ödeme API engeli, oturum/CSRF ve adres sahipliği aynıdır. [Güncel davranış ve kabul](mobile-guest-checkout.md).


## Google ve Apple hazırlığı

Sosyal kimlikler ayrı `provider_identities` tablosunda sağlayıcı ve değişmeyen subject ile tutulur. `users.password_configured` eski yerel hesaplar için varsayılan 1, `users.email_verified` varsayılan 0 olarak eklenir; mevcut kullanıcı verileri ve oturum sürümleri değiştirilmez. Yerel hesap zarfı artık `user.hasPassword` ve gerçek doğrulama durumunu içerir; eski üç capability aynı kalır.

`GET /api/account/social` sağlayıcıların hazır/bağlı durumunu, kendi bağlı hesap e-postalarını ve varsa onay bekleyen birleştirme bilgisini verir. `POST /api/account/oauth/{google|apple}/start`, `POST /api/account/social/unlink`, `POST /api/account/social/merge` ve `POST /api/account/social/merge-cancel` aynı origin/JSON/CSRF korumasını kullanır. Google GET ve Apple form POST dönüşleri tek kullanımlık state ve ayrı işlem çereziyle kontrol edilir. `/api/account/oauth/complete` ilk taraf GET adımında asıl oturumu eşleştirir ve başarıda yeniler.

Sağlayıcı ayarı olmayan kurulumda düğmeler devre dışıdır ve başlangıç API’si `503 social_not_configured` döndürür; Drive anahtarları kullanılmaz. Sosyal API başarısız olsa bile e-posta/parola girişi devam eder. Hazırlık, sonraki sağlayıcı ayarları ve test sınırları [sosyal giriş kurulum belgesindedir](social-auth-setup.md).

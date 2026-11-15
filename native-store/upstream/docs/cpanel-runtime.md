# cPanel / PHP yayın paketi

**Canlı sürüm:** Gerçek HTTPS ve tarayıcı kabulü tamamlandı. Güncel sürüm özeti, test raporları ve işletme bağımlılıkları [teslim-durumu.md](teslim-durumu.md) içindedir.

**11 Kasım 2026 paketleme güncellemesi:** Katalog artık eski mobilya, kapı/kapak ve tedarikçi kayıtlarını birlikte içerir. Aşağıdaki ilk sürüme ait altı dosya listesi güncel manifestin tam listesi değildir; yetkili dosya kümesi paketleyici ve `deploy-cpanel.py` içindeki listelerdir. Tedarikçi bulunan kataloglarda gerçek açıklama indeksi/blobu, görsel onayı ve rasterler test paketine de dahil edilir. Test rasterleri kullanılan paket `testOnly` kalır ve yayıncı tarafından reddedilir. Onaysız/eksik tedarikçi görseli veya tam katalog sözleşmesindeki fark derlemeyi durdurur. [Ayrıntı ve yeniden derleme kanıtları](supplier-publication-2026-11-10.md).

Canlı ödeme durumu paket içindeki varsayılan kapalı yapılandırmadan ayrı, kalıcı özel depodaki doğrulanmış sağlayıcı ayarıyla belirlenir. Genel yayın yardımcısının kapalı ödeme beklentisi varsayılan olarak korunur; açık mağazaya yapılan kontrollü yayında mevcut açık durum açıkça beklenir ve tekrar doğrulanır. Bu kontrol sağlayıcı ayarını değiştirmez. Güncel ödeme ve belge davranışı [teslim durumunda](teslim-durumu.md) yer alır.

`npm run build` ortak uygulamayı oluşturur. Ardından `node scripts/build-cpanel.mjs`, derlenmiş Worker'ın `/api/catalog` ve `/api/config` yanıtlarını aynen alır; katalog normalleştirme veya çeviri kurallarını tekrar uygulamaz. Web dosyalarını Worker'daki kopyalarla karşılaştırır ve fontlar dahil tüm dosyaları aynı baytlarla paketler. Worker eskiyse paketleme durur.

Çıktı `artifacts/cpanel-release/` altındadır:

```text
public/             ← alan adlarının ortak document root dizini
  index.php
  .htaccess
  app.js, styles.css, i18n.js, görseller, fontlar…
private/            ← hiçbir alan adının document root dizini içinde bulunmaz
  account.php
  catalog.json
  config.json
  media.json
  index.html
  release.json
  cache/
```

Özel paket altı dosyadan oluşur: `account.php`, `catalog.json`, `config.json`, `media.json`, `index.html`, `release.json`. `cache/` görsel önbelleğidir; hesap veritabanı değildir. Hesap verisi ve oturumlar paketlenmez.

`public` içeriği document root'a, `private` içeriği bunun dışındaki ayrı sürüm dizinine yüklenir. PHP varsayılan olarak `dirname(__DIR__) . '/private'` kullanır. Turhost yayın yardımcısı, document root'un bir üst dizinindeki webden erişilemeyen `nodeno-runtime.php` dosyasına üç ayrı yol yazar:

```php
<?php
return [
    'privateRoot' => '/home/nodenoho/nodeno-releases/RELEASE_HASH/private',
    'storageRoot' => '/home/nodenoho/nodeno-data',
    'mediaRoot' => '/home/nodenoho/nodeno-media',
];
```

Bu dosya yalnız dizin yolları içerir; kimlik bilgisi gerekmez. `privateRoot` her sürümde değişir; `storageRoot` sabit kalır. PHP, özel dizin document root içinde kaldığında isteği reddeder. Özel dizin ve önbellek PHP kullanıcısınca okunabilir/yazılabilir olmalıdır. Yayın güncellemesinde sunucunun `cache/` içeriği korunabilir; yerel paket her oluşturulduğunda temiz bir önbellek dizini hazırlanır. Elle dosya aktarımında binary mod kullanılmalıdır; satır sonu değişikliği bütünlük denetimini bozar.

Apache 2.4 veya uyumlu LiteSpeed üzerinde `.htaccess`, rewrite ve `Options -Indexes -MultiViews` desteği gerekir. PHP 8.1 veya üstü, cURL, fileinfo, JSON, PDO SQLite, session, güvenli rastgele sayı üretimi ve parola özetleme işlevleri gerekir. SQLite 3.24 veya üstü gerekir. cURL sertifika doğrulaması açıktır; sunucuda güvenilir CA deposu bulunmalıdır. Paket TLS doğrulamasını kapatmaz. PHP'nin geliştirme sunucusu üretim için kullanılmaz. `hosting/dev-router.php` ve `hosting/runtime-checks.php` yalnız yerel doğrulama araçlarıdır ve pakete girmez.

Genel GET/HEAD uçları `/api/catalog`, `/api/config`, `/api/health`, `/media/ÜRÜN_KİMLİĞİ/GÖRSEL_SIRASI`, `/`, `/index.html`, `/index.php` ve `/robots.txt` şeklindedir. Sayfa/ürün/dil gezinmesi bu HTML üzerinde `?page=...`, `?product=...`, `?lang=...` parametreleriyle çalışır; yenilemede aynı uygulama açılır.

`/api/account` ve alt yolları genel GET/HEAD kısıtından önce `private/account.php` modülüne yönlendirilir. Kayıt/giriş/çıkış, profil, parola, adres ve sepet/favori değişiklikleri kendi POST/PATCH/PUT/DELETE sözleşmesini kullanır; aynı kaynak, CSRF, oturum ve nesne sahipliği doğrulanır. Hesap API'sinin tam yöntem/yanıt tablosu [account-runtime.md](account-runtime.md) içindedir. Tanımsız yollar 404, desteklenmeyen yöntemler 405 döndürür. Genel katalog/config yanıtları ortak uygulamadakiyle aynıdır. Sipariş/gönderi okuma yalnız hesaba ait gerçek kayıtları döndürür; sipariş oluşturma ve ödeme kapalıdır. E-posta doğrulama ve parola sıfırlama e-postası gönderilmez.

## Kalıcı hesap verisi

`/home/nodenoho/nodeno-data` altında `accounts.sqlite`, varsa WAL/SHM dosyaları ve `sessions/` saklanır. Veri/oturum dizinleri `0700`, veritabanı `0600` izinleriyle hazırlanır. Web kökleri, sürüm dizinleri ve sembolik bağlantılar hesap deposu olamaz. Bu dizin yayın manifestine, ZIP'e veya public ağaca girmez; yeniden yayın tarafından silinmez veya üzerine yazılmaz.

Public site yedeği hesap verisi yedeği değildir. SQLite için tutarlı çevrimiçi yedekleme kullanılmalıdır; WAL etkin veritabanının yalnız ana dosyasını kopyalamak yeterli değildir. Yedek ve geri yükleme de web kökü dışında kalır. Ayrıntılı erişim/saklama sözleşmesi üyelik belgesindedir.

Görseller özel `media.json` haritasındaki ürün ve sıralardan seçilir. İstekten kaynak URL alınmaz. Kaynak URL yalnız özel arşiv kimliği olarak HTTPS ve tam `witcdn.adoremobilya.com` alan adıyla doğrulanır; üretim görsel rotası ağdan tedarikçi dosyası indirmez. Bütün onaylı temizlenmiş ve değiştirilmemiş görseller doğrudan Turhost'un özel `mediaRoot` kasasından okunur; eksik dosya için CDN'e dönüş yoktur. Her sunumda SHA-256, gerçek MIME, boyut ve ölçü kontrol edilir. Google Drive aşaması kullanıcının talebiyle ertelenmiştir. Ayrıntı [clean-media-runtime.md](clean-media-runtime.md) içindedir.

HTML her istekte yeni bir script nonce değeriyle ve `no-store` ile sunulur. CSP yerel fontları ve yerel betikleri kullanır; `unsafe-inline` eklenmez. `.htaccess` kaynak, ayar, gizli dosya ve özel dizin yollarını engeller; dizin listeleme kapalıdır.

`nodenohome.com.tr` ve `nodenohome.com` aynı public document root'u paylaşmalıdır. Bu uygulama alan adları arasında yönlendirme yapmaz; API, görsel, varlık ve ürün bağlantıları göreli yollar kullanır. cPanel'de alias veya aynı document root seçimi yapılır; sunucu düzeyinde ayrıca tanımlanan alan adı yönlendirmeleri kapalı olmalıdır. [cPanel ortak içerik/alias açıklaması](https://support.cpanel.net/hc/en-us/articles/360055638573-How-can-I-create-a-domain-that-uses-the-same-content-as-an-existing-domain).

Yeni `/api/health`, `runtime: "php"`, gerçek PHP sürümü, `accountsEnabled: true`, `checkoutEnabled: false`, `driveConnected: false` ve adaptörün `releaseHash` değerini döndürür. PDO SQLite yeteneği de sağlık kontrolüne dahildir. Sağlık yanıtı tek başına kayıt/giriş uçtan uca kabulü değildir.

Yayın özeti; public PHP, `.htaccess`, web dosyaları, özel `account.php`, katalog/config/medya JSON verileri ve HTML şablonunun sıralanmış SHA-256 özetlerinden oluşturulur. Sağlık isteği kurulu dosyaları tekrar özetler; değişen veya eksik dosyada 503 döndürür. Worker özeti aynı değer değildir; izlenebilirlik için özel `release.json` içinde tutulur. Manifest kendi özetine, görsel önbelleği, kalıcı hesap verisi ve sunucuya özgü dizin ayarı da yayın özetine katılmaz.

Doğrulama:

```powershell
npm run build
node scripts/build-cpanel.mjs
$env:PHP_BINARY = 'C:\PHP\php.exe'
node --test tests/cpanel-artifact.test.mjs tests/cpanel-runtime.test.mjs tests/account-runtime.test.mjs
```

`PHP_BINARY`, PDO SQLite içeren gerçek PHP CLI yoludur; örnek yol ortama göre değiştirilir. PHP bulunamazsa gerçek PHP testleri açık gerekçeyle atlanır; bu durum PHP veya üyelik çalışmasının doğrulandığı anlamına gelmez. Yerel HTTP testleri bağımsız geçici veritabanı kullanır. Apache/LiteSpeed rewrite, HTTPS aliasları, güvenli oturum çerezi ve gerçek hesap akışları yayın sunucusunda ayrıca kontrol edilir. cURL protokol, TLS ve callback seçenekleri [resmî PHP cURL başvurusuna](https://www.php.net/manual/en/curl.constants.php) dayanır.
# Büyük dil dosyalarının yayın yedeği

12 Kasım 2026 tarihli ürün ayrıntısı düzeltmesinden itibaren, 1 MB üzerindeki izinli dil JSON’larının eski sürümü fiziksel dosya boyutu ve önbelleksiz HTTPS yanıtının SHA-256 özetiyle doğrulanır. cPanel metin düzenleyicisinin sınırı artırılmaz. Özel yayın yedeğinde bu dosyalar 450.000 baytlık ham parçaların Base64 karşılıklarıyla saklanır; her parça yüklemeden sonra birebir geri okunur. `<dosya>.parts.json`, parça sırasını, ham uzunluklarını ve SHA-256 özetlerini içerir.

Elle kurtarmada manifest sırasındaki parçalar Base64’ten çözülüp birleştirilir; her parça ve birleşik dosyanın uzunluğu/özeti doğrulanmadan dosya yüklenmez. Otomatik geri alma, yayın öncesinde doğrulanmış özgün baytları ve önceki özel sürüm işaretçisini kullanır. Bu yedekler web kökünün dışında kalır; müşteri, ödeme ve görsel kasalarının yerleri değiştirilmez. Davranış testleri `tests/native_publication_readback_test.py` içindedir.

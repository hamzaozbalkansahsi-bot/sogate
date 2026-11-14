# PHP test hostingi

14 Kasım 2026: hedef sıradan Linux/cPanel hostingtir. Sunucuda Node, Next sunucusu, Passenger veya PostgreSQL çalıştırılmaz. `/test` uygulaması PHP8.3.36 ve MySQL8.0.46 üzerinde çalışır. Ana hazırlanıyor sitesi ve onun Search Console doğrulaması korunur. Eski Next/TypeScript kaynakları silinmedi; onların modül tamamlanma durumu PHP runtime'a otomatik aktarılmaz.

## Giriş ve yerel çalıştırma

Test adresi: https://sexogate.com/test. Son kullanıcı kararıyla vitrin ve misafir alışverişi yaş beyanından sonra hesapsız açılır; özel test erişim kapısı yalnız yönetim ve yönetici API'lerinde kalır. Arama motorlarına `noindex, nofollow`, cevaplara `private, no-store` uygulanır. Üç izole katalog örneği ve test kuralları gerçek satış kataloğu değildir. Gerçek ödeme kapalıdır.

İki ayrı kimlik vardır. Özel test kapısı ve uygulama yöneticisinin bilgileri yalnız Git dışı `.local/php-stage-access.json` dosyasındadır. Yönetici `/test/yonetim/giris` adresinden giriş yapar; TOTP gerekir. Tarayıcı kabulünde kurulan TOTP anahtarı ve tek kullanımlık kurtarma kodları aynı yerel dosyadadır. Bunları kaynak koduna, sohbete veya destek kaydına kopyalamayın. Geliştirme ortamının ayrı bilgileri `.local/php-access.json` içindedir. Test erişim kapısı, müşterilerin hesap parolası değildir.

Yerelde projenin kendi MySQL55433 süreci açık olmalıdır. Node yalnız mevcut yerel MySQL başlatıcısı ve tarayıcı test aracı için kullanılabilir; hosting bağımlılığı değildir.

```powershell
node scripts/native-mysql.mjs
python scripts/setup-php.py
python scripts/build-php-assets.py
& './.local/php-runtime/php.exe' -S 127.0.0.1:3183 -t hosting/php/public hosting/php/router.php
```

Son komut ayrı terminalde açık tutulur; yerel adres `http://127.0.0.1:3183/test/`.3000 numaralı mevcut Next önizlemesi ve diğer sohbetlerin uygulamaları bu süreç değildir.

Kurulum özel PHP DB kullanıcısı ve `sexogate_php_preview_test` oluşturur. Önceden var olan sahipsiz DB üzerine yazmaz. Örnek kurallar/katalog yalnız development/test ve `_test` DB'de yüklenebilir. Yerel PHP binary/Composer `.local/php-runtime` içindedir; resmî PHP8.3.36 arşivi SHA256 ve Composer kurucusu SHA384 ile doğrulanmıştır. PHP dosyaları UTF-8, PDO native prepared statement, UTC, strict MySQL ve InnoDB kullanır.

## Yapılandırma

Yerel runtime `hosting/php/config.local.json`, hosting runtime webden403 ile kapalı `/test/app/config.local.json` kullanır. JSON dosyaları Git dışıdır. Yapılandırma alanları:

| Alan | Kullanım |
|---|---|
| `env` | development/test/production; test sağlayıcısı production'da reddedilir |
| `base_path`, `app_url` | Sabit `/test` ve ilgili yerel/HTTPS adres |
| `db_dsn`, `db_user`, `db_password` | Yalnız bu test DB'sine erişen PDO bağlantısı |
| `secret` | En az32 bayt; teklif, takip, MFA şifreleme ve oturumla ilişkili imzalar |
| `payment_provider`, `live_sales` | Bu yayında test ve false; Stripe seçilmesi gerçek ödeme bağlantısı oluşturmaz |
| `stage_access`, `stage_user`, `stage_password_sha256` | İnternetteki test ortamının zorunlu yönetim erişim kapısı; müşteri vitrini bu kapıya yönlendirilmez |
| `asset_prefix` | Etkin sürümün `/test/assets/releases/<id>` yolu |
| `smtp_dsn`, `mail_from` | Sunucu tarafı e-posta; yapılandırılmadığında işler SMTP_NOT_CONFIGURED ile ertelenir |
| `bootstrap_admin` | Yalnız ilk kurulumda kullanılır; sunucudaki konfigürasyondan kurulum bitince kaldırılır |

FTPS/cPanel erişimi `.env.local` içindeki `FTP_*`, `CPANEL_HOST`, `CPANEL_USERNAME`, `CPANEL_PASSWORD` veya `CPANEL_API_TOKEN` alanlarından okunur. Yedek şifreleme anahtarı `BACKUP_ENCRYPTION_KEY` içindedir. Gerçek değerler komut satırı argümanına veya çıktıya yazılmaz. Üçüncü taraf hesap bilgileri taşınmadı.

## Test ve yayın

```powershell
python scripts/test-php.py
node scripts/test-php-browser.mjs
python scripts/package-php.py
python scripts/test-php-install.py
python scripts/publish-php-test.py --inspect
python scripts/publish-php-test.py --deploy
python scripts/publish-php-test.py --verify
node scripts/test-php-browser.mjs --remote
python scripts/setup-php-cron.py
python scripts/setup-php-cron.py --check
python scripts/backup-php-test.py
```

Yayından önce son yerel test ve paket kurulumu başarılı olmalıdır. Paket ayrı dizinde `composer install --no-dev --classmap-authoritative --no-scripts` ile hazırlanır; lockfile sabittir. Ortak kaynaklar ve çalışan Next derlemesi temizlenmez. Paket sır içermez; kendi SHA256 ve dosya manifesti vardır. Ana index/.htaccess/robots hash'leri yayının başında ve sonunda karşılaştırılır. cPanel hesabının alan adı sahipliği, DB/kullanıcı ve FTP `/test` sahiplik kaydı doğrulanır. Ana köke dosya yazılmaz.

`/test/app/.htaccess` kaynak ve konfigürasyon aktarımından **önce** yüklenir ve gerçek HTTP403 kontrol edilir. Tek kullanımlık kurucu yalnız sabit arşivi açar; dışarıdan SQL, komut veya dizin kabul etmez. ZIP path traversal/symlink/boyut kontrolleri ve manifest doğrulaması uygulanır. Aynı kanonik MySQL migration kaynağı (bu test yayınında001–021) checksum/DDL hata kaydıyla yürür. Kurucu, sırrı ve arşiv temizlenir; geçerli release özel `active.php` işaretçisiyle etkinleşir.

Ana hazırlanıyor sayfasının CSP başlığı `/test` altına miras kaldığı için alt uygulama kendi dar CSP'sini kendi `.htaccess` dosyasında tanımlar. Ana güvenlik başlıkları değiştirilmez. `strict-origin` referrer politikası native giriş formunun Origin bilgisini korur, sipariş sorgu parametrelerini referrer'a taşımaz. Origin ve CSRF ayrı doğrulanır.

## Worker ve geri dönüş

cPanel cron her dakika yalnız `/test/app/cron.php` dosyasını doğrulanan PHP8.3 CLI ile çalıştırır. CLI dışı erişim kapalıdır. Yerel/uzak kilit aynı işçi turunun üst üste binmesini önler; işler SKIP LOCKED,120 saniye kira, deneme sayısı ve geri çekilme kullanır. Süreli rezervasyonlar çözülür. E-posta servisi eksikse bildirim gönderilmiş sayılmaz ve ödeme yeniden alınmaz. SMTP'nin belirsiz sonucunda tam bir kez e-posta garantisi yoktur; sabit Message-ID kullanılır. Stripe mutabakatı inbox/worker üzerinden taşındı; gerçek Stripe anahtar/kategori kabulü yokken etkinleştirilmez. Tanımsız iş türü görünür hata olarak kalır.

`worker-health.json` özel dizindedir; sağlık kaydı webden403 olmalı, yalnız FTPS ile okunmalıdır. Cron'un API kaydı, gerçekten çalıştığına dair kanıt değildir; `--check` gerçek heartbeat okur. Diğer cron satırları değiştirilmez. cPanel'in resmî belgesine göre Cron için UAPI karşılığı bulunmadığından yalnız listcron/add_line API2 işlemleri kullanılır.

Bir önceki özel release korunur; önceki işaretçi `/test/app/previous.php` içindedir. Geri dönüş, yalnız doğrulanmış önceki release ID'sini atomik işaretçiyle etkinleştirir; o release'in asset_prefix değeri de özel konfigürasyonda eşleşmelidir. Kaynak geri dönüşü DB migration'ını geri almaz. DDL hatasında migration dirty olarak durur; rastgele tekrar/geri SQL yürütülmez. Önce geri yükleme veya ileri düzeltme planı uygulanır. Force push, ana site yayını ve DNS bu akışta yoktur.

## Yedek ve geri yükleme

`backup-php-test.py` yalnız bu test DB'si için kısa ömürlü, kimliği doğrulanmış sabit helper kullanır. InnoDB consistent snapshot, migration kilidi, her tablo için count/hash ve UTF-8/binary değerlerin kayıpsız kodlanması uygulanır. DB ve özel konfigürasyon sunucuda AES-256-GCM ile şifrelenir; düz dump webden veya yerel diske yazılmaz. Oturum ve giriş hız sınırı satırları geri yüklenmez. Helper ve geçici anahtar talebi işlem sonunda temizlenir.

Şifreli dosya `.local/php-stage-backups` içine FTPS ile indirilir. Sadece yeni, rastgele adlandırılmış yerel55433 test DB'sine açılır; migration checksum'ları, bütün tablo count/hash'leri ve FK ilişkileri doğrulanır. Generated column değerleri yeniden hesaplanır. Yerel hedefin migration'dan gelen trigger tanımları veri yüklerken geçici kaldırılır ve aynen geri eklenir; dump'tan keyfî trigger kodu çalıştırılmaz. Bu, **uzak test DB'sinden yerel izole geri yükleme tatbikatıdır**; canlı üretim geri yükleme testi değildir.

Medya bu testte paketin SVG/font, uygulama PNG/ICO ve onaylı Liora WebP varlıklarıdır; sürümlü yayın arşivi bunları içerir. Gerçek müşteri yüklemeleri/S3, uzak yedek saklama süresi, günlük otomatik yedek ve production tatbikatı ayrıca kurulmalıdır. Şifreli yedek ile anahtar ayrı erişim/saklama süreçleriyle korunmalıdır; yalnız aynı hostingte duran kopya yeterli değildir.

## Gerçek modül durumu

| PHP runtime modülü | Durum |
|---|---|
| Katalog/varyant oluşturma, mal kabulü, yayın, sunucu araması | Test ortamında çalışıyor ve test edildi |
| Sunucu sepeti, fiyat/vergi/ülke/hukuk kontrolü, imzalı teklif | Test ortamında çalışıyor ve test edildi |
| İşlemsel depo/lot/set/tedarikçi rezervasyon çekirdeği | Kod taşındı; temel depo akışı/son-adet yarışı test edildi; bütün lot/set/tedarikçi PHP kabul matrisi tamamlanmadı |
| İmzalı test ödeme, tekrar koruması, geç ödeme istisnası | Yerel DB ve uzak tarayıcıda test edildi |
| Hesap, Argon2id, TOTP, rol/alan/sahiplik ve CSRF | Temel sınırlar test edildi; tam kimlik güvenlik denetimi değildir |
| Katalog/depo/sipariş listesi ve satıcı alanları | Temel açık admin çalışıyor; bütün operasyon panelleri tamamlanmadı |
| Apache `/test`, özel kaynaklar, PHP CLI cron, sürümlü kurulum | Uzak gerçek kontroller uygulanıyor; son kanıt progress dosyasındadır |
| Stripe adaptörü/webhook/iadeler/mutabakat | PHP teknik sınırı yerelde resmî SDK ve kontrollü HTTP ile test edildi; gerçek Stripe test hesabı, işletme/kategori kabulü ve anahtar bekliyor |
| SMTP | Dış erişim/yapılandırma bekliyor; gönderildi gösterilmez |
| Manuel depo sevki, karantinalı iade/kısmi para iadesi | PHP21 test yayınında Chromium/WebKit ve gerçek DB ile test edildi; gerçek taşıyıcı API'si yok |
| Satın alma/lot/set, CMS/hukuk/SEO kontrolü, rapor/rol/kuyruk, adres/favori/tercih | PHP21 teknik akışları test edildi; kapsam içindeki bütün yönetim özellikleri henüz tamamlanmadı |
| Tedarikçi operasyonu ve CSV/XLSX | PHP23 test yayınında iki tarayıcıyla kabul edildi; otomatik dış API ve mevcut ürün güncelleme importu yok |
| Ülke/vergi/fiyat ve SKU/model/taşıyıcı uygunluğu | PHP25 servis/HTTP testleri ve temel admin ekranları var; uluslararası müşteri seçimi, kur/adres editörü ve kapsamlı sayfalama tamamlanmadı |
| Gizlilik başvuruları, medya/S3 ve tam katalog düzenleme | PHP portu tamamlanmadı |
| Resmî fatura | Kontrollü dış referans servisi var; sağlayıcı ve tam ekran akışı bekliyor |
| Gerçek katalog, satıcı kimliği, hukuk/ülke/vergi onayları | İşletme ve hukuki onay bekliyor |

Bu yayın, çalışır test akışını incelemeye açar. Ana sözleşmenin bütün modülleri tamamlandı veya gerçek satışa hazır denmez.

14 Kasım son yayın: PHP25 etkin paket `7f9c90294d9c9e6b64b9cf64`. Vitrin yaş beyanı ardından hesapsız açılır; görünür krediler kaldırıldı ve ana ekran ikonları eklendi. Operasyon kullanımı ve rapor tanımları [PHP operasyon rehberinde](php-operations-guide.md). Daha yeni yerel işlerin durumu progress dosyasında ayrıdır.

Yerel disk alanı için yalnız bu görevin paketleri D: üzerine taşındı. Yeni paket için `python scripts/package-php.py --output-root D:\sexogate-local-artifacts-20261114\builds`; kurulum için `python scripts/test-php-install.py --sandbox-root D:\sexogate-local-artifacts-20261114\private-installs`; yayın için `python scripts/publish-php-test.py --deploy --package-root D:\sexogate-local-artifacts-20261114\builds`. Sırlar içeren sandbox kökü yalnız kullanıcı ve SYSTEM erişimine açık tutulmalıdır. `.local/php-package.json` güncel arşiv yolunu kaydeder. Varsayılan komutlar C: üzerinde yeterli alan olduğunda yine geçerlidir.

# Güvenli cPanel yayın otomasyonu

**Yeni mağaza/üyelik sürümü Turhost üzerinde yayımlandı ve canlı kabulü tamamlandı.** Güncel kanıt [teslim kaydında](teslim-durumu.md) bulunur; aşağıdaki sözleşme yayın otomasyonunun davranışını açıklar.

`scripts/deploy-cpanel.py` yalnız oluşturulmuş `artifacts/cpanel-release/` paketini kullanır. Varsayılan işlem, uzak sunucuya yazmayan `--plan` modudur. Yerel paket dosyaları, SHA-256 özetleri, PHP sürüm kimliği ve katalog modu denetlenir; beklenmeyen dosya, symlink, kaynak/ayar dosyası veya eksik dosyada işlem durur.

Python ortamında `requests` bağımlılığı bulunmalıdır; yerel doğrulama `requests 2.33.0` ile yapılmıştır. Ortak multipart yardımcısı yalnız `requests.Request(...).prepare()` ile standart istek gövdesi hazırlar; Requests üzerinden ağ isteği veya oturum açılmaz. Dosya MIME türü uzantıdan belirlenir, bilinmeyen türde `application/octet-stream` kullanılır ve binary baytlar aynen korunur. Gerçek aktarımın TLS ve kimlik doğrulaması mevcut korunan POST istemcisinde kalır. Bu sunucuda özel uzun boundary ile kapanış satırının dosyaya eklenmesi gözlendiği için standart encoder kullanılır; dağıtım ve geri alma her dosyayı ayrı, sıralı `overwrite=1` isteğiyle yollar. Bütün dosya adları ilk istekten önce doğrulanır; bir dosyanın başarısız yanıtı sırayı durdurur. Hazırlama ve gönderme ayrımı [Requests resmî belgesinde](https://requests.readthedocs.io/en/latest/user/advanced/#prepared-requests), dosya MIME alanı [multipart belgesinde](https://requests.readthedocs.io/en/latest/user/quickstart/#post-a-multipart-encoded-file) açıklanır.

Güncel özel dosya izin listesi yedi dosyadır: `account.php`, `catalog.json`, `config.json`, `media.json`, `media-approved.json`, `index.html`, `release.json`. Hesap veritabanı, oturumlar, yerel çalışma ortamı, `.env.local`, `client_secret*.json.local` ve diğer kimlik bilgileri pakete alınmaz. Kimlik dosyalarının yerelde bulunması Drive bağlantısı veya başarılı aktarım kanıtı değildir. `testOnly:true` taşıyan sentetik test paketleri üretim yükleyicisince reddedilir.

```powershell
python scripts/deploy-cpanel.py --plan
python scripts/deploy-cpanel.py --apply --expect-release PLANDA_GORULEN_RELEASE_HASH
```

`--expect-release`, incelenen plandan sonra paket değişmişse yayını engeller. Paket yeniden oluşturulduğunda önce plan tekrar alınır. Plan ve yayın başlangıcı cPanel `DomainInfo/domains_data` yanıtından ana alan adını, `94.199.205.78` IP adresini, `/home/nodenoho/public_html` document root'unu ve `nodenohome.com` ortak alias kaydını kontrol eder.

Kimlik bilgileri mevcut `scripts/hosting-probe.py` yardımcı koduyla, Git tarafından dışlanan `.env.local` dosyasından belleğe alınır. Argümanlara, çıktıya veya günlük dosyasına yazılmaz. cPanel bağlantıları yalnız `https://srvc77.trwww.com:2083` üzerinden, sertifika ve ana makine doğrulaması açık olarak yapılır. HTTP yönlendirmesi takip edilmez. FTP veya doğrulaması kapalı TLS kullanılmaz.

Yayın sırası:

1. Canlı hedefi yeniden doğrular ve mevcut public dosyaları listeler.
2. Bilinen eski metin dosyalarını ve varsa eski runtime ayarını okur. Yeni paketin üzerine yazacağı, gerçekten mevcut bütün public varlıkların eski binary baytlarını da alır; aşağıdaki eksiksiz yedek kapısı sağlanmadan uzak dosya değişimi başlamaz. Hepsini dışlanan `artifacts/hosting-backups/ZAMAN-SURUM/` altında, varlıkları kendi `public/` klasör yollarıyla saklar. `public-assets.json` dosyası byte sayısı ve SHA-256 özetlerini kaydeder.
3. Uzak `public_html` ağacının tamamını cPanel'in sunucu içi kopyalama işlemiyle `/home/nodenoho/nodeno-backups/ZAMAN-SURUM/` altına ayrıca yedekler. Böylece mevcut fontlar ve görseller dahil binary veriler sunucuda korunur. Yedeğin üst dizin kayıtlarını ve dosya boyutlarını doğrular. Otomatik geri alma, sunucu içi kopyalamanın üzerine yazma davranışını varsaymaz; doğrulanmış yerel baytları yeniden yükler.
4. Yedi özel dosyayı, üyelik kodu `account.php` ve görsel onayları dahil, `/home/nodenoho/nodeno-releases/RELEASE_HASH/private/` altına yükler; aynı yerde webden erişilemeyen `cache/` dizinini hazırlar. Kalıcı hesap dizini `/home/nodenoho/nodeno-data` ve temizlenmiş görsel kasası `/home/nodenoho/nodeno-media` sürümlerden ayrı hazırlanır; mevcut içerikleri yükleme paketiyle değiştirilmez.
5. Public varlıkları binary multipart aktarımıyla yükler. `.well-known` ağacı ve paketin değiştirmediği sağlayıcı dosyaları korunur.
6. Webden erişilemeyen `/home/nodenoho/nodeno-runtime.php` dosyasına sürüme özgü `privateRoot` ile sabit `storageRoot` ve `mediaRoot` yollarını yazar. Public `index.php` ve `.htaccess` dosyalarını en son yükler.
7. PHP girişini, `.htaccess` dosyasını ve özel dizin ayarını cPanel üzerinden tekrar okuyup beklenen baytlarla karşılaştırır. Aynı geri alma koruması içinde gerçek `https://nodenohome.com/api/health` yanıtının HTTP 200, `status: "ok"`, beklenen `releaseHash` ve `checkoutEnabled: false` değerlerini doğrular. PDO, görsel kasası, sürüm bütünlüğü veya HTTPS sorunu otomatik geri almayı tetikler.

Binary yedekler yalnız paketteki izinli statik yollar için, sabit `https://nodenohome.com` adresinden alınır. Her üst klasör ve hedef UAPI listesinde normal klasör/dosya olarak doğrulanır; symlink hedefi reddedilir. Bağlantı TLS sertifikasını ve alan adını doğrular, yönlendirme izlemez, kimlik bilgisi veya Authorization/Cookie başlığı göndermez. İstek sıkıştırmasız ve önbelleği atlayan biçimdedir; yanıtın gerçek byte sayısı UAPI dosya boyutuyla eşleşmelidir. Dosya başına sınır 20 MB, toplam binary yedek sınırı 100 MB'dir. Eksik, erişilemeyen, sıkıştırılmış, fazla büyük veya boyutu uyuşmayan bir varlıkta hiçbir public yazı başlamaz.

Herhangi bir public güncelleme, son okuma veya sağlık kontrolü başarısız olursa önce üzerine yazılan bütün eski varlıklar kendi klasörlerine aynı binary baytlarla yüklenir. Ardından eski runtime ayarı, `index.php` ve `.htaccess` geri getirilir. Böylece eski `#hero/#catalog` HTML'iyle yeni `#page` JavaScript'inin karışması önlenir. Önceki yayında `index.php` bulunmuyorsa sağlayıcının eski `index.php8` veya `index.php5` içeriği `index.php` olarak geri getirilir; bunlar da yoksa geçici 503 bakım yanıtı hazırlanır. Eski runtime ayarı bulunmuyorsa etkisiz `return [];` ayarı yazılır.

Geri alma yüklemeleri yalnız API başarı bildirimine dayanmaz: eski varlıklar HTTPS üzerinden tekrar okunup hash/boyutları, pointer/giriş/yönlendirme dosyaları UAPI üzerinden tekrar okunup eski baytları doğrulanır. Tek bir geri yükleme veya doğrulama başarısız olsa da diğer dosyaları kurtarma denenir; sonuç `manual_restore_required` ve yedek yoludur. Uzak dosya silinmez; yeni eklenen dosyalar kalabilir. Sağlayıcı ve ACME dosyaları, kalıcı hesap deposu ve görsel kasası geri alınırken değiştirilmez.

Public ağaç ve runtime ayarı yedeği SQLite hesap yedeği içermez. Hesap deposu sürümden bağımsızdır ve geri alma sırasında silinmez veya eski bir paketle üzerine yazılmaz. Tutarlı hesap yedeği/geri yüklemesi ayrı işletim işidir; WAL/oturum ayrıntıları [account-runtime.md](account-runtime.md) içinde açıklanır.

Bu yardımcı SSL sertifikası kurmaz ve alan adı/DNS kaydını değiştirmez. Başarı sonucu `uploaded_verified_health` durumudur; tarayıcı kabulünün tamamlandığı anlamına gelmez. Gerçek HTTPS üzerinden ana alan adı ve `.com` aliası, katalog, ürün görselleri ve UI akışları ayrıca doğrulanmalıdır. Yeni sürüm kabulü; gerçek kayıt/giriş/çıkış, parola/oturum iptali, adresler ve kullanıcıya ait kalıcı seçimler, sipariş/gönderi boş durumu, dört dil ve 1366/768/390 görünüm kontrollerini de kapsar. Geçici kabul hesapları kontrol sonunda silinir; gerçek müşteri verisiyle deneme yapılmaz. Ödeme kapalı ve Drive bağlantısı yok durumları doğrulanır.

Uzak sağlık uç noktası kurulu public dosyalar ve manifestteki özel kod/veri dosyalarının özetini kontrol eder; kalıcı hesap veritabanının içerik özeti değildir. Son canlı sonuç kesinleşene kadar teslim belgelerindeki başlangıç özeti değiştirilmez.

SSL sertifikasının kayıtlı bitiş tarihi 29.01.2027'dir. AutoSSL kapalıdır; mevcut yenileme yardımcısı elle çalıştırılır. Yayın yardımcısı otomatik yenileme takvimi kurmaz.

Yerel, kimlik bilgisi kullanmayan doğrulama:

```powershell
python -m unittest discover -s tests -p 'deploy*.py'
```

Testler izole paket ve sahte cPanel/HTTPS yanıtları kullanır; ağa çıkmaz. Planın yazmadığını, yanlış hedefi, dosya bütünlüğünü, kimliksiz ve sınırlı HTTPS yedeklemeyi, eksik yedekte durmayı, binary aktarımı, yayın sırasını, sağlık hatasında bütün eski varlıkların geri gelmesini ve sessiz geri alma bozulmasının başarı sayılmamasını kontrol eder. ACME/sağlayıcı dosyaları ile kalıcı SQLite ve görsel kasasının korunması da doğrulanır. Gerçek API yazmasının gerçekleştiği iddia edilmez.

Aktarım ve dosya işlemleri için resmî başvurular: [UAPI multipart upload_files](https://api.docs.cpanel.net/guides/quickstart-development-guide/tutorial-use-uapis-fileman-upload-files-function-in-custom-code), [API2 Fileman fileop](https://api.docs.cpanel.net/cpanel-api-2/cpanel-api-2-modules-fileman/cpanel-api-2-functions-fileman-fileop), [API2 Fileman mkdir](https://api.docs.cpanel.net/cpanel-api-2/cpanel-api-2-modules-fileman/cpanel-api-2-functions-fileman-mkdir). API2 yalnız eşdeğer UAPI işlemi bulunmayan sunucu içi kopyalama ve dizin oluşturma için kullanılır.

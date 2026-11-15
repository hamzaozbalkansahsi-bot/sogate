# Onaylı ürün görsellerinin yayınlanması

Yeni PHP sürümü ürün görsellerini yalnız tamamlanmış bir onay manifestiyle sunar. `pending`, `review_required`, `failed`, eksik referans veya değişmiş dosya yayını engeller. Temizlenmiş dosya bulunamazsa tedarikçi görseline dönülmez.

Orijinaller `artifacts/media-originals/` altında değişmeden korunur. İndirme kanıtı `artifacts/media-download.json`, temizleme ve inceleme sonucu `artifacts/media-cleanup.json` dosyasındadır. İkinci dosyada bütün referanslar son duruma ulaşmış olmalı ve son görsel/yapısal incelemeden sonra `publicationReady: true` olmalıdır. Bu alanın bulunmaması veya false olması, diğer durumlar onaylı görünse bile üretim derlemesini ve yüklemeyi durdurur. Geçici kalibrasyon çıktıları yayımlanmaz.

Ortak `lib/media-approvals.mjs` yardımcısı `loadMediaApprovals({root, media})` ile çağrılır ve `{manifest, mediaVersion, testOnly}` döndürür. Aynı yardımcı Worker ve cPanel derlemelerinde kullanılır; ürün çevirileri veya katalog kuralları çoğaltılmaz. Her kaynak URL'nin SHA-256 kimliği, tüm ürün/görsel referansları, indirme doğrulaması, kaynak ve çıktı dosyalarının gerçek SHA-256/uzunluk değerleri, raster imzası ve boyutları denetlenir. Temizlenmiş çıktılar ürün boyutlarını değiştiremez. Onaylanmış fakat değiştirilmemiş görüntü kaynakla aynı baytlara sahip olmalıdır.

Yayın paketinin webden erişilemeyen `private/media-approved.json` dosyası yerel dosya yolları ve zaman damgaları içermez. Şeması:

```json
{
  "schema": 1,
  "policy": "approved-only-v1",
  "referenceCount": 5129,
  "uniqueCount": 5129,
  "counts": {"approved_unmodified": 0, "approved_cleaned": 0},
  "references": {"2393:0": "KAYNAK_URL_SHA256"},
  "images": {
    "KAYNAK_URL_SHA256": {
      "state": "approved_cleaned",
      "sourceSha": "ORIJINAL_BAYT_SHA256",
      "outputSha": "ONAYLI_BAYT_SHA256",
      "mime": "image/webp",
      "bytes": 1000,
      "width": 880,
      "height": 880,
      "file": "ONAYLI_BAYT_SHA256.webp"
    }
  }
}
```

Örnekte sayımlar yalnız şemayı gösterir; gerçek derlemede bütün 5.129 referans ve hesaplanan doğru sayımlar bulunur. `approved_unmodified` için `file` null, `sourceSha` ve `outputSha` aynıdır. `mediaVersion`, deterministik manifest baytlarının SHA-256 değeridir; Worker bunu `catalog.meta.mediaVersion` içine koyar. cPanel Worker yanıtını aynen paketler ve sürümün aynı onay manifestine bağlı olduğunu kontrol eder.

Tarayıcıya gönderilen bütün ürün görselleri `/media/ÜRÜN/SIRA?v=MEDIA_VERSION` biçiminde sürümlenir. Bu değer önceki, bir gün önbelleklenmiş görsel yanıtlarının yeni arayüzde yeniden kullanılmasını engeller. Bu işlem dosyanın kendisindeki temizliğin yerine geçmez.

Temizlenmiş ve değiştirilmemiş bütün onaylı dosyalar sürüm dizinlerinden ve bütün document root dizinlerinden ayrı, kalıcı `/home/nodenoho/nodeno-media/` kasasında tutulur. Korunan `/home/nodenoho/nodeno-runtime.php` dosyasının `mediaRoot` alanı bu mutlak yolu seçer. Kasa symlink olamaz ve bir public/sürüm dizini altında bulunamaz. Her iki onay durumu için dosya adı yalnız onaylı içerik SHA-256 değeri ve doğrulanmış MIME uzantısından türetilir. URL, ürün adı veya istek parametresi dosya yolu seçemez.

PHP bütün dosyaların gerçek yolunu, MIME türünü, byte sayısını, piksel boyutunu ve SHA-256 değerini her sunumda kontrol eder. Değiştirilmemiş görseller de aynı yerel kasadan sunulur. Üretim görsel rotası CDN'e bağlanmaz ve eksik ya da değişmiş yerel dosyada hata döndürür. Eski URL tabanlı veya `approved-OUTPUT_SHA.bin` önbellekleri üretim rotasında kullanılmaz.

Yükleyici:

```powershell
python scripts/upload-clean-media.py --plan
python scripts/upload-clean-media.py --apply --expect-release INCELENEN_PHP_RELEASE_HASH
```

Varsayılan plan yalnız okur. Araç tamamlanmış üretim paketini ve temizleme manifestini birlikte denetler; hem `approved_cleaned` hem `approved_unmodified` dosyalarını yükler. Aynı gerçek içeriğe sahip dosyalar içerik hashleriyle tekilleştirilir. Aktarım mevcut cPanel yardımcısının doğrulanmış TLS ve korunan POST istemcisini kullanır; parola veya ham API hatası çıktı değildir.

Ortak multipart kodlayıcısı için Python ortamında `requests` gereklidir. Bu bağımlılık yalnız standart istek gövdesini hazırlar; aktarım mevcut korunan istemcide kalır. Standart boundary ve dosyanın gerçek MIME türü kullanılır; ayrıntılar [yayın otomasyonu belgesindedir](deployment-automation.md).

Çok dosyalı multipart aktarımında sunucu kaynaklı sorun yaşanırsa aynı komutlara `--single-files` eklenebilir. Bu seçenek her dosyayı ayrı bir `overwrite=0` isteğiyle gönderir; aynı anda en fazla dört HTTPS isteği çalışır. Mantıksal gruplar ve dosya boyutu sınırları değişmez. Bir grubun bütün istekleri sonlandıktan sonra kasa yeniden listelenir; yanıtı kaybolmuş başarılı dosyalar korunur ve yalnız hâlâ eksik dosyalar yeniden denenir. Plan çıktısı bu aktarım seçeneğini ve eşzamanlı istek sınırını gösterir. Seçenek verilmezse mevcut çok dosyalı aktarım kullanılır.

Kasa dosyaları içerik adlarıyla değişmezdir. Mevcut aynı ad/boyut kaydı devam ettirme için atlanır; boyut veya tür çakışması işlemi durdurur. `overwrite=0` kullanılır, uzak dosya silinmez ve eski kasa dosyaları korunur. Normal gruplar en çok 50 dosya ve 14.900.000 byte içeriktir. Katalogdaki 15.780.884 byte orijinal GIF gibi daha büyük onaylı dosyalar, görüntü değiştirilmeden tek başına aktarılır; dosya sınırı çalışma zamanıyla aynı 20.000.000 byte, multipart istek sınırı 20.100.000 byte'tır. Geçici hata sonrası yeniden listeleme, yanıtı kaybolmuş başarılı yüklemenin tekrarlanmasını önler. Tekrar çalıştırmak güvenlidir.

Boyut eşleşmesi bir uzak SHA-256 kanıtı olarak sunulmaz. İlk PHP sağlık kontrolü onay manifestinin yayın bütünlüğünü, tüm referansları ve her iki onay durumundaki bütün yerel kasa dosyalarının gerçek içeriklerini doğrular. Sonuç, özel kasada releaseHash, mediaVersion, kanonik kasa yolu ve her dosyanın boyut/mtime/ctime/inode/dev parmak izine bağlı bir doğrulama makbuzuna kaydedilir. Sonraki sağlık çağrıları bütün dosyaların türünü, symlink olmadığını ve metadata parmak izini denetler; değişiklik varsa tam içerik doğrulamasını yeniler. Böylece her genel sağlık isteğinde yaklaşık 600 MB tekrar okunmaz. Nonblocking dosya kilidi aynı anda birden çok tam taramayı önler; tarama sırasında set değişirse makbuz yazılmaz. Görsel rotası her sunumda gerçek SHA-256 denetimine devam eder. Başarılı yanıtta `mediaReady`, `mediaApproved`, `mediaCounts` ve `mediaVersion` alanları bulunur; mevcut hesap/PDO kontrolleri korunur. Yayından sonra genel HTTPS görsel yanıtlarının gerçek SHA-256 değerleri de onay manifestiyle karşılaştırılmalıdır. Google Drive aşaması kullanıcının talebiyle ertelenmiştir; görseller doğrudan Turhost kasasında barındırılır.

Sınırlı testler:

```powershell
node --test tests/clean-media-approvals.test.mjs tests/clean-media-runtime.test.mjs
python tests/clean-media-upload.test.py
```

PHP testleri gerçek PHP çalıştırıcısını kullanır; `PHP_BINARY` ile mutlak yol seçilebilir. Normal cPanel testlerinde `NODENO_MEDIA_APPROVAL_FIXTURE=raster-test-v1` yalnız `NODE_TEST_CONTEXT` ve onaylı izole çıktı dizini birleşiminde çalışır. Sentetik paket `release.testOnly=true` taşır ve üretim yükleyicileri tarafından reddedilir. Bu seçenek üretim çıktısında kullanılamaz ve gerçek temizlik tamamlanmış sayılmaz.

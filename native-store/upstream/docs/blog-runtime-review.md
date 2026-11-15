# Blog yayın motoru: yerel güvenlik ve davranış incelemesi

12 Kasım 2026. Bu kayıt yalnız blog sunucu motorunu kapsar. Canlı Turhost kabulü, cron kurulumu ve siteye bağlama işlemleri bu kayıtla doğrulanmış sayılmaz.

İncelenen dosyalar: `hosting/blog-store.php`, `hosting/blog-worker.php`, `hosting/blog-admin.php`, `scripts/blog-runner.php`; davranış testleri `tests/blog-runtime.test.mjs` ve `tests/fixtures/blog-runtime.php`.

## Sonuç

Gerçek PHP/PDO SQLite ile 16 davranış testi geçti; başarısız ve atlanan test yok. Beş PHP dosyasının sözdizimi denetimi geçti. Son çalıştırma çıktısı `artifacts/blog-runtime-review-tests.log` içinde, 19,96 saniyelik koşudur.

```powershell
node --test tests/blog-runtime.test.mjs
& 'artifacts/runtime-php/php.exe' -l hosting/blog-store.php
& 'artifacts/runtime-php/php.exe' -l hosting/blog-worker.php
& 'artifacts/runtime-php/php.exe' -l hosting/blog-admin.php
& 'artifacts/runtime-php/php.exe' -l scripts/blog-runner.php
& 'artifacts/runtime-php/php.exe' -l tests/fixtures/blog-runtime.php
```

## Düzeltilen bulgular

1. **CLI çalışma dizininin yanlış web kökü sayılması.** PHP CLI'da `DOCUMENT_ROOT` boş olduğunda `realpath('')` geçerli çalışma dizinine döner. Hosting ana dizininden çağrılan cron, bu nedenle meşru `nodeno-data` dizinini web kökünde sanıp reddedebiliyordu. Boş belge kökü artık çözülmüyor. Regresyon testi önce `blog_storage_unsafe` hatasıyla başarısız oldu; düzeltmeden sonra hosting ana dizinini taklit eden çalışma dizininden seed başarıyla tamamlandı.
2. **Windows junction denetimi.** Bu PHP çalışma ortamında dizin junction'ları için `is_link()` false, `lstat` tür biti sıfır dönüyor. Kalıcı depoya ve özel içerik bankasına junction üzerinden erişim başlangıçta kabul ediliyordu. İki kökte normal dizin türü artık ayrıca doğrulanıyor. Testler önce erişimin reddedilmediğini gösterdi; düzeltmeden sonra `blog_storage_unsafe` ve `blog_bank_unavailable` sonuçları alındı. Normal Windows kısa yol adları korunur; Unicode gerçek yol ile sözcüksel karşılaştırma yapılmaz.

## Doğrulanan davranışlar

- Europe/Istanbul 09:30 ve 18:30 slotları sırasıyla gerçek UTC `06:30:00Z` ve `15:30:00Z` olarak kaydediliyor. 288 adet beş dakikalık tick içeren tam günde her slotta bir yayın oluştu. Aynı 288 tick tekrarlandığında yeni yayın oluşmadı.
- Ayrı bir PHP süreci dosya kilidini tutarken ikinci süreç `busy` dönüyor ve yayın oluşturmuyor. Kilit bırakıldıktan sonra sekiz eşzamanlı ayrı PHP süreci toplam iki yazıyı birer kez yayımladı; iki yayın olayı oluştu.
- Slotlar ve duraklatma kalıcı SQLite verisinde saklanıyor. Yeni PHP süreçleri bunları koruyor. Kaçırılan yayınlar bir tick'te en çok dört kayıtla işleniyor.
- Yeni banka kayıtları mevcut en büyük ordinal sonrasına ekleniyor. Banka dizisinin sırası değişse bile mevcut yayın tarihleri değişmiyor. Seed sırasında sonradan kimlik uyuşmazlığı oluşursa işlem tamamen geri alınıyor; kısmi kayıt eklenmiyor.
- Medyanın SHA-256 özeti tutmazsa yazı yayımlanmıyor. Yeniden deneme gecikmesi korunuyor; beş başarısız denemeden sonra kayıt `dead` durumuna geçiyor. Bir yazıdaki hata aynı slottaki diğer yazının yayınını engellemiyor. Banka düzeltmesi bekleme süresini kendiliğinden sıfırlamıyor; onarılmış medya ile izin verilen zamanda yeniden yayın yapılabiliyor.
- Yeni içerik sürümü seed edildikten sonra eski banka snapshot'ıyla elle yayın isteği `blog_content_integrity_failed` sonucuyla reddediliyor.
- Yayımlanan içerik veritabanında snapshot olarak saklanıyor. Sonraki sürümde aynı yazının banka metni değişse bile mevcut yayımlanmış metin sessizce değişmiyor. Gelecekteki, bekleyen, başarısız veya duraklatılmış yazılar public listede ve tekil yazı okumasında gösterilmiyor.
- Çevirisi bulunmayan dilde tekil yazı `null`, liste boş dönüyor. Dil içeriği için sessiz Türkçe fallback yapılmıyor. `availableLocales` yalnız dolu içerikleri bildiriyor.
- Yönetim işlemleri mevcut `nodenoControlRequire` üzerinden kimlik, pazarlama yazma yetkisi ve yakın zamanda yeniden doğrulama gerektiriyor. Yetkisiz denemeler değişiklik yapamıyor. Elle yayın yalnız seçilen kayda uygulanıyor; tekrarı yeni olay ve yayın oluşturmuyor.
- Pause, resume, retry, hold, schedule ve manual publish olayları blog veritabanına kaydediliyor. Gerçek yönetim bağlamında ayrıca mevcut kontrol denetim kaydına yazılıyor. Kaynak gövde, teknik hata yığını veya erişim bilgisi olaylara konmuyor.
- Depo junction'ları, özel banka junction'ları, geçersiz slug ve traversal içeren medya URL'si reddediliyor. Public dizinin dışına çözülen görseller hash'i aynı olsa da yayımlanmıyor.

## Entegrasyon sözleşmesi ve sınırlar

`nodenoBlogAdmin` mevcut, aynı kaynak ve CSRF korumalı yönetim HTTP akışından çağrılmalıdır. İşlev, kendi başına HTTP gövdesi/Origin/CSRF denetleyicisi değildir. `ctx.root` kalıcı özel depo, `ctx.publicRoot` gerçek public kök, `ctx.db` mevcut yönetim PDO bağlantısıdır. `ctx.db` bulunduğunda yönetim denetim izi mevcut tabloda oluşturulur.

İçerik doğrulaması, banka üretimi ve yayına hazırlık denetimiyle birlikte kullanılır. Worker yalnız `original-diagram` türündeki, `/assets/blog/` altında bulunan ve SHA-256 özeti doğrulanan varlıkları kabul eder; bir kaynak CDN'ine geri dönüş yapmaz. Bankanın `schemaVersion`, zaman dilimi, slotları, benzersiz kimlikleri ve temel içerik yapısı çalışma anında tekrar kontrol edilir.

`blog.sqlite` müşteri ve ödeme veritabanından ayrıdır. CLI runner kalıcı `nodeno-runtime.php` işaretçisinden güncel özel sürüm kökünü alır; sunucunun `nodeno-blog/heartbeat.json` dosyasına sonuç yazar. Başarılı yayın tarihi gerçek işlem zamanıdır. Banka tükendiğinde `exhausted` ve kalan kayıt sayısı görünür durumdadır; motor yeni teknik ürün bilgisi veya ücretli AI çağrısı üretmez.

Başlangıçta yapılan tam `npm test` koşusu 427 testte 420 başarılı, 7 başarısız sonuç verdi (`artifacts/blog-runtime-full-tests.log`). Dört başarısızlık eşzamanlı geliştirilen blog sayfası testleriydi. Diğer üçü mevcut cPanel paketleme testlerinde `Supplier Worker/catalogue differs from the reviewed projection` hatası ve onun eksik çıktı sonucuydu. Bu inceleme sırasında katalog, genel derleyici ve ortak yönetim dosyaları değiştirilmedi; son yerel sonuç bu belgede belirtilen 16 blog runtime testiyle sınırlıdır.

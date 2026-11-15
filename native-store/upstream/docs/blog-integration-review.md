# Blog entegrasyonu inceleme bulguları

12 Kasım 2026. Kod değiştirilmedi. Aşağıdaki durumlar inceleme sırasında gözlendi; ilk bulguya yönelik eşzamanlı kök ajan düzeltmesi ayrıca kaydedildi.

## [P1] Otomatik çeviri kontrolü bozuk uygulama bilgilerini yayıma kabul ediyor

**Konum:** `scripts/compile-blog.py:100`, `scripts/translate-blog-local.py:42`, `scripts/translate-blog-local.py:78`.

İlk incelemede derleyici `checks: []` ve `reviewStatus: automatic-checks-passed` olan çevirileri doğrudan yayın bankasına alıyordu. Kontrol yalnız boş/kısa metni, sayı tokenlarını, belirli tekrarı ve alfabe varlığını denetliyor; anlamı veya hesap operatörlerini doğrulamıyor. Gerçek `data/blog-locales/ar/workshop-035.json:29` dosyasında `12×2?8=3`, aynı dosyanın 35. satırında `128=1,5` ve çevrilmemiş `In another label1` bulunuyor. İlgili makbuzun `checks` dizisi boş ve durumu başarılı. Boya katı bazı yerlerde bina katı anlamındaki `طوابق` sözcüğüne dönüşmüş. `data/blog-locales/ru/home-001.json` da dar oda başlığını `комнате Дар`, alan planlaması anahtar sözcüğünü `космическое планирование` olarak içeriyor.

**Düzeltme:** Otomatik sonuçları inceleme bekleyen taslak olarak tutun; doğrulanmış editoryal çeviriler yayıma alınsın. Formül operatörleri/birimler ve kaynak anlamı kontrol edilmeli. Düzeltilmiş veya incelemesi tamamlanmış içerik dışında reciprocal hreflang oluşturulmamalı. Mevcut dört test, semantik içerik kalitesini doğrulamıyor.

**Eşzamanlı durum:** Kök ajan, inceleme sırasında `compile-blog.py:100` kapısını yalnız `editor-reviewed` kabul edecek biçimde değiştirdi. Otomatik taslakların yayına alınması bu değişiklikle engelleniyor; dosyalardaki bozuk çevirilerin düzeltilmesi ve gerçek editoryal onay hâlâ ayrı içerik işidir. İnceleme ajanı bu kod değişikliğini yapmadı.

## [P1] Hreflang araç, kategori ve sayfa bağlamını kaybediyor; makale canonical'ı gereksiz araç sorgusunu koruyor

**Konum:** `hosting/blog.php:24`, `hosting/blog.php:25`, `hosting/blog.php:33`, `hosting/blog.php:35`.

Araç sayfasının canonical'ı `/blog?tool=paint` iken EN alternate `/blog?lang=en` oluyor; bu adres araç yerine yazı listesidir. Kategori ve sayfalama bağlamında da alternate bağlantıları liste köküne dönüyor. Dil gezinmesi kategoriyi ve sayfa numarasını kaybediyor. Ayrıca yayımlanmış makaleye `?tool=paint` eklendiğinde canonical aynı makalenin araç parametresi taşıyan ayrı adresi oluyor. `tool` ve `category` birlikte verildiğinde canonical kategoriye dönerken içerik araç ekranı olabiliyor.

**Düzeltme:** Gerçek sayfa türünden tek bir normalize sorgu türetin. Makalelerde bağlam sorgularını kaldırın; araç/kategori/sayfa varyantlarında canonical, alternate ve dil gezinmesi eşdeğer içeriği göstermeli. İzole gerçek PHP HTTP isteğiyle `/blog?tool=paint` ve `/blog?category=planning&lang=en` üzerindeki eşdeğer olmayan alternate adresler doğrulandı; kanıt `artifacts/blog-integration-review-http.json` içindedir.

## [P1] Yönetim işlem hatası yenileme tarafından hemen siliniyor

**Konum:** `web/blog-admin.js:16`, `web/blog-admin.js:17`.

`command()` hata yakaladığında yeniden kimlik doğrulama veya başka bir hata mesajını gösteriyor; `finally` içinde `refresh()` çağrılıyor. Durum GET'i başarılı olunca `refresh()` koşulsuz `message('')` çağırarak az önce gösterilen hatayı kaldırıyor. Böylece örneğin 5 dakikalık yetki yükseltme süresi dolduktan sonra “Şimdi yayımla” işlemi yapılmıyor ve gereken yeniden doğrulama açıklaması ekranda kalmıyor.

**Düzeltme:** İşlem hatasını başarılı durum yenilemesi temizlememeli. Hata ayrı tutulmalı veya sessiz yenileme seçeneği kullanılmalı. Yeniden doğrulama gerektiren POST ardından başarılı GET senaryosu tarayıcı testinde doğrulanmalı.

## [P2] Yönetim kayıtları runtime zaman ve hata alanlarıyla eşleşmiyor

**Konum:** `web/blog-admin.js:14`.

Runtime kayıtlarında zaman `at` ISO alanında, açıklama `detail` nesnesinde ve hata `error` alanında geliyor. Arayüz `occurredAt || occurred_at` ile `detail_json` okuyor. Bu nedenle yayın olayının zamanı tire olarak görünüyor; ayrıntılı hata ve yeniden deneme bilgileri kayboluyor. Kuyruk için yeni `queue` alanı doğru okunuyor; kayıt gösterimi henüz aynı sözleşmeye taşınmamış.

**Düzeltme:** `row.at`, `row.error` ve anlamlı `row.detail` alanlarını kullanın; olay zamanı ile hata sebebini gerçek runtime yanıtıyla kontrol edin.

## [P2] Yayımlanmamış makale önizlemesi arayüze bağlanmamış

**Konum:** `web/blog-admin.js:11`, `web/blog-admin.js:12`, `hosting/blog-admin.html:1`.

Planlı kaydın başlık bağlantısı public `/blog/<slug>` adresine gidiyor; doğru public gizlilik davranışı nedeniyle bu adres 404 döndürüyor. Yeni özel `GET /api/admin/blog/articles/<id>` önizleme ucu arayüzden çağrılmıyor. Kullanıcı şu anda metni incelemek için “Şimdi yayımla” eylemini kullanmak zorunda kalabilir.

**Düzeltme:** Pazarlama okuma yetkisiyle özel önizleme açın; metin ve teknik kaynakları yayın öncesinde gösterebilsin. Public gizliliği koruyun. İzole HTTP kontrolde gelecekteki yazı 404, yetkisiz özel önizleme 401 döndü ve gelecekteki başlık/slug public listeye veya sitemap'e sızmadı.

## [P2] Dil sayfalarında açıklayıcı görselin içindeki metin Türkçe kalıyor

**Konum:** `scripts/compile-blog.py:71`, `scripts/compile-blog.py:91`, `scripts/compile-blog.py:102`.

SVG görsel, Türkçe başlık ve `visual.labels` ile bir kez üretiliyor. Dil varyantlarına yalnız `imageAlt` ekleniyor; İngilizce, Rusça ve Arapça makaleler aynı Türkçe yazılı SVG'yi gösteriyor. Özellikle açıklayıcı çizimdeki yönergelere ihtiyaç duyan okuyucu çevrilmiş gövdeyle farklı dilde bir görsel alıyor.

**Düzeltme:** Açıklamaları gerçek dil içeriğinden üretin veya görseli dilden bağımsız tutup çevrilmiş açıklamayı HTML içinde verin. Alt metni çevirmek görsel içindeki etiketi çevirmiyor.

## Doğrulama sınırı

`node --test tests/blog-public.test.mjs tests/blog-tools.test.mjs` komutundaki 9 test geçti. İzole gerçek PHP HTTP isteklerinde public ve private kökler ayrıldı; `lang[]=ar&q[]=x&pg[]=4` girdisi 200 ile güvenli varsayılanlara döndü; yönetim durum/önizleme uçları oturumsuz 401 verdi. Origin ve CSRF koruması mevcut `nodenoControlBody()` üzerinden korunuyor. CSP başlıklarında self kaynaklı modül betikleri izinli ve public JSON-LD nonce'u mevcut. Bu incelemede gerçek tarayıcı yürütmesi yapılmadı; araçların DOM bağlama davranışı ve CSP altında etkileşimi için ayrıca tarayıcı kabulü gerekir. Canlı yayın yapılmadı.

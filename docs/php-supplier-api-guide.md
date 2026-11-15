# Canlı tedarikçi API bağlantısı — 15 Kasım2026

Kapsam: kullanıcının “API ile canlı al” isteği, mevcut PHP kaynak kataloğu ve cron kuyruğuna otomatik güncelleme ekler. Yalnız `/test` yayın yetkilidir; ana site, satış/ülke onayları ve başka sohbetlerin işleri korunur. Kullanıcının mimari ayrıntıları belirleme ve sürekli onay istemeden ilerleme talimatı esas alınır.

## Doğrulanan erişim ve karar

xShopum'un belgelenmiş WooCommerce Store API'sinde `stock_status=instock,outofstock,onbackorder` ile1.022 ürün, `hide_empty=false` kategori sorgusunda48 kategori vardır. Önceki varsayılan API sorgusu stokta olmayan354 ürünü dışarıda bırakıyordu. Kamu fiyatı ve bulunabilirlik bayi maliyeti/kesin miktar değildir.

Yerel standart PHP cURL ve gerçek cPanel PHP8.3.36 isteği403/Cloudflare erişim engeli aldı. Yerel Python standart HTTP istemcisi200 aldı; bu, hosting erişiminin çalıştığını kanıtlamaz. Özel `/test` probu tek kullanımlık token ile çalıştırıldı, kaldırıldı ve ana site fingerprint'i değişmedi (`.local/supplier-api-host-probe.json`). Proxy, challenge atlatma veya farklı işletme kimliği kullanılmaz.

Özel bayi API/XML alanları yerel dosyada boş: `XSHOPUM_XML_URL`, `LIONA_XML_URL`, `SISTINA_XML_URL`. xShopum [resmî rehberi](https://www.xshopum.com/xml-entegrasyon-rehberi/) bayi token'ını gerektirir. Liona/Sistina için doğrulanmış makine erişimi ve format olmadan hayalî API kurulmaz. Kullanıcıya erişimin bulunduğu yerel dosya soruldu; gizli değer istenmedi. [WooCommerce ürün API belgesi](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/products/) teknik kaynaktır.

## Uygulama ve kabul planı

1.030 SQL: kaynak batch'i `collecting/complete/failed`, API bağlantıları, çalıştırmalar ve sayfa hash/tekillik kayıtları. Eski aktarımlar complete kalır. Başarısız/yarım batch son başarılı katalog yerine geçmez.
2. Sabit HTTPS host/endpoint izin listesi, global IP denetimi ve cURL DNS sabitleme, TLS doğrulaması, redirect kapalı, süre/boyut sınırı olan istemci. Yalnız kamu katalog GET'i; müşteri/sipariş/ödeme verisi gönderilmez.
3. Her kalıcı kuyruk işi bir API sayfası alır. Sayfa yeniden teslimi ikinci kayıt üretmez. Header toplamları ve son tekil kayıt sayısı uyuşmadan complete olmaz. Boş/bozuk/kısmi yanıt eski veriyi silmez. Ürün açıklaması ve fiyatı müşteri kataloğuna otomatik yazılmaz; stok hiçbir zaman fiziksel depoya geçmez.
4. Mevcut PHP cron uygun açık bağlantıyı saatlik sıraya alır.401/403 erişim gerekli durumudur ve otomatik çekim kapanır; geçici hata sınırlı tekrar ve görünür başarısızlık üretir. MFA'lı katalog/yönetici bağlantıyı deneyebilir; ancak başarılı gerçek kontrol olmadan otomatik güncelleme açılamaz.
5. Gerçek DB testleri: sayfalama/tekrar teslim, eşzamanlı başlangıç, toplam uyuşmazlığı/atomik koruma,403 devre kesmesi, zaman aşımı/tekrar, rol ve fiziksel stok ayrımı. Yerel suite/syntax/browser, paket/temiz kurulum, şifreli yedek/restore, yalnız `/test` dağıtım ve gerçek cron erişim kontrolü. Çalıştırılmamış kontrol PASS sayılmaz.

## Gerçek durum

030 migration, sabit host/DNS IP sabitlemeli cURL, kalıcı sayfa kuyruğu, tamamlanma kontrolü,401/403 devre kesmesi, saatlik zamanlama ve MFA korumalı yönetim ekranı uygulandı. Gerçek xShopum API yanıtlarının12 sayfası izole yerel DB'de tekrar işlendi:1.022 ürün/48 kategori,0 depo/teklif/yayın yazımı. Bu tekrar işleme testi hosting ağ erişimi kanıtı değildir. Son yerel ve uzak kabul/yayın bilgisi `docs/progress.md` içinde tutulur. Hostingten gerçek başarılı API yanıtı gelmeden “canlı API çalışıyor” denmez.


## Yönetim kullanımı

1. `/test/yonetim/tedarikci-katalogu` ekranına katalog/yönetici hesabı ve MFA ile girin. **Canlı API bağlantıları** her tedarikçiyi ayrı gösterir.
2. xShopum **API bağlantısını dene** işlemi idempotency anahtarıyla bir çalıştırma başlatır; sayfalar dakikalık PHP cron'da ayrı kalıcı işler olarak alınır. Tekrar tıklama etkin çalıştırmayı çoğaltmaz; yeni denemeler arasında en az60 saniye vardır.
3. Başarılı gerçek sunucu bağlantısı varsa60–1440 dakika aralığında otomatik alım açılabilir. Manuel yerel dosya yüklemesi bu koşulu sağlamaz.401/403 halinde otomatik alım kapanır, hata panelde kalır. Geçici hata üç deneme sonunda başarısız olur; bir saati aşan terk edilmiş çalıştırma sonlandırılır.
4. **Son tamamlanmış kataloglar** yalnız bütün sayfaları/toplamları doğrulanan snapshot'ları gösterir. Toplam değişirse veya sayfa eksik/bozuksa önceki tamamlanmış sürüm korunur; kısmi veri taslaklaştırılamaz.
5. Liona/Sistina için onaylı bayi bağlantısı ve resmî format beklenir. Gizli URL/anahtarları sohbet, ekran görüntüsü veya Git'e koymayın. İlgili Git dışı `.env.local` alanları `XSHOPUM_XML_URL`, `LIONA_XML_URL`, `SISTINA_XML_URL`; bunlar henüz uygulanmış B2B adaptör değildir. Yeni erişim, izinli hedef/format doğrulandıktan sonra ayrı adaptörle bağlanmalıdır.

Sunucu403 engeli için xShopum'un bu hostingin çıkış adresine izin vermesi veya onaylı bayi API/XML sağlaması gerekir. Challenge taklidi, IP/kimlik değiştirme ve dolaylı proxy kullanılmaz. Güncel xShopum API kataloğu yerelde gerçekten alınır ve yetkili native yükleme ile yalnız özel `/test` incelemesine taşınabilir; bu yöntem sunucunun otomatik API bağlantısı olarak sunulmaz.

## Tekrarlanabilir yerel kontrol

```powershell
python scripts/test-source-catalog.py
python scripts/source-catalog.py --vendor xshopum --api-only --output-root D:/sexogate-local-artifacts-20261114/private-installs/supplier-api-live-20261115
python scripts/test-php.py --filter SourceApiTest
python scripts/test-php-source-api.py --capture-root D:/sexogate-local-artifacts-20261114/private-installs/supplier-api-live-20261115
python scripts/test-php-source-browser.py --test-api
python scripts/test-php.py --testdox
```

İlk ağ çekiminde boş, yeni bir özel çıktı kökü kullanın; aynı kökteki yanıt önbelleği ağ güncelliği kanıtı değildir. `test-php-source-api.py` sadece rastgele yerel test DB'sinde kayıtlı gerçek API yanıtlarını işler ve DB'yi kaldırır. Pozitif test taşıması yayın paketinde ayarlanamaz. `test-php-source-browser.py --test-api` ise standart gerçek HTTP istemcisini ve cron kuyruğunu kullanır; mevcut ortamda beklenen gerçek sonuç403 ve kapalı otomasyondur.

Ürün uç noktasında `orderby=id` desteklenir; kategori API'si bu değerde400 verdiği için belgelenmiş `orderby=name` kullanılır. [Resmî kategori API belgesi](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/product-categories/). `X-WP-Total` başlığı, sayfa boyutu ve son tekil kaynak sayıları sunucu adaptöründe doğrulanır. Kamu API bulunabilirliği gerçek tedarikçi miktarı değildir; tüm kayıtlarda `supplierQuantity=null` korunur.

## Dağıtım ve geri dönüş

Yalnız `/test` paketi kullanılır.030 öncesi uzak şifreli DB yedeği yerelde geri yüklenip29→30 ileri migration ile sınanır; sonra yeni paket/migration etkinleştirilir. Sağlık, özel dosya erişimi, ana site fingerprint'i ve cron heartbeat kontrol edilir. API denemesinden sonra91 tabloluk yeni yedek de tekrar geri yüklenir; dosya varlığı tek başına kanıt sayılmaz.

030'dan önceki uygulama kodu snapshot durumlarını tanımaz. API çalıştırması oluşturulduktan sonra29 koduna yalnız aktif dosya değiştirerek dönülmez: önce otomasyonu durdurun, yeni inceleme çıktısını güvenli saklayın ve doğrulanmış030 öncesi test DB yedeğini kontrollü geri yükleyin; ardından önceki paketi etkinleştirip sağlık/katalog/cron kontrolünü tekrarlayın. Ana site DB'si veya başka işletmenin yedeği kullanılmaz. Kod/schema birlikte korunmalıdır.

Açık operasyon işleri: onaylı bayi API formatı, gerçek maliyet/miktar/sipariş ve görsel lisansı; kaynak snapshot'ları için işletmenin belirleyeceği saklama/temizleme süresi. Şu an otomasyon kapalıdır; saatlik sınırsız arşiv üretildiği varsayılmaz. DB yedeği özel medya dosyası yedeği değildir.

# PHP operasyon kullanımı

Bu rehber `/test` PHP uygulaması içindir. Test ürünleri, test ödemeleri ve tarayıcı testlerinin taşıma referansları gerçek satış/sevkiyat sayılmaz. Gerçek sağlayıcı erişimi olmayan işlem başarılı gösterilmez. Yönetim girişi MFA ister; depo rolüne maliyet ve müşteri e-postası dönmez.

## Katalog ve depo

1. Yönetim → Ürünler: Türkçe/İngilizce ad, SKU, fiyat ve maliyeti girin. Fiyat alanı `149,50` kabul eder; sunucu alt birime çevirir.
2. Depo: fiziksel kabulü referans ve tekil işlem anahtarıyla kaydedin. Tedarikçi bildirimi fiziksel stok değildir.
3. Lot takibini stok girmeden açın. Gerekli lot numarası/son kullanma olmadan mal kabulü reddedilir. Tarihsel lot ilişkisi varken takip kapatılamaz.
4. Lot geri çağırma satılabilir miktarı karantinaya alır. Açılmış mühürlü veya geri çağrılan lota bağlı iade otomatik satışa dönmez.
5. Ürünü ülke için inceleyip yayımlayın. Ülke, belge, vergi ve ödeme kabulü ayrıca kontrol edilir. Arşivleme geçmiş siparişleri silmez.

Satın alma önce gerçek tedarikçiye bağlı sipariş, sonra ayrı mal kabulüdür. Çok satırlı kabul tek işlemde geri alınabilir. Mevcut ekran komut başına bir satır işler; çok satırlı kabul ekranı henüz tamamlanmadı.

PHP23 test yayınında tedarikçi oluşturma ve manuel dış sevk ekranları çalışır. Yönetim → Tedarikçiler ve gönderim: gerçek tedarikçi → sözleşme/veri aktarımı/ambalaj/iade referansları → ülke/para/gerçek taşıyıcı tarifesi → dış SKU ve süreli stok bildirimi → kaynak seçimi sırasını izleyin. Yeni bildirim ödenmiş tahsisi silmez. Dış siparişin gerçek teyidini paket ekranına kaydedin; sonra gerçek takip ve kalan adetlerle sevk edin. Mutabakat yalnız teyitten sonra yenilenmiş bildirimde ve açıkça seçilen tahsiste yapılabilir. Dış teslim ve QC kanıtı İadeler ekranında ayrı kaydedilir; kendi stok artmaz. Bu kayıtlar otomatik tedarikçi API bağlantısı değildir.

## CSV/XLSX içe aktarma

PHP23 test yayını: Yönetim → İçe aktarma. UTF-8 CSV şablonunu indirin; mevcut kategori kodu ve izinli görsel yolu kullanın. Fiyat `149,50` olabilir. Alternatif başlıklarda sütun eşlemesini değiştirin. Dosya2 MB,500 veri satırı,30 sütun ve XLSX'te tek sayfayla sınırlıdır. Makro, dış bağlantı, XML varlığı ve formül kabul edilmez. Özgün dosya kalıcı saklanmaz; hash ve doğrulanan önizleme kaydedilir.

Önizlemede bütün satırları kontrol edin; hata raporunu indirin. Hata varsa dosyayı düzeltip yeniden yükleyin. Hatasız önizleme24 saat içinde yalnız taslak ürün/varyant oluşturabilir. Önizlemeden sonra SKU/bağlantı çakışırsa bütün aktarım geri alınır. İçe aktarma stok, yayın veya ülke uygunluğu üretmez. Mevcut ürün güncellemesi ve tedarikçi XML/API çekimi bu sürümde uygulanmadı.

XLSX okuyucusu [PhpSpreadsheet5.11.0 resmî sürümü](https://github.com/PHPOffice/PhpSpreadsheet/releases/tag/5.11.0), [MIT lisansı](https://github.com/PHPOffice/PhpSpreadsheet/blob/5.11.0/LICENSE) ile sabitlenmiştir. [Resmî güvenlik açıklaması](https://phpspreadsheet.readthedocs.io/en/latest/topics/reading-files/#security) yanında uygulamanın boyut/makro/dış ilişki kontrolleri çalışır. Kurulum GD/ZIP/XML/PDO gerektirir; bu hostingte destekleri doğrulandı. PHP bağımlılık lisansları vendor arşivinde korunur.

## Toplama, paketleme, sevk

Sevkiyat ekranında ödenmiş sipariş ve varyant miktarıyla paket hazırlayın. Barkod varsa gerçek barkodu, yoksa SKU'yu önce toplama, sonra paketleme aşamasında okutun. Hazırlanmamış paket sevk edilemez. Aynı miktar iki pakete ayrılarak fazla sevk edilemez.

Manuel sevkte gerçek taşıyıcı ve gerçek takip numarası girilir. Pil/sıvı kısıtı varsa taşıyıcı kabulü gerekir. İade için ayrılmış, henüz sevk edilmemiş miktar paketlenemez. Sevk stoktan ikinci kez düşmez; ödeme stok çıkışını zaten işlemiştir. Gerçek kargo API'si ve etiket satın alma bağlı değildir.

## İade ve para iadesi

Müşteri, kendisine ait hesap/sipariş ekranından veya özel takip bağlantısından ürün, adet, gerekçe ve mühür durumuyla başvurur. Destek başvuruyu gerekçeyle kabul/reddeder. Fiziksel teslim alma, kalite kontrol ve para iadesi ayrı komutlardır.

Teslim alınan ürün karantinaya girer. Kontrol sonucu satışa dönüş, imha veya karantinada tutma kaydedilir. Açılmış/unknown mühür ve geri çağrılan lot için satışa dönüş engellenir. Tedarikçiden doğrudan sevk iadesi fiziksel depo kabulüyle otomatik artırılamaz; bu yolun PHP operasyonu henüz tamamlanmadı.

Para iadesini finans yetkisi yapar. Kısmi iadede sipariş anındaki indirim/vergi payı tamsayı hesabıyla dağıtılır. Test sağlayıcı yalnız test ortamında sonuç üretir. Stripe iadesi kalıcı iş kuyruğuna gider; API/webhook doğrulanmadan tamamlandı sayılmaz.

## İçerik, hukuk ve hesap

İçerik ekranında taslak kaydetme ve yayımlama ayrı işlemlerdir. Türkçe/İngilizce sürümler ayrıdır; diğer diller tamamlanmadan yayımlanamaz. Rehber sayfaları yayımlanan sürümü gösterir. Banner/menü/footer içerik türlerinin vitrindeki bütün bağlantıları henüz tamamlanmadı.

Hukuk ekranında taslak → işletme bilgileri ve inceleme referansıyla onay → yürürlüğe alma akışı kullanılır. Satıcı değişikliği hukuk onayını geçersiz kılar. Yeni metin geçmiş siparişin sözleşme snapshot'ını değiştirmez. Test hukuk örnekleri hukuki onay değildir.

Müşteri hesabında adresler, favoriler ve ayrı iletişim/analitik tercihleri bulunur. Pazarlama varsayılan kapalıdır. Girişte anonim sepet sunucuda deterministik birleşir. Hesap sahipliği her kayıtta denetlenir.

## Rapor ve işler

Rapor tarih aralığı sipariş oluşturulma kohortudur; tahsil edilmiş siparişlerin brüt tutarı, bu siparişlerin iadeleri, kaydedilen vergi/maliyet/giderleri ayrılır. Ortalama sepet tahsil edilmiş sipariş brütü / sipariş sayısıdır. Katkı net işletme kârı değildir; eksik giderler ayrıca belirtilir. Dönem içinde gerçekleşen bütün muhasebe hareketlerinin nakit raporu değildir.

Kuyruk ekranı deneme sayısı ve hata kodunu gösterir; gizli yükü göstermez. Yalnız başarısız işler yetkili olarak yeniden denenebilir. SMTP yoksa e-posta ertelenir; ödeme tekrar alınmaz. Rol değişikliği eski oturumları iptal eder. İşlem geçmişi yöneticiye açıktır.

## Stripe yapılandırma sınırı

Git dışı PHP yapılandırmasında `payment_provider`, `stripe_secret_key`, `stripe_webhook_secret`, `stripe_business_approved` ve `stripe_enabled_currencies` alanları kullanılır. `stripe_business_approved` yalnız gerçek işletme/kategori kabulünden sonra true olabilir. Bu yayında test sağlayıcısı korunur; Stripe hesabı/anahtarı/kategori kabulü doğrulanmış değildir.

Webhook adresi `/test/api/payments/webhook` için ham gövde ve Stripe imzası doğrulanır; tarayıcı dönüşü ödeme kanıtı değildir. Ödeme girişimi, olay inbox'ı ve kuyruk kalıcıdır. Tutar, para birimi, ortam ve oturum/sipariş eşleşmesi denetlenir. Mutabakat işi kayıp bildirimi API'den araştırır. Yerel SDK testleri gerçek Stripe test hesabı kabulü yerine geçmez.

Resmî kaynaklar: [Checkout oturumları](https://docs.stripe.com/api/checkout/sessions), [webhook imzaları](https://docs.stripe.com/webhooks/signature), [iadeler](https://docs.stripe.com/api/refunds), [kısıtlı işletmeler](https://stripe.com/legal/restricted-businesses). Teknik hazırlık kategori kabulü sağlamaz.
## Vitrine giriş ve ana ekran kısayolu — 14 Kasım

`https://sexogate.com/test/` müşteri vitrini yaş beyanı ardından üyelik istemeden açılır. İsteğe bağlı hesap sayfası, sipariş geçmişi ve kayıtlı adresler için kullanılmaya devam eder. Yönetim `/test/yonetim/giris` adresindedir; test personel erişimi, yönetici parolası ve MFA ayrı korumalardır. Müşteri girişindeki görünür geliştirici/tasarımcı kredisi kaldırılmıştır.

iOS Safari'de Paylaş → Ana Ekrana Ekle; Android tarayıcısında menü → Ana ekrana ekle / Uygulamayı yükle kullanılabilir. İkonlar manifest ve Apple Touch Icon ile sunulur. Daha önce ikonsuz eklenen kısayol eski işletim sistemi önbelleğini kullanıyorsa kaldırılıp `/test/` bağlantısından yeniden eklenebilir. Gerçek cihaz kurulumu henüz doğrulanmadı; tarayıcı kontrolleri manifest kapsamı ve gerçek PNG dosyalarını doğrular. Çevrimdışı alışveriş veya hassas sayfalar için ortak önbellek eklenmemiştir.

Ülke ve vergi `/yonetim/pazarlar`, fiyat listeleri `/yonetim/fiyatlar`, SKU/model belgesi ve taşıyıcı incelemesi `/yonetim/uygunluk` ekranlarındadır. Yeni ülke kapalı oluşturulur; koşul değişince inceleme sürümü yenilenir. Onay referansı ve son kontrol zamanı gerçek incelemeye dayanmalıdır. Belgelerin kaydı, ürün yayın onayını kendiliğinden vermez. Uluslararası müşteri seçimleri ve bütün yönetim editörleri henüz tamamlanmadı; yabancı para depo maliyet dönüşümü uygulanana kadar o kaynakla yabancı para checkout kapalıdır. Gerçek Stripe ve ticari satış onayları bu test ekranlarıyla sağlanmış sayılmaz.

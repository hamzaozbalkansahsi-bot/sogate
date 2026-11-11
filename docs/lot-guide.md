# Lot, son kullanma ve geri çağırma rehberi

Lot takipli fiziksel SKU'lar mevcut depo toplamıyla aynı işlemsel veriyi kullanır. Lot ayrıntısı toplam stoktan bağımsız ikinci bir stok kaynağı değildir. Bu akış tek sevkiyat deposu `main` içindir; çok depolu tahsis ve lotlar arası transfer henüz uygulanmadı.

## Takibi açma

Yönetici veya MFA doğrulanmış depo rolü, **Lot ve son kullanma → Lot takibini aç** üzerinden SKU seçer. Tüm depolarda kullanılabilir stok, karantina ve etkin rezervasyon sıfır olmalıdır. Son kullanma tarihinin zorunlu olup olmadığı burada kaydedilir. Varsayılan olarak mevcut SKU'larda takip kapalıdır ve eski stok akışı korunur.

Mevcut stoğu tahminen üretici lotlarına dağıtan dönüştürme yoktur. Belgeye dayalı stok atfetme aracı ayrıca geliştirilmeden sıfır olmayan stoğa takip açılamaz. Set üst SKU'su yerine fiziksel bileşenler izlenir.

## Mal kabulü

Satın almaya bağlı teslimatlar **Satın alma ve mal kabul** bölümünden alınır. Satın alma kaydını ve SKU'yu arayıp seçin; gelen miktarı, her gerçek lotun etiket/tarih/adet ve belge referansını girin. Bir SKU birden çok lotla gelebilir; lot toplamı kabul adedine eşit olmalıdır. **Mal kabulü önizle** ile kalanları ve karantina kararlarını inceleyip **Mal kabulü kaydet** ile onaylayın. Lotlu ve normal SKU'lar aynı kabulde bulunabilir. Yönetici/depo kabul eder; yönetici/katalog satın alma oluşturur; finans fiziksel kabul yazamaz. Ayrıntı: [purchase-lot-guide.md](purchase-lot-guide.md).

**Lot mal kabulü** formu satın alma dışı belgeli giriş içindir. Gerçek üretici lot numarası, etiket tarihi, adet ve kaynak belge referansı girilir; satın alma kalanını kapatmaz. Referans girilmesi dış belge doğrulamasının otomatik yapıldığı anlamına gelmez. Özel ağdan belge veya tedarikçi stoğu çekilmez. Takipli SKU'da genel stok artırma, sayım düzeltme ve lot bilgisi taşımayan satın alma kabulü kapalıdır.

Her kabulde toplam depo ve ilgili lot ayrıntısı tek transaction içinde bir kez değişir. Satın almaya bağlı kabul aynı işlemde alınan miktarı, kalanı ve satın alma durumunu da günceller. Aynı işlem anahtarının tekrarı ikinci mal kabulü üretmez; farklı içerikle tekrarı reddedilir. Yanıt alınamazsa satın alma önizlemesindeki **Aynı kabulü yeniden dene** kullanılır. Formu kapatıp yeni kabul açmak aynı anahtarı korumaz; önce mevcut kayıtları kontrol edin. Aynı üretici lotunun tarihi kabul sonrasında form üzerinden değiştirilemez. Aynı fiziksel teslimatı ayrıca satın alma dışı yoldan tekrar girmeyin.

Tarihi geçmiş ürün yalnız açık karantina kabulüyle kaydedilebilir. Lotun kalan tüm stoğu karantinaya alınabilir; ayrı kontrol kararıyla açılabilir. Geri çağrılan veya tarihi geçen lotun karantinası satış için açılamaz.

## Satın alma kaynakları

Lot satırındaki **Satın alma kaynakları** düğmesi tedarikçi, gerçek satın alma/kabul kimlikleri, kabul miktarı, bunun içindeki karantina miktarı, belge referansı ve kayıt zamanını gösterir. Arama ve 25 kayıtlık sayfalama vardır. Kimlikler gerçek sistem kayıtlarıdır; irsaliye/fatura numarası gibi sunulmaz. Panel yönetici, katalog, depo ve finansın MFA doğrulanmış oturumlarına açıktır; maliyet, banka veya müşteri iletişim alanları içermez.

Bir lot farklı satın almalardan veya kısmi kabullerden oluşmuşsa bütün gerçek kaynaklar ayrı görünür. Bu görünüm, belirli bir satılmış adedin tek satın alma kaynağını ispatlamaz. Satın alma dışı giriş ayrı kartla gösterilir; eksik tarihsel kaynaklara uydurma tedarikçi veya belge eklenmez. Kaynak ilişkisi geri çağırma sırasında silinmez.

## FEFO ve sipariş

Son kullanma tarihi önce gelen uygun lot önce ayrılır. Tarih gerektirmeyen lotlar en sona gelir; eşit tarihlerde lot kimliği sabit sıra sağlar. Türkiye deposunda tarih, Europe/Istanbul gününe göre değerlendirilir: etiketteki tarihin başladığı günden itibaren satışa ayrılmaz. Bu muhafazakâr operasyon kuralı etiket ve gerçek ürün politikasıyla canlı öncesinde doğrulanmalıdır.

Satılabilir miktar, geçerli lotların kullanılabilir miktarı ile toplam depodaki kullanılabilir miktarın küçüğünden güvenlik payı düşülerek bulunur. Karantina, geri çağırma, tarih ve etkin rezervasyonlar hesaba katılır. Checkout toplam depo satırlarını sabit sırayla kilitler; lot tahsislerini `reservation_lots` içine kaydeder. Ödeme bu tahsisleri tüketir, yeniden bir lot seçmez. Set bileşenleri de aynı akışa dahildir.

Başarısız ödeme, iptal ve rezervasyon süresi dolması lot tahsisini etkin olmaktan çıkarır. Süresi geçmiş veya arada geri çağrılmış/uygunsuz olmuş lota gelen başarılı ödeme `payment_exception` olur. Stok negatif olmaz ve otomatik sevkiyat açılmaz. Aynı ödeme olayı tekrar tüketim üretmez.

## Geri çağırma

Lot satırındaki **Lot işlemi → Lotu geri çağır** alanına karar belgesi ve gerekçe girilir. Kalan fiziksel stok karantinaya taşınır; ilişkili rezervasyon ve ödenmiş siparişlere erişim **Sipariş ilişkileri** raporundan sağlanır. Depo raporu müşteri iletişimini ve maliyetleri içermez. İlişkili lotla sevkiyat kapalıdır.

Bu işlem müşteri veya üreticiye e-posta/SMS göndermez. Gönderilmiş ürünün geri çağırma koordinasyonu işletmenin yetkili ekibince ayrıca yürütülür. Fiziksel toplama/paketleme ekranında lot barkodu okutma ve paket içindeki seri/lot doğrulaması henüz yoktur; yazılım tahsisi fiziksel etiket eşleşmesinin kanıtı değildir.

## Lotu doğrulanmamış iadeler

İade kabulü önceki siparişin değişmez fiziksel bileşen kaydını kullanır. Takipli bileşen lotu iade sırasında tahmin edilmez. Stoğu ayrı iade karantinasında kalır; lot stok satırları artırılmaz. **Lotu doğrulanmamış iadeler** görünümü bu kayıtları gösterir. Mührü kapalı olsa bile normal kalite kontrol veya genel karantina açma işlemi bu stoğu satışa döndüremez.

Belgeye ve fiziksel etikete dayanarak iade lotunu yeniden doğrulama, yeniden atfetme veya imha işlemi bu sürümde uygulanmadı. Lot bilinmeyen iade için kalite kontrol sonucu **Karantinada tut** olmalıdır.

## Teknik kayıt ve doğrulama

018 migration mevcut `inventory_lots` ve `inventory_movements.lot_id` ilişkisini genişletir. `inventory_lot_balances` fiziksel ayrıntıyı, `reservation_lots` sipariş tahsisini, `lot_operations` idempotent işlemleri tutar. 025 migration, satın alma kabulü–lot–gerçek hareket bağlantısını `purchase_receipt_lots` ile ekler; alınan miktar satın alma kalanıyla birlikte korunur. Yeni kabul/karantina/satış hareketleri lot kimliği taşır; aynı işlem için ikinci toplam hareketi yazılmaz. Kaynak ve karar referansları işlem günlüğünde korunur.

Yerel bağımsız test: `npx tsx --env-file=.env.local scripts/lot-integration.ts`. Komut yalnız yerel `TEST_DATABASE_URL` üzerinden rastgele `sexsogate_<hex>_lot_test` oluşturur; test sonunda yalnız kendi oluşturduğu veritabanını siler. Tarayıcı testi `npx playwright test tests/e2e/lots.spec.ts`; yerel geliştirme veritabanında yalnız kendi fixture kayıtlarını kullanıp temizler. Gerçek üretici lotu, gerçek kullanıcı veya canlı tahsilat oluşturmaz.

11 Kasım 2026 yerel kanıtı: yetkili takip açma çağrısı önce mevcut çekirdekte 403 ile RED verdi; uygulamadan sonra lot entegrasyonunun 11 kontrolü, mevcut operasyon entegrasyonunun 14 kontrolü ve 112 birim testi geçti. Chromium ve WebKit gerçek form senaryosu geçti; 390 px ekranında sayfa taşması ölçülmedi. Masaüstü ve mobil çıktılar `docs/screenshots/admin-lots-desktop-{chromium,webkit}.png` ve `docs/screenshots/admin-lots-{chromium,webkit}.png` içindedir. Bu kayıt gerçek cihaz, gerçek depo kabulü veya üretimde geri çağırma tatbikatı kanıtı değildir. Genel lint, typecheck, build ve tüm-site testlerinin nihai durumu `docs/progress.md` içinde ayrı tutulur.

Yukarıdaki tarihsel lot kontrolünden sonra yeni `tests/e2e/purchase-lots.spec.ts` Chromium/WebKit **2/2 PASS** geçti. Kendi yerel satın alması ve stoklarında 390/1440 px önizleme/kaynak paneli, klavye, Axe, kaybolan gerçek başarılı yanıtın aynı anahtarla tekrarı ve kısmi/tam kabul doğrulandı. `docs/screenshots/purchase-lot-{preview,sources}-{chromium,webkit}-{desktop,mobile}.png` ekranları üretildi. Son toplu koşu **94/94 E2E (47+47), 246 birim/232 DB** ve build sonucunun kanonik kaydı [test-evidence.md](test-evidence.md) içindedir. Güncel kapsam [progress.md](progress.md) ile izlenir. Fiziksel lot barkodu/paket kontrolü, lotu bilinmeyen iadeyi yeniden atfetme/imha ve çok depolu transfer açık kalır.

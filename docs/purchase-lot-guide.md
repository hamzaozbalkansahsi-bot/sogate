# Lotlu satın alma mal kabulü

Bu modül fiilen kabul edilen miktarı mevcut satın alma siparişinin kalanına ve üretici lotuna bağlar. Depo `main` olarak kalır. Satın alma kaydı veya tedarikçi stoğu tek başına satış stoğu oluşturmaz. Sunucu ve yönetim arayüzü son başarılı yerel kontrol noktasında doğrulandı; kaynak sürümü ve toplu sonuçlar [progress.md](progress.md) ile [test-evidence.md](test-evidence.md) içindedir.

## Sunucu girdi sözleşmesi

`POST /api/admin/purchases`, `action: "receive"` için satın alma kimliği, sabit `idempotencyKey`, teslimat belgesi `sourceReference`, işlem `reason` ve `items` alır. Yeni kabullerde teslimat kaynağı zorunludur; gerçek irsaliye/arşiv referansını girin. Belge veya üretici lotu yazılım tarafından oluşturulmaz, referansın verilmesi dış belgenin doğrulandığını göstermez.

Her SKU satırı `{variantId, quantity}` biçimindedir. Lot takipli SKU ayrıca `lots: [{lotNumber, expiresAt, quantity, quarantined, sourceReference}]` ister. Lot adetlerinin toplamı SKU kabul adedine tam eşit olmalıdır. Takipsiz SKU'ya lot alanı eklenemez. Kaynak alanları teslimat başlığında ve lot etiketinde ayrı tutulur; birbirinin üstüne yazılmaz.

Sınırlar: bir kabulde en çok 100 SKU ve toplam 200 lot; SKU başına en çok 50 farklı lot; adetler 1–1.000.000 tam sayı; lot numarası 1–300, kaynak 5–1000, gerekçe 5–500 karakter. Aynı SKU veya aynı SKU'da aynı lot numarası tekrarlanamaz. İstemciden maliyet, rol, tedarikçi veya hesaplanmış kalan miktar kabul edilmez. İzinli şema [purchase-receipts.ts](../src/shared/purchase-receipts.ts) içindedir.

Güncel SKU politikası sunucuda denetlenir. Son kullanma zorunluysa tarih boş olamaz. Tarihi bugüne ulaşmış/geçmiş lot yalnız açık karantina kabulüyle alınabilir. Aynı SKU+üretici lot numarasının kayıtlı tarihi değiştirilemez; geri çağrılmış lotta yeni kabul yapılamaz. Mevcut lotun bütününe uygulanan karantina durumu ile yeni kabul çelişirse işlem reddedilir. Kısmen karantinaya ayırma modeli varmış gibi aynı lotu iki farklı durumla açmayın.

## Tek kabul, tek stok hareketi

PO ve kalemleri, mantıksal set kimliği, ürün/SKU, ana depo ve lot bakiyeleri sabit kilit sırasıyla korunur. PO kalanından fazla alım reddedilir. `receiveLotStock`, çağıranın transaction'ını kullanır; kendi başına ikinci transaction veya bağımsız mal kabulü açmaz.

Normal SKU'da mevcut tek depo hareketi; lot takipli SKU'da her lot için tek lot hareketi oluşur. Ortak lot yazıcısı hem toplam depo hem lot bakiyesini bir kez artırır; satın alma döngüsü lotlu satırın toplamını ikinci kez artırmaz. `purchase_receipt_items` toplam fiziksel SKU kabulünü; `purchase_receipt_lots` lot ayrıntısını ve aynı gerçek hareketi bağlar. Bu kayıtlarla `purchase_items.received` ve PO durumu aynı commit'te güncellenir.

Karma kabulde bir hatalı lot, tarih, kalan miktar veya politika bütün işlemi geri alır. Önceki normal satırın stoğu da kısmen yazılmaz. Başarısız istekte yeni kabul başlığı, lot, hareket veya alınan adet kalmaz. Mantıksal set üst SKU'suna fiziksel kabul yapılamaz; fiziksel bileşenler kullanılmalıdır.

`quantity`, satılabilir ve karantina dahil **toplam fiziksel kabul** miktarıdır. `quarantineQuantity` bunun içindeki kısımdır; toplama yeniden eklenmez. Karantinaya kabul PO kalanını azaltır, satış stoğunu açmaz. Yerinde reddedilen ve depoya alınmayan miktar kabul adedine girmez. Tedarikçiye iade, mali mahsup ve hasar tazmini ayrı operasyonlardır; bu modül bunları tamamlanmış göstermez.

## Tekrar ve eski kayıtlar

Yeni v2 istek hash'i aktörü, normalize edilen SKU/lot satırlarını, adetleri ve kaynakları kapsar. Sadece satır sırasının değişmesi yeni kabul üretmez. Aynı anahtar ve aynı aktör/içerik önceki kabul sonucunu döndürür. Başka kişi veya değiştirilmiş içerik aynı anahtarla kullanılamaz. Ağ hatasında aynı kayıt tekrar denenir; düzeltilmiş farklı kabul ayrı bir işlem olarak hazırlanmalıdır.

Doğrudan lot kabulü ile satın alma kabulü ortak stok-kabul anahtar kilidini kullanır. Aynı anahtar iki yoldan farklı stok hareketi üretemez. Eski v1 normal kabulün aynı aktör ve eski içerikle tekrarı korunur; yeni belgesiz v1 kabul açılmaz. Eski kayda sonradan kaynak veya yeni onaylayan kişi uydurulmaz.

**Lot mal kabulü** ekranındaki doğrudan giriş PO dışı belgeli giriştir ve PO kalanını kapatmaz. PO'ya bağlı teslimat satın alma mal kabulünden yapılmalıdır. Farklı yeni anahtarlarla aynı fiziksel teslimatı iki kez elle girmek, serbest belge metninden kesin tespit edilemez; aynı irsaliye çok SKU/lot içerebildiği için belge referansı global tekil yapılmamıştır. Operasyon aynı teslimatı iki yolda ayrı kayıt olarak girmemelidir.

## Kaynak izi, roller ve FEFO

`lotSources(principal, lotId, {q, page})` gerçek PO/kabul/tedarikçi, toplam kabul ve karantina payı, lot kaynağı, teslimat belgesi ve kayıt zamanını döndürür. 25 kayıtlık sayfa/toplam aynı SQL snapshot'ındadır. Doğrudan kabul `kind: "direct"` olarak ayrılır; PO/kabul kimliği ve tedarikçi alanı boştur. Kaynağı bağlanamayan eski kayıtta referans boş veya sonuç yoktur; lotun ilk referansı her eski kabulün kaynağıymış gibi çoğaltılmaz. PO ve kabul modelinde numara alanı yoktur; kimliklerden sahte belge numarası üretilmez.

Satın alma oluşturma yönetici/katalog; kabul yönetici/depo ve gerçek MFA ister. Kaynak paneli hem lot hem satın alma okuma yetkisi gerektirir: yönetici, katalog, depo ve finans okuyabilir. Destek, pazarlama ve müşteri bu ilişkileri alamaz. Depo yanıtlarında birim maliyet, banka ve iletişim verisi yoktur. Finans yetkisi fiziksel kabul yazma yetkisi değildir.

FEFO ve ödeme aynı `reservation_lots → inventory_lots` tahsisini korur. Yeni ilişki `lot → purchase_receipt_lots → purchase_receipts → purchase_orders/tedarikçi` kaynak zincirini sağlar. Aynı üretici lotu birden çok PO'dan geldiyse bütün gerçek kaynakları gösterir; belirli bir satılmış adedi tek PO'ya atamış gibi davranmaz. Geri çağırma kaynak ilişkilerini silmez; otomatik e-posta/SMS veya fiziksel etiket taraması üretmez. Lotu bilinmeyen iadeler ve çok depolu transfer bu teslimin kapsamı değildir. Mevcut stok/FEFO sınırları [lot-guide.md](lot-guide.md) içinde açıklanır.

## Migration ve yerel sunucu kanıtı

`025_purchase_lot_receipts.sql`, kabul başlığına kaynak/hash sürümü; lot-kabul-hareket ilişkisi ve doğru SKU'yu koruyan FK'ler; alınan adet için `0 ≤ received ≤ quantity` CHECK ekler. Mevcut hatalı eski veri varsa migration sessizce düzeltmez. Uygulanmış dosyanın checksum'u değiştirilmez. Migration yerel geliştirme DB'sinde uygulanmıştır; sunucu regresyonları ayrı, benzersiz yerel test DB'lerinde çalışır. Staging veya production migration'ı yapılmadı.

Yeni karma kabul ilk denemede eski sunucunun lot alanını `INVALID_INPUT` ile reddetmesiyle RED verdi. Şema birim testi önce modül yokluğunda RED oldu. Son hedefli sonuç:

- `npx vitest run tests/unit/purchase-receipts.test.ts` — 5/5 PASS.
- `npx tsx --env-file=.env.local scripts/purchase-lots-integration.ts` — 14/14 PASS: karma/karantina/kalan, canonical ve actor replay, eski v1 tekrar, farklı anahtarlı son adet yarışı, doğrudan/PO aynı anahtar yarışı, FK/limit, maliyetsiz rol alanları, bir lotta çok PO kaynağı, gerçek quote→checkout→FEFO ödeme→recall ve tamamlama.
- Mevcut operasyon, lot, set ve quote DB regresyonları yeni şemayla geçti. Kapsam ve toplu komut sonuçlarının kanonik kaydı ana ilerleme/test belgesindedir.

Üretici belgesi, fiziksel depo kabulü, gerçek cihaz veya dış sağlayıcı kabulü bu yerel testlerden türetilmez. Sunucu ve tarayıcı kontrolleri ayrı kanıt türleridir; son ortak kaynak sürümü [test-evidence.md](test-evidence.md) içinde tanımlıdır.

## Yönetim ekranından satın alma kabulü

1. Yetkili hesabınızla giriş yapın ve oturumun iki adımlı doğrulamasını tamamlayın. **Satın alma ve mal kabul** bölümünü açın. Satın alma oluşturma ile fiziksel kabul ayrı işlemlerdir.
2. Yönetici/katalog rolü **Yeni satın alma** ile tedarikçiyi ve gerçek SKU'ları seçer; sipariş adedi ve TRY kuruşu cinsinden birim alış maliyetini girer. Kaydı oluşturmak stok artırmaz. Depo rolünde bu form ve maliyet alanları gösterilmez.
3. Teslimat geldiğinde tedarikçide arayın; ilgili satın alma satırındaki **Mal kabul** düğmesini kullanın. Alternatif olarak üstteki **Satın almadan mal kabulü** düğmesinden tedarikçi arayıp satın alma kaydını seçin. Bu ikinci yol da seçilen satın almaya bağlıdır. Liste ve kayıt seçimi 25 kayıtlık sunucu sayfalarıyla çalışır.
4. **Kabul edilecek stok kodunda ara** alanıyla sipariş içindeki SKU'yu bulun ve **Ürünü kabule ekle** seçin. Her satır sipariş, teslim alınan ve kalan miktarı gösterir. **Kabul adedi** alanına yalnız o teslimatta fiilen alınan miktarı yazın. Seçilmeyen SKU'lar beklemede kalır; kalan miktarın tamamını almak zorunda değilsiniz.
5. Lot takipli SKU'da gerçek üretici lot numarasını, lot adedini, etiket tarihini ve **Lot belge referansı** alanını doldurun. Bir SKU birden çok lotla geldiyse **Lot ekle** kullanın. Ekrandaki **Lot toplamı**, kabul adedine tam eşit olmalıdır. Zorunlu son kullanma tarihi boş bırakılamaz. Takipsiz SKU'da lot alanı açılmaz.
6. Doğrudan karantinaya alınacak lotta **Doğrudan karantinaya kabul et** seçin. Karantinaya alınan adet de fiziksel kabul sayılır ve satın alma kalanını azaltır; satılabilir stoğu artırmaz. Aynı mevcut lotun tarihi ve karantina durumu korunur. Uyuşmayan etiketi düzeltmek için yeni, uydurma bir lot numarası açmayın; fiziksel kayıt ve belgeyi inceleyin.
7. Teslimatın genel **Mal kabul belgesi referansı** ve **Mal kabul açıklaması** alanlarını doldurun. Genel irsaliye/teslimat kaynağı ile her lotun etiket referansı ayrı kaydedilir. Kaynak numarası yazmak dış belgenin otomatik doğrulandığı anlamına gelmez.
8. **Mal kabulü önizle** ile kaydedilecek SKU/lot adetlerini, karantina kararlarını, kaynakları ve işlem sonrası kalanları kontrol edin. Bu aşama stok yazmaz. Yanlış toplam veya kalan adetten fazla kabulde hata özeti ilgili alana götürür. Kaydı başlatmadan **Önizlemeyi düzenle** ile düzeltin.
9. **Mal kabulü kaydet** ile onaylayın. Sunucu güncel kalan, SKU politikası ve lot bilgisini tekrar denetler. Başarılı kabul sonrası satın alma listesi yenilenir: bir kısmı geldiyse **Kısmen teslim alındı**, bütün satırlar tamamlandıysa **Teslim alındı** gösterilir. Karantinadaki miktarlar bu teslim sayımının içindedir.

| Rol | Satın alma oluşturma | Fiziksel kabul | Lotun kaynaklarını okuma |
| --- | --- | --- | --- |
| Yönetici | Evet | Evet | Evet |
| Katalog | Evet | Hayır | Evet |
| Depo/sevkiyat | Hayır | Evet | Evet; maliyet alanları dönmez |
| Finans | Hayır | Hayır | Evet |

Bu işlemler doğrulanmış yönetim oturumu gerektirir. Destek, pazarlama ve müşteri bu kaynak ilişkilerini okuyamaz. Finans rolü satın alma ve kaynakları inceleyebilir; fiziksel teslim alma yetkisi kazanmaz.

## Yanıt alınamadığında izlenecek yol

Önizleme onayından sonra alanlar ve işlem anahtarı aynı deneme için sabit kalır. Bağlantı kesilirse sunucu işlemi tamamlamış olabilir. **Aynı kabulü yeniden dene**, aynı SKU/lot miktarları, referanslar ve aynı işlem anahtarıyla gönderir; başarılı ilk kabulün sonucu geri dönebilir. Yanıt alınamadığı anda kabul başarısız veya tamamlanmış sayılmaz. Sunucunun başarı durumu döndürmesine rağmen yanıtın boş, kesilmiş veya gerekli kabul alanları eksik olması da belirsiz sonuçtur; başarı bildirimi gösterilmez. Önizleme ve aynı işlem anahtarı korunur, yeniden deneme tekil kabul kaydını doğrular.

Sonucu belirsiz istekte önizleme düzenlemeye açılmaz. **Kayıtları kontrol etmek için kapat** seçeneği satın alma listesini yeniler; kalan miktarı ve **Satın alma kaynakları** panelini inceleyin. Sunucu isteği kesin olarak reddetmiş ve **Önizlemeyi düzenle** seçeneği açılmışsa bilgileri düzelterek yeni önizleme hazırlayabilirsiniz. Yetki hatasında rol değerini değiştirmeye çalışmayın; yetkili işletme yöneticisine başvurun.

Ekranı kapatmak, sayfayı yenilemek veya yeni bir kabul açmak eski önizlemenin aynı işlem anahtarını korumaz. Önce önceki kabulün kayıtlarda bulunup bulunmadığını doğrulayın. Aynı fiziksel teslimatı yeni anahtarla yeniden girmek yazılım tarafından her durumda ayırt edilemez; belge referansı global tekil değildir. Aynı teslimatı ayrıca **Lot mal kabulü** ekranından da girmeyin.

## Lotun gerçek satın alma kaynaklarını inceleme

**Lot ve son kullanma** bölümünde lotu arayıp satırdaki **Satın alma kaynakları** düğmesini açın. Panelde tedarikçi, gerçek satın alma/kabul kimlikleri, kabul adedi, bunun içindeki karantina adedi, kaynak belge referansı ve Türkiye saatine göre kayıt zamanı görünür. Kimlikler sistemin gerçek kayıt kimlikleridir; irsaliye veya fatura numarası olarak kullanılmaz. Maliyet, banka ve müşteri iletişim verileri bu panele eklenmez.

**Mal kabulü kaynaklarında ara** tedarikçi, kayıt veya belge referansında arar; **Önceki/Sonraki** 25 kayıtlık sayfaları gösterir. Aynı lot birden çok satın alma veya kabulden gelmişse bütün gerçek kayıtlar ayrı görünür. Panel belirli bir satılmış adedi tek bir satın almaya bağladığı iddiasında bulunmaz. **Satın alma dışı mal kabulü** kartı bağımsız belgeli depo girişini ayırır; bu kayıtta satın alma/kabul kimliği ve tedarikçi ilişkisi bulunmaz.

Fiziksel lot barkodu okutma, pakette lot/seri doğrulama, lotu bilinmeyen iadeyi yeniden atfetme/imha ve çok depolu transfer ayrı açık işlerdir. Kaynak paneli bunların tamamlandığını göstermez.

## Yerel UI kabulünün durumu

`tests/e2e/purchase-lots.spec.ts` son optimize standalone sürümde Chromium ve WebKit ile geçti. Kendi yerel SKU/satın alma kayıtlarında hatalı lot toplamı, fazla kabul, normal+çok lotlu kısmi kabul, gerçek sunucu başarısından sonra kaybolan yanıtın aynı anahtarla tekrarı, tamamlanan kalan, maliyetsiz çok kaynak raporu ve finansın yazma yasağı doğrulandı. 390/1440 px taşma, klavye ve Axe kontrolleri geçti; önizleme ve kaynak panelinin iki motordaki masaüstü/mobil görüntüleri üretildi.

Hedefi yeniden çalıştırma komutu `npx playwright test tests/e2e/purchase-lots.spec.ts` şeklindedir; önce aynı kaynak için optimize build ve test ortamını hazırlayın, tek runner kullanın. Son toplu build, lint/typecheck, birim/DB ve tarayıcı sonuçlarının kanonik kaydı [progress.md](progress.md) ve [test-evidence.md](test-evidence.md), görüntüler [visual-review.md](visual-review.md) içindedir. Bu yerel kabul gerçek depo provası, fiziksel okuyucu veya dış sağlayıcı kabulü değildir.

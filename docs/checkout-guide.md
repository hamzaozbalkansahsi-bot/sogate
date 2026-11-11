# Sipariş öncesi toplam teklifi

Bu belge sunucu sözleşmesini açıklar. Teklif hesabı ve ekranı başarılı yerel kontrol noktasında optimize standalone sürüm üzerinde Chromium ve WebKit ile doğrulandı. Sonraki sepet sahipliği düzeltmesinin sunucu regresyonları geçti; bu yeni kaynak için toplu build/tarayıcı kabulü ayrı doğrulanır. Hangi kaynak sürümünün test edildiği, komutlar ve başarısız koşular dahil kanonik sonuçlar [progress.md](progress.md) ve [test-evidence.md](test-evidence.md) içindedir. Yerel test ödemesi gerçek tahsilat veya sağlayıcı kabulü değildir.

## Müşteri akışı

1. Sepetten ödemeye geçin. Teslimat ülkesi ve tahsilat para birimini kontrol edin; gösterim parası ile tahsilat parası ayrı olabilir. Üyeyseniz kayıtlı adres seçebilir veya yeni teslimat adresi yazabilirsiniz. Ülkenin onaylı alanları kullanılır; hesap açma veya pazarlama izni zorunlu değildir.
2. **Sipariş özeti** ürün/varyant/adet, ara toplam, varsa indirim, teslimat, toplam ve toplama dahil vergiyi gösterir. İndirim kodunu **Kodu uygula** ile kontrol edin; kaldırdığınızda sunucu özeti yeniden hesaplar. Dahil vergi toplamın üzerine eklenen ikinci vergi değildir.
3. Aydınlatma ve satış koşullarını bağlantılarından açıp okuyun. Gerekli kutular başlangıçta seçili değildir. Gerçek satıcı ve onaylı ülke/hukuk kuralları yoksa canlı satış kapısı bu örnek akışla açılmaz.
4. **Ödemeye devam et** güncel toplamla yeni sipariş başlatır. Teklifin süresi bitmiş veya koşullar değişmişse özet yenilenir; yeni tutarı inceleyip tekrar tıklayın. Sistem değişen tutarı kendiliğinden kabul ederek ikinci ödeme başlatmaz. **Sipariş özetini güncelle** yalnız hesabı yeniler, ürün ayırmaz.

Özet yüklenirken veya hatalıyken ödeme başlatılmaz; eksik ülke/fiyat/vergi/belge kapısı düzeltilmeden ilerlenmez. Yerel test ödeme ekranı gerçek tahsilat yapmaz ve kart bilgisi istemez. Tarayıcının dönüş adresi ödeme kanıtı değildir; sipariş durumu doğrulanmış sunucu olayından gelir.

Ekrandan ayrılınca veya hesap değişince gecikmiş eski yanıt o ekrana özel veri/yönlendirme taşımaz. Ancak isteği kapatmak sunucuda başlamış siparişi iptal etmez. Sonucu belirsiz işlem için güvenli sipariş ekranını veya hesabınızı kontrol edin; yeni tahsilat başlatmadan mevcut kaydı doğrulayın.

## Sunucuda tek hesap

`commerce/checkout-pricing.ts`, teklif ve yeni sipariş için aynı fiyat listesi, SKU sınıfı vergisi, kupon, katkı sınırı, kargo ve kargo vergisi hesabını üretir. Fiyatlar KDV dahildir: `totalMinor = subtotalMinor − discountMinor + shippingMinor`. Ürün ve kargo vergisi bu toplamın içindeki paylardır; toplam üzerine yeniden eklenmez. Kupon satırlara tamsayı dağıtılır; sipariş ve kısmi iade aynı satır snapshot'larını kullanır.

`quoteCheckout(token, input, callerUserId = null)` mevcut sepeti `REPEATABLE READ READ ONLY` transaction içinde okur. Sepet oluşturmaz veya birleştirmez; sipariş, ödeme, rezervasyon, kupon kullanımı, hareket, sözleşme kabulü veya iş kuyruğu kaydı yazmaz. Aynı snapshot içinde `cart.user_id` denetlenir: anonim sepet veya mevcut oturumun kendi sepeti okunabilir. Olmayan ve başka kullanıcıya ait sepet aynı `EMPTY_CART` hatasını verir. `callerUserId` HTTP katmanının doğruladığı oturumdan gelir, JSON girdisine eklenemez. Ayrı istek kotası bu finansal hesaplamanın dışındadır.

Teklif, ürün ayırmaz ve fiyatı beş dakika boyunca sabitlemez. Stok/lot, ülke, belge, adres, hukuk ve canlı hazırlık kuralları yeni sipariş sırasında tekrar doğrulanır. Sepet toplamını görmek tahsilat veya sevk onayı değildir.

## Alan sözleşmesi

Girdi: `CheckoutQuoteInput` yalnız `country`, `currency`, `locale` ve varsa `couponCode` taşır. Dil ve tahsilat para birimi ayrı alanlardır; kur uydurulmaz. Fiyat, indirim veya rol istemciden kabul edilmez.

`CheckoutQuote` yanıtı:

- `quoteToken`, `expiresAt`, `currency`, `deliveryTerm`.
- Her satırda `variantId`, sunucu kaynağından `name` ve `variantName`, `quantity`, `unitMinor`, `discountMinor`, `taxMinor`, `lineTotalMinor`.
- `subtotalMinor`, `discountMinor`, `shippingMinor`, `goodsTaxMinor`, `shippingTaxMinor`, `taxMinor`, `totalMinor`.

Tutarlar para biriminin alt birimindedir. `lineTotalMinor`, satırın indirim sonrası KDV dahil tutarıdır. Maliyet, tedarikçi, özel katkı kuralı ve belge inceleme notu yanıt alanı değildir. Checkout aynı adres/onay/idempotency alanları yanında `quoteToken` ister; kupon kodu teklif ile aynı seçimdir.

## İmza, süre ve değişiklik

`quote-token.ts` mevcut `BETTER_AUTH_SECRET` ile amaç ayrımlı HMAC kullanır. Yeni secret veya migration gerekmez. Token sepet kimliği ve hashlenmiş sepet anahtarına, ülke/dil/para/kupon seçimine ve deterministik ekonomik parmak izine bağlıdır. Ham sepet anahtarı, adres ve e-posta içermez. Özel maliyetin dar bir aralıktan tahmin edilmemesi için parmak izi de anahtarlı HMAC'dir; yalnız imzalı düz hash değildir.

İz; ürün/varyant kimliği, adet, sunucuda gösterilen adlar ve siparişe kopyalanan açıklama/bakım/uyarı/malzeme/üretici/görsel; geçerli fiyat listesi, vergi sınıfı/kuralı, set bileşenleri, kupon kuralları, kargo, adres profili ve hukuk sürümlerini bağlar. Para aynı kalsa bile ilgili metin veya kural değişince yeniden inceleme gerekir. Başlangıç zamanı gelecekte olamaz; tokenın ömrü en fazla beş dakikadır.

| Kod | Davranış |
| --- | --- |
| `CHECKOUT_QUOTE_REQUIRED` | Yeni sipariş için önce güncel toplam istenir. |
| `CHECKOUT_QUOTE_INVALID` | Bozuk veya imzası geçersiz teklif reddedilir. |
| `CHECKOUT_QUOTE_EXPIRED` | Süresi dolan teklif yenilenip tekrar incelenir. |
| `CHECKOUT_QUOTE_CHANGED` | Sepet/seçim/tutar/koşullar değişmiştir; güncel özet yeniden incelenir. |

Bu dört durum HTTP 409'dur ve yeni finansal kayıt oluşmaz. Eksik belge, stok veya vergi kuralı kendi iş kuralı koduyla da reddedilebilir. İstemci otomatik olarak değişen tutarı kabul edip ödeme başlatmamalıdır.

## Kilitler ve idempotency

HTTP katmanı sepet/sipariş çağrısına doğrulanmış oturum kimliğini ayrı argümanla geçirir; JSON'dan sahiplik kabul edilmez. `getCart(token, currency, callerUserId)` sahiplik, satırlar ve stok gösterimini aynı `REPEATABLE READ READ ONLY` snapshot'ta okur. Yalnız eksik sepet için yapılan ilk `INSERT ... ON CONFLICT DO NOTHING` sahiplik veya özel satır okumaz. Sonradan gerçekleşen hesap birleşmesi bu snapshot'a yeni özel ürünler ekleyemez. Birleşme önce tamamlandıysa anonim veya başka kullanıcı çağrısı genel `CART_NOT_FOUND` yanıtı alır.

`setCartItem(..., callerUserId)` adet artırma, değiştirme ve sıfır adetle silme işlemlerinde hesap birleşmesiyle aynı sepet satır kilidini kullanır. Sahiplik denetimi, mutasyon ve dönen sepet aynı transaction/connection içinde kalır. Dıştaki cookie kontrolünün geçmiş olması yetki kanıtı sayılmaz; işlem başlamadan yabancı cookie için yeni sepet seçilebilir, devam eden istek sahiplik değişince başka sepette sessizce uygulanmaz.

Yeni sipariş sepeti kilitler, güncel hesabı tekrar üretir. Tanım kimliği için paylaşımlı advisory; ürün, SKU ve sepet satırları için sıralı okuma kilidi; kullanılan fiyat/vergi/ülke/profil ve kupon için uygun satır kilitleri tutulur. Ürün veya varyant teknik değişikliği, siparişin kabul ettiği hesapla yazım arasına giremez. Fiziksel stok/lot ve kupon kapasitesi kendi atomik denetimlerini korur. Salt okunur teklif bu yazım kilitlerini almaz.

`quoteToken` idempotency isteğinin semantik hash'ine katılmaz. Aynı sepet/idempotency ve aynı iş girdisi için mevcut sipariş, teklif süresi veya yeni teklif yüzünden ikinci siparişe dönüşmez. Mevcut kayıt kontrolü teklif doğrulamasından önce yapılır; farklı adres/iş girdisi aynı anahtarla kullanılamaz. Ödeme sağlayıcı oturumunu yeniden açma veya mutabakat, mevcut sipariş üzerinden ilerler; yeni tahsilat gerekçesi üretilmez.

Checkout, kilitlediği sepetin sahibini mevcut sipariş dönüşünden önce denetler. Hesap birleşmesi eski sepeti üyeden ayırmış olsa da geçmiş siparişin `user_id` alanı değişmez ve ayrıca doğrulanır. Anonimleşmiş eski sepet anahtarı üyeye ait siparişin idempotent tekrarına erişim vermez; doğru üye aynı iş girdisiyle tekrarı sürdürebilir. Bu denetim özel takip bağlantısının ayrı erişim sözleşmesini değiştirmez.

Sipariş snapshot'ındaki `checkoutQuote`, ilk kabuldeki sürüm/zaman/ekonomik iz bilgisini tutar; ham token saklanmaz. Yeni teklif veya sonradan değişen katalog bu snapshot'ı değiştirmez. Bu kayıt müşterinin ekranı fiilen okuduğunu veya hukuki uygunluğu tek başına kanıtlamaz.

## Yerel sunucu kanıtı

İlk gerçek DB regresyonu, geçerli sepette teklif olmadan sipariş oluşturulmasını `Missing expected rejection` ile yakaladı. Yeni token modülünün ilk birim koşusu modül yokluğunda RED verdi. Sonrasında:

- `npx vitest run tests/unit/quote-token.test.ts`: 7/7; değiştirme, başka sepet/seçim, kesin süre sınırı, deterministik ve özel anahtarlı iz.
- `npx tsx --env-file=.env.local scripts/quote-integration.ts`: yazmasız teklif, karma vergi/kupon/kargo eşitliği, değişen koşullarda finansal rollback, kopya/bozuk token, pending/ödenmiş siparişin eski/yeni token ile idempotent tekrarı, önceden verilmiş kupon teklifleri yarışı ve gerçek DB ürün/SKU yazıcısının kilitte beklemesi geçti. Dış anonim sahiplik kontrolü ile snapshot arasına gerçek üye sepet birleşmesi konduğunda anonim okuma reddedilir. Snapshot birleşmeden önce başladıysa sonraki özel satırları görmez; doğru üye bunları kendi isteğinde görebilir. Aynı tutarlı eski anonim teklif, hesap birleşmesinden sonra sipariş yazamaz; üyeden ayrılan eski sepet de sipariş sahibini aşamaz.
- `npx tsx --env-file=.env.local scripts/security-boundary-integration.ts`: dış sahiplik kontrolünden sonra gerçek birleşmeyle anonim sepet okuma/güncelleme/silme reddi, okuma önce başladığında özel satırları görmeme, yazım önce kilitlediğinde birleşmenin beklemesi ve iki üyenin aynı anonim sepeti farklı hesaplara alamaması geçti. İlk anonim okuma ve checkout regresyonları eski kodda `Missing expected rejection` verdi; ayrılmış eski siparişin tekrarı da ayrı RED ile yakalandı.

Test DB'si yalnız loopback üzerindeki benzersiz `*_quote_test` adında oluşturulur ve temizlenir. Mevcut core/operasyon/lot/hukuk/vergi/uygunluk testleri gerekli teklifi geçerli başlangıçta alır; negatif durum sonra oluşturulur. Son adet ve kupon yarışında iki teklif yarıştan önce hazırlanır. Teklif aşamasında reddedilen isteği checkout güvenlik testinin başarısı diye saymak uygun değildir. `tests/e2e/checkout-quote.spec.ts` toplamın görünmesi, kupon, değişen tutarın açıkça yeniden kabulü, başka sepete token taşıma ve geciken hesap yanıtlarını son yerel tarayıcı koşusunda doğruladı. Masaüstü/mobil görüntüler ve build sonucu [test-evidence.md](test-evidence.md) ile [visual-review.md](visual-review.md) içinde izlenir; gerçek cihaz veya sağlayıcı sandbox kabulü çıkarılmaz.

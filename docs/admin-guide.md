# Yerel yönetim ve kullanım

Önce README.md kurulumunu tamamlayın. http://127.0.0.1:3000 müşteri vitrini; /yonetim yönetim paneli. Yerel örnek stok ve fiyatlar gerçek üretici kataloğu değildir, üretime yüklenmez. `npm run dev`, yerelde Webpack ve loopback adresiyle başlar; geliştirme çıktısı `.next-local`, optimize derleme `.next` altında ayrıdır. Yeni kaynak değişikliklerinin son toplu test/build sonucu `progress.md` içinde izlenir; bu rehber canlı yayın onayı değildir.

Önceki çekirdek kaydı [checkpoint-core.md](checkpoint-core.md) içindedir. Güncel kaynak ve fazların sonucu [progress.md](progress.md) ile [test-evidence.md](test-evidence.md) dosyalarındadır; eski checkpoint sonraki değişikliklerin kabulü yerine geçmez. Bu rehber mevcut kullanımı tarif eder; gerçek sağlayıcı veya canlı yayın onayı değildir.

## İlk yönetici
`npx tsx --env-file=.env.local scripts/bootstrap-admin.ts` yalnız development/test ortamında hesap oluşturur. Bilgiler `.local/admin-access.txt` içindedir; bu dosyayı paylaşmayın. /hesap üzerinden giriş yapın, Güvenlik bölümünde doğrulayıcı uygulamaya anahtarı ekleyip altı haneli kodu doğrulayın. Kurtarma kodlarını ayrı güvenli yerde saklayın. /yonetim erişimi bu oturumdaki MFA doğrulamasını gerektirir; dört saat sonunda kod yeniden doğrulanır. Kurulumdan önceki parola oturumları MFA yetkisi kazanmaz.

## Katalog ve depo
Ürünler ve varyantlar bölümünde SKU, TR/EN metin, kategori, fiyat ve malzemeyi girin; yeni ürün taslak olarak oluşur. Üretici, fotoğraf hakları ve gerekli belgeler sağlanmadan gerçek ürün yayınlamayın. Satın almaya bağlı teslimatı **Satın alma ve mal kabul** bölümünden alın. Satın alma dışı takipsiz giriş için **Depo ve stok**, lot takipli giriş için **Lot mal kabulü** kullanılır. Aynı teslimatı bu yollarda ikinci kez kaydetmeyin. Mevcut stoğu doğrudan yazıp geçmişi silmeyin. Katalog incelemesi sonrası yayın akışı stokla birlikte kontrol edilir.

**Kategoriler** ve **Markalar** bölümlerinde Türkçe/İngilizce adı ve bağlantı adını oluşturun veya düzenleyin. **Kayıtlarda ara → Ara** sunucu araması yapar; **Önceki/Sonraki** 25 kayıtlık sayfaları değiştirir. Düzenleme penceresinde arşivleme seçeneği vardır; geçmiş siparişleri silmez. Kategori arşivlenince o kategori vitrine kapatılır. Üründeki marka bugün metin etiketidir; marka kaydını değiştirmek veya arşivlemek ürün etiketlerini topluca değiştirmez ve ürün/belge onayı vermez.

Varyantta beden/ölçü, renk ve gerçek pil türü bilgilerini; mevcutsa sıvı ve hijyen mührü işaretlerini kaydedin. Bunlar vitrin filtre seçeneklerinin kaynağıdır. Veri yokken özellik uydurmayın; pil adından şarj edilebilirlik, tıbbi malzeme, sertifika veya su geçirmezlik sonucu çıkarmayın. Teknik değişiklik sonrası belge/uygunluk incelemesi gerekir.

Yeni ürünün ilk seçeneğinde ve varyant düzenleme ekranında **Vergi sınıfı** bulunur. `*`, ortak sınıfın açık değeridir; özel sınıfı SKU'ya kaydedin. Boş sınıf kabul edilmez. Özel sınıfta ülke/yürürlük kuralı yoksa ortak sınıfa otomatik düşülmez; ödeme engellenir. Sınıf değişince yayın ve uygunluk yeniden incelenir. Alanı doldurmak vergi oranı veya hukuki sınıflandırma onayı değildir; oranı yetkili finans/yönetici tanımlar.

İçe aktarma bölümünde CSV/XLSX şablonunu indirin, dosyayı önizleyin, kolon eşlemesi ve satır hatalarını düzeltin; onay yalnız hatasız önizleme için geçerlidir. İçe aktarma yayın veya stok girişi yapmaz. Ayrıntı import-guide.md.

### Vitrin filtreleri ve fiyat gösterimi

Ürünler ekranında arama, kategori, marka, malzeme, beden, renk, pil/güç türü ve veride bulunan özellikleri seçip **Filtrele** düğmesine basın. Boş kaynak alanları filtre seçeneği oluşturmaz. Mobilde aynı form filtre çekmecesindedir. Filtreler URL'ye yazılır; yenileme ve sayfalama seçimi korur. **Filtreleri temizle** başlangıç listesine döner. Filtre toplamı sayfadaki kart sayısından ayrı gerçek ürün toplamıdır; sayfada en fazla 24 ürün gösterilir. Mobil/klavye tarayıcı kabulü son toplu [test-evidence.md](test-evidence.md) kaydında doğrulandı.

Fiyat/beden/renk/güç/özellik/stok seçimi aynı varyantta karşılanır. **Yalnız stoktakiler** ana sevk deposu `main` için aktif rezervasyon, güvenlik payı, uygun lot ve set bileşenlerini dikkate alır; yalnız başka depoda duran stok satılabilir görünmez. Kart, eşleşen seçenekler içindeki seçili gösterim para biriminin en düşük geçerli fiyatını ve o fiyatın seçenek adını gösterir. Sunucunun fiyat sıralaması da aynı minimum fiyatı kullanır. Eksik liste sıfır veya başka para biriminden hesaplanmış fiyat olarak gösterilmez.

**Varyantlar ve fiyatlar → Düzenle → Para birimi fiyat listeleri** üzerinden TRY/EUR/USD/GBP tutarlarını ilgili alt birimde girin; boş para için fiyat oluşmaz. Mevcut bu dört para biriminde iki basamak kullanılır. Ortak biçimlendirici 0/2/3 basamak, BigInt ve Arapça rakam düzenini destekleyen altyapıya sahiptir; bu durum yeni tahsilat parası veya Arapça mağaza yayını açmaz. Gösterim parası ülkenin onaylı tahsilat parasını değiştirmez. Teknik davranış: [catalog-filter-guide.md](catalog-filter-guide.md).

**Varyantlar → Düzenle → Set bileşenlerini düzenle** ile gerçek fiziksel SKU/adet seçin, sunucu önizlemesini kontrol edip gerekçeyle sürümlü kaydedin. Üst SKU ve bileşenlerin ülke/exact belge onayı ayrıdır; set tanımı fiyat veya stok üretmez. Fiziksel stok set üst koduna değil bileşen SKU'larına kaydedilmelidir. Sürüm/rezervasyon/lot sınırları ve yeni stok kabulü kontrolünün kanıtı [set rehberi](bundle-guide.md) ile genel kayıttadır.

**Ürün belgeleri ve uygunluk** ekranında SKU'yu açın; gerçek teknik alanları ve SKU/model/ülke/tür/tarih/ref içeren belgeyi incelemeye sunun. Yönetici belge inceleme/iptal ve ülke kararını ayrı verir; normal yayın artık uygunluk onayı oluşturmaz. Kaynaklı üretici/sorumlu iletişimi yönetici incelemesinden sonra public DTO'ya girer; özel referans, maliyet ve tedarikçi bilgisi girmez. PDF yükleme/tarama yoktur. Ayrıntı: [belge ve teknik bilgi rehberi](compliance-guide.md).

**Sosyal tasarım** ekranında yayımdaki gerçek ürün/seçenek veya CMS koleksiyon/rehberini, dil ve görünümü seçin; güncel fiyat ve hak/hash kontrolünden oluşan SVG'yi önizleyip indirin. Dosya herhangi bir hesaba gönderilmez; reklam kabulü verilmez. Kaynak ve lisans bilgileri: [sosyal rehber](social-guide.md).

**Ülkeler ve satış → Ülkelere göre adres alanları** yönetici MFA'sı ve kritik kararda yeniden parola doğrulamasıyla kaynaklı alan/sürüm tanımlar. Onay ülkeyi satışa açmaz. Checkout geçerli profil ile doğrular, eski siparişin alan/sürüm snapshot'ı değişmez. Üye **Adreslerim** bölümünde yalnız kendi adreslerini oluşturur/görür/düzenler/siler; customer adres işlemi yönetici profil yetkisi vermez. Ayrıntı: [adres rehberi](address-guide.md).

## Satın alma ve lotlu mal kabulü

Yönetici/katalog **Yeni satın alma** ile tedarikçi, SKU, sipariş miktarı ve TRY kuruşu birim maliyeti kaydeder; satın alma oluşturmak stok üretmez. Fiziksel kabulü yönetici/depo yapar; finans yalnız inceler. Depo ekranı ve API yanıtlarında alış maliyeti bulunmaz.

Tedarikçide arayıp satın alma satırından **Mal kabul** açın veya **Satın almadan mal kabulü** düğmesinden kayıt seçin. **Kabul edilecek stok kodunda ara → Ürünü kabule ekle** ile fiilen gelen satırları ekleyin. Kabul adedi kalan miktarı aşamaz. Lotlu SKU'da her lotun gerçek numara/tarih/adet/ref bilgilerini ve karantina kararını ayrı girin; lot adetleri SKU kabul adedine eşit olmalıdır. Normal SKU için lot bilgisi istenmez.

Genel teslimat belgesi referansı ile her lotun etiket kaynağını ayrı doldurun. **Mal kabulü önizle** kaydedilecek miktarları ve işlem sonrası kalanları gösterir; stok yazmaz. İnceledikten sonra **Mal kabulü kaydet** kullanın. Kısmi kabul bekleyen miktarı korur; karantinaya kabul teslim sayılır ama satılabilir stoğu artırmaz.

Yanıt alınamazsa **Aynı kabulü yeniden dene** mevcut önizlemenin aynı içerik ve işlem anahtarını kullanır. Sonucu bilinmeyen kabulü yeni anahtarla yeniden oluşturmayın; önce satın alma kalanı ve kaynak kayıtlarını inceleyin. Formu kapatmak veya yenilemek eski işlem anahtarını korumaz. Ayrıntılı adımlar ve belirsiz yanıt sınırları: [lotlu satın alma rehberi](purchase-lot-guide.md).

**Lot ve son kullanma → Satın alma kaynakları** gerçek tedarikçi, satın alma/kabul kimlikleri, kabul/karantina miktarı ve belge referanslarını gösterir. Bir lotun birden çok gerçek kaynağı bulunabilir; belirli satılmış adet tek satın almaya atanmış sayılmaz. **Lot mal kabulü** ekranındaki satın alma dışı giriş satın alma kalanını kapatmaz. Fiziksel lot barkodu/paket doğrulaması ve lotu bilinmeyen iadeyi yeniden atfetme açık işler olarak kalır.

Lotlu satın alma akışı son optimize koşuda Chromium/WebKit **2/2 PASS** geçti: hatalı toplam/fazla kabul, normal+çok lotlu kısmi kabul, gerçek sunucu başarısından sonra kaybolan yanıtın aynı anahtarla tekrarı, kalan tamamlanması, maliyetsiz kaynak paneli ve finansın yazma yasağı doğrulandı. 390/1440 px klavye, Axe, yatay taşma ve ekran kayıtları da bu akışa dahildir. Son **94/94 E2E (47+47), 246 birim/232 DB** ve build kanıtı [test-evidence.md](test-evidence.md), açık operasyon/dış erişim koşulları [progress.md](progress.md) içindedir; fiziksel depo/okuyucu veya canlı kabulü değildir.

## Medya

Medya kütüphanesinde PNG/JPEG/WebP yükleyin ve kullanım hakkı kaynağını yazın. Dosya yeniden WebP olarak işlenir; SVG/HTML yüklemesi kabul edilmez. Henüz yayımlanmış ürüne bağlanmayan dosyayı yalnız MFA doğrulanmış yönetici/katalog/pazarlama görebilir. Görselin yayınlanması lisans veya üretici belgesinin doğrulandığı anlamına gelmez. Yerel yükleme/özel erişim çalışır; gerçek S3 hesabı ve bucket politikası henüz bağlanmadı.

## Sipariş ve sevkiyat
Vitrinde varyantı sepete ekleyin; adres ve teslimat özetinden test ödeme ekranına geçin. Bu ekran gerçek kart veya tahsilat kullanmaz. Başarılı dönüş yerine doğrulanmış sunucu olayı siparişi onaylar. Güvenli takip bağlantısını saklayın; sipariş numarası tek başına erişim sağlamaz.

Sipariş listesinden **Siparişi aç** seçilir. Depo rolüne yalnız ödemesi doğrulanmış siparişin SKU/adet/paketleri ve gerekli teslimat adresi/telefonu döner; e-posta, maliyet/kârlılık, tahsilat tutarı/referansı ve müşteri geçmişi API'de de dönmez. Müşteri hizmetleri ilgili iletişim/sevk, finans ise adres/e-posta olmadan finans alanlarını görür. Pazarlama ve katalog rolü bu ayrıntıya erişemez.

Paket için kalan miktarları seçip **Paket hazırlığı oluştur** düğmesini kullanın. Ürünü toplarken kayıtlı gerçek barkodu veya siparişteki SKU'yu girip **Toplamayı doğrula** seçin. Tüm adetler toplandıktan sonra paket içine koyarken kodu tekrar doğrulayın. Paketleme tamamlanınca taşıyıcının gerçek belgesindeki adı ve takip numarasını girip **Manuel sevki kaydet** seçin. Fazla adet, yanlış kod, ödeme durumu değişikliği ve tekrar komutlar sunucuda denetlenir. Takip kaydı taşıyıcı API'si veya ücretli etiket oluşturmaz.

Eski Sevkiyatlar → Yeni kayıt yolu, aktif hazırlığa ayrılmamış uygun miktarlar için korunur; bu yol barkod kontrolü yapmış sayılmaz ve başka göreve ayrılan adedi tüketemez. Ayrıntılı rol/işlem kapsamı ve yerel kanıt: [Personel sipariş rehberi](staff-order-guide.md). `017_staff_fulfillment.sql` migration'ı uygulanmış olmalıdır. Personel entegrasyonu 11/11 ve Chromium/WebKit hedef akışı 2/2 geçti; bu kanıt son tam suite'in yerine geçmez. Fiziksel okuyucu/depo ve gerçek taşıyıcı kabulü bekliyor.

## İade ve işler
Müşteri güvenli sipariş ekranından ürün, adet, gerekçe ve mühür durumunu seçer. Başvuruyu müşteri hizmetleri inceler; depo teslim alır, karantinaya koyar ve QC sonucu kaydeder. Depoya kabul satışa dönüş değildir. Açılmış mühür yeniden satışa alınamaz. Set iadesinde satış anındaki bileşenler korunur.

Finans/yönetici para iadesinde parolasını yeniden doğrular. Stripe iadesi sipariş/iade iş akışına ve kalıcı kuyruğa bağlıdır; önce **Para iadesi bekliyor** durumunda kalır. Doğrulanmış sağlayıcı sonucu gelmeden iade edildi sayılmaz veya tahsilat toplamı azaltılmaz. Worker referans/metadata ile sorgular; sonucu bilinmeyen eski işlemi yeni tahsilat/iade isteği gibi körlemesine tekrarlamaz. Gerçek Stripe hesabı, kategori kabulü ve sandbox iade/kesinti testi yoktur. Yerel test iadesi gerçek sağlayıcı iadesi değildir.

İşlem kuyruğunda SMTP veya sağlayıcı bağlantısı bulunmayan işler yeniden denenir, sonrasında başarısız listesinde kalır. “Tamamlandı” durumu gerçek handler başarıyla çalışmadan oluşmaz. Dış erişim yokken e-posta gönderildiğini varsaymayın.

## Kurulum, hukuk ve SEO

Lot/son kullanma ve geri çağırma işlemleri için [lot-guide.md](lot-guide.md); çoklu varyant CSV/XLSX için [import-guide.md](import-guide.md); vitrini, koleksiyonları ve planlı rehber/SSS yayınını düzenlemek için [cms-guide.md](cms-guide.md) kullanın. Kişisel veri başvuru kuyruğu yalnız yönetici/müşteri hizmetlerine açıktır; ayrı veri sorumlusu ve ülke süre/saklama kuralları yönetici tarafından yapılandırılır. [privacy-guide.md](privacy-guide.md), kimlik doğrulaması ve tamamlanan dış işlem kanıtının kaydını açıklar; bu ekran otomatik mali kayıt silme işlemi değildir.
İşletme ayarlarındaki satıcı alanları başlangıçta boştur. Geliştirici kredisi satıcı unvanı yerine yazılmaz. Hukuk metinleri taslak oluşturulur; gerçek şirket ve veri akışlarıyla yetkili inceleme sonrası sürüm/onay kaydı gerekir. Sipariş anındaki hukuk snapshot'ı değişmez.

SEO denetiminde dil seçerek ürün başlığı, meta açıklaması, görsel alt metni ve o dilin ürün bağlantısını düzenleyin. Canonical dil yolundan üretilir; bağlantı değişiminde eski yol aynı ürüne yönlenir. Manuel yönlendirme yalnız mevcut açık site içi hedefe verilir; özel hesap/API/sipariş yolları, dış adres, zincir ve döngü kabul edilmez. Ürün raporu sayfalıdır ve tam site crawler'ı değildir. Sitemap index/bölümleri gerçek açık ürünleri filtreler; bunların bulunması Google indeks/sıralama kabulü değildir. Son SEO regresyonları ve tüm güncel test sonuçları son toplu çalıştırma kaydıyla değerlendirilmelidir.

Entegrasyon ve canlıya hazırlık bölümleri açık engelleri gösterir. Gerçek S3/SMTP/Stripe sandbox, staging geri yükleme, remote CI ve canlı dağıtım doğrulanmadı. Hiçbir yerel hazırlık onayı domain, gerçek sağlayıcı veya üretim yayını yapmaz.

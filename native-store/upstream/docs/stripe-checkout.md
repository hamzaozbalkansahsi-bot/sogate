# Stripe kartla ödeme

Bu entegrasyon mevcut katalog ve misafir bilgi adımlarına Stripe’ın barındırdığı kart ekranını ekler. Kart numarası NODENO sunucusuna gelmez. Fatura kesen işletme kullanıcı tarafından PTYS Technologies LLC olarak belirtilmiştir. Canlı tahsilat için bu satıcının Türkiye teslimatlarındaki vergi/fatura uygulaması ve satış belgeleri doğrulanmalı; Stripe hesabı ve imzalı webhook bağlantısı kurulmalıdır. Kodun hazırlanması bu işlemlerin tamamlandığı anlamına gelmez.

Mevcut katalog fiyatları KDV hariçtir. İşletmenin belirttiği kurala göre bitmiş mobilyaya %10, kapı/kapak ürününe %20 eklenir. Ölçülü kapaklarda toplam alanın net bedeli bir kez yuvarlanır; KDV satır toplamına uygulanır. Karttan yalnız KDV dahil ürün bedeli çekilir. Kargo/ambar ücreti hesapta sıfır veya ücretsiz gösterilmez; bedel ürüne dahil değildir ve alıcı tarafından doğrudan taşıyıcıya ödenir. Müşteri ödeme öncesinde bunu ayrıca kabul eder.

İlk kart akışı Türkiye teslimatı ve TRY içindir. Diğer ülkelerde mevcut toptan teklif talebi sürer. Kapıda Türkiye için 5 takım, yurt dışında teklif için 10 takım; ölçülü kapaklarda mevcut alan sınırları korunur. Bilinmeyen/teklif gereken ürün tutarı karttan alınmaz. Stok kontrollü ürünler, stok rezervasyonu bağlanıncaya kadar kartla ödemeye kapalıdır. Ödeme denemesi anında güncel yayınlanmış fiyatlar sunucuda yeniden hesaplanır; farklı toplamda yeniden kontrol istenir.

## Yönetimden bağlantı

1. `/yonetim` → Entegrasyonlar bölümündeki **Stripe / Kartla ödeme** alanını firma sahibi açar. Kritik değişiklikler yakın zamanda yapılmış yönetici doğrulaması gerektirir.
2. Önce ödeme kapalı halde Stripe hesap kimliği, aynı ortama ait gizli API anahtarı ve webhook imzalama sırrını kaydedin. Bunları sohbete, Git’e veya yayın paketine koymayın. Anahtarlar özel SQLite deposunda şifreli tutulur; yönetim API’si kayıtlı sırları geri döndürmez.
3. Stripe endpoint adresi `https://<ziyaret edilen NODENO alan adı>/api/payments/stripe/webhook` olur. Birincil endpointi seçin; aynı SQLite deposu diğer NODENO alan adlarındaki ödeme durumlarını da günceller. `checkout.session.completed`, `checkout.session.expired`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `refund.created`, `refund.updated`, `refund.failed` olaylarını bağlayın. API sürümü `2026-10-28.endive` kullanılır.
4. **Stripe hesabını doğrula** ile gerçek hesap kimliği ve tahsilat yetkisini denetleyin. Doğru ortamdan imzalı olayın sunucuya ulaştığını doğrulayın. İlk olay ayrıca aynı API anahtarıyla Stripe’dan okunarak hesap bağlantısı denetlenir; kısıtlı anahtarda Events okuma izni gerekir. Canlı bağlantı kabulünde kart bilgisi girilmeyen, kontrollü bir Checkout oturumu oluşturulup hemen sona erdirildi; `checkout.session.expired` bildirimi HTTP 200 ile kabul edildi ve sunucudaki hesap/imza doğrulaması denetlendi. Bu kontrol NODENO siparişi veya tahsilat oluşturmadı. Kontrol için oluşan geçici ürünler arşivlendi. Test ortamındaki olay canlı ortamı doğrulamaz. Ekrandaki **Durumu yenile** güncel durumu getirir.
5. Satıcının fatura unvanı/adresi/e-postası, belge sürümü, dört dilde satış/iade metinleri ve işletme sahibinin fiyat/fatura/vergi uygulaması onayını tamamlayın. `taxConfirmed` işletmenin bu uygulama için verdiği onayı kaydeder; bir devlet makamının tescil kontrolü değildir. Resmî kayıt doğrulanmadıysa doğrulanmış gibi yazılmaz. Bu alanlara tahmini veya başka bir şirkete ait bilgi yazmayın. Test işlemleri gerçek muhasebe/sevkiyat kaydı değildir.
6. Sağlayıcı testi, sunucu testleri ve gerçek alan adı kontrolü tamamlanınca kartla ödemeyi etkinleştirin. Test ortamı halka açık üretim mağazasında tahsilat açmaz. Test ve canlı para akışı ayrı tutulur. Anahtar dönüşümünde önceki webhook sırları açık oturumların geç bildirimleri için yedi gün şifreli korunur.

## Siparişin oluşması

İletişim/adres taslağı ödeme başlatılana kadar yalnız açık sayfanın belleğindedir. Kullanıcı ödeme düğmesine basınca doğrulanmış iletişim ve fatura/teslimat adresleri özel depoya şifreli kaydedilir; hesap açılmaz ve adres defteri değiştirilmez. Sunucunun değişmez fiyat, ürün seçimi ve satış belgesi kaydıyla bir ödeme denemesi oluşur. Aynı isteğin tekrarı aynı Stripe oturumunu kullanır. Ağ hatasında yeni tahsilat açmak yerine aynı anahtarla tekrar denenir.

Stripe’tan siteye dönüş ödeme onayı sayılmaz. İmzalı bildirimin hesap, ortam, oturum, sipariş numarası, tutar ve para birimi kayıtla uyuştuğunda durum **Ödendi** olur. Geç gelen süre dolumu bildirimi ödenmiş kaydı geri almaz. Tekrarlanan olay bir kez uygulanır. Durum bağlantısı müşteri adı, e-posta veya adres göstermez. Üye alışverişlerinde doğrulanmış canlı ödeme Siparişlerim listesine eklenir. Misafir müşteri dönüş ekranındaki sipariş numarasını kullanır.

Yönetim → Müşteri siparişleri altında kartla ödeme kayıtları, tutarlar, seçilen ürünler/ölçüler ve yetkili personelin görebildiği adresler bulunur. Bu kayıtların ödendi durumu elle düzenlenmez. Fatura, KolayBi belgesi, kargo kaydı veya sevkiyat otomatik oluşturulmaz. İadeyi yetkili kişi Stripe panelinde başlatır; mağaza kendiliğinden para iadesi yapmaz. İade sonucu imzalı Stripe bildirimiyle müşterinin ödeme ekranına, Siparişlerim ve yönetimdeki kart kaydına yansır. Ödeme bildirimi tek başına fiziksel sevkiyat başlatmaz.

## Kısmi ve tam iade takibi

Stripe panelinde ilgili ödemeyi açıp iade edilecek tutarı kontrol ederek iadeyi başlatın. Her iadenin tutarı ayrı izlenir. Başarılı kısmi iade **Kısmen iade edildi**, toplamın tamamı başarılı olduğunda **İade edildi** görünür. Bekleyen iade tamamlanmış para dönüşü olarak sayılmaz; başarısız iade için ayrıca uyarı gösterilir. Kartın bakiyesine yansıma süresini bu durum ekranı garanti etmez.

Bildirimler tekrar geldiğinde ikinci kez tutar eklenmez. Gecikmiş ödeme/süre dolumu bildirimi başarılı iadeyi silmez. İade bildirimi ödeme onayından önce ulaşırsa eşleşen ödeme onayında birlikte işlenir. Hesap, ortam, ödeme kimliği, para birimi ve toplam eşleşmezse siparişe uygulanmaz. İade verilmiş siparişler müşteri geçmişinden kaldırılmaz.

## Gerçek Stripe test ortamı kabulü — 10 Kasım 2026

Resmî Stripe CLI ile canlı hesaptan ayrı, geçici bir test ortamı açıldı. Gerçek Stripe Checkout ekranında başarılı kart, reddedilen kart, 3D Secure onayı ve başarısız 3D Secure denendi. Kısmi ve kalan tutarın tam iadesi Stripe test API'sinde oluşturuldu; gerçek imzalı bildirimler NODENO'nun yayıma hazırlanan PHP koduna ve yalıtılmış SQLite deposuna ulaştı. Türkçe masaüstü ile İngilizce, Rusça ve Arapça mobil iade ekranları da kontrol edildi.

Beş sağlayıcı senaryosu geçti. Test ortamının `rkcs_test_` anahtar biçimi desteği ve iade sonucunun sipariş durumuna yansıması bu testte düzeltildi. Geçici test anahtarı canlı ortamda kabul edilmez. Test siparişleri, örnek müşteri ve tutarlar canlı mağazaya aktarılmaz; gerçek karttan para çekilmedi. Canlı anahtarlar test anahtarıyla değiştirilmedi.

Tekrar çalıştırma: `artifacts/commerce-qa-python/Scripts/python.exe tests/provider/stripe_sandbox.py --release artifacts/cpanel-release-stripe-sandbox-20261110 --scenario success` komutunda senaryoyu `decline`, `3ds`, `3ds-fail` veya `refund` olarak değiştirin. Özel test profili yalnız sahibin erişebildiği `.codex/private/nodeno-stripe/sandbox-20261110` dizinindedir; yedi günlük geçici ortamın süresi dolduğunda yenisi gerekir. Özel profil ve ham bildirim günlükleri paylaşılmaz. Kabul kanıtı `artifacts/stripe-sandbox-20261110` dizinindedir.

## Doğrulama

`node --test tests/payments-*.test.mjs` gerçek PHP ve SQLite ile fiyat, KDV, asgari miktar, CSRF/origin, imza, ortam/hesap/tutar eşleşmesi, tekrar deneme, kişisel veri ve yönetim izinlerini denetler. Yerel tarayıcı kabulü gerçek Stripe kart testi yerine geçmez. Üretime çıkarken medya onayları, yayın özeti ve kalıcı müşteri deposunun korunması ayrıca doğrulanır. Canlı anahtar veya kişisel veri test raporlarına yazılmaz.

Kaynaklar: [Stripe Checkout oturumu](https://docs.stripe.com/api/checkout/sessions/create), [ödeme doğrulaması](https://docs.stripe.com/checkout/fulfillment), [KDV Genel Uygulama Tebliği](https://cdn.gib.gov.tr/api/gibportal-file/file/getFileResources?objectKey=arsiv%2Ffileadmin%2Fuser_upload%2FTebligler%2FKDV%2Fkdv_genteb.htm). Vergi oranları işletmenin talimatıdır; bu kod bir vergi mükellefiyeti oluşturmaz.


## 10 Kasım 2026 gerçek bağlantı kabulü

PTYS canlı hesabına NODENO için ayrı, altı sınırlı izinli anahtar bağlandı. Sunucu anahtarı ve webhook imza sırrı özel depoda şifrelidir. Gerçek TRY Checkout isteği kabul edildi; kontrol oturumları hemen sona erdirildi ve ödeme yapılmadı. İmzalı canlı olay sunucu tarafından doğrulandı. Endive sürümü için `allowed_payment_method_types` kullanılır; boolean alanlar `true`/`false` olarak kodlanır. İlk TRY akışında Adaptive Pricing kapalıdır. Bu sağlayıcı bağlantısı, müşteri tahsilatının açıldığı anlamına gelmez: satıcı vergi/fatura ve satış/iade belgeleri hâlâ tamamlanmalıdır. Yönetici parola kurtarma işlemi mevcut hesap ve MFA’yı korudu. Özel bakım görevi tamamlandıktan sonra geçici çalıştırıcısı kaldırılır; web üzerinden bir bakım kapısı açılmaz.

## Satış ve iade belgesi taslakları

`data/legal/payment-documents.*.json` kaynaklarında Türkçe, İngilizce, Rusça ve Arapça ön bilgilendirme/mesafeli satış koşulları ile iptal, cayma, iade ve isteğe bağlı cayma formu hazırlandı. Kapsam Türkiye tüketici satışı ve TRY'dir; ihracat/B2B'ye otomatik uygulanmaz. Firma sahibinin doğruladığı iade adresi **Zafer Mah. Turgut Özal Cad. No:100/C, Buca/İzmir** olarak dört dilde yer alır. Wyoming kayıt adresi ürün iade adresi değildir. Posta kodu verilmediği için uydurulmadı.

Yönetim → Entegrasyonlar → Stripe / Kartla ödeme → Satıcı ve satış belgeleri alanındaki `2026-11-10.1-draft` sürümü işletme bilgileri tamamlanmadan müşteri tahsilatı açmaz. Standart üründe 14 günlük cayma, gerçekten kişiye özel üretimde ürüne özgü istisna ve ayıplı mal hakları ayrı tutulur. 1 Ocak 2026 kurallarıyla geri gönderim ve geri ödeme başlangıçları ayrılır; alıcı ödemeli ilk sevkiyat, iade ücretini tüketiciye aktarmak için kullanılmaz.

Özel `install-sale-documents` bakım eylemi yalnız ödeme kapalıyken, beklenen ayar sürümüyle çalışır; yalnız belge sürümü ve sekiz dil/metin alanını değiştirir. Canlı anahtarları, hesap/webhook doğrulamasını, satıcı kimliğini ve vergi/yetki beyanlarını korur. Vergi onayı veya tahsilat açma parametresi kabul etmez. Aynı işlemde denetim kaydı yazılamazsa belge kaydı da geri alınır.

Türkiye mükellefiyeti, gerçek fatura düzenleyicisi, KDV beyanı ve KolayBi/uygun manuel fatura yolunda eksik olan bilgiler ile mali müşavire verilecek metin [PTYS Türkiye fatura hazırlığında](ptys-turkiye-fatura-hazirlik.txt) bulunur. Metinlerin dolması bu ticari bilgilerin doğrulandığı anlamına gelmez. Siparişe özel kalıcı belge teslimi ve ödeme alınan sağlayıcı senaryoları canlı tahsilat öncesi ayrıca kabul edilir.

## Sahibin ABD faturası ve Türkiye teslimatı talimatı

Firma sahibi 10 Kasım 2026'da faturaların ABD'de kayıtlı PTYS tarafından düzenleneceğini, ürünlerin Türkiye'den teslim edileceğini belirterek tahsilatın açılmasını açıkça istedi. Dört dildeki `2026-11-10.2` koşulları bu düzeni ve No:100/C iade adresini taşır. Fiyatlar için daha önce verilen net + %10 mobilya / %20 kapı-kapak kuralı korunur; ABD faturası gerekçesiyle KDV sıfırlanmaz.

Özel `activate-payments` işlemi bu talimatı `billingDecision.approvalSource=explicit_owner_instruction` olarak, resmî vergi kaydı doğrulanmadığı bilgisini de `governmentTaxRegistrationVerified=false` olarak kaydeder. Yetki, canlı anahtar/hesap eşleşmesi, imzalı webhook, dört dilde son metinler ve güncel Stripe kart tahsilat yetkisi denetlenir. CAS ayar sürümü ve tek işlemde denetim kaydı korunur; kayıt hatasında etkinleştirme geri alınır. İşletme onayı, başka şirket adına tahsilat veya doğrulanmamış kayıt numarası üretme izni değildir. Faturanın otomatik kesilmesi bu mağaza akışının parçası değildir; PTYS faturası ayrıca düzenlenir ve kalıcı sözleşme kopyası sevkiyattan önce müşteriye sağlanır.


## Belge merkezi ve sipariş sözleşmesi — 2026-11-10.3

Dört dilde belge merkezi `/legal` adresinde yayındadır. 10/11/2026 sürümündeki kart akışı sözleşme kopyasını indirdikten sonra ayrı kart ekranına devam ediyordu; eski açık ekranlar belge protokolünü göndermediğinde tahsilat oturumu açamaz. Siparişe özgü kopya aynı misafir oturumuna veya hesap sahibine özeldir, şifreli/değişmez tutulur. KVKK aydınlatması satış veya pazarlama rızasıyla birleştirilmez. Metin sürümü 2026-11-10.3, ödeme ayarı sürümü 5 ve canlı tahsilat açıktır. [İşleyiş ve resmî takip](legal-documents.md).


## Kargo dahil doğrudan ödeme — 12/11/2026

Belge protokolü 2 kullanılır. Kartla öde otomatik HTML indirmeden doğrudan doğrulanmış `https://checkout.stripe.com` adresine yönlendirir. Koşullar ödeme öncesi modal pencerelerde okunur; onay sürümü ve içerik revizyonu sunucuda kontrol edilir. Eski protokol geçerli bir ödeme başlatamaz. Siparişin şifreli ve değişmez sözleşme arşivi korunur; eski belgeler yeniden yazılmaz.

Türkiye sevkiyatında `freight.kind=included`, `feeMinor=0` ve `includedInCharge=true` döner. Ayrı taşıma onayı alınmaz. Yurt dışı ülke kartla tahsilat yoluna sokulmaz; nakliye ve gümrük teklifine yönlendirilir. Mevcut canlı Stripe anahtarları, webhook, satıcı ve yetki ayarları değiştirilmez.

Kargo fiyat politikası [kapı/kapak ticareti kılavuzunda](kapi-ve-kapak-ticareti.md) tanımlıdır. Kaynak fiyat bir kez %20 artırılır, ardından geçerli KDV hesaplanır; mobilya fiyatı bu artıştan etkilenmez. Yönetimde kayıtlı fiyat, bu politikanın uygulanacağı net tabandır. Sepet ve ödeme tutarları sunucudan yeniden hesaplanır. Geçmiş siparişler kayıtlı tutarlarını korur.

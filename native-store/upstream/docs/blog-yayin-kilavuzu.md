# NODENO blog yayın kılavuzu

Bu kılavuz, hazır rehber bankasının günlük yayınını yöneten işletme kullanıcısı içindir. Günlük kullanımda kod yazmanız, bir AI hesabı açmanız veya API anahtarı girmeniz gerekmez.

## Yönetim ekranına giriş

[Blog yayınları](https://nodenohome.com/yonetim/blog) ekranını açın. Önce oturum açmanız istenirse [NODENO Yönetim](https://nodenohome.com/yonetim) üzerinden mevcut yönetim hesabınızla giriş yapıp blog ekranına dönün. Hesabınızda pazarlama görüntüleme yetkisi bulunmalıdır; yayın durumunu değiştiren işlemler için pazarlama düzenleme yetkisi gerekir.

“Bu hesapta pazarlama erişimi bulunmuyor” mesajı içerik hatası değildir. Hesap yetkisi işletmenin yetkili yöneticisi tarafından kontrol edilmelidir. Kimliğinizi yeniden doğrulamanız istenirse yönetim ekranında doğrulamayı tamamlayıp geri dönün. Giriş bilgilerini veya doğrulama kodlarını yayın kayıtlarına eklemeyin.

Müşterilerin gördüğü sayfa [NODENO Blog](https://nodenohome.com/blog) adresidir. Yönetimde **Yazıyı aç** bağlantısı yalnız yayımdaki rehberlerde görünür. Henüz yayımlanmamış bir rehberin halka açık adresinin bulunamaması beklenir; metin ve görsel kontrolü için oturumlu **Önizle** kullanılır.

## Yayın düzeni ve ilk gün

Hazır banka **250 farklı rehberden** oluşur. Türkçe, İngilizce, Rusça ve Arapça sürümler aynı rehberin dil seçenekleridir; günlük yayın sayısını dört katına çıkarmaz. Olağan takvim İstanbul saatine göre günde iki rehberdir: **09:30 ve 18:30**, saat dilimi **Europe/Istanbul**.

İlk kurulum için başlangıç kuralı şöyledir: ilk iki rehber ilk başarılı sunucu çalışmasında, çalışmanın gerçek yayın tarihi ve saatiyle yayımlanır. Sonraki rehberler ertesi İstanbul gününden itibaren 09:30/18:30 düzenine girer. İlk günün saatleri geçti diye geçmiş bir yayın yapılmış gibi tarih üretilmez; aynı gün için iki ek olağan yayın daha oluşturulmaz.

Gece yarısı sınırı İstanbul gününe göre ele alınır. Örneğin ilk sunucu çalışması İstanbul’da **13/11/2026 00:05** olursa başlangıç günü 13/11/2026’dır; ilk iki rehberin gerçek yayımı bu güne aittir ve düzenli sonraki gün 14/11/2026’dır. Bu bir açıklama örneğidir, canlı sistemin gerçekleşmiş yayın kaydı değildir.

Blog yayını ve arama motoru bildirimi için ortak özel zamanlayıcı Turhost sunucusunda her dakika kontrol yapar. Kalıcı kurulumun ve son çalışmanın canlı kanıtı aşağıdaki kabul kayıtlarından doğrulanır. Zamanı gelen rehber, çalışan zamanlayıcının sonraki kontrolünde işlenir; plan saati ile gerçek yayım saati farklı olabilir. Kurulum ve canlı kontrol tamamlandığında bilgisayarınızın açık kalması gerekmez. Bu belgenin sonundaki canlı doğrulama durumunu ayrıca kontrol edin.

## Tarih ve saatleri okuma

Türkiye tercihinde tarih **gg/aa/yyyy**, saat 24 saatlik **SS:dd** biçiminde gösterilir; örneğin **12/11/2026 22:05**. Türkiye için gösterim saat dilimi Europe/Istanbul’dur. Ülke tercihinizi değiştirdiğinizde ekrandaki tarih/saat biçimi ve gösterim saat dilimi o ülkeye uyarlanır. Dil değiştirmek ülke tercihini değiştirmez.

Ülke seçimi işletmenin yayın takvimini taşımaz: 09:30/18:30 hedefleri Europe/Istanbul’da sabit kalır. Başka ülkede farklı bir yerel saat görmeniz ikinci bir yayın planı oluştuğu anlamına gelmez. “Plan / yayım” sütunundaki ilk zaman planı, varsa ikinci zaman gerçekleşen yayımı belirtir. Gerçekleşen zaman kaydı plan tarihine geri çekilmez.

## Günlük kontrol

1. Blog yayınları ekranında **Yenile** düğmesine basın. Ekran kendiliğinden sürekli güncellenmez.
2. “Yayın takvimi açık” veya “Yayınlar duraklatıldı” bilgisini okuyun. **Son sunucu kontrolü** ve **Son başarılı yayın** zamanlarını karşılaştırın.
3. **Planlı / yeniden deneme** ve **İnceleme gerekli** sayılarına bakın. Hazır kalan rehber, yaklaşık kalan gün ve son planlı yayın bilgisini okuyun. “İnceleme gerekli” sıfır değilse ilgili satırları filtreleyin; düşük banka uyarısı varsa yeni içerik planını başlatın.
4. Yaklaşan rehberleri **Önizle** ile okuyun; gereken tekil yazıyı bekletin. Hazır ve onaylı banka için her gün yeniden onay vermeniz gerekmez.
5. Yeni yayından sonra **Yazıyı aç** bağlantısını kullanıp sayfayı, çizimi, ürün kartlarını ve dil seçeneklerini kontrol edin.

**Önizle** penceresindeki **Önizleme dili** alanından Türkçe, English, Русский veya العربية seçin. Seçilen dilin başlığını, görselini, girişini, bütün bölüm metinlerini ve kontrol listesini birlikte inceleyin. Arapça önizleme sağdan sola gösterilir. Yönetim oturumu gerektiren bu önizleme henüz yayımlanmamış içerik ve görselleri kontrol etmek içindir; halka açık bir taslak paylaşım bağlantısı değildir. Önizlemeyi kapatmak yayını durdurmaz. Yayımdaki bir rehberin önizlemesi kaydedilmiş yayım sürümünü esas alır.

## Dört planlama aracı

Araçlar blogdan açılır ve Türkçe, İngilizce, Rusça ve Arapça kullanılır. Sonuçlar bir ürünün teknik uygunluğunu veya evinizdeki nihai sonucu onaylamaz.

| Araç | Ne için kullanılır? | Sonucun sınırı |
| --- | --- | --- |
| [Geçiş alanı](https://nodenohome.com/blog?tool=space) | Duvarlar arasındaki ölçüden iki taraftaki eşya derinliğini çıkararak kalan boşluğu görmek. | Kapak açılımı, sandalye hareketi, kişisel erişim ve montaj koşulları ayrıca kontrol edilir. |
| [Boya miktarı](https://nodenohome.com/blog?tool=paint) | Dört duvarın net alanından, gerçek etiket sarfiyatı ve kat kapsamıyla yaklaşık miktar hesaplamak. | Başlangıç değerleri örnektir. Tavan, mobilya ve özel yüzeyler bu dört duvar hesabına dahil değildir; ürünün etiket verisi girilmelidir. |
| [Renk ilişkisi](https://nodenohome.com/blog?tool=palette) | Dijital bir başlangıç renginin diğer tonlarla ilişkisini denemek. | Üretici kartelası, resmî boya kodu veya gerçek numune yerine geçmez. |
| [Yüzey ön kontrolü](https://nodenohome.com/blog?tool=surface) | Malzeme, mevcut yüzey, kullanım ortamı ve görülen soruna göre önce araştırılacak noktaları sıralamak. | Teşhis, kimyasal uygulama reçetesi veya marka/ürün tavsiyesi değildir. Zımparasız ya da astarsız sonuç garantisi vermez. |

Yüzey aracında emin olmadığınız alanda **Bilinmiyor** seçin. Nem seçildiğinde önce kaynağın ve malzemenin durumunun netleştirilmesi; dökülme seçildiğinde önce eski katmanın sağlamlığı ele alınır. MDF kenarları, ince kaplama, metal ve plastik için ayrı teknik kontrol gerekir. Su teması veya dış ortamda tam sistemin ve mobilyanın bu kullanıma açık uygunluğu ayrıca doğrulanır. “Sağlam görünüyor” seçmek bile ürün uygunluğu onayı oluşturmaz.

Seçimler değiştiğinde ön kontrol planı güncellenir; **Ön kontrol planını göster** düğmesiyle de okuyabilirsiniz. Bilgileri bir üreticiye veya uygun uygulayıcıya iletirken planın belirlediği eksik noktaları kullanın. Bu araç için hesap açmanız, kod veya anahtar girmeniz gerekmez.

## Düğmeler ne yapar?

| İşlem | Sonuç | Ne zaman kullanılır? |
| --- | --- | --- |
| **Önizle** | Seçilen dilin başlığını, görselini, tam metnini ve kontrol listesini yönetim içinde açar; yayımlamaz. | İçeriği yayımdan önce kontrol etmek için. |
| **Yayınları duraklat** | Bütün otomatik yayın akışını duraklatır. Yayımdaki sayfalar yerinde kalır. | Genel bir kontrol veya geçici ara gerektiğinde. |
| **Yayınları sürdür** | Genel duraklatmayı kaldırır. | Otomatik akışa dönmeye hazır olduğunuzda. |
| **Beklet** | Yalnız seçilen, henüz yayımlanmamış rehberi otomatik akıştan çıkarır. | Tek bir yazı incelenecek veya değiştirilecekse. |
| **Yeniden dene** | Seçilen rehberi yeniden planlı duruma alır; deneme sayısını ve son hatayı sıfırlar. | Hatanın nedeni düzeltildikten sonra veya bekletilmiş bir rehberi geri almak için. |
| **Şimdi yayımla** | Seçilen rehberi hemen yayımlamayı dener; gerçek yayım zamanını kaydeder. Görsel ve içerik kontrolleri yine geçerlidir. | Plan saatini beklemeden, bilinçli olarak öne almak için. |
| **Yenile** | Sunucudaki güncel durum ve kayıtları getirir. | İşlem sonrasında ve günlük kontrolde. |

**Beklet** ile genel **duraklatma** farklıdır. Yayınları sürdürmek, tek tek bekletilmiş yazıları serbest bırakmaz. Bekletilen yazı için **Yeniden dene** kullanılır. Bu düğme eski plan zamanını korur; plan zamanı geçmişse genel akış açıkken sonraki sunucu kontrolünde yayımlanabilir.

Genel duraklatma, **Şimdi yayımla** işlemini engellemez. Bu düğme doğrudan yayım isteğidir. El ile öne alınan bir rehber normal kuyruğa ikinci kez eklenmez. Yayımdaki rehberin satırında tekrar yayımlama, bekletme ve yeniden deneme düğmeleri gösterilmez.

Uzun bir aradan sonra **Yayınları sürdür** demeden önce geçmiş planlı satırları inceleyin. Mevcut kuyruk geçmiş planları ileri tarihe otomatik dağıtmaz; zamanı geçmiş rehberler sonraki kontrollerde işlenebilir. Bu nedenle el ile yayım veya birikmiş kuyruğun tamamlanması, bir günde olağan iki yayından fazla gerçek yayım oluşturabilir. Belirli yazıları önce **Beklet** ile ayırabilirsiniz.

## Durumlar, denemeler ve yayın kayıtları

| Durum | Anlamı |
| --- | --- |
| **Planlı** | Sırası geldiğinde otomatik yayın için hazırdır. |
| **Yeniden denenecek** | Bir yayın denemesi başarısız olmuş, sonraki deneme bekleniyordur. |
| **Bekletilen** | İşletme tarafından otomatik akıştan çıkarılmıştır. |
| **İnceleme gerekli** | Beş başarısız denemeden sonra otomatik deneme durmuş durumdadır. |
| **Yayında** | Gerçek yayım zamanı kaydedilmiş ve rehber halka açılmıştır. |

“Deneme / hata” sütunu deneme sayısını ve varsa son hatanın açıklamasını gösterir. Otomatik hata denemeleri ilk başarısızlıktan sonra 5, ardından 10, 20 ve 40 dakika bekleme uygular; gerçekleşme sunucu kontrollerine bağlıdır. Beşinci başarısız denemede “İnceleme gerekli” durumuna geçilir. Hata nedeni giderilmeden **Yeniden dene** düğmesine art arda basmak çözüm üretmez.

**Yayın kayıtları** bölümünü açın. Son 100 olay burada en yeniden eskiye gösterilir. Kayıtlar; bankanın kuyruğa alınmasını, otomatik veya el ile yayımı, duraklatma/sürdürme, bekletme ve hata denemelerini ayırt etmeye yardımcı olur. Ekrandaki liste bütün geçmişin tek dökümü değildir.

Destek isterken rehber başlığını, görünen hata mesajını, son sunucu kontrolü zamanını ve ilgili kayıt zamanını iletin. Gizli anahtar, parola veya müşteri bilgisi gerekmez.

## Hata gördüğünüzde

- **Son sunucu kontrolü ilerlemiyorsa:** Önce Yenile ile güncel durumu alın. İnternet sayfasının açık olması sunucu zamanlayıcısının çalıştığını kanıtlamaz. Kurulum kabulü tamamlandıktan sonra iki kontrol aralığına yakın süre geçmesine rağmen zaman güncellenmiyorsa teknik sorumluya bildirin.
- **Kontrol güncel, yeni yayın yoksa:** Genel duraklatmayı, yazının durumunu, plan zamanını, varsa yeniden deneme beklemesini ve kalan bankayı kontrol edin. Gelecekte planlı, bekletilen veya inceleme isteyen yazı sırf sunucu kontrolü yapıldı diye yayımlanmaz.
- **Görsel bütünlüğü veya onay hatası varsa:** İlgili yazıyı bekletin; onaylı dosya ve içerik paketi teknik sorumlu tarafından düzeltilmelidir. Başka bir internet görseliyle geçiştirmeyin.
- **“Blog hizmetine şu an ulaşılamıyor” veya başka hizmet hatası varsa:** Yenile ile durumu tekrar okuyun ve hata mesajını teknik sorumluya iletin. Sonucu görmeden aynı yazıya tekrar tekrar Şimdi yayımla basmayın.
- **“İnceleme gerekli” varsa:** Yazıyı ve son hata kaydını inceletin. Sorun çözüldükten sonra Yeniden dene ile akışa alın; istenirse doğrudan Şimdi yayımla kullanılabilir.

## Kalan banka ve bitiş

250 rehber, olağan **iki rehber/gün ile 125 yayın günlük sonlu bir bankadır**. Başlangıç günü ilk iki rehberi de bu sayıya dahildir. Duraklatma, tekil bekletmeler, başarısız yayınlar veya el ile öne alma nedeniyle gerçek bitiş tarihi farklılaşabilir.

“Kalan banka” ile “otomatik yayına hazır kalan” aynı değildir. Bekletilenler bankada kalır ama hazır akışa dahil değildir. “İnceleme gerekli” yazılar da sorun giderilmeden otomatik akışı devam ettirmez. Hazır kalan gün hesabı, planlı ve yeniden denenecek rehber sayısının ikiye bölünüp yukarı yuvarlanmasıdır; kesintisiz yayın garantisi değildir.

Yönetimde **hazır kalan rehber**, **yaklaşık kalan gün** ve **son planlı yayın** bilgileri gösterilir. Son planlı zaman, otomatik akışta planlı veya yeniden denenecek durumdaki rehberlerin son zamanıdır; bekletilen bir yazı bu akışın dışında kalır.

Sistem, otomatik akışa hazır rehber sayısı **28’in altına** düştüğünde yönetimde düşük banka uyarısı gösterir. Bu, olağan hızla yaklaşık 14 günlük eşiğin altına gelindiğini anlatır. Gün göstergesi yukarı yuvarlandığı için 27 hazır rehberde 14 gün yazarken de uyarı görülebilir. Uyarı, yeni içerik planlamaya başlama işaretidir. Hazır rehber kalmadığında ve bankanın durumuna göre “İçerik bankası tükendi” bilgisi de gösterilir.

Banka bitince eski yazılar tekrar yayımlanmaz ve otomatik yeni metin üretilmez. Henüz sorunlu veya bekletilmiş yazılar varsa önce durumlarını inceleyin; yalnız “tükendi” mesajından tüm metinlerin başarıyla yayımlandığı sonucunu çıkarmayın. Hazır banka tamamlandığında yeni onaylı rehber eklenene kadar yeni yayın akışı biter; yayımdaki rehberler okunmaya devam eder.

## Yeni rehber ne zaman ve nasıl eklenir?

Düşük banka uyarısını beklemeden de yeni konu listesi hazırlanabilir. İşletme, okuyucunun hangi kararını çözecek özgün konular istediğini ve ilgili gerçek ürün bilgilerini içerik sorumlusuna verir. Mevcut yönetim ekranı metin yazma veya otomatik AI üretimi formu sunmaz; işletme kullanıcısının kod dosyası ya da anahtar girmesi gerekmez.

Yeni paket; özgün metin, teknik iddiaların kaynak kontrolü, örnek sayıların açıklığı, görsel doğrulaması ve Türkçe/İngilizce/Rusça/Arapça anlam incelemesinden geçirilir. Yeni ürün özelliği, malzeme, ölçü, stok veya fiyat yalnız doğrulanmış gerçek bilgiye dayanır. Uygun içerik ve görseller işletmenin yayın onayından sonra teknik sorumlu tarafından bankaya eklenip kuyruk doğrulanır. Mevcut onaylı 250 rehberin günlük otomatik yayımı için ek bir günlük onay gerekmez.

Yayımdaki rehberin metni mevcut düğmelerle düzenlenmez. Bankaya yapılan bir düzeltme daha önce yayımlanmış sayfayı kendiliğinden değiştirmez. Yayımdaki içerikte hata fark edilirse rehber adresini ve düzeltme isteğini teknik/içerik sorumlusuna iletin; ayrı içerik düzeltmesi ve kontrol gerekir.

## Ücret, görseller ve kaynakların sınırı

Bu yayın akışı ücretli AI aboneliğine veya her gün ücretli içerik üretim çağrısına dayanmaz. Hazır banka sunucudan yayımlanır; çalışmak için yeni bir AI anahtarı istenmez. Bu ifade hosting, alan adı veya gelecekte ayrıca sipariş edilebilecek içerik hizmetlerinin ücretsiz olduğu anlamına gelmez.

Rehber kapakları konuya özel özgün açıklayıcı çizimlerdir. Ölçekli teknik ürün çizimi veya gerçek uygulanmış dönüşüm fotoğrafı gibi sunulmaz. İlgili ürün kartlarında mevcut onaylı gerçek ürün fotoğrafları kullanılır. Fotoğrafın veya çizimin varlığı; ürünün ölçüsünü, malzemesini, taşıma kapasitesini ya da bir boya sisteminin o ürüne uygunluğunu tek başına kanıtlamaz.

Kaynak bağlantıları, teknik bilginin dayanağını sorgulayabilmeniz içindir. Bir üretici sayfasına erişilebilmesi, o ürünün elinizdeki mobilyaya ve kullanım koşuluna uygunluğunu garanti etmez. Özellikle ana boya, efekt ve koruyucu aynı işlevde değildir; gerçek etiket, hedef yüzey, hazırlık ve kullanıma dönüş koşulları ilgili tam ürün için doğrulanmalıdır.

## Canlı kurulum ve kabul durumu

**13/11/2026 canlı kabulü tamamlandı.** 250 rehberin Türkçe, İngilizce, Rusça ve Arapça bankası hazırdır. İlk iki rehber gerçek sunucu yayım tarihleriyle yayındadır; kalan 248 rehber mevcut takvimde korunmuştur.

| Kontrol | Doğrulanan durum |
| --- | --- |
| Blog sürümü | Güncel canlı tabana dar güncelleme yapıldı; 3.763 ürün ve ödeme durumu korundu. |
| Yayın kuyruğu | 2 yayında, 248 planlı. Mevcut yayın tarihleri yeniden yazılmadı. |
| Kalıcı sunucu zamanlayıcısı | Arama bildirimiyle ortak mevcut her dakikalık Turhost görevi korundu; ikinci görev eklenmedi. |
| Tekrarlanan sunucu kontrolleri | Ardışık iki gerçek kontrolde yeni yayın 0, kalan rehber 248; tekrar yayım yok. |
| Müşteri ekranları | Masaüstü/mobil, dört dil, dört araç, gelecek yazı ve görselin 404 olması canlıda denetlendi. |
| Yönetim güvenliği ve önizleme | Canlı anonim erişimde içerik/görsel gizli. Oturumlu dört dil önizlemesi ve yetkiler yerelde gerçek HTTPS/PHP/SQLite ile doğrulandı; canlı hesapla işlem yapılmadı. |
| Site haritası ve akış | Ana harita blog alt haritasını içeriyor; 4 liste ve 8 yayımdaki dil adresi, akışta yalnız iki gerçek yayın var. |
| Alan adları | .com, www.com, .com.tr ve www.com.tr adreslerinde ziyaretçi alan adı korunuyor. |

Güncel kabul kaydı `artifacts/blog-20261112/acceptance.json`; yayın, zamanlayıcı, ardışık son kontroller, tarayıcı ve HTTP kanıtları aynı klasördedir. İlk arama bildirimi kurulumunun tarihsel kanıtları `artifacts/search-automation-20261112/` içinde korunur. Genel paylaşılan depo testlerinde bu değişikliklerden bağımsız beş hata vardır; nedenleri `artifacts/blog-20261112/code-review.json` dosyasında kayıtlıdır. Blog/tarih kontrolleri ve dar canlı paketin kabulü geçmiştir.

Tarih ve saat gösterimi [tasarım anayasasına](tasarim-anayasasi.md) bağlıdır. Türkiye'de `gg/aa/yyyy`, 24 saat ve açık `Europe/Istanbul` kullanılır. Ülke değişince yerel biçim ve saat dilimi otomatik değişir; arayüz dili ülke tercihini değiştirmez. İşletmenin 09:30/18:30 İstanbul yayın takvimi sabittir.

## Yeni yazıların arama motorlarına bildirilmesi

Zamanlayıcıyla yayımlanan yazı aynı sunucu çalışmasında bildirim kuyruğuna girer. Yönetimden elle yayımlanan yazı en geç beş dakikalık taramada yakalanır; taslak ve bekletilen yazılar girmez. Dört dil adresi blog site haritasında da görünür. IndexNow HTTP 200 kabulü, 202 bekleme ve yeniden deneme durumları [SEO kılavuzunda](seo-kilavuzu.md#otomatik-yeni-içerik-bildirimi) açıklanır. Google yeni yazıları Search Console'a daha önce gönderilen ana site haritasındaki blog alt haritası üzerinden keşfedebilir; her yazı için elle yeniden harita gönderilmesi gerekmez.

250 rehberin dört dilde onaylı bankası kullanılır. Bir yazının sıraya alınması yayına çıktığı anlamına gelmez. İlk iki rehber ilk başarılı çalışmada gerçek zamanla yayımlanır; kalan 248 rehber günde iki yayın takvimini izler. `artifacts/search-automation-20261112/heartbeat-live.json` son sunucu çalışmasını, `browser-live.json` gerçek blog görünümünü kaydeder. Bu kayıtlar yoksa yalnız yerel testi canlı kurulum gibi değerlendirmeyin.


İlk arama otomasyonu kabulü `artifacts/search-automation-20261112/acceptance.json` dosyasında tarihsel olarak korunur. Son blog ve tarih/saat kabulünün kaydı `artifacts/blog-20261112/acceptance.json` dosyasıdır.

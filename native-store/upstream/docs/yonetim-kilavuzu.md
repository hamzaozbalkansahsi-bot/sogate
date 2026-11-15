# NODENO mağaza yönetimi

Yönetim adresi: https://nodenohome.com/yonetim. `/admin` aynı girişe yönlendirir. Müşteri hesabı yönetici hesabından ayrıdır.

## İlk sahip hesabı

Sahip e-postası `hamzaozbalkan@gmail.com` olarak sabitlenmiştir. İlk kurulum kodu yalnız teslim edilen yerel özel dosyada bulunur; parola değildir. Sunucuda kodun SHA-256 özeti ve süresi tutulur. Kod yedi gün geçerlidir ve yalnız ilk sahip hesabı için kullanılabilir.

1. Yönetim girişinde **İlk kurulum** bölümünü açın. E-posta ve kurulum kodunu girin; en az 14 karakterlik kendi parolanızı belirleyin. Parola bcrypt sınırı nedeniyle en fazla 72 bayt olabilir.
   Parola alanının sağındaki göz düğmesi yazdığınız parolayı gösterir ve gizler. Klavyede düğmeye Tab ile ulaşabilir, Enter veya Boşluk ile değiştirebilirsiniz; bu düğme formu göndermez.

2. Gösterilen anahtarı doğrulama uygulamanıza ekleyin. Google Authenticator, Apple Parolalar veya TOTP destekleyen başka bir uygulama kullanılabilir.
3. Güncel altı haneli kodu girin. Kullanılmış kod yeniden kabul edilmez; gerekirse sonraki kodu bekleyin.
4. Gösterilen on kurtarma kodunu güvenli saklayın. Her biri bir defa kullanılabilir. Bu kodlar daha sonra geri gösterilmez.

Parola, kurulum kodu, doğrulama anahtarı ve kurtarma kodlarını müşteri mesajına veya sohbete yazmayın. Yönetim oturumu 15 dakika hareketsizlikte veya en fazla sekiz saatte sona erer. Yayınlama, servis sırrı ve personel işlemleri için beş dakikadan sonra yeniden doğrulama istenir.

## Ürünler, fiyatlar ve stok

**Ürünler ve fiyatlar** bölümünde kaynak katalogdaki 667 renk/SKU kaydı bulunur. Ürün adı, kod veya kayıt numarasıyla arayabilirsiniz. 392 modelin farklı renkleri teknik olarak ayrı SKU olarak korunur. Sitedeki renk gruplaması devam eder.

Bir ürünü açın. Dil sekmelerinden Türkçe, İngilizce, Rusça ve Arapça metinlerini düzenleyin. Boş bırakılan metin kaynak katalogdan gelir. Fiyat TRY cinsinden girilir, sunucuda kuruş olarak saklanır. Kaynak ürün kodu, ölçü, renk, teknik bilgi veya görsel adresi bu formla değiştirilemez.

**Kaydet ve yayınla** formdaki son değişiklikleri tek işlemle kaydeder ve yayınlar. Fiyat ve metin mağaza API’sine, ilk HTML içeriğine ve arama motoru verisine aynı yayın katmanından yansır. **Taslağı kaydet** vitrini değiştirmez. **Yayından kaldır** panel değişikliğini kaldırır; kaynak katalog tekrar geçerli olur. Ürünü tamamen gizlemek için “Vitrinde göster” seçeneğini kapatıp yayınlayın.

Stok doğrulanmadıysa “Stok miktarı doğrulandı” seçeneğini açmayın. Bu kayıt manuel stok bilgisidir; tedarikçi veya depo senkronizasyonu kurulmuş olduğu anlamına gelmez.

Bir kayıt başka personel tarafından değiştirilmişse sürüm çakışması gösterilir. Formu kapatıp güncel kaydı açın; eski sürüm yeni değişikliği ezmez.

## Kampanya, kupon ve vitrin

**Kampanyalar → Yeni kampanya** seçin. Ürün adı veya koduyla arayın, fotoğraflı satırlardaki kutuları işaretleyin. Aramayı değiştirince önceki seçimler korunur. **Listelenenleri seç** yalnız aramada görünen ürünleri seçer; arama boşsa tüm kataloğu seçer. **Seçimi temizle** bütün seçimleri kaldırır.

Oranı ve başlangıç/bitiş saatini girin; **Kampanyayı etkinleştir** açık olmalı. Saatler cihazınızın saat diliminde gösterilir; sunucu aynı zaman aralığını değerlendirir. **Kampanya hesabı** yayınlanmış baz fiyata uygulanacak oranı gösterir. **Kaydet ve yayınla** formdaki son değerleri birlikte yayınlar. **Taslağı kaydet** fiyatı değiştirmez.

Kartta **Yayın bekliyor**, **Aktif**, **Başlangıcı bekliyor**, **Sona erdi** veya **Devre dışı** durumu görünür. Yayındaki kampanyayı taslak olarak düzenlerseniz **değişiklik bekliyor** ibaresi çıkar; önceki yayın geçerli kalır. Aktif kartta mağazadaki gerçek fiyat ve ürün bağlantısı bulunur. Başka bir kampanya daha yüksek oran veriyorsa ayrıca belirtilir. Bağlantı kesilirse formu ve değerleri koruyarak aynı düğmeyle yeniden deneyin; aynı işlem ikinci bir kampanya oluşturmaz.

Aynı üründe çakışan kampanyaların en yüksek tek oranı uygulanır; oranlar üst üste eklenmez. Ürün seçilmeden veya sonucu sıfır fiyata düşüren bir oranla yayın yapılamaz. Kampanya ürün fiyatını yönetir; ana sayfa vitrin fotoğrafı ve metni **Vitrin düzeni** bölümünden yönetilir. Hayali önceki fiyat yazılamaz. Panelden fiyatı veya kampanyası yönetilen ürünlerde etkin kampanya aralıklarını kapsayan eksiksiz geçmiş bulunmadığı için çizili fiyat üretilmez. Yalnız baz fiyat kayıtları önceki fiyat kanıtı sayılmaz. Bu koruma kampanya kaldırıldıktan sonra da sürer. Kaynak mağaza fiyatının mevcut doğrulanmış geçmişi korunur.

Kuponlar, gerçek ödeme henüz kapalı olduğu için hazırlık kaydıdır. Kupon kaydetmek tahsilat veya ödeme sırasında kupon kullanımını açmaz.

**Koleksiyonlar** bölümünde ürün seçimi, onaylı tam kapak fotoğrafı, metin ve sıralama düzenlenebilir. **Vitrin düzeni** ana vitrin ürününü ve dört dildeki başlık/açıklamayı değiştirir. Yalnız katalogdaki onaylı görseller seçilebilir. Marka logosu, yazı tipi ve renkleri korunur; panele keyfi HTML/JavaScript eklenemez.

## Yurt dışı adet ve takım teklifleri

Müşteri sayfası `https://nodenohome.com/?page=wholesale&lang=tr`; dört dilde yayımlanır. Bağımsız ürünler **adet**, kaynakta takım olarak satılan ürünler **takım** birimindedir. **Kendi takımını oluştur** seçeneği müşteriyi katalogdan doğrulanmış oda koleksiyonlarına götürür. İstediği parçaları, renkleri ve adetleri seçip takım sayısını belirtir. Üyelik gerekmez. Talep, kesin sipariş veya ödeme oluşturmaz.

**Yurt dışı toplu teklifler** bölümünde gerçek talebi açın. Kayıtlı takım sayısı, her takımın içeriği ve toplam parça adetleri ayrı gösterilir. Örneğin 10 takımın her birinde 2 komodin varsa toplam 20 komodin bulunur. Seçilmeyen karyola/baza eklenmez. Talep anındaki iletişim, içerik, miktar ve varsa doğrulanmış fiyat anlık kaydı korunur; bu editörde değiştirilmez. Durum ve iç not düzenlenebilir. “Teklif hazırlandı” için teklif koşulları zorunludur. Kaydetmek müşteriye otomatik e-posta/SMS veya KolayBi faturası göndermez.

**Toptan adet, takım ve fiyat** bölümünde ürünün asgari adet/takım miktarını ve üç fiyat kademesini tanımlayabilirsiniz. Kademeler aynı SKU'nun talepteki toplam satış birimi miktarına göre değerlendirilir; eşikler artmalı, birim fiyat artmamalıdır. Para birimini açıkça seçin. Perakende fiyat otomatik toptan fiyata dönüşmez. Veri henüz yoksa fiyat boş kalır ve teklif hazırlanır. Taslak kaydı kontrol ettikten sonra yayınlayın.

Koli/palet bilgisi satış birimi olarak kullanılmaz. Önceki lojistik ayarları ve eski talepler korunur; adet/takım miktarları eski paket sayılarından çevrilmez. Yeni satış formlarında eski alanlar gösterilmez. Eski kaydedilmiş paket/palet talebi anlık kaydı tarihsel olarak okunabilir kalır.

Bir talepte en fazla 50 farklı kaynak SKU bulunabilir. Farklı takım içerikleri aynı talepte yer alabilir; aynı içerik yeniden eklenirse takım adedi birleştirilir. Sunucu katalog üyeliğini ve tanım sürümünü yeniden doğrular. Farklı para birimleri veya eksik fiyatlar tek bir toplam gibi sunulmaz. Taşıma/vergi/teslim koşulları teklif aşamasında teyit edilir.

## Türkiye perakende takım kurucusu

`?page=sets` sayfasında müşteri 17 katalog koleksiyonundan birini açar. Her modelde dahil et/çıkar, mevcut renk ve adet seçimi vardır. Tüm parçalar opsiyoneldir; en az 1 parça gerekir. Bir mobilyanın birleşik bazalı karyola SKU'su, doğrulanmış ayrı SKU'ları yoksa baza/karyola diye bölünmez. Modüler gardırop gövde/kapakları açık kapsam notuyla gösterilir.

Seçim gerçek SKU kalemleri olarak tek işlemle sepete eklenir. Mevcut sepet miktarıyla birleşince ürün başına99 veya toplam100farklı ürün sınırı aşılırsa hiçbir parça eklenmez. Fiyatı doğrulanmamış veya artık görünmeyen ürün varsa kısmi ekleme yapılmaz. Sepette parçalar ayrı ayrı düzenlenebilir. Bu akış mevcut ödeme öncesi hazırlık sınırını açmaz.

Ürün sayfasındaki “Bu ürünle takımını oluştur” bağlantısı ilgili oda ve ürünü ön seçer. Koleksiyon üyelikleri [katalog eşleşme kaydında](furniture-sets.md) kanıtlıdır. Güncel listede bulunmayan 5 katalog kodu aynı dosyada raporlanır; bunlar satılabilir ürün olarak oluşturulmadı.

## Ülke hizmet koşulları ve arama motorları

Hedefler Türkiye, Almanya, Birleşik Krallık, Kazakistan, Türkmenistan, Azerbaycan, Irak, Suriye, İran, Özbekistan ve Kırgızistan olarak hazırlanmıştır. Ülke kaydı ile içerik dili ayrıdır. Yeni pazarı etkinleştirmeden önce gerçek teslimat, iade, vergi ve gümrük koşullarını doldurun.

**Arama motorları** bölümünde dört dilde ana sayfa başlık/açıklamalarını ve Google, Bing, Yandex doğrulama değerlerini kaydedip yayınlayabilirsiniz. Tam HTML etiketi yerine sağlayıcının verdiği doğrulama değerini girin. Search Console/Webmaster bağlantılarında kendi hesabınızla mülk doğrulaması yapmanız gerekir.

IndexNow sahiplik dosyasını hazırladıktan sonra bekleyen değişiklikleri bildirebilirsiniz. Kuyruk ve gerçek yanıt durumu aynı bölümde görünür. “İstek alındı” dizine eklenme veya sıralama anlamına gelmez. Google normal ürün sayfaları için bu kanalı kullanmaz; Google’a site haritası Search Console üzerinden verilir.

## Sipariş, kargo ve belgeler

**Siparişler ve taslaklar** telefon/e-posta gibi kanallardan alınan gerçek taleplerin manuel hazırlığı içindir. Yeni talepte kalemlerin fiyatı yayınlanan katalogdan hesaplanır; önizleme sürümü değişmişse kaydetme durur ve güncel fiyatı yüklemeniz istenir. Kaydedilmiş kalemlerin birim fiyatları daha sonra not/adres/adet düzenlerken korunur. Güncel katalog fiyatına geçmek için sipariş formundaki “Kalemleri güncel katalog fiyatlarıyla yeniden hesapla” seçeneğini açın, gösterilen eski/yeni toplamı kontrol edip kaydedin. Kargo dahil ürün toplamı gösterildiği iddia edilmez. Taslak, hazırlandı veya iptal durumları vardır. Gerçek müşteri siparişleri ayrı **Müşteri siparişleri** bölümünde mevcut kalıcı kayıtlardan okunur.

Ödeme kuruluşu ve yasal firma henüz hazır olmadığı için gerçek ödeme, ödenmiş sipariş veya tamamlanmış sevkiyat elle üretilemez. Misafir alışveriş akışı ödeme öncesine kadar korunur.

**Kargo firmaları** anlaşmalı firmayı ve takip bağlantısını; **Kargo kuralları** ülke, bedel, ücretsiz kargo sınırı ve doğrulanmış teslimat aralığını tutar. Kural taslak/yayın akışına tabidir. Hiç kural yoksa ücretsiz kargo veya teslimat süresi uydurulmaz. Sevkiyat hazırlığı gerçek talep ve etkin kargo firmasına bağlanır. Kargo etiketi satın alan bir servis bağlantısı henüz yoktur.

Sipariş ayrıntısından **Proforma görüntüle** veya **Paketleme listesi** açılır. Tarayıcının yazdır/PDF kaydet işlevi kullanılabilir. Belgeler açıkça “mali belge değildir” ibaresi taşır; müşteri verisine yalnız yetkili personel erişir.

## KolayBi

1. KolayBi’de seçilen ortama ait API anahtarı ve Channel oluşturun. Sandbox ve canlı bilgiler farklıdır.
2. **Entegrasyonlar → KolayBi** bölümünde ortam ve bilgileri kaydedin. Gizli değerler şifreli saklanır ve geri gösterilmez. Boş alan mevcut değeri korur; ortam değiştirilirse iki değer birlikte yeniden girilmelidir.
3. Bağlantı ayarları sürümlüdür. Başka bir sahip ayarları değiştirmişse eski form veya eski doğrulama yanıtı yeni bilgileri ezmez. **Bağlantıyı doğrula** token alır ve gerçek şirket listesini sorgular. Başarısız yanıt bağlantı kurulmuş sayılmaz.
4. **Firma ve vergi ayarları** bölümünde fiyatların KDV dahil/hariç esasını tanımlayın. Canlı taslak fatura için firma unvanı, vergi numarası ve adres de gerekir.
5. Ürün, cari, adres ve uzak belge ID’leri doğrulanmış bağlantı kimliğine bağlanır. Ortam veya kimlik bilgisi değiştiğinde eski eşleştirme otomatik kullanılmaz; yeni bağlantıyı seçerek doğru ID’leri yeniden eşleştirin. Önceki bağlantıya ait belgeyi gerekirse KolayBi uygulamasından kontrol edin. **KolayBi ürün eşleştirme** bölümünde NODENO ürününü, KolayBi ürün ID’sini ve doğrulanmış KDV oranını eşleştirin. Oran otomatik varsayılmaz.
6. Fatura kaydını gerçek sipariş taslağına bağlayın. KolayBi cari ve adres ID’lerini girin. Kontrol ettikten sonra **KolayBi taslağı oluştur** işlemini başlatın.
7. **KolayBi durumunu kontrol et** gerçek uzak kayıt durumunu sorgular. Uzak kayıt resmileştirilmiş ve ETTN bilgisi gelmişse PDF belge indirilebilir. Dönen bir URL otomatik takip edilmez; yalnız sabit KolayBi API’sinden doğrulanan PDF verisi alınır.

Zaman aşımı belirsiz sonuç sayılır; kör yeniden deneme yapılmaz. Önce KolayBi’de NODENO kayıt numarası/açıklamasıyla kontrol edin. Taslak oluşturulması GİB’e gönderim değildir. Gerçek e-fatura gönderimi, kullanıcının bekleyen yasal kurulum kararı nedeniyle sunucuda kapalıdır.

Resmî bağlantı sözleşmesi: [KolayBi kimlik doğrulama](https://developer.kolaybi.com/docs/auth/intro), [fatura oluşturma](https://developer.kolaybi.com/docs/invoices/create), [belge görüntüleme](https://developer.kolaybi.com/docs/invoices/e-document-view).

## Müşteri mesajları, bildirim ve reklam

Sitedeki **Yardım → Bize yazın** formu mesajı kaydeder ve başvuru numarası verir. Mesajlar panelde açık/işlemde/kapandı olarak takip edilir. Bu işlem otomatik e-posta gönderildiği anlamına gelmez.

Bildirim şablonları, ileti taslakları ve reklam planları gerçek kalıcı kayıtlardır. Pazarlama iletisi için izin ve izin kaydı referansı gerekir. E-posta/SMS sağlayıcısı ve reklam platformu adaptörü seçilip kurulmadığı için panel gönderilmiş ileti veya yapılmış reklam harcaması üretmez. KolayBi muhasebe bağlantısı bu servislerin yerine geçmez.

## Analiz ve öneri sıralaması

Mağaza ziyaretçisi analiz için açık seçim yapar. “Yalnız gerekli” seçilirse isteğe bağlı olay gönderilmez. İzin gizlilik tercihlerinden geri alınabilir; ilgili ziyaretçinin analiz kayıtları silinir. Analiz olayında e-posta, serbest URL, adres veya mesaj kabul edilmez. Ham IP olay tablosunda tutulmaz. Seçilen pazar varsa bu ziyaretçi beyanıdır, konum tespiti değildir.

Görüntüleme, sepete ekleme ve favoriye ekleme ziyaretçi/ürün/işlem başına günde bir kez sayılır. Kayıtlar 90 günle sınırlandırılır; panel son 30 günü gösterir. Veri yoksa grafik ve sayaçlara örnek veri eklenmez.

**Ürün öneri ayarları** ağırlıkları ve dönemi değiştirir. Ürün bazındaki öncelik ve mevcut kategori ilişkileri de kullanılır. Aynı modelin farklı renkleri tekilleştirilir; gizli veya doğrulanmış stoku tükenmiş ürün önerilmez. Veri yokken deterministik katalog/kategori sırası kullanılır. Bu özellik kişiye özel satın alma geçmişi varmış gibi iddia üretmez.

## Personel, yedek ve kurtarma

Sahip: tüm yönetim. Mağaza yöneticisi: mağaza işlerini yönetir; sahip, servis sırrı ve personel yetkisi işlemlerini yapamaz. Katalog: ürün/koleksiyon. Operasyon: sipariş/kargo/belge/müşteri. Pazarlama: kampanya/ileti/reklam ve analiz. Analist: yalnız analiz ve genel görünüm.

Davet kodunu ilgili personele güvenli bir kanaldan iletin; panel kendiliğinden e-posta göndermez. Davet 24 saat geçerlidir. Personel **Davetle katıl** üzerinden kendi parola ve TOTP kurulumunu yapar. Yetki değişikliği mevcut oturumları iptal eder. Son etkin sahip kapatılamaz.

Üretim verileri `/home/nodenoho/nodeno-data` altındadır. SQLite/WAL verisi, yönetici oturumları, OAuth ayarları ve `control-key.bin` web kökünün dışındadır. Şifreleme anahtarı olmadan servis sırları/TOTP sırları çözülemez; veritabanıyla birlikte güvenli yedeklenmelidir. SQLite için tutarlı yedek/hosting snapshot kullanın; yazma sırasında yalnız ana `.sqlite` dosyasını kopyalamayın.

Onaylı görseller `/home/nodenoho/nodeno-media` altındadır. Sürüm paketleri ve yayın yedekleri bunlardan ayrıdır. Yayın betiği mevcut veritabanını veya görsel deposunu silmez. Tüm doğrulama araçları kaybedilirse sahip kurtarması hosting yetkilisiyle özel doğrulama gerektirir; herkese açık parola sıfırlama kestirmesi yoktur.

## Kapı ve dolap kapağı talepleri

**Kapı, kapak ve proje talepleri**, mağazadaki ölçülü sepetten gönderilen talepleri gösterir. Durum, teklif koşulları ve iç not düzenlenir; müşterinin orijinal ürün/ölçü seçimi ve fiyat anlık kaydı korunur. Kapı takımı ile kapak m² minimumları bağımsızdır. Ürün fiyatı veya kampanya değişikliği yeni teklif hesabına yansır; eski talep kaydı yeniden fiyatlandırılmaz. Kullanım, kaynaklar, kur kuralı ve sonraki ödeme bağlantısı için [kapı ve kapak ticareti](kapi-ve-kapak-ticareti.md) belgesine bakın.

## Tedarikçiler ve gerçekleşen alışlar

**Tedarikçiler ve alışlar** bölümünde NODENO kodu ve tedarikçinin değişmeyen kodu birlikte görünür. Adore, Alka Ahşap ve Altın İş Ağaç kayıtlarında **Tedarikçide aç** doğrudan kaynak ürün sayfasını yeni sekmede açar; siparişi tedarikçinin kendi ekranında tamamlarsınız. Liste/katalog kaynaklı Göktaş ve NDECOR ürünlerinde doğrulanmış ürün bağlantısı olmadığı için bağlantı uydurulmaz. **Eşleştirmeyi düzenle** ile mevcut tedarikçi/kaynak kodu/ürün bağlantısı güncellenebilir; yalnız seçilen firmanın alan adı kabul edilir.

**Alış kaydet** ile her gerçekleşen alışı ayrı kaydedin: tarih, miktar, adet/takım/metre/m²/paket birimi, birim bedeli, para birimi, belge ve sipariş referansı. Aynı siparişin sonraki parça teslimatını yeni alış kaydı olarak girin. Bu kayıtlar müşteriye gösterilmez; mevcut satış fiyatı ve geçmiş sipariş bedeli değişmez. Farklı para birimleri veya ölçü birimleri tek toplam altında karıştırılmaz.

**Fiyat listesi yükle** şu CSV biçimini kabul eder: `sourceCode;unitPrice`. Örneğin `739;2575,00`. Binlik ayraç kullanmayın. Her yüklemede tedarikçi, para birimi, fiyat birimi ve KDV esası seçilir. Önce **Fiyat listeleri → Karşılaştırmayı aç** ile değişen, yeni, eşleşmeyen, birden çok ürüne denk gelen ve yeni listede bulunmayan kodları inceleyin. **Listeyi onayla** listeyi sonraki karşılaştırmanın temeli yapar; mağaza satış fiyatlarını otomatik değiştirmez. Yanlış dosya onaylanmadan yeni dosya yüklenebilir. Siz karşılaştırırken başka bir liste onaylanırsa dosyayı yeniden yükleyerek güncel farkı alın. Orijinal CSV, hash ve işlem geçmişi özel depoda tutulur.

Listeyle çalışan tedarikçilerde son onaylı listenin alındığı tarihten 15 gün sonra uyarı görünür; henüz panelde liste kaydı bulunmayan firmalarda güncel liste kontrolü istenir. Ayrı Codex hatırlatması da 15 günde bir çalışır. Bu işlem tedarikçiye otomatik e-posta göndermez. Kaynak PDF/Excel listeleri doğrudan bu CSV ekranında ayrıştırılmaz; kod/fiyat sütunları kontrol edilip CSV olarak hazırlanmalıdır.

Alka ve Altın İş fiyat kuralı koşulsuz güncel satıcı fiyatı üzerine %20, Adore kuralı %30 ilavedir. Mevcut satış fiyatı tekrar çarpılmaz. Seçenekli üründeki başlangıç fiyatı bütün varyantlara atanmaz. Yeni kaynak ürünler görsel, dil ve birim doğrulaması bitene kadar hazırlık kataloğundadır; sadece indirilmiş olması mağazada yayınlandığı anlamına gelmez. Kur hesabı mevcut TCMB haftanın en yüksek döviz satış kuru ilkesini korur.


10 Kasım çoklu ölçü güncellemesi: Kapı/kapak talebi birden fazla ölçü, adet, uygulama ve cam modelini ayrı satır kimlikleriyle taşır. Orijinal seçim anlık görüntüsü korunur. 95/115/145/165 mm kasada fark yoktur; 185 ve 215 mm farkları takım başına uygulanır. Mağaza demosu sipariş veya talep oluşturmaz. [Kullanım ve ölçü sözleşmesi](kapi-ve-kapak-ticareti.md).


## Kartla ödeme ve doğrulanmış siparişler

Entegrasyonlar → Stripe / Kartla ödeme bölümünü yalnız firma sahibi yönetir. Gizli anahtarlar yazıldıktan sonra tekrar gösterilmez. Hesap kimliği, aynı ortama ait API anahtarı ve imzalı bildirim bağlantısı doğrulanmadan ödeme açılmaz. Yasal satıcı PTYS Technologies LLC olarak belirtilmiştir; Türkiye satışlarına ait fatura/KDV uygulaması ayrıca doğrulanmalıdır. Satış/iade metinleri dört dilde tamamlanır. Müşteri siparişleri ekranının altındaki kart kayıtları yalnız gerçek imzalı bildirimle Ödendi olur; elle ödeme onayı verilmez. Fatura ve sevkiyat ayrıca yönetilir. Ayrıntılar ve bağlantı adımları: [Stripe ödeme kılavuzu](stripe-checkout.md).


Parola unutulduğunda mevcut sahip hesabı silinmez. Yetkili hosting bakım işlemiyle parola yenilenebilir; doğrulama uygulaması ve kurtarma kodları korunur, eski oturumlar geçersizleşir. Yeni parola yalnız sahibin erişebildiği özel yerel dosyadan teslim edilir; sohbet, yayın paketi veya Git’e yazılmaz. Bu yöntem otomatik bir müşteri/parola sıfırlama e-postası göndermez.

Satış/iade metinlerinin `2026-11-10.2` sürümü dört dilde yayındadır. Entegrasyonlar → Stripe / Kartla ödeme → Satıcı ve satış belgeleri altında dil başlığını açarak düzenleyin. Türkiye iade adresi No:100/C'dir; kayıtlı ABD adresine ürün gönderilmesi istenmez. Satıcı/fatura/vergi uygulaması kutusu işletme sahibinin ticari düzen onayını ifade eder; devlet makamınca tescil kontrolü değildir. Resmî kayıt bilgisi uydurulmaz. Muhasebe takibi ve mali müşavire verilecek hazır not: [PTYS Türkiye fatura hazırlığı](ptys-turkiye-fatura-hazirlik.txt). Metin veya satıcı düzeni değiştiğinde yeni belge sürümüyle kaydedin; eski sipariş koşulları değişmez.

Son talimatla hazırlanan `2026-11-10.2` sürümünde fatura düzenleyicisi PTYS / ABD, sevk ülkesi Türkiye'dir. Sahibin açık etkinleştirme kararı, fatura/fiyat/vergi uygulamasının işletme adına onayı olarak kaydedilir; resmî vergi tescili denetlenmiş gibi sunulmaz. Bu karar mevcut sahip yetkisi, doğrulanmış canlı hesap ve imzalı webhook koşullarını kaldırmaz. Otomatik fatura üretimi bağlanmadı; PTYS faturaları ayrıca düzenlenir. İşletme, yasal fatura/KDV yükümlülüklerinin takibini sürdürür.

İade için Stripe panelinde ilgili ödemeyi açın ve iade tutarını kontrol ederek işlemi orada başlatın. Mağazada otomatik para iadesi düğmesi eklenmedi. `refund.created`, `refund.updated`, `refund.failed` bildirimleri bağlandığında başarılı tutar yönetimde ve müşterinin ödeme ekranında görünür. Kısmi iade ve tam iade ayrı durumdur; bekleyen/başarısız iade tamamlanmış para dönüşü sayılmaz. İade edilen sipariş müşteri geçmişinde kalır. Test ve canlı ortamlar birbirinden ayrıdır; test siparişi sevkiyat veya fatura oluşturmaz. [İade takibi ve test kabulü](stripe-checkout.md#kısmi-ve-tam-iade-takibi).


## Bilgilendirme ve sözleşmeler

Belge merkezi https://nodenohome.com/legal?lang=tr adresinde dört dilde sunulur. Üyelik kabulü ayrı sürüm/özet/zaman kaydıyla saklanır; KVKK aydınlatması analiz veya pazarlama izni değildir. Ödeme öncesi indirilen sözleşme kopyası siparişe bağlı ve değişmezdir. İade, vergi/fatura, veri başvurusu, garanti ve resmî kayıt takibi için [belge merkezi kılavuzunu](legal-documents.md) ve [işletme takip kaydını](legal/compliance-register.md) kullanın.

## Telefonda yönetim

Sol üstteki menüden bölümler arasında geçebilirsiniz. Dar ekranda ana işlemler tek sütun, özet sayılar iki sütun gösterilir. Menü açıkken arka sayfanın kayması durur; bir bölüme geçince menü kapanır ve yeni bölümün başı görünür. Giriş, doğrulama ve düzenleme alanları mobilde en az 16 piksel yazı kullanır. Kullanıcının kendi yakınlaştırması kapatılmaz. Geniş tablolar kendi çerçevesi içinde yatay kayar; sayfanın tamamı taşmaz. Düzenleme penceresini kapatınca kaydetmediğiniz değişiklikler yayınlanmaz.

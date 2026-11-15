# NODENO kategori kartları: resmî görsel referans incelemesi

31 Ekim 2026. Amaç, ana vitrinin sağındaki Antre ve çocuk odası kartlarının görsel niteliğini düzeltmek için fotoğraf, kırpma, metin ve mobil oran kararlarını somutlaştırmaktır. NODENO'nun kendi marka kimliği korunur. Başka markaların fotoğrafları siteye indirilmedi veya kopyalanmadı; yalnız referans ekran görüntüleri kaydedildi.

## Erişim ve kanıt sınırı

| Resmî sayfa | 1366 × 900 | 390 × 844 | Bu incelemeden çıkarılabilecek sonuç |
|---|---|---|---|
| [Muuto](https://www.muuto.com/) | HTTP 200; hero, ürün koleksiyonu ve ev hikâyeleri görüldü | HTTP 200; aynı bölümlerin mobil yerleşimi görüldü | Gerçek görsel kompozisyon gözlemi var. Çerez tercihi penceresi orta alanı kapatıyor; açıkta kalan alanlar ve DOM ölçüleri incelendi. Pencere gizlenmedi, tercih düğmelerine basılmadı. |
| [Zara Home Türkiye](https://www.zarahome.com/tr/) | HTTP 403 Access Denied | HTTP 403 Access Denied | Gerçek sayfanın görsel tasarımı incelenemedi. Web metin okuyucu yalnız gezinme kabuğunu döndürdü; bu görsel kanıt sayılmadı. |
| [HAY](https://www.hay.com/) | İlk belge HTTP 403, güvenlik doğrulaması | İlk belge HTTP 403, güvenlik doğrulaması | Alternatif denendi; gerçek ana sayfa görüntülenemedi. Web metin okuyucunun içeriği görsel kanıt yerine kullanılmadı. Doğrulama aşılmadı. |

Tarayıcı bağlamı hesap içermiyordu. GET/HEAD/OPTIONS dışı istekler engellendi. Muuto'da iki, HAY'de yedi otomatik istek engellendi; hiçbir güvenlik/çerez ekranı DOM'dan kaldırılmadı veya geçilmiş gibi gösterilmedi. Muuto ve HAY'e ilişkin erişim sonucu bu kontrollü araştırma ortamına aittir; tüm kullanıcıların erişimi hakkında hüküm değildir.

## Doğrudan gözlenen kompozisyon

Muuto girişinde tek mobilya kesiti yerine odanın duvarını, zeminini, ışığını ve çevresindeki nesneleri de gösteren büyük bir yaşam alanı fotoğrafı kullanılıyor. Aşağıdaki ev hikâyelerinde fotoğraf geniş yüzey kaplıyor; başlık ve açıklama düzenli, ayrı bir metin yüzeyinde okunuyor. Ürün koleksiyonu ise beyaz zemindeki ürün fotoğraflarıyla ayrı bir bölüm oluşturuyor. Bu ayrım, ilham veren oda fotoğrafı ile katalog ürün kesitinin farklı görevlerini görünür kılıyor. [Resmî sayfa](https://www.muuto.com/)

Gözlenen mobil sayfa, masaüstünü yalnız küçültmüyor: tipografi ve fotoğraf yeri değişiyor, içerik akışı yeniden kuruluyor. Çerez penceresi merkezi alanı kapattığından mobil metin/fotoğraf birlikteliğinin bütünü görülmüş veya etkileşimleri doğrulanmış sayılmaz.

## NODENO'ya uygulanacak beş karar

1. **Fotoğraf bütün kartı kaplasın.** Antre için seçilen `2738:0`, çocuk odası için `2595:1` gerçek NODENO yaşam alanı görselleri kenardan kenara kullanılmalı. Küçük fotoğraf, beyaz iç çerçeve ve bağımsız limon yeşili zemin kaldırılmalı. Odanın kullanım bağlamı ve mobilya silueti ilk bakışta anlaşılmalı. Bu, referanstaki oda fotoğrafının görevinden çıkarılmış NODENO uygulama kararıdır.

2. **Kırpma her görsel için ayarlansın.** `object-fit: cover` tek başına yeterli değildir. Kapak, masa, yatak veya depolama ünitesinin ayırt edici bölümü 1366 ve 390 genişlikte görülmeli. Fotoğrafın odağı her kartta ayrı `object-position` ile korunmalı; önemli mobilyayı kesen ortak merkez kırpması kullanılmamalı. Önce fotoğrafın odağı belirlenmeli, sonra kart oranı seçilmeli.

3. **Metin tek ve okunabilir bir alanda toplansın.** NODENO uygulamasında alt kısımda sakin koyu bir geçiş, kategori başlığı ve açık eylem metni yeterlidir. Fotoğrafı bütünüyle karartan bir katman kullanılmamalı. Normal metin için en az 4.5:1 karşıtlık, tüm fotoğraf değişkenlerinde kontrol edilmeli; yalnız gölge eklemek yeterli kabul edilmemeli. Başlık, örneğin “Antre” veya “Çocuk odası”; bağlantı da gerçekten açacağı kategoriyi adlandırmalı. Dekoratif ok karakteri, kesme işaretiyle bölünen kısa sloganlar veya ürünle ilgisiz dolgu açıklaması eklenmemeli.

4. **İki kart aynı görsel düzeni paylaşsın.** Eşit kenar boşluğu, tutarlı alt hizalama, aynı başlık ailesi ve benzer fotoğraf yoğunluğu kullanılmalı. Bir kartta ürün kesiti, diğerinde küçük oda karesi gibi karışık kurgu yapılmamalı. NODENO'nun kendi tipografisi ve renkleri korunmalı; Muuto'nun kahverengi yüzeyi, büyük kampanya başlığı veya marka dili taklit edilmemeli. Bu küçük vitrin için tutarlılık önerisi tasarım çıkarımıdır; referanstaki bütün hikâye kartlarının eşit boyda olduğu iddia edilmez.

5. **Mobil fotoğrafı küçültmesin, yeniden kadrajlasın.** Telefon görünümünde kartlar üst üste gelerek oda fotoğrafının okunabilir yüksekliğini korumalı. Başlık iki gereksiz satıra sıkışmamalı; kartın tamamı erişilebilir bağlantı olabilir. Dokunma alanı en az 44 × 44 CSS piksel olmalı. Yükleme sırasında aynı kart yüksekliği ayrılmalı; başlık ve çevresindeki içerik fotoğraf gelince sıçramamalı. İki gerçek görsel için mobil ekran ayrıca gözle kontrol edilmeli.

`ui-ux-pro-max` için hedefli `image overlay text contrast --domain ux` sorgusu kullanıldı. Eşleşen sonuçlar metin karşıtlığı, 4.5:1 alt sınırı ve anlamlı görsel alternatifi konularını destekliyor. Fotoğraf seçimi, alt geçişin biçimi ve mobil kart kararı bu görev için yapılan tasarım çıkarımlarıdır; bir skill çıktısının ölçülmüş mevcut site sonucu gibi sunulması söz konusu değildir.

## Dosyalar

- [Muuto masaüstü giriş](../artifacts/design-reference/muuto-1366-0.png)
- [Muuto masaüstü ürünler](../artifacts/design-reference/muuto-1366-1.png)
- [Muuto masaüstü ev hikâyeleri](../artifacts/design-reference/muuto-1366-2.png)
- [Muuto mobil giriş](../artifacts/design-reference/muuto-390-0.png)
- [Muuto mobil alt bölüm](../artifacts/design-reference/muuto-390-2.png)
- [Zara Home erişim sonucu](../artifacts/design-reference/zarahome-1366-0.png)
- [HAY erişim sonucu](../artifacts/design-reference/hay-1366-0.png)

`artifacts/design-reference/report.json` ve `hay-report.json` durum, URL, metin ve görünür öğe ölçülerini saklar. `capture.mjs` kullanılan salt okunur çekim betiğidir. Uygulama, katalog, backend, hesap ve yayın ayarlarına bu incelemede değişiklik yapılmadı.

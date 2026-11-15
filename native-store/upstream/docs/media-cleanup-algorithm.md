# Katalog görsellerinde marka temizleme algoritması

Kullanıcının açıkça onayladığı kapsam, Adore yazısını/logosunu görsele işlenmiş filigranlardan ve fiziksel ürün rozetlerinden kodla kaldırmaktır. Hat gerçek görsel piksellerini işler; CSS ile kapatma, yeni marka etiketi bindirme veya yapay ürün sahnesi üretme kullanmaz. Kaynak görselleri değiştirmez. Bu belge yalnız temizleme algoritmasını anlatır; indirme/doğrulama için `docs/media-cleanup.md`, yayın için onay manifestini kullanan sunucu akışı esas alınır.

## Çalıştırma

Çalışma klasörü `C:/Users/Hamza ÖZBALKAN/Desktop/Nodeno` olmalıdır. İzole ortamda Pillow, OpenCV, NumPy, rapidocr-onnxruntime 1.4.4 ve onnxruntime 1.31.1 kullanılır.

```powershell
& './artifacts/media-tools/Scripts/python.exe' -B -m unittest tests/media_clean_test.py
& './artifacts/media-tools/Scripts/python.exe' -B './scripts/media-clean.py' --apply --limit 24 --workers 4
& './artifacts/media-tools/Scripts/python.exe' -B './scripts/media-clean.py' --apply --workers 8 --follow-downloads
```

`--apply`, sadece yerel onaylı kopyaları yazar; siteye yükleme veya yayın yapmaz. Parametre verilmezse adaylar raporlanır, yeni dosya yayın onayı almaz. `--limit`, yeni işlenecek kayıt sayısını sınırlar. `--follow-downloads`, indirme manifestine sonradan eklenen doğrulanmış dosyaları da alır. `--retry-failed`, aynı sürümdeki hata kayıtlarını yeniden dener. Sekiz işçi üst sınırdır; her işçinin ONNX işlem içi iş parçacığı sayısı iki, OpenCV iş parçacığı sayısı birdir.

## Değişmez kaynak ve tespit

Girdi `artifacts/media-download.json` içindeki `images[urlSha]` kayıtlarıdır. Sadece `status: verified` kayıtlar işlenir. Dosyanın gerçek SHA-256 değeri, işlemeden önce manifestteki `sha256` ile karşılaştırılır; işlem sonunda kaynak tekrar doğrulanır. Aynı URL, başka bir ürünün görsel listesinde kullanılıyorsa `references['productId:index']` bağı korunur.

Her dosyada tüm görüntü OCR ve rozet şablonu taramasından geçer. RapidOCR'nin PP-OCRv4 algılayıcısı en uzun kenarda 1280 sınırıyla çalışır; dönen kutular özgün piksel koordinatlarındadır. Metin skoru eşiği 0,30'dur. `Adore`, `Adore Mobilya`, alan adı, `ad0re` ve Kiril/Arapça yazım karşılıkları Unicode normalleştirme ile sınıflandırılır. Yakın yazımlar kesin marka kabul edilmez; incelemeye gider. Marka ve ölçü/birim bilgisi aynı OCR satırındaysa bu satır otomatik silinmez.

OCR modeli bütün dünya yazı sistemleri için eksiksiz bir model değildir. Kiril/Arapça karşılıklar dönen metinde aranır; bu, o alfabelerde tam okuma garantisi anlamına gelmez. Ürünlerdeki Latin harfli fiziksel logoları OCR'den bağımsız yakalamak için ikinci yol kullanılır. Hiç tespit çıkmaması da görünmez, aşırı küçük, açı nedeniyle bozulan veya referansa benzemeyen bütün olası logoların yokluğunu kanıtlamaz.

Şablon, kullanıcının verdiği örnek ekran görüntüsündeki gerçek siyah/beyaz/turuncu Adore rozetinden çıkarılmıştır. Kaynak dosya değişmez; örnek kırpımın kaynağı, koordinatı ve SHA değeri `artifacts/media-cleanup/templates/reference.json` içindedir. Bu kırpım sadece algılama referansıdır, mağazada ürün fotoğrafı olarak kullanılmaz. Gri tonlu, çok ölçekli normalize korelasyon ve kenar uyumu taranır. Ölçekler 24 pikselden görüntü genişliğinin üçte birine kadar ilerler. Şablon skoru 0,79–0,91 arasında inceleme gerektirir; en az 0,91 güçlü eşleşmedir. Aynı kutuda güvenilir OCR bulunduğunda iki kanıt birlikte değerlendirilir. Bir kolajda birden fazla rozet bulunabilir.

Animasyonların bütün kareleri tek tek taranır; bütün RGB kareleri bellekte biriktirilmez. Saydam görseller hem beyaz hem siyah kompozitte taranır. Kod, boyut/dtype ve gerçek çözülmüş RGB baytlarının SHA-256 değeri tamamen aynıysa aynı analiz sonucunu yeniden kullanır; her kare raporunda içerik SHA'sı ve yeniden kullanım kanıtı bulunur. Bu, aynı GIF'i farklı URL'lerle tekrar taramayı ve aynı kareyi tekrar tekrar ONNX'e vermeyi azaltır. Önbellek en fazla 4096 sonuç tutar, görüntü dizileri tutmaz. Animasyonda/saydam görüntüde marka tespit edilirse kare/alpha bütünlüğünü koruyan ayrı inceleme gerekir. Hiçbir kare/kompozitte marka bulunmazsa özgün animasyon/saydam dosyanın baytları aynen kopyalanır.

## Maske ve gerçek rötuş

Fiziksel siyah plaka korunur; sadece üstündeki marka baskısı kaldırılır. Böylece plakanın altında görünmeyen ahşap dokusu veya ürün köşesi yeniden üretilmez. Plakaya yeni bir NODENO imalat etiketi eklenmez.

İki gerçek logo referansının yerel ölçek, yükseklik ve eğim eşleşmesiyle baskı alanının dörtgeni bulunur. İkinci referans, katalogdaki ince harfli gerçek rozettir; kaynağı ve SHA değeri `templates/catalog-reference.json` içindedir. Referans kırpımları fiziksel dış çerçevenin iç baskı alanını gösterir. Bu yüzden bu dörtgenin dışına maske büyütülmez; dış çerçeve, ürün kenarı ve komşu malzeme pikselleri aynen kalır. Dörtgen içi, plakanın kendi koyu arka plan örneklerinin medyan tonuyla temizlenir.

Gri görüntü korelasyonuna ek olarak gerçek kırmızı/turuncu baskı çizgisinin renk korelasyonu kullanılır (%72 gri, %28 renk). Bu, düşük çözünürlükte yazı ile aynı yeri tutan fakat alt çizgiyi kesen bir şablon yerleşimini azaltır. Yerel bileşik uyum en az 0,57 olmalı; koyu zemin desteği, plakanın alanı (en fazla görüntünün %1,5'i) ve OCR güveni de kontrol edilir. Sırf gri değeri koyu olan bütün ahşap/kırmızı parçaların convex hull'ı alınmaz. Fiziksel plaka eşleşmesi belirsizse bütün siyah rozeti yok edip mobilya köşesini inpaint etme yoluna dönülmez.

Saydam/harici filigran gibi plaka içermeyen durumlarda maske marka harflerini kapsar. Düz, açık yüzeylerde harf pikselleri yerel renk farkıyla bölütlenir. Bu arka plan rötuşu yolu aşağıdaki ek kapıları kullanır:

Aşağıdaki durumlarda dosya otomatik onay alamaz:

- Tespit güveni belirsizdir veya yazı önemli ölçüde perspektiflidir.
- Marka kutusu görüntünün genişliğinin %30'unu ya da yüksekliğinin %18'ini aşar.
- Toplam maske görüntü alanının %2,5'ini aşar.
- Komşu renk değişimi dokulu yüzey, ürün kenarı veya birleşim riski gösterir; hem medyan hem P90 renk uzaklığı kontrol edilir.
- Aynı metin satırında teknik ölçü/birim bilgisi vardır.

Bu arka plan yolunda OpenCV Telea ve Navier–Stokes inpainting adayları, maskenin dışındaki kaynak komşuluğunu kullanır. Düz yatay bir yüzeyde iki taraftaki aynı satır renk profilleri güçlü biçimde uyuşuyorsa yönlü sınır interpolasyonu da adaydır. Güçlü satır uyumu yoksa maske sınırındaki eğrilik ve yerel renk tutarlılığı skoruyla aday seçilir. Bu puanlar görünmeyen özgün malzemeyi doğrulayamaz; önemli geometri riski varsa dosya incelemede kalır. Fiziksel plakalar bu mobilya yüzeyi yeniden oluşturma yoluna gönderilmez.

Maske dışı tüm RGB pikselleri işlemden sonra kaynaktan açıkça geri konur. Adayın tamamında yeniden OCR ve şablon taraması yapılır. Kalan marka/şüpheli eşleşme, renk tutarsızlığı veya kodlama hatası `review_required` ya da `failed` sonucudur. Böyle dosyalara onaylı çıktı yolu verilmez.

## Bayt ve görüntü doğrulaması

`approved_unmodified`, tarama sonucunda marka bulunmayan özgün dosyanın bayt düzeyinde kopyasıdır. Çıktı SHA-256 değeri kaynak SHA-256 ile aynı olmalıdır.

`approved_cleaned`, maske içindeki rötuşun kayıpsız WebP çıktısıdır. Kayıpsız kodlama seçilmesinin nedeni ürünün maske dışındaki renk ve geometrisini JPEG/WebP nicemlemesiyle yeniden değiştirmemektir. Dosya yeniden açılır ve kodlanmış/çözülmüş bütün RGB piksellerinin aday görüntüyle aynı olduğu doğrulanır. Boyutlar aynen korunur. Maske dışında maksimum/ortalama kanal farkı ve değişen değer sayısı sıfır, dış maske SSIM değeri 1,0 olmalıdır. Bu ölçüm yalnız maskenin dışını doğrular; maskenin arkasındaki bilinmeyen gerçek yüzeyin birebir geri kurulduğu iddiası değildir.

OpenCV algoritmaları için birincil kaynak: [OpenCV Image Inpainting](https://docs.opencv.org/4.x/df/d3d/tutorial_py_inpainting.html). Telea komşuluktan doldurur; Navier–Stokes bilinen kenarların sürekliliğini izleyerek doldurma yapar.

## Manifest ve karantina

`artifacts/media-cleanup.json` özel çalışma manifestidir; kaynak URL ve yollarını içerir, halka açık belge değildir. Anahtar URL'nin SHA değeridir. Üst alanlar: `schemaVersion`, `pipelineVersion`, `publicationReady`, `config`, `sourceCatalogSha256`, `references`, `images`, `totals`, `updatedAt`. CLI her başlangıçta `publicationReady:false` yazar; bitince kendiliğinden true yapmaz. Yayın bütün dosyalar son durumda ve son görsel kabul tamamlanmadan açılmamalıdır.

Her görsel kaydı şu alanları taşır:

| Alan | Anlamı |
| --- | --- |
| `state` | `pending`, `approved_unmodified`, `approved_cleaned`, `review_required`, `failed` |
| `sourceSha`, `sourcePath`, `sourceBytes` | Doğrulanmış değişmez kaynak |
| `outputSha`, `path`, `filename`, `mime`, `bytes` | Sadece onaylı çıktıda yayınlanabilir dosya bilgileri |
| `width`, `height` | Kaynakla aynı çıktı boyutları |
| `report` | Tam özel OCR, kutu, maske ve doğrulama raporu |
| `pipelineVersion` | Algoritma kaynak kodu, ayarlar ve referans PNG'lerin SHA birleşimi |
| `reason`, `maskCoverage` | Kararın nedeni ve değiştirilen alan oranı |

Tam raporlar `artifacts/media-cleanup/reports/<urlSha>.json`, maskeler `masks`, inceleme kırpımları ve adaylar `review` altındadır. Son tarama bitince 48 kayıtlık inceleme temas sayfaları üretilir. Aday rötuş dosyası bulunması, dosyanın onaylı olduğu anlamına gelmez. Yayın yalnız iki `approved_*` durumunu, gerçek çıktı hashini ve geçerli hat sürümünü kabul etmelidir; `review_required`, `pending` veya `failed` görsellerde kaynağa sessiz dönüş yapılamaz.

Checkpoint JSON, flush/fsync edilmiş geçici dosya ve atomik `os.replace` ile yazılır. Windows'ta kısa süreli açık okuyucunun paylaşım kilidi için sınırlı PermissionError tekrarları vardır; hedef dosyayı silme/truncate etme yedeği yoktur. Aynı sürümde devam etmek için kaynak gerçek SHA'sı ve varsa onaylı çıktı gerçek SHA'sı tekrar doğrulanır. Kod/ayar/şablon değişirse eski onaylar önce `pending` yapılır ve yeniden taranır. Çalışma sürerken manifest bir ilerleme kaydıdır; bütün 5.129 dosyanın tamamlandığı anlamına gelmez. Sonuç değerlendirilirken `totals.pending`, `review_required`, `failed`, her kaydın `pipelineVersion` değeri ve yayın kapısı birlikte kontrol edilir.

## Kalibrasyon ve test kapsamı

Kullanıcının 1163 × 376 örneğinde OCR `adore` sözcüğünü yaklaşık 0,913 güvenle okudu; bağımsız rozet şablonu aynı yerde yaklaşık 0,826 skor verdi. Son fiziksel plaka yöntemi ayrıca gerçek katalogdaki 24 ilk işaretli dosyada çalıştırıldı; yakın kırpım, maske ve tam görüntü çiftleri `artifacts/media-cleanup/calibration/final-candidates` altındadır. Bunlar bütün katalog için başarı garantisi değildir ve yayın kapısını açmaz.

12 test; gerçek rozet şablonunun iki boyutta yakalanmasını, turuncu çizginin maskeye alınmasını, maske dışındaki çizgi/geometri ve rastgele RGB değerlerinin kodlama sonrasında korunmasını, beyaz görselde işlem yapılmamasını, kaynak SHA uyuşmazlığının işleme başlamadan reddini, post taramada marka kalırsa onaylı çıktı oluşmamasını, çok renkli ürün köşesinin yalnız medyanla gözden kaçmamasını, fiziksel plaka dörtgeninin dışına tek piksel taşılmamasını, geçici Windows paylaşım hatasında eski JSON'un kaybolmamasını ve özdeş kare analizinin içerik SHA'sıyla tekrar kullanılmasını denetler.

Tamamlanma raporu, sayısal manifest sonucuyla verilmelidir. Sıfır tespit çıkan dosyaları “elle bütün ayrıntıları doğrulandı” şeklinde tanımlamak veya inceleme kuyruğu varken “bütün logolar kesin temizlendi” demek doğru değildir.

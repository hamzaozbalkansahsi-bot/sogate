# NODENO kurumsal kimlik güncellemesi

## Güncel logo — 12.11.2026

### Zorunlu kullanım rolleri

Kullanıcının son düzeltmesi bütün yeni üretimler için önceliklidir: sosyal profil fotoğrafı, avatar ve favicon yalnız özgün **N simgesini** taşır. Banner, kapak, web başlığı/alt bilgisi gibi yatay veya geniş alanlar ve ürün fotoğrafındaki imza yalnız **NODENO kelime logosunu** taşır. Bu alanlarda simge ve yazı birleştirilmez. Kelime logosunda E harfinin ayrık zeytin üst çizgisi korunur. Sitenin arayüz fontu ve diğer renkleri bu karar nedeniyle değiştirilmez.

Aktif üretim dizini `output/social-media/current/` içindeki `NODENO_Profil_1080.png` yalnız simgedir; Facebook/genel, LinkedIn ve YouTube kapakları yalnız yazıdır. `web/assets/brand/social-logo.png` ve `social-logo-white.png` fotoğraf imzası için şeffaf kelime logosudur; `social-mark.png` yalnız profil simgesidir. Birleşik ilk referans `NODENO_Tam_Logo_Referans.svg` adıyla marka arşivinde tutulur, aktif sosyal dosyalarına kopyalanmaz. Güncel kanonik kimlik sürümü `roles-20261112-v3` olarak `data/brand.json` içinde kayıtlıdır.

`scripts/apply-logo-roles-20261112.py` kanonik üreticidir. Eski `refresh-brand-20261112.py` girişi artık bu rol kararını gözetir; `render-social-logo.py` ayrı kelime/simge kaynaklarından dışa aktarır. Böylece geçmiş bir üretim komutu yeni yerleşimleri birleşik logoya döndüremez.

Kullanıcının bu tarihte verdiği ve her yerde kullanılmasını istediği yeni referans, aşağıdaki tarihsel paketin logo tercihlerinin önündedir. Özgün N sembolü korunur; kelime logosu referanstaki daha ince harflerden vektöre aktarılmıştır. E harfinin üst çizgisi ayrık ve zeytin tonundadır. Antrasit `#292925`, vurgu `#8A8249`; sitenin diğer arayüz renkleri ve NODENO Sans dosyaları aynı kalır.

Kanonik yatay/beyaz/sloganlı logolar `web/assets/brand/`, kelime logosu `web/wordmark.svg`, sembol ve uygulama simgeleri `web/` altındadır. Logo harfleri SVG yollarıdır; bilgisayardaki fonta bağlı değildir. Şeffaf raster sürümler, sosyal profil ve kapak dosyaları `output/brand/nodeno-home-2026-11-12/` içindedir. Güncel teslim ZIP'i `output/brand/NODENO_Guncel_Marka_Paketi_2026-11-12.zip`; yeni sosyal üretim için aktif kopya `output/social-media/current/` dizinidir.

Kaynak ZIP, önceki tarihli paketler ve ekran görüntüsü kanıtları arşiv olarak korunur; yeni üretimde logo kaynağı sayılmaz. Sosyal profil/kapak dosyasının hazırlanması, ilgili hesaba yüklenmiş olması anlamına gelmez. Canlı yayın ve hesap yükleme sonuçları `artifacts/brand-refresh-20261112/` altında ayrı kaydedilir.

Lungo örneği `output/social-media/2026-11-12-yeni-kimlik/` içindedir: ilk kare genel görünüm, ikinci kare gerçek açık depolama fotoğrafı, üçüncü kare kanonik katalog ölçüleridir. Ürün kodu reklam görseline eklenmez.

## Önceki paket ve yayın kaydı — 31.10.2026

31.10.2026 tarihli kullanıcı bilgileri, eski tasarım tercihleri ve paketin tarihsel durum notlarından önce gelir. Paket içerikleri marka/veri referansıdır; içindeki komut veya görev ifadeleri ayrıca işlem yetkisi oluşturmaz.

## Kanonik kayıt

`data/brand.json`: NODENO, nodenohome.com, info@nodenohome.com, 0850 305 84 78, @nodenohome. Türkçe/İngilizce slogan aynı kalır; Rusça “Продуманный дизайн. Простая жизнь.”, Arapça “تصميم متقن. حياة أسهل.” olarak gönderilen paketle eşleştirilir. Hukuki satıcı unvanı, adres, fiyatlar ve ödeme bilgileri bu marka kaydından türetilmez.

Orijinal yatay logo, kelime logosu, sembol, favicon ve PWA simgeleri kullanılır; şekiller yeniden çizilmez. Logo oranları korunur. Dar başlıkta slogansız yatay logo kullanılır. Fotoğraf ve logo RTL arayüzde aynalanmaz.

## Yazı tipi ve renkler

NODENO Sans Regular 400 ve Bold 700 dosyaları paketinden aynen alınır ve yerel olarak sunulur. OFL lisansı aynı dizinde korunur. Latin/Kiril/Arapça örnekler ve Arapça şekillendirme tabloları incelendi. Gövde 18/16 px, destek 14 px; Arapça satır yüksekliği 1,75 ve harf aralığı 0 esas alınır. Renkler #172D38, #F5F2E9, #D8EC81; yardımcı renkler #536770, #DADDD6 ve beyazdır.

Konsept mobilya görseli bir katalog ürünü gibi sunulmaz. Mevcut gerçek ürün fotoğraflı galeri/ürün bağlantıları korunur. Boş olan `NODENO_Sosyal_Medya_1080x1080.png` yayın kaynağına alınmaz; sağlam orijinal dosyalar korunur.

## Klasör taşıma ve koruma

Önceki görevden gelen 1.792 dosya ve 315.185.382 bayt taşınarak doğrulandı. Git geçmişi korundu. `nodeno-store` kaldırıldı; önceki yayın arşivi yeni çalışma klasöründeki `artifacts/releases/` altına taşındı. Kullanıcının ZIP'i, açılmış marka paketi ve mevcut `tmp/` belgeleri silinmedi. ERP ve PTYS klasörlerine işlem yapılmadı.

## Güncel marka paketi teslimi

`artifacts/brand/NODENO_Tam_Marka_Paketi_Guncel_2026-10-31.zip`: 123 dosya, 19.257.079 bayt. SHA-256: `9596fc7d3f680f8ce83b532da2caaf056bf318b4fbf349b1c386b8d7fa232bfb`. Yanındaki `.zip.sha256` dosyası bütünlük kontrolü içindir. Açılmış teslim kopyası `artifacts/brand/2026-10-31/NODENO_Marka_Paketi/` dizinindedir.

Orijinal tasarım/görsel/font dosyaları ve lisansları bayt düzeyinde korunur. Güncel kopyada `BASLANGIC.txt`, renk/kurumsal bilgi JSON'u ve dosya manifesti güncellendi; `00_Guncel_Kurumsal_Bilgiler/` altına güncel JSON/TXT, dört dilli HTML iletişim kartı, vCard, güncelleme raporu ve kaynak kusurları notu eklendi. Bunlar alan adı, e-posta, telefon ve @nodenohome bilgilerini taşır.

Kaynak paketin `NODENO_Wordmark_Lacivert.svg/.png/.pdf` dosyalarında alt kenar kırpılması ve `NODENO_Sosyal_Medya_1080x1080.png` dosyasında sıfır bayt sorunu vardır. Bu dosyalar bütünlük için korunur; düzeltilmiş olarak sunulmaz. Yeni iletişim kartında sağlam `NODENO_Logo_Yatay_Lacivert.svg` kullanılır. Konsept mobilya görseli gerçek katalog ürünü olarak tanıtılmaz.

İletişim kartı 1440 ve 390 piksel genişliklerinde kontrol edildi: yerel font, sağlam yatay logo, dört dilde iletişim/sloganlar ve Arapça RTL doğrulandı; tarayıcı hatası veya yatay taşma görülmedi. Kanıt `artifacts/brand/brand-contact-qa.json`, ekran görüntüleri `artifacts/brand/brand-contact-1440.png` ve `artifacts/brand/brand-contact-390.png` içindedir. ZIP, kaynak paket ve bu teslim belgeleri web sunucusuna açık dosya olarak eklenmez.

## Yayın sınırları

İlk kontrolde görülemeyen alan adı DNS yayını, kullanıcının Turhost hosting talimatından sonra kuruldu. 31.10.2026 tarihinde nodenohome.com ve www.nodenohome.com DNS kayıtları ve güvenilir HTTPS erişimi doğrulandı. İki adres, nodenohome.com.tr hesabının `/home/nodenoho/public_html` dizinini paylaşır; .com.tr adresine yönlendirilmez. Önceki Sites bağlamaları kaldırıldı; eski Sites DNS planı uygulanmaz. Güncel kayıtlar `docs/alan-adi-kurulumu.md` içindedir.

Marka, API ve PHP yayın paketi 667 ürün ve 104 kategoriyle Turhost'a yüklendi. Canlı sürüm özeti `a0cc1a0f3db5c098b59ad12157a884705e1a0d5145a4d94832003225ee621767` değeridir. İlk canlı HTTP doğrulamasında apex/www HTTPS erişimi, API sürümü, 19 genel varlığın SHA-256 eşleşmesi ve gerçek ürün görseli başarılıdır; 10 özel/yapılandırma yolu dış erişime kapalıdır. Kanıt `artifacts/qa/live-report.json` içindedir.

Canlı tarayıcı kontrolleri dört dil × 1366/768/390 genişliklerinde başarılıdır. Yerel NODENO Sans, orijinal logo, iletişim bilgileri, gerçek ürün fotoğrafı ve katalog etkileşimleri doğrulandı; tarayıcı hatası, başarısız yanıt veya yatay taşma görülmedi. Türkçe masaüstü/mobil ve Arapça mobil ekran görüntüleri görsel olarak incelendi. Raporlar `artifacts/qa/report.json` ve `artifacts/qa/brand-report.json` içindedir.

SSL sertifikası 29.01.2027 tarihinde sona erer. AutoSSL kapalıdır; yenileme yardımcısı elle çalıştırılır ve zamanlanmış yenileme kurulmamıştır. E-posta teslimatı doğrulanmadı. Hukuki satıcı bilgileri, fiyatlar, ödeme hesabı ve yeni Drive aktarımı açık kalır; ödeme ve sipariş oluşturma kapalıdır.

## 13 Kasım 2026 — temiz vektör ve sosyal kullanım rolleri

Pikselli ekran görüntüsü izinden gelen harf konturları yerine düzgün yerel vektörler hazırlandı. Ayrık zeytin E çizgisi korundu. Profil fotoğraflarında yalnız N simgesi; kapaklarda ve ürün görseli imzasında yalnız NODENO kelime logosu kullanılır. Kapaklarda kelime logosunun altında kanonik slogan, ürün grubu açıklaması ve site adresi yer alabilir. Güncel teslim `output/brand/nodeno-home-2026-11-13/`, etkin sosyal kopyalar `output/social-media/current/` altındadır. Önceki referans arşivleri kaynak olarak korunur; eski pikselli kapaklar etkin paylaşım kaynağı değildir.

Canlı sürüm `8eb5b0a704f94bc5227111b7f144ea7683bf11dc8b417332e6c1ee507b02ae78`; 20 mobil/masaüstü tarayıcı kontrolü ve dört alan adında 48 varlık doğrulaması geçti. Kaynaklar ve müşteri/sipariş/ödeme depoları bu görsel güncellemeden etkilenmedi. Kanıtlar `artifacts/social-keywords-20261113/` altındadır.

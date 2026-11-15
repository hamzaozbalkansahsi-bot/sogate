# Tam katalog görsel güncellemesi - 1 Kasım 2026

Bu düzeltme, katalog ile sitenin son eşitlenen **168 sayfalık / 709 kayıtlı tam kataloğunu** temel alır. Eski 86 sayfalık paylaşım dosyasından yeniden üretilmemiştir. Sitedeki 667 ürün ve yalnız katalogda tutulan 42 kayıt korunur.

20 ürün paneli, web görsellerinin son temizliği öncesindeki fotoğrafları içeriyordu. Sayfa ve ürün kodu eşleştirmesinin yanında, eski fotoğrafların JPEG baytları yeniden oluşturularak her panel için tek bir yerel PDF görseliyle birebir eşleşme arandı. Studia 510 / `Ndn-CMS-510-TT-1`, 96. sayfadaki bu gruba dahildir.

PDF'nin önceki katalog bölümünde ayrıca sekiz yerel görselde marka baskısı bulundu. İlk genişletilmiş taramanın kaçırdığı eğik makyaj masası magnetleri tam sayfa görsel kontrolünde görüldü. Bu iki gerçek örnek ayrı, hash ile bağlı ek taramaya alındı; ilk taramanın kodu ve sonuçları korunmuştur.

Toplam **28 görselde 36 marka alanı** düzeltildi. Bütün fotoğrafı yeniden sıkıştırmak yerine yalnız incelenen baskı maskeleri içindeki yerel RGB örnekleri değiştirildi. Maske dışındaki pikseller, çözünürlük, yumuşak alfa maskeleri, ICC profilleri, ürün geometrisi ve sayfadaki yerleşim aynı kaldı. Ürün adı, kod, ölçü, renk, sayfa metni/konumu, bağlantılar ve dizin değişmedi.

Kaynak tam PDF'nin değişmez kopyası `artifacts/pdf-media-refresh-20261101/baseline-complete-catalogue-37a49d0b.pdf` dosyasındadır. Kaynak paylaşım PDF'si ve orijinal ürün fotoğrafları korunur. Eski paylaşım dosyası bu işlemin güncel çıktısı değildir.

Doğrulama paketi `artifacts/pdf-media-refresh-20261101/` altındadır. Kaydedilen PDF'de 168 sayfa ve 709 ürünün gövde/dizin eşleştirmesi; 1.129 yerel görsel kaydı, 11 satır içi görsel örneği, bütün metin aralıkları, sayfa kutuları, içindekiler ve bağlantılar karşılaştırıldı. 1.101 değişmeyen görsel ve 2.842 hedef dışı veri akışı aynı bulundu. İki ayrı tarama da gösterilen 1.133 farklı görselin tamamını kapsar. Son 432 aday alanın tamamı gerçek büyütülmüş görsel incelemesiyle veya yalnız baytları aynı incelenmiş kesitlerin yeniden kullanımıyla sonuçlandırıldı. Bütün sayfalar Poppler ile çizdirildi; sayfa düzeni ve değişen alanlar ayrıca incelendi.

`complete-identities.json` içindeki `mediaRevision`, temiz PDF'nin ve kanıt paketinin kimliğini taşır. Tarihsel `build_complete_catalog.py`, bu kayıt varken eski 86 sayfalık tabandan üzerine yazmaya başlamadan durur. Yeni katalog düzenlemesi bu temiz tam dosyadan başlamalı ve görsel denetimi tekrar yapılmalıdır; eski kaynak dosya otomatik geri dönüş olarak kullanılmaz.

Bu görev yerel katalog güncellemesidir. Web sitesine yeni yayın yapılmaz; mevcut ürün medyası ve 42 kaydın siteye eklenmeme kararı değişmez. Son teslim kimliği, bağımsız inceleme ve güncel test sonuçları `delivery-record.json` içinde kaydedilir.

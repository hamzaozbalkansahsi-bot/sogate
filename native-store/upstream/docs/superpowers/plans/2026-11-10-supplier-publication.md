# Alka ve Altın İş müşteri vitrini yayını

Kullanıcı tüm indirilmiş ürünlerin kontrollerini tamamlamayı, hazır grupları bekletmeden yayımlamayı istedi. Mevcut katalog, hesap, ödeme ve medya verileri korunur. Çalışma mevcut depoda, tek yürütücüyle sürer.

- [x] Kaynak metinleri, gerçek satış birimlerini, minimumları ve seçenekleri normalleştir; fiyatı olmayan ürünlerde fiyat uydurma.
- [x] Türkçe teknik içeriği koruyarak İngilizce, Rusça ve Arapça çeviri belleği oluştur; sayısal değerleri ve ürün kodlarını bağla/doğrula.
- [x] Kaynak görsellerin tamamını tara; değişen görsellerde piksel maskesi, kaynak/çıktı hashleri, yazı ve geometri kontrolü tut. Temiz kaynakları da görsel incelemeden geçir.
- [x] Altın İş ve temiz Alka ürünlerinden ilk doğrulanmış grubu güncel canlı sürümün üzerine ekle. Kaynak firma ve sipariş bağlantıları yalnız yönetimde kalır.
- [x] Alka tekrarlanan filigranlarının kalanlarını temizle ve aynı geçitten geçir. Belirsiz sonuçlara otomatik onay verme.
- [x] Seçenek gruplarını, birim/miktar hesabını, mükerrer adaylarını, dört dil/RTL'yi ve yönetici eşlemesini gerçek PHP paketiyle test et.
- [x] Her yayında güncel canlı tabanı doğrula, geri dönüş yedeği al, yeni görselleri doğrulanmış dosya olarak yükle ve kalıcı kullanıcı verisini koru.
- [x] Son PDF/katalog, eksik veya teklife bağlı fiyatlar ve yayın sayıları için bir sonuç raporu üret; yalnız doğrulanan işleri tamamlandı say.

Risk kontrolleri: adet/metre/boy/kg ayrımı, varyasyon fiyatını ana ürün aralığından türetmeme, bir görseli paylaşan farklı ölçüleri birleştirmeme, kaynak SKU'yu değiştirmeme, çeviride ölçü kaybı ve kaynak satıcı reklamı bırakmama, eşzamanlı başka yayını ezmeme.

Sonuç: 2.581 yeni ürün/varyasyon kaydı ve toplam 3.602 kayıt canlıda. 2.168 farklı yeni görsel onaylıdır. Kaynaktaki test kaydı hariç tutuldu; AK74 kulp fotoğraf yok açıklamasıyla yer alır. Canlı fiyat, kod, açıklama API, üç alan adı ve Chromium/WebKit kontrolleri geçti. Ayrıntı: docs/supplier-publication-2026-11-10.md.

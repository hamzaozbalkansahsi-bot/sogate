# Bağımsız görsel inceleme geçişleri

Bu geçişler `37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9` temel temizleme sürümünün kaynaklarını, kodunu, raporlarını ve ana manifestini değiştirmez. Üretilen dosyalar özel adaylardır; bir aday dosyasının mevcut olması yayın onayı değildir.

## Statik adaylar ve baskı kenarı düzeltmeleri

`scripts/media-review.py`, inceleme kuyruğundaki statik fotoğraflar için açık dörtgenlerle dar rötuşlar üretir. Fiziksel siyah plaka durur; kendi koyu zemininden alınan tonla yalnız baskı içi temizlenir. Kumaşta düz renk doldurma uygun değildir. Kumaş etiketi adayları `scripts/media-review-special.py` içinde aynı kaynak fotoğrafın gerçek baskısız kumaş dokusuyla hazırlanır.

`scripts/media-ink-margin.py`, temel sürümün 123 düzenlenmiş fotoğrafında küçük beyaz ve turuncu baskı kırıntılarını ayrıca kontrol eder. Çerçeve, ahşap rengi ve metal kenarları marka baskısı gibi doldurulmaz. `artifacts/media-ink-margin/candidates.json` içindeki 123 kayıt, üç özel düzeltme bulunan `manual-corrections.json` ile birlikte okunmalıdır. Aynı URL için özel düzeltmenin açıkça seçilen çıktı SHA değeri önceliklidir.

Her aday kaynak SHA, çıktı SHA, maske SHA, gerçek boyut, MIME, bayt sayısı, maske dışı piksel karşılaştırması ve sonraki OCR/şablon sonucunu taşır. Kayıpsız WebP çıktısı yeniden açılıp karşılaştırılır. Maske dışındaki çözülmüş RGB değerleri aynıdır. Alfa bulunan dosyalarda alfa kanalı ayrıca aynen korunur. Kaynak dosyaya yazılmaz.

## Bütün katalogda simge kontrolü ve görsel kararlar

`scripts/media-symbol-audit.py` iki gerçek Adore alevi referansını kaynak ve geçerli çıktı dosyalarında tarar. Animasyonlarda her gerçek kare, alfa varsa her tanımlı arka plan bileşimi kontrol edilir; aynı RGB içeriği yalnız hesaplama önbelleğini paylaşır. Kare, zamanlama ve kaynak bağları korunur. Bir şablon eşleşmesi otomatik marka kararı değildir: kumaş örgüsü, metal yansıması, kitap harfi ve işlevsel koltuk parçaları benzer desenler oluşturabilir.

`artifacts/media-symbol-audit/review-progress/build_review.py`, tarama raporlarını değiştirmeden bağımsız görsel sayfalar üretir. Eski grup indeksleri korunur, yeni gruplar sona eklenir ve her `review.json` sürümü SHA adıyla arşivlenir. Kararlar gerçek `hitId` ve rapor/dosya SHA değerleriyle bağlanır; değişebilen sayfa numaraları tek başına kanıt değildir.

Yakın kırpmanın yanında geniş bağlam ve gerektiğinde komşu animasyon kareleri de incelenir. Örneğin, c21 animasyonundaki 774/775 kırpmaları tek başına beyaz etiket ve turuncu baskı gibi görünmüştür. Komşu 22. kare, dört metal temaslı USB konnektörü olduğunu göstermiştir; bu işlevsel parça değiştirilmez. Küçük bir eşleşme metal yansıması olabilirken hemen yanında ayrı gerçek marka plakası bulunabilir. Böyle durumda eşleşme yanlış pozitif olarak kaydedilir; bağlamda bulunan gerçek baskı için ayrı temizleme adayı gerekir.

## Küçük plaka ve stilize yazı sınırı

`artifacts/media-review/tiny-plaque-candidates/` içindeki özel adaylar, Profile 3787 ailesinin sekiz galerisinin gerçek boyutta incelenmesiyle bulunan baskılardır. 1, 2, 3, 4 ve 6 numaralı galerilerde fiziksel plakalar; 0 ve 5 numaralı yaşam alanı fotoğraflarında plakasız ürün; 7 numarada ölçü çizimi görülür. 6 numaralı fotoğraftaki üç üründe üç ayrı baskı vardır. Piksel koordinatlarıyla çizilen dar iç maskeler plakanın dış biçimini ve raf kenarını korur. İlk iki kabul edilmiş aday ve sonraki üç aday ayrı makbuzlarda kalır; kabul edilmiş dosyalar üzerine yazılmaz.

Küçük plakanın düşük kontrastlı farklı görüntüsü yüksek şablon eşiğinden kaçabilir. AdoreGaming gibi bitişik ve stilize yazı da kelime OCR eşleşmesinden kaçabilir. Bu nedenle yalnız sıfır OCR veya yalnız simge eşleşmesinin yokluğu marka tamlığı iddiasına yeterli değildir. Küçük plaka geçişi, kayıtlı OCR içindeki birleşik marka denetimi, ilgili ürün ailesinin bütün galerileri ve gerçek görsel inceleme birlikte değerlendirilir.

## Son yayın kapısı

`scripts/finalize-media.py` açık çıktı SHA seçimleriyle adayları birleştirir. Varsayılan işlem plandır; birleştirme yayın kapısını açmaz. Kaynaklar, temel raporlar ve kabul makbuzları değişmez arşivde tutulur. Bütün 5129 başvuru, seçili gerçek çıktılar, kare zamanlamaları, bütün zorunlu tarama aileleri ve her eşleşmenin görsel kararı doğrulanmadan `publicationReady` açıkça `true` yapılamaz. Yerel doğrulama canlı yayın kabulünden ayrıdır.

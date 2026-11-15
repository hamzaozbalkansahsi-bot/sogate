# Katalogla ürün adı ve kodu eşleştirmesi

## Tam katalog ve güncel kapsam

Son talimatla 286 site ürünü onaylı görselleriyle `output/pdf/NODENO_Mobilya_Katalogu_2026_Tam_Katalog.pdf` dosyasına eklendi. Yeni PDF 709 ürün ve 168 sayfadır; SHA-256 değeri `37a49d0b5d76a54f48accec53f2ab25bac34525079c0dbf40510ef89531be0d1`. İlk PDF korunur. Önceki 423 kayıt, ek ürün grupları ve bütün 709 kaydı kapsayan bağlantılı dizin tamamlandı.

Sitedeki 667 ürünün tamamı `Ndn-` + değişmeyen tam kaynak kodu standardındadır. `MXY122FS` ve uzun `YTV-...` kodları da bu önekle sürer. 381 önceki PDF adı korunur; 286 ek üründe model/ölçü/renk bilgileri ve dört dil karşılıkları kullanılır. Kimlik ve ürün bağlantısı sabittir.

`python scripts/import-complete-catalog.py`, PDF'nin gerçek dizin ve ürün sayfalarını her kayıt için okuyarak `data/catalog-identities.json` dosyasını üretir. 667 site kaydı ile değerlendirme bekleyen 42 PDF kaydı hesaplanır. Rapor `output/catalog/NODENO_Katalog_Eslestirme_Tam.csv` içindedir. Eski içe aktarma yardımcısı tam eşleştirmenin üzerine yazmayı reddeder.

Kullanıcı 42 kaydı önce görmek ve değerlendirmek istedi. Bunlar PDF'de korunur; siteye eklenmeleri bekletilir. Altı farklı güncel kod adayı aynı ürün kabul edilmez. Liste `output/catalog/NODENO_Sitede_Olmayan_42_Urun.md` dosyasıdır. Güncel fiyat yöntemi [catalogue-pricing.md](catalogue-pricing.md) içindedir. 667 kimlik, 5.129 görsel referansı, kategoriler ve teknik satırlar korunur.

## Önceki 381 ürünlük eşleştirme kaydı

Kullanıcının belirlediği `output/pdf/NODENO_Mobilya_Katalogu_2026_Paylasim_Son.pdf` dosyasının 78–85. sayfalarındaki ürün dizini esas alınır. PDF 86 sayfadır; SHA-256 özeti `326f3d643638e1bbf2a69f91786f1e2f03ad559d61762a3ab4551a27bcb12238`.

423 benzersiz katalog kodunun her biri, dizinde verilen ürün sayfasındaki tam kodla ayrıca doğrulandı. Eşleştirme yalnız katalog kodunun başındaki `Ndn-` çıkarıldığında kaynak koduyla birebir aynı olmasıyla yapılır. Benzer model, renk veya ölçüden eşleştirme yapılmaz.

- Sitedeki 381 ürünün gösterilen kodu ve Türkçe adı katalogla aynı oldu. Örnek: `2393 / ADR-322-BB-1` artık `Ndn-ADR-322-BB-1 / Utila 322 Çok Amaçlı Dolap` olarak gösterilir.
- Aynı 186 özgün adın İngilizce, Rusça ve Arapça karşılıkları gözden geçirildi. Seri adları ve numaraları çevrilmez.
- Sitedeki 286 ürün katalogda bulunmadığından önceki bilgilerini korur.
- Katalogdaki 42 kodun sitede karşılığı yoktur. Bunlar benzer renkli ürünle eşlenmedi ve yeni ürün olarak eklenmedi.

Eşleştirme `data/catalog-identities.json`, gözden geçirilmiş adlar `data/catalog-name-translations.json`, ürünün yalnız gövde/kapak/üst modül olduğuna ilişkin açıklamalar `data/catalog-identity-notes.json` içindedir. Eşleşen açıklamalar yeni ad, kod, mevcut ölçü ve renk ile oluşturulur. On üründeki parça ve kapsam açıklamaları dört dilde açıkça korunur. Teknik özellik satırları aynen korunur; uyumluluk satırlarındaki eski seri/kod referansları bu adlandırma işlemiyle değiştirilmez.

Kaynak `data/catalog-source.json` ve PDF değiştirilmez. Ürün kimlikleri, URL'leri, kategori üyelikleri, görsel sırası ve onayları, teknik satırları, sepet/favori bağları sabit kalır. Fiyat ve stok oluşturulmaz; ödeme açılmaz.

`python scripts/import-catalog-identities.py` gerçek PDF'yi yeniden okur; sabit PDF özeti, dizin/ürün sayfası kodları, birebir kaynak eşleşmesi ve çeviriler doğrulanınca eşleştirmeyi ve `output/catalog/NODENO_Katalog_Eslestirme.csv` raporunu üretir. CSV üç durumu da içerir. Yeni PDF veya farklı ürün kapsamı önce yeniden incelenmelidir; bu sürüm sessizce tahmini eşleşme yapmaz.

Üretim derlemesi eşleştirmeyi zorunlu yükler ve ham kaynak dosyanın özetine bağlar. Değişmiş kaynak kodu/adı, yinelenen kimlik/kod, eksik dil, eksik kapsam veya çakışan kod yayını durdurur. `tests/catalog-identities.test.mjs` 381 ad/kod, 667 ürünün korunması, 286 değişmeyen kayıt, on parça notu ve hatalı eşleştirmelerin reddini denetler. Canlı kabul ayrıca gerçek API ve tarayıcıdan yapılır; kayıt `artifacts/catalog-pdf-audit/` altındadır.

Son mağaza sunumunda `modelName` kısa adı ve `modelId` renk ailesi kullanılır. Kanonik `name`, ürün kimliği/kodu, PDF ve fiyat geçmişi korunur. Sepet ve fiyat hesabı model ailesiyle değil seçilen renk satış koduyla yapılır. [Güncel renk düzeni](product-variants.md).

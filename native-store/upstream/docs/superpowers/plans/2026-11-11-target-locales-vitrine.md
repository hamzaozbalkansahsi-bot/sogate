# Hedef ülke dilleri ve hareketli ürün vitrini

Kapsam: Almanca, Azerbaycanca, Kazakça, Türkmence, Özbekçe, Kırgızca ve Farsça; ülke/dil/para birimi bağlantısı; kart başlığı boşlukları ve kompakt fiyat/birim/KDV sunumu; doğrulanmış ürünlerle hareketli ana sayfa.

- [x] Yeni ülkeler için tek dil kaydı, RTL ve varsayılan para birimi eşleştirmesi; İngilizceye sessiz dönüşü kaldır.
- [x] Arayüz, tam katalog açıklamaları, formlar, belgeler, hata metinleri ve SEO için kaynak/çeviri envanteri; sayılar, model adları ve ölçüler korunur.
- [x] Yerel çeviri modeliyle önbellekli çeviriler; kapsam, yer tutucu, ölçü ve script doğrulaması; kritik metinlerde örnek inceleme.
- [x] Sunucu ve istemci dil doğrulaması, ürün/teklif/ödeme/belge akışları, harita ve üst menü birlikte tamamlanır.
- [x] Kartlardaki zorunlu başlık boşluğunu kaldır; fiyat, birim ve KDV notunu okunabilir bir satır düzeninde topla.
- [x] Gerçek ürün ve yaşam alanı görselleriyle oynat/durdur, dokunma, klavye ve hareket azaltma destekli vitrin; yalnız gerçek indirim varsa kampanyalı ürün alanı.
- [x] Kaynak/katalog/medya ve davranış testleri, masaüstü/mobil ve Farsça RTL; eksik dil veya onaysız medya yayını durdurur.
- [x] Güncel canlı taban, özel veri korunarak yedekli yayın; canlı ülke geçişleri ve ekran görüntüleri; kullanım belgesi ve kabul kaydı.

Tamamlanma: 12 Kasım 2026. Son canlı sürüm `af4206253f7b99b51084f2c71d195186cfe2bfbae6850729cbd6311518a0a821`; kanıtlar `artifacts/target-locales-20261111`. 379 Node + 237 Python testi, 14 yerel tarayıcı senaryosu, dört alan adı ve 11 dilin canlı HTTP kontrolü başarılı. İki kaynak fiyat değişimi ve yeni doğrulanan bir kaynak fiyatı yalnız derleme kanıtında kaldı; mağazanın onaylı canlı katalog/fiyat dosyası aynen korundu. Kullanılmayan model ve başarısız paket dosyaları kullanıcı isteğiyle temizlendi.

Başlangıç: son canlı `689f6e49f504c40493898e96d5a138e18ef030b2fd0bfe26e9decbb21708288d`. Kaynak başlangıç kopyaları `artifacts/target-locales-20261111/baseline`. Katalogda başlangıçta doğrulanmış indirim yoktur; oran, satış adedi, stok veya teslimat vaadi üretilmez. Çeviri modeli ve araçları yayın paketine konmaz. Asıl katalog/fiyat/medya kanıtları korunur.

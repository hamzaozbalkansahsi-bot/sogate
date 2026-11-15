# Ürün ayrıntılarında bağlantı hatasından kurtarma

Kapsam: devam talimatı üzerine canlı mağazanın 11 dilde takım, sepet, toplu teklif ve giriş ekranlarını kontrol etmek; bulunan sessiz ürün ayrıntısı hatasını gidermek. Fiyat, katalog, ödeme bağlantısı ve müşteri verileri korunur.

- [x] Canlı mağazada 33 salt okunur alışveriş ekranı kontrolü.
- [x] Eski sürümde HTTP 503 sonrasında yeniden deneme düğmesinin bulunmadığını gösteren başarısız regresyon testi.
- [x] Yükleme/hata durumu, açık yeniden deneme ve istek durumunun temizlenmesi.
- [x] Kısa uyarıların 11 dilde karşılıkları, yeni önbellek sürümü ve kaynaklara bağlı çeviri kontrolü.
- [x] 379 Node + 244 Python testi, gerçek aday paketle 14 mobil/masaüstü tarayıcı kabulü ve son kod incelemesi.
- [x] Korunan ticari verilerle sınırlı canlı yayın, dört alan adında/11 dilde canlı kabul ve üç canlı tarayıcı görünümü.

Kanıt klasörü: `artifacts/storefront-followup-20261112`. Önceki canlı temel: `af4206253f7b99b51084f2c71d195186cfe2bfbae6850729cbd6311518a0a821`.

Tamamlanan canlı sürüm: `f9453eba124fed16cd7a10fef7e064d542bfe6fd257b9aa17e14feec9b9cfec2`. HTTP 503 ve geçersiz yanıtın ardından gerçek açıklama yeniden yükleniyor; miktar korunuyor. Canlı kontrollerde gerçek sipariş/tahsilat oluşturulmadı.

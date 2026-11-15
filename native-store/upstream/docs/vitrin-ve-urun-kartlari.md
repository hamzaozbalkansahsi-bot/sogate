# Ana sayfa vitrini ve ürün kartları

11 Kasım 2026 tarihinde ana sayfaya gerçek katalog ürünlerini gösteren kaydırmalı vitrin eklendi. Mutfak, antre ve genç odası sekmeleri ilgili ürünü açar. Ürün fotoğrafları, adları ve fiyatları katalog kaydından gelir. Doğrulanmamış indirim veya satış adedi gösterilmez.

Masaüstünde önceki/sonraki düğmeleri, mobilde yatay kaydırma kullanılabilir. Sekmeye basmak veya dokunarak kaydırmak otomatik geçişi durdurur. Oynat/durdur düğmesi hareketi yönetir. Sistem hareket azaltma tercihi varsa otomatik geçiş başlangıçta kapalıdır. Görünmeyen sayfada, açılır pencere açıkken veya vitrinle etkileşim sürerken geçiş yapılmaz.

Ürün kartlarında başlık için ayrılan zorunlu boş yükseklik kaldırıldı. Ürün çeşidi ve renk başlığın hemen altında gösterilir. Fiyat ve ölçü birimi aynı gruptadır; KDV bilgisi saklanmadan, mevcut genişliğe göre yanına veya altına yerleşir. Mobilde hızlı inceleme görselin üzerinde gösterilmez.

İlk görsel sürüm: `749612d42020fc5688ebb4bdbc8a12697111ec5468669715800ad271da26784b`. İlk kabul kayıtları `artifacts/vitrine-20261111` altındadır.

12 Kasım 2026 tarihli güncel canlı sürüm `af4206253f7b99b51084f2c71d195186cfe2bfbae6850729cbd6311518a0a821` ile 11 dil ve mobil fiyat satırı düzeni tamamlandı. 390 piksel Türkçe kartta fiyat, `/ m²` ve KDV notu yan yana görünür. Daha dar ekranlarda veya uzun dillerde vergi bilgisi eksilmeden gerektiğinde alt satıra geçebilir; fiyat ve ölçü birimi birlikte kalır. Fotoğraflar yüklenmeden görsel kabul verilmez.

Güncel kabul `artifacts/target-locales-20261111` altında: 379 Node, 237 Python, 14 yerel tarayıcı senaryosu ve dört alan adında canlı kontrol. Mobil Türkçe, masaüstü Almanca ve 320 piksel Farsça canlı ekran görüntüleri `live-home-*` ve `live-cards-*` dosyalarındadır. Ayrıntılar [hedef ülke dilleri belgesindedir](hedef-ulke-dilleri.md).

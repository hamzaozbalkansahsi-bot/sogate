# Ürün kodlarının gösterimi

1 Kasım 2026. Ürün kartlarında müşterinin fotoğraf, ürün adı, renk ve fiyatı daha rahat taraması için kod satırı kaldırıldı. Ana sayfa rafları, katalog, favoriler, son bakılanlar ve benzer ürünler aynı kart bileşenini kullanır. Değişiklik masaüstü ve mobilde dört dil için geçerlidir.

Ürün detayındaki küçük, kopyalanabilir kod, kodla arama ve sepet/ödeme öncesi ürün ayrımı korunur. Kaynak SKU, model/renk bağlantıları, fiyat, stok ve medya verisi değiştirilmez. Katalog kimliğindeki kanonik kod hiçbir yerden silinmez.

Kod incelemesi: ortak kart şablonundan yalnız görünür bir `bdi` satırı kaldırıldı. JavaScript giriş dosyasının önbellek anahtarı ilerletildi; değişmeyen modüllerin anahtarları korunur. Yeni API, veri değişimi, bağımlılık veya stil kuralı eklenmedi.

## Kabul

**YAYINLANDI VE CANLIDA DOĞRULANDI.** Sürüm `aceadc6f779f1c8988d99d1cbad8a48e532cfb7326c81f284fda8232edaeee60`, kaynak `d1facfa`, kabul `2026-11-01T10:50:19.213709+00:00`. 174 kaynak ve 18 dağıtım testi geçti. Gerçek pakette ve canlıda ayrı ayrı 20 genel mağaza senaryosu ile iki genişlikte kodsuz kart/kodla arama/detay kodu kontrolü geçti. Dört HTTPS alan adı, 37 varlık, 13 özel yol, üç ek koleksiyon yolu ve 15 medya örneği doğrulandı. Katalog/fiyat/medya aynı kaldı. Yedek `/home/nodenoho/nodeno-backups/20261101T104600Z-aceadc6f779f-bca990`. Ekran görüntüleri ve makine kaydı `artifacts/product-code-display/` içindedir. Önceki yayın ve diğer görevlerin çalışma ağacı değişiklikleri korunur.

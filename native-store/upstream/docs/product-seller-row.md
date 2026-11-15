# Ürün detayında satıcı satırı

1 Kasım 2026. Kullanıcının isteğiyle, kendi mağazasındaki ürün detayında tekrarlanan **Satıcı: NODENO** satırı kaldırıldı. Ortak ürün başlığı şablonu değiştiği için masaüstü, mobil ve dört dilde aynı sonuç uygulanır.

Ürün adı, küçük kopyalanabilir kod, gerçek fiyat, renk/adet ve satın alma eylemleri korunur. Veri, fiyat, SKU, görsel, hesap ve ödeme ayarı değiştirilmez. İnceleme: yalnız görünür bir paragraf kaldırıldı ve giriş dosyasının önbellek anahtarı ilerletildi; yeni API, bağımlılık veya stil eklenmedi.

## Kabul

**YAYINLANDI VE CANLIDA DOĞRULANDI.** Sürüm `f20cd2a2cfb8932728dc7f49a03a4109f32e0cb143abb0aeb59a974c8308474e`, kaynak `f3f0796`, kabul `2026-11-01T11:08:38.319744+00:00`. 174 kaynak ve 18 dağıtım testi geçti. Gerçek pakette ve canlıda ayrı ayrı 26 ürün düzeni senaryosu ile iki genişlikte satıcı satırının kaldırılması/ürün kodu/satın alma alanı kontrolü geçti. Dört HTTPS alan adı, 37 varlık, 13 özel yol, üç ek koleksiyon yolu ve 15 medya örneği doğrulandı. Katalog/fiyat/medya aynı kaldı. Yedek `/home/nodenoho/nodeno-backups/20261101T110553Z-f20cd2a2cfb8-04e281`. Ekran görüntüleri ve makine kaydı `artifacts/product-seller-row/` içindedir. Windows WebKit fiziksel iPhone testi değildir. Önceki yayınlar ve diğer görevlerin çalışma ağacı korunur.

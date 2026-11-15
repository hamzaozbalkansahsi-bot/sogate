# Sayfa odağı ve görsel koleksiyonlar

1 Kasım 2026. Kullanıcının mobil ekran görüntülerindeki başlık çerçeveleri ve ana sayfanın altındaki logo bandı düzeltildi.

## Davranış

Sayfa ve ürün bölümü geçişlerinde odak başlığa/bölüme taşınmaya devam eder. Bu, klavye ve ekran okuyucu gezinmesini korur. WebKit'in programla odaklanan, etkileşimli olmayan başlıklara çizdiği 3 px `auto` çerçeve bastırılır. Bağlantı, düğme, giriş, seçim ve diğer gerçek kontrollerin klavye odak göstergesi korunur. Genel `outline:none` kuralı eklenmez.

Ana sayfanın sonundaki tek logo/slogan bandı, **Koleksiyonları keşfedin** bölümüyle değiştirilir. Dört kart, antre düzeni, çalışma masaları, salon/TV üniteleri ve genç odası çalışma gruplarına açılır. Fotoğraflar mevcut onaylı katalogdan alınır, kartın görsel alanını doldurur. Kartlar masaüstünde dört, mobilde iki sütunda gösterilir. Ürün adetleri gerçek model sayısından hesaplanır. Her kart ilgili filtrelenmiş ürün listesini açar; geri tuşu önceki konumu korur.

Türkçe, İngilizce, Rusça ve Arapça/RTL desteklenir. Kullanıcının kendi kaydettiği **Koleksiyonlarım** alanı ayrı çalışmaya devam eder. Kaynak ürünler, fiyatlar, medya sürümü, ödeme ve sağlayıcı ayarları değiştirilmez.

## Doğrulama ve inceleme

WebKit'te eski başlığın `outlineStyle:auto`, `outlineWidth:3px` sonucu ve eski sayfada görsel koleksiyon kartı bulunmaması ayrı başarısız tarayıcı testleriyle kaydedildi. Yeni test; sayfa/bölüm odağını, görünür klavye odağını, dört gerçek fotoğrafı, dört ayrı hedefi, ürün listesini ve geri dönüşü sınar. Dört dil × iki tarayıcı × iki genişlik, toplam 16 senaryo vardır. Ürün düzeni ve genel mağaza testleri ayrıca çalıştırılır.

Kod incelemesi: yeni HTML değerleri mevcut kaçış ve yerel görsel doğrulama işlevlerini kullanır. Yeni API, dış URL, bağımlılık veya hesap yetkisi eklenmez. CSS yalnız odak ve yeni koleksiyon bileşenine aittir; eski ana stiller değiştirilmez. Görseller tembel yüklenir ve önceden belirlenmiş oranda yer tutar. Özel veriler ve orijinal medya korunur.

## Canlı kabul

**YAYINLANDI VE CANLIDA DOĞRULANDI.** Sürüm `de79083780577fa541d6ec47eae9c0aed10b4dc14991c703307beab52a41b462`, kaynak `a9262d9`, kabul `2026-11-01T10:27:47.696464+00:00`. 174 kaynak ve 18 dağıtım testi geçti. Gerçek paket ve canlıda ayrı ayrı 16 gezinme/koleksiyon, 26 ürün düzeni ve 20 genel mağaza senaryosu geçti. Dört HTTPS alan adı, 37 varlık, 13 genel özel yol, üç ek koleksiyon yolu ve 15 medya örneği doğrulandı. Katalog/fiyat ve medya sürümü önceki canlı tabanla aynıdır. Yedek `/home/nodenoho/nodeno-backups/20261101T102319Z-de7908378057-786169`. Nihai kayıt ve gerçek ekran görüntüleri `artifacts/navigation-collections/delivery-record.json` içindedir. Windows WebKit testi fiziksel iPhone testi değildir.

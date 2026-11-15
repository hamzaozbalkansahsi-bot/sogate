# Ürün sayfası düzeni incelemesi

Kapsam: masaüstü görsel hiyerarşisi, sınırlı içerik genişliği, ürün/renk/adet/satın alma yerleşimi, ilgili raf bağlantıları ve aynı akışların mobil/RTL davranışı. Yeni ödeme veya hesap servisi eklenmedi.

## Düzeltilen bulgular

- **Geniş ekranda sayfanın açılması:** genel `.wrap` taşma kuralı masaüstü üst genişlik sınırını eziyordu. Yeni ortak masaüstü sınırı 1440/1920 görünümünde aynı okunabilir ürün sütunlarını korur; dar ekranda yüzde genişlik sürer.
- **Özelliklere ulaşmak için gereksiz kaydırma:** temel bilgiler satın alma alanının hemen altına taşındı. Gerçek tarayıcı kontrolü bunların görsel alanına eşlik ettiğini doğrular.
- **İki eşit satın alma eylemi:** Sepete ekle belirgin marka vurgusunu alır; Şimdi al ikincil düğmedir. Adet, düğmelerle aynı masaüstü sırasında kalır. Telefonun sabit satın alma alanı korunur.
- **Galerinin yanlış sınıra oturması:** yeni yükseklik gerçek `.gallery-main` kapsayıcısına uygulanır; ürün fotoğrafı kırpılmadan sığdırılır. Galeri düğme/sayaç/klavye/dokunma kontrolleri gerçek pakette ve canlıda tekrar çalıştırıldı.
- **Favoride klavye odağı:** gizlenen masaüstü fotoğraf kalbi ilk eşleşme olduğu için eski odak dönüşü çalışmıyordu. Önce başarısız Space/odak testi kaydedildi. Yeni düğme aynı eylem yerinde odaklanır; görünmez elemana dönülmez.
- **İlgili raflar:** sabit bölüm kimlikleri ve mevcut odak/geçmiş mekanizması kullanılır. Yeni gezinme geçmişi gidiş ve geri dönüşte gerçek tarayıcıda sınanır.
- **Dil bütünlüğü:** dört yeni yardımcı etiket Türkçe/İngilizce/Rusça/Arapça sözlüğüne eklendi. Dört dilde aynı kaynak ürün, gerçek fiyat ve gerçek renk varyantı kullanılır.

## Güvenlik ve doğrulama

Ürün/kod/metin ve bağlantı çıktıları mevcut kaçış işlevlerini kullanır. Bölüm kimlikleri sabit, izin verilen kimliklerdir; kullanıcıdan gelen HTML veya yeni ayrıcalıklı uç nokta yoktur. Telefon/e-posta, mevcut doğrulanmış marka yapılandırmasından gelir. Kaynak görseller, fiyat hesapları, stok, yorum, kargo veya kampanya verisi değiştirilmez/üretilmez. CSP ve medya kapısı gevşetilmedi; onaylı paket ve gerçek medya kasası kullanılır. Yeni bağımlılık eklenmedi.

Değişiklikten önce 174 kaynak testi geçti. Ürün düzeni testi eski sayfada beklenen biçimde başarısız oldu; odak regresyonu için ayrı başarısız deneme kaydedildi. Tam kaynak testi derleme sonrasında tekrar çalıştırıldı; 174/174 geçti. Yerel kaynak, gerçek paket ve canlı kabul birbirinin yerine geçmez. Nihai sayılar ve sürüm [kabul kaydında](product-layout-reference.md) bulunur.

Referans, Trendyol'un açıklama işaretli resmî uluslararası mağaza örneğidir. NODENO'nun stok/yorum/ödeme verisi olmayan alanlarına referanstaki pazarlama iddiaları kopyalanmadı. Fiziksel iPhone veya gerçek ödeme/Google/Apple sağlayıcı kabulü iddia edilmez.

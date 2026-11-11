# Tasarım sistemi

Referans: kullanıcı tarafından verilen 1-Yapıştırılan-Görsel-1.jpg. Rafine serif SEXSOGATE; kapı/kemer içindeki S, küçük boynuzlar ve zarif kuyruk. Kaynak raster; yeniden çizimler birebir özgün vektör kaynağı değildir. ® ve sahte sosyal kanıt yok.

## Yön
Açık alışveriş yüzeyleri ve bordo editoryal kampanya. İmza öğesi: iki kanatlı kemer çizgileriyle çevrili kumaş etkili bordo kampanya; alışverişe açık krem bir geçit. Model fotoğrafı kullanım hakkı doğrulanmadığından referanstaki kişi görseli yayınlanmaz. Ürün fotoğrafları gelene kadar yalnız yerel, özgün ürün illüstrasyonları. Sahte indirim ve çok satan iddiası yok.

## Tokenlar
surface-base #FBF4EF; surface-card #FFFFFF; surface-soft #F3E6E8; brand-burgundy #5A0A20; brand-wine #8E0F38; brand-rose #FF2E7A; brand-rose-metal #E7B4BD; text-primary #24191D; border-soft #E6D8DC; brand-dark #0B0B0D. Merkezi kaynak `src/app/globals.css` dosyasıdır. Başlangıçtaki text-secondary #76676D, yumuşak yüzeyde normal metin kontrastını sağlamak için #716168 olarak koyulaştırıldı; özgün renk text-secondary-reference tokenında korunur. Form sınırı border-control #8D737E olarak ayrıdır. Pembe metin/CTA varsayılanı değildir; koyu bordo üzerinde açık yazı kullanılır.

`tests/unit/contrast.test.ts` gerçek CSS tokenlarını okuyarak 11 kontrol yapar: normal metin/düğme için 4,5:1, kontrol sınırı ve odak halkası için 3:1. Bordo hero/footer içindeki odak halkası açık kremdir. Bu testler tüm olası içerik veya görsellerde erişilebilirlik sertifikası değildir; tarayıcı/klavye denetimi ayrıca uygulanır.

## Tipografi ve düzen
Başlık Playfair Display, arayüz ve fiyat Montserrat; Arapça Noto Sans Arabic. Yerel woff2, font-display:swap ve lisans dosyaları. Latin genişletilmiş ve Kiril desteği; yalnız tamamlanmış tr/en yayınlanır. Metin 16px, küçük açıklama en az 12px, 1.5 satır aralığı, fiyat tabular-nums. 1200px içerik, 24px mobil kenar, 8px ritim, 44px dokunma hedefi.

## Bileşenler
Sade header, klavye menüsü, modal dialog odak hapsetme, görünen focus, semantik etiket ve satır hatası, boş durumda yönlendirme. Kartlar açık yüzey, ürün adı/fiyat/varyant/gerçek bulunabilirlik. Admin açık, işlem odaklı, aramalı tablolar. Toast yalnız tamamlanan gerçek işlemler için. Azaltılmış hareket, yatay taşmasız mobil, fiziksel yön yerine CSS logical properties.

## Değerlendirme
ui-ux-pro-max ilk otomatik sonucu genç/renkli yeşil-turuncu tema önerdi; ürün ve verilen kimlikle eşleşmediği için uygulanmadı. Kullanıcı paleti bağlayıcıdır. Ekran görüntüleri docs/progress.md içinde doğrulanır; gerçek cihaz ve saha metrikleri yapılmadan iddia edilmez.

# SEXSOGATE marka varlıkları

Son kontrol: 10 Kasım 2026. Marka yazımı **SEXSOGATE**, slogan **Tutkunu Keşfet.**

## Kaynak ve yeniden çizimin niteliği

Ekli `1-Yapıştırılan-Görsel-1.jpg` görsel referans olarak incelendi. Yeni dosyalar, bu raster referansın kemer içindeki S, küçük boynuz, kıvrılan kuyruk ve bordo/gül metalik karakterinin **geometrik yeniden yorumudur**. Referansın kaynak vektörü veya piksel düzeyinde eşleştirmesi değildir. S'nin kıvrımları, boynuz ve kuyruk bağlantısı yeniden çizildi; küçük boyutta kapı çizgileri azaltıldı. Wordmark, lisanslı Playfair Display gliflerinden düzenlenebilir SVG path geometrisine dönüştürüldü. SVG'lerde gömülü raster, script veya yabancı HTML yoktur.

Referanstaki model fotoğrafının kullanım hakları verilmediğinden yayımlanacak varlıklara alınmadı. Takipçi/yorum sayıları, doğrulama rozetleri ve tescil simgesi taşınmadı. Alan adı sahipliği ve marka tescili doğrulanmış değildir.

## Dosyalar

Tüm yollar `public/` altındadır; tarayıcıda başına `/` konularak kullanılır.

| Dosya | Kullanım / ölçü |
| --- | --- |
| `brand/logo-horizontal.svg` | Açık header, rose simge + bordo wordmark; 690×114 |
| `brand/logo-horizontal-dark.svg` | Tek renk koyu; açık yüzey |
| `brand/logo-horizontal-light.svg` | Tek renk açık; bordo yüzey |
| `brand/logo-vertical.svg` | Dikey metalik kilit; 690×420 |
| `brand/symbol.svg` | Tam metalik simge; 240×260 |
| `brand/symbol-dark.svg` / `symbol-light.svg` | Tek renk tam simge |
| `brand/favicon.svg` | İç kapı çizgileri sadeleştirilmiş 32×32 simge |
| `brand/favicon-16.png` / `favicon-32.png` | Gerçek 16/32 piksel PNG çıktıları |
| `brand/social-profile.svg` / `social-profile.png` | Düzenlenebilir SVG ve hazır 1080×1080 PNG profil |
| `brand/profile-48.png` | 48 piksel profil kontrol çıktısı |
| `brand/hero-silk.svg` | Özgün soyut bordo ipek ve kemer; 1600×900 |
| `brand/share-preview.svg` / `share-preview.png` | Düzenlenebilir SVG ve OG için hazır PNG; 1200×630 |
| `brand/social-post-light.svg` / `social-post-dark.svg` | Düzenlenebilir 1080×1350 gönderi |
| `brand/social-story-light.svg` / `social-story-dark.svg` | Düzenlenebilir 1080×1920 hikâye |
| `brand/social-cover.svg` | Düzenlenebilir 1640×624 kapak |
| `brand/social-product-dark.svg` | Ürün tanıtımı; 1080×1350, `data-field` metin alanları |
| `brand/social-collection-light.svg` | Koleksiyon tanıtımı; 1080×1350 |
| `brand/social-information-light.svg` | Rehber/bilgi kartı; 1080×1350 |

Ürün ve koleksiyon şablonlarında örnek ürün adı illüstrasyonla eşleşir; fiyat, satış hacmi, stok kıtlığı veya gerçek müşteri yorumu üretilmez. `data-field="product-title"`, `product-cta`, `collection-title`, `collection-cta`, `article-title`, `article-summary`, `article-cta` düzenleme noktalarıdır. Bunları gerçek ürün kaydıyla otomatik dolduran sosyal tasarım editörü **bu varlık tesliminin parçası olarak uygulanmış değildir**. Şablonlar vektör editöründe açılıp düzenlenebilir; paylaşım veya hesaplara gönderim yapılmadı.

## Yerel katalog illüstrasyonları

`media/atelier-01.svg` saten göz maskesi, `02` gecelik, `03` hediye kutusu, `04` saklama kesesi, `05` çift aksesuarı, `06` bakım ambalajıdır. Bunlar bu proje için hazırlanmış **yerel geliştirme illüstrasyonlarıdır**; gerçek üretici/model, lisanslı katalog fotoğrafı, malzeme belgesi veya satış ürünü beyanı değildir. Gerçek katalog açılmadan SKU'ya ait hakları doğrulanmış profesyonel fotoğraflarla değişmelidir. Sayfa dışına bir tedarikçinin resmi kopyalanmadı.

## Boyut ve boşluk

- Logonun en/boy oranını koruyun; `object-fit: contain` kullanın. SVG viewBox'ı kırpmayın.
- Yatay logonun çevresinde en az simge genişliğinin dörtte biri kadar boşluk bırakın. Dar alanda wordmark'ı sıkıştırmak yerine yalnız simgeyi kullanın.
- İç kapı çizgileri yalnız tam simgede bulunur. Favicon'da azaltılmış geometri kullanılır; 16 px çıktıda karakter okunurluğu, boynuzlar ve kuyruk görsel olarak kontrol edildi.
- Metalik efekt metin ve form alanlarına taşınmaz. Açık yüzeyde `logo-horizontal.svg`, koyu yüzeyde `logo-horizontal-light.svg` kullanılır.

## Yerel fontlar ve lisans

Resmî Google Fonts deposundan alınan orijinal değişken TTF dosyaları, glifler değiştirilmeden WOFF2 konteynerine sıkıştırıldı. Google CSS yanıtı bu ortamda beklenen WOFF2 altküme bloklarını vermedi; bu nedenle tam glif kapsamı korunmuştur. Üç WOFF2 toplamı yaklaşık **684 KB**; Arapça dosyası yalnız Arapça içerik gerçekten etkinleştiğinde yüklenmelidir. Varsayılan arayüz için iki latin/Kiril fontu kullanılır. Tüm fontları preload etmeyin. CSS bildirimleri `public/fonts/fonts.css`, kaynak ve SHA-256 kayıtları `sources.json` içindedir.

| CSS ailesi | Dosya | Ağırlık | Lisans |
| --- | --- | --- | --- |
| Playfair Display | `fonts/playfairdisplay-variable.woff2` | 400–700 | SIL OFL 1.1; `playfairdisplay-OFL.txt` |
| Montserrat | `fonts/montserrat-variable.woff2` | 400–700 | SIL OFL 1.1; `montserrat-OFL.txt` |
| Noto Sans Arabic | `fonts/notosansarabic-variable.woff2` | 400–600 | SIL OFL 1.1; `notosansarabic-OFL.txt` |

Kaynaklar: [Playfair Display](https://github.com/google/fonts/tree/main/ofl/playfairdisplay), [Montserrat](https://github.com/google/fonts/tree/main/ofl/montserrat), [Noto Sans Arabic](https://github.com/google/fonts/tree/main/ofl/notosansarabic). Tam lisans metinleri dağıtıma dahildir; kaldırılmamalıdır. Lisanslı font kullanımı marka tescili veya model fotoğrafı lisansı sağlamaz.

## Tekrar üretim ve kontrol kanıtı

`python scripts/brand-assets.py` varlıkları ve yerel fontları üretir; Python `fontTools` ve `brotli` gerekir. `node scripts/brand-preview.mjs` yerelde kurulu `sharp` ile PNG'leri ve `tmp/pdfs/` altındaki kontrol görsellerini üretir. App bağımlılıkları kurulmadan önce kullanılan bundled runtime yolu `BRAND_SHARP_PATH` ile yalnız geçici oturumda verilmiştir; kaynak kodda makineye özgü yol yoktur.

10 Kasım 2026'da: 25 SVG XML olarak ayrıştırıldı; logo, soyut hero, açık/koyu gönderi ve 16/32/48 px kontrol görselleri render edilip incelendi. Font cmap testinde `İıŞşĞğÜüÖöÇç`, `РоссияЖжЁё` ve Arapça `العربية` örneklerinde eksik glif bulunmadı. Bu glif testi tek başına gerçek Arapça sayfa yerleşimi veya şekillendirme testi değildir; RTL sayfa testi uygulama doğrulamasında ayrıca izlenir. Masaüstü/mobil tüm sayfaların marka sadakati bu dosyanın kontrolüyle tamamlandı sayılmaz.

Kullanıcı tarafından belirtilen tasarım kredisi **Hamza ÖZBALKAN**, geliştirme kredisi **PTYS Technoligess LLC** olarak kaydedilmiştir. Bu kredi, satıcı, veri sorumlusu, fatura düzenleyicisi veya ödeme hesabı sahibi tayini değildir.

## Sipariş belgesi PDF font türevleri

PDF üretiminde değişken WOFF2 altkümesi fontkit ile işlenirken hata görülmesi üzerine, aynı lisanslı Google Fonts ailelerinden fontTools ile **400 ağırlığında statik TTF örnekleri** oluşturulmuştur. PDF için iç aile adları `SexsogateBody` ve `SexsogateDisplay` olarak ayrılmıştır; bu türevler `assets/fonts/` altında sunucu tarafında kullanılır. Bunlar özgün yeni yazı tipi veya rasterden çıkarılmış vektör logo değildir. İlgili SIL OFL lisansları ve kaynak bilgileri korunmalıdır; türetilmiş font adı kaynak ailenin tescil/sahiplik iddiası olarak kullanılamaz.

`public/fonts/` altındaki web WOFF2 dosyaları bu PDF uyarlaması nedeniyle değiştirilmemiştir. Uygulamanın sipariş belgesi PDF'si **resmî e-Fatura/e-Arşiv veya mali belge değildir**; gerçek fatura sağlayıcı ve hukuki satıcı onayı ayrı gerekir. PDF metin çıkarımı ve sayfa render kanıtı ana `docs/progress.md` kaydında tutulmalıdır.

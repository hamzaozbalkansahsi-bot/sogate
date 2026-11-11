# Katalogdan sosyal tasarım hazırlama

Bu bölüm, mevcut `public/brand` şablonlarını koruyarak yayımlanmış ürün, koleksiyon ve rehber kayıtlarından **düzenlenebilir SVG** üretir. Dosya indirilir; sosyal hesaba, reklama, ürün feed’ine veya pazaryerine gönderilmez. Kategoriye ilişkin reklam ve mağaza kabulü doğrulanmış sayılmaz.

## Kullanım

1. Yönetici, katalog veya pazarlama rolündeki hesabınızla giriş yapın ve oturumun iki adımlı doğrulamasını tamamlayın. Yönetim → **Sosyal tasarım** bölümünü açın.
2. Şablon, açık krem/koyu bordo görünümü ve Türkçe/İngilizce dilini seçin. Ürün şablonunda ayrıca fiyat listesini seçin. Para listesi dil tercihinden bağımsızdır; kur dönüşümü yapılmaz.
3. Ürün ve seçeneği arayarak seçin. Stok kodu, seçenek adı ve fiyat aynı varyant kaydından okunur. Seçilen para biriminde yürürlükte pozitif fiyat yoksa o seçenek gösterilmez. Eksik İngilizce ürün açıklaması/adı veya seçenek adı tamamlanmalıdır.
4. Koleksiyon ve rehber için o dilde **yayımdaki** kaydı seçin. Geleceğe zamanlanmış sürüm erkenden kullanılmaz; taslaklar dışa aktarılmaz.
5. **Tasarımı hazırla** düğmesiyle dosyayı oluşturun. Önizlemeyi inceleyin; **Düzenlenebilir SVG indir** aynı dosyayı indirir. Seçimler değiştiğinde önceki önizleme kaldırılır.
6. Vektör düzenleyicinizde SVG’yi açarak metin, konum ve renkleri düzenleyebilirsiniz. SVG metinleri `<text>/<tspan>`, logo ise ayrı vektör geometrisidir. Font desteği düzenleyiciye göre değişir; aynı lisanslı fontların ayrıca kurulması gerekebilir. Dış düzenlemede fiyat, kullanım hakkı ve zorunlu bilgiler yeniden incelenmelidir.

| Şablon | Boyut | Kaynak |
| --- | --- | --- |
| Gönderi | 1080 × 1350 | Gerçek ürün + aynı ürünün seçeneği + güncel fiyat |
| Hikâye | 1080 × 1920 | Gerçek ürün + aynı ürünün seçeneği + güncel fiyat |
| Profil | 1080 × 1080 | Mevcut marka simgesi + onaylı slogan |
| Kapak | 1640 × 624 | Mevcut yatay logo + onaylı slogan |
| Ürün | 1080 × 1350 | Gerçek ürün + aynı ürünün seçeneği + güncel fiyat |
| Koleksiyon | 1080 × 1350 | Yürürlükteki koleksiyon sürümü + uygun gerçek katalog üyeliği |
| Bilgi ve rehber | 1080 × 1350 | Yürürlükteki rehber başlığı ve kısa alıntısı |

Yedi şablonun açık ve koyu sürümü vardır. Ürün ve gönderi aynı ürün odaklı kompozisyonu paylaşır. Koleksiyona fiyat veya indirim uydurulmaz. Rehber gövdesi sınırlı uzunlukta, düz metin olarak yer alır; tam içerik yerine geçmez. Başlık ve seçenek metni ölçülerek satırlanır; okunabilir en küçük boyutta dahi sığmayan kayıt için hata döner. Kaynak kaydını kısaltıp yeniden hazırlayın.

## Kaynak, hak ve lisans

Ürün görseli yalnız `/uploads/<uuid>.webp` biçimindeki **mevcut medya kaydından** alınır. `media_assets.rights_reference` dolu olmalı; nesne boyutu ve SHA-256 değeri kayıtla eşleşmelidir. Bu kontrol, kaydedilen hak belgesinin hukuken yeterli olduğunu kendiliğinden onaylamaz; hak kaynağını işletme doğrulamalıdır. PNG/JPEG/WebP medya yükleme akışı SVG kabul etmez; güvenli WebP çıktısı üretir. Dış URL, dosya yolu veya ham SVG bu editöre girilemez; sunucu dış görsel adresine istek atmaz.

Yerel örnek ürünlerde `/media/atelier-01.svg`–`06.svg` yalnız geliştirme/test ortamında kullanılabilir. Bunlar özgün temsili illüstrasyondur, gerçek ürün fotoğrafı değildir. Böyle bir kaynakla oluşturulan dosyanın `fixture` işareti ve yönetim önizlemesindeki açıklaması korunur. Production bu ürünleri listeden dışlar ve dosya üretimini reddeder. Örnek işaretini kaldırmak gerçek katalog doğrulaması yerine geçmez.

Logo, kullanıcının raster marka referansının geometrik yeniden yorumudur; özgün kaynak vektörünün kusursuz teslimi olarak sunulmaz. Logoya raster ürün fotoğrafı gömülmesi onu vektör fotoğraf yapmaz. Fotoğraf `<image>` olarak, vektör logo ayrı geometri olarak saklanır. Kaynak ayrımı SVG’nin metadata alanında korunur. Tescil simgesi eklenmez. Önceki kaynak ve lisans açıklamaları [brand-assets.md](brand-assets.md) içinde geçerliliğini korur.

Sunucu, `assets/fonts/SexsogateBody-Regular.ttf` ve `SexsogateDisplay-Regular.ttf` dosyalarını SVG içine gömer. Bunlar aynı lisanslı Montserrat/Playfair Display ailesinden statik TTF türevleridir; SIL OFL 1.1 metinleri SVG metadata’sına dahil edilir. Fontlar ve lisanslar silinmemelidir. Arapça sosyal metin üretimi bu editörde yayımlanmamıştır; TR/EN ile sınırlıdır.

SVG metadata’sı kaynak kimliği/sürümü, aynı stok kodu ve fiyat snapshot’ı, oluşturulma zamanı, görsel hak referansı ve hash içerir. Dosya oluşturulduktan sonraki katalog/fiyat değişikliği önce indirilmiş dosyayı değiştirmez. İndirme anında işletmenin güncel fiyatını ayrıca kontrol edin. Sunucu dosyayı herkese açık bir klasöre kaydetmez; indirme işlemi kaynak kimliği ve hash ile `audit_log` tablosuna yazılır. Müşteri, sepet, arama veya sipariş verisi bu şablonlara aktarılmaz.

## Teknik sınırlar ve saklama

- `GET /api/admin/social`: `view=products|variants|collections|information`, `locale`, `currency`, `q`, `page`, gerekiyorsa `productId`. 25 kayıtlık sunucu sayfalaması vardır.
- `POST /api/admin/social`: şablona göre ürün/seçenek, koleksiyon anahtarı veya rehber bağlantı adı; dil ve görünüm. Sunucu fiyat/görsel/metin/rol alanı kabul etmez. Gövde sınırı 16 KiB’dir. Yanıt özel/no-store SVG indirmesidir.
- `StorageProvider.get(key, options?)` mevcut `Buffer` dönüşünü korur. Varsayılan 8 MiB/5 saniye; açık seçenekle en fazla 16 MiB/30 saniye. Yeni ortam değişkeni veya ikinci depolama yapılandırması yoktur.
- Yerel okumada güvenli anahtar, gerçek kök altında çözülmüş yol, dosya türü/boyutu ve sınırlı fd okuması denetlenir. Dosya okuma sırasında değişirse reddedilir. S3’te Range isteği tek kontrol değildir: gerçek akış byte sayısı sayılır, limitte bağlantı iptal edilir; süre sınırı başlık ve gövdeyi kapsar.
- Medya en fazla 8 MiB, SVG çıktısı en fazla 16 MiB’dir. Local storage production’da açılmaz; gerçek özel S3 ayarları mevcut depolama ayarları üzerinden girilir. Gerçek S3 hesabıyla uçtan uca doğrulama bu yerel kanıtın kapsamına girmez.
- Önizleme tarayıcıdaki özel Blob URL’sidir. Yeni seçim/istek geldiğinde eski indirme ve Blob iptal edilir; bileşen kapanınca kaynaklar bırakılır. Paylaşılan yönetim oturumunun kullanıcı/rol/MFA anahtarı bileşen state’ini de ayırır. İndirilen dosyaları işletmenin saklama politikasına göre yönetin.

## Doğrulama kaydı — 11 Kasım 2026

Çalıştırılan yeni kontroller:

```powershell
npx vitest run tests/unit/social-assets.test.ts tests/unit/storage-bounds.test.ts
npx tsx --env-file=.env.local scripts/social-integration.ts
npx eslint src/server/social-assets.ts src/server/providers/storage.ts src/server/providers/contracts.ts src/app/api/admin/social/route.ts src/components/admin-social.tsx scripts/social-integration.ts tests/unit/social-assets.test.ts tests/unit/storage-bounds.test.ts tests/e2e/social.spec.ts
```

İlk modül yokluğu ve önceki sınırsız okuma davranışı RED olarak görüldü; yeni sınırlı okuma ve renderer ile düzeltildi. Son hedefli sonuç **24 birim kontrolü PASS**: 13 depolama + 11 sosyal varlık. Küçük dosyanın gereksiz 8 MiB tampon ayırması ayrıca RED→GREEN düzeltildi. İzole, adı rastgele `*_social_test` ile biten yerel DB’de **13 entegrasyon kontrolü PASS**; 001–024 migration zinciri uygulandı ve test DB’si/medya klasörü temizlendi. Gerçek WebP hak/hash kaydı, aynı SKU ve fiyat, eksik/süresi geçmiş kur, yanlış varyant, yetki/MFA, yayın sürümü, 14 XML şablonu ve production örnek veri engeli doğrulandı. S3 stream limit/timeout kontrolleri hermetik SDK/stream testidir; gerçek bulut bağlantısı kanıtı değildir.

`tests/e2e/social.spec.ts` Chromium/WebKit **2/2 PASS**: gerçek medya yüklemesi, MFA, Türkçe TRY / İngilizce EUR için aynı SKU indirmesi, Axe kontrolü ve 390 px taşma kontrolü doğrulandı. `docs/screenshots/social-{chromium,webkit}-mobile.png` dosyaları üretildi. Son optimize tam koşu **94/94 E2E (47+47)**, 246 birim ve 232 DB kontrolüyle birlikte geçti; kanonik sonuç [test-evidence.md](test-evidence.md) ve [progress.md](progress.md) içindedir. Bu güncel kayıt önceki 72 E2E checkpoint’inden ayrıdır. Gerçek cihaz, gerçek S3 bağlantısı ve bağımsız vektör düzenleyici kabulü yapılmadı.

Sayfalama düzeltmesi: 26 eşleşen kaynak için üçüncü boş sayfada toplam 0 dönmesi izole DB’de RED görüldü (`products: boş sayfa toplamı`, 0 ≠ 26). Kaynak ve toplam tek SQL snapshot’ından çözülecek biçimde düzeltildi. Ürün, varyant, koleksiyon ve rehber türlerinin tamamında sayfa 1→25 kayıt, sayfa 2→1 kayıt, sayfa 3→0 kayıt ve her sayfada toplam 26 GREEN. Son entegrasyon 13/13 PASS; açık şablon ekranındaki Axe WCAG 2.2 AA denetimi de son iki motor E2E koşusunda geçti. Otomatik denetim tek başına tüm erişilebilirlik gereksinimlerinin sertifikası değildir.

# Set tanımı, düzenleme ve satış uygunluğu

## Yönetim ekranı

Yönetim → Varyantlar bölümünde üst stok kodunu bulun, **Düzenle → Set bileşenlerini düzenle** seçin. Yönetici veya katalog rolü ve doğrulanmış MFA gerekir. Depo ve finans set tanımını API üzerinden okuyabilir; tanım veya önizleme yazamaz. Maliyetler bu yanıtlara dahil edilmez.

1. Fiziksel ürün adını veya stok kodunu arayın. Arama sunucuda 25 kayıtla sayfalanır. Seçilen üst SKU ve mevcut set üst kodları sonuçlara girmez.
2. Her sette kullanılacak fiziksel SKU'ları ve adetleri belirleyin. Bir tanımda en çok 20 ayrı SKU, her SKU için 1–99 adet desteklenir. Aynı SKU iki kez, setin kendisi, arşiv SKU veya iç içe set kabul edilmez. Fiziksel bileşen lot takipli olabilir.
3. **Değişikliği önizle** ile sunucunun eski/yeni adet farklarını ve mevcut stokla hazırlanabilir set sayısını inceleyin. Önizleme fiziksel stok ayırmaz; fiyat, onay, hareket veya geçmiş kaydı yazmaz. Checkout stok ve belge şartlarını tekrar doğrular.
4. En az beş karakterlik gerekçe yazıp kaydedin. Kayıt yeni tanım sürümü, aktör, gerekçe ve eski/yeni SKU kimliği/ad/adet snapshot'ını saklar. Ürün yeniden **İncelemede** olur; üst SKU'nun ülke, belge ve taşıyıcı kabulü geçersizleştirilir. Fiziksel bileşenlerin onayları değiştirilmez. Yeniden onay ve yayın, ayrı uygunluk akışında yapılır.

Fiziksel veya karantina stoğu bulunan üst SKU set koduna dönüştürülemez. Üst kod lot takipliyse, başka setin bileşeniyse veya etkin ödeme rezervasyonu/süresi dolmamış ödeme siparişi varsa değişiklik kapalıdır. Bu ekran stok silmez, oluşturmaz veya geçmiş stok için lot tahmin etmez. Boş bileşen tanımıyla seti fiziksel SKU'ya dönüştürme desteklenmez.

Geçmiş siparişte normal fiziksel ürün veya satılmış setin fiziksel bileşeni olan SKU, güncel stoğu sıfır olsa bile set üst koduna dönüştürülemez. Yeni bir üst SKU oluşturun. Bu kural, eski siparişin iadesinin sonradan mantıksal set koduna fiziksel stok yazmasını önler; mevcut gerçek setlerin tanımını değiştirme ve eski bileşen snapshot’ına göre iade davranışı korunur.

Set üst koduna **Depo ve stok** üzerinden giriş/ayarlama/karantina/açma veya satın alma mal kabulü yapılamaz; fiziksel bileşen kodlarını kullanın. Karma mal kabulündeki tek set üst kodu bütün işlemi reddeder; diğer satırın stoğu, kabul adedi veya hareketi kısmen yazılmaz. Eski/elle bozulmuş kayıtta set üst koduna yönelen fiziksel iade de sessizce kabul edilmez; yetkili operasyon stok ve sipariş kayıtlarını araştırmalıdır.

İki yetkilinin aynı sürümü değiştirmesi durumunda yalnız bir kayıt başarılı olur. Diğeri güncel tanımı yükleyip taslağını yeniden hazırlamalıdır; **Güncel tanımı yükle ve taslağı sıfırla** mevcut yerel seçimi temizler. İlk eski tanım sürüm 0 kabul edilir; geçmişe dönük aktör veya gerekçe uydurulmaz. Ekran son 10 tanım değişikliğini gösterir, tüm sürümler veritabanında korunur. Geçmiş sipariş bileşen snapshot'ları ve rezervasyon tahsisleri tanım değiştiğinde yeniden yazılmaz.

## Teknik kayıt ve eşzamanlılık

022 migration, mevcut `bundle_components` kaynağının yanına `variants.bundle_version` ve `bundle_changes` ekler; ikinci stok kaynağı kurmaz. GET `variants?view=bundle&id=…` mevcut tanım/sürüm/blokaj/geçmişi, `view=bundleCandidates` fiziksel SKU aramasını döndürür. POST `bundlePreview` ve `bundle` ayrı, sıkı şemalardır. Kaydetme `{id,expectedVersion,components:[{variantId,quantity}],reason}` ister. Eski ilk oluşturma çağrılarında atlanan sürüm 0 sayılır; sonraki sürümde atlamak eski sürüm çatışmasıdır.

Tanım değişiklikleri ortak transaction advisory kilidiyle sıralanır; böylece eşzamanlı A→B/B→A setleri oluşmaz. Ürün ve varyant satırları sabit sırada, eski kaldırılan bileşenler de dahil kilitlenir. Başlamış checkout önce tamamlanırsa düzenleyici yeni rezervasyonu görür ve değişikliği reddeder. Var olan transaction deadlock/serialization tekrar politikası korunur. Bu kilitler eşzamanlı ödeme kontrolünü veya stok rezervasyonunu devre dışı bırakmaz.

Fiziksel yazım aynı advisory kilidin paylaşımlı sürümünü, ardından aynı ürün → SKU → bakiye sırasını kullanır. Set dönüşümü ile stok girişi veya satın alma kabulü yarışırsa yalnız biri başarılı olabilir. Bu sınır yalnız ekran seçicisine dayanmaz; API ve iade stok servisi de aynı guard’dan geçer.

## Satış uygunluğu

Set üst SKU'sunun yayın ve ülke onayı, içindeki fiziksel SKU'ların ülke ve belge onayının yerine geçmez. Checkout her bileşenin etkinliğini, hedef ülkeye onayını ve isteniyorsa aynı SKU/ülke/belge türüne bağlı incelenmiş, yürürlükte belge kaydını doğrular. Boş belge referansı, başka SKU'nun belgesi, yanlış ülke, gelecekte başlayacak veya süresi geçmiş belge kabul edilmez. Teknik SKU değişikliğiyle iptal edilen inceleme yeniden yapılmalıdır.

Fiziksel bileşen yalnız set içinde satılabilir; kendi ürününün vitrinde ayrıca **Yayında** olması zorunlu değildir. Taslak bir bileşen etkin SKU, ülke onayı ve gerekli belgelerle setin parçası olabilir. Bu karar tek başına ülke veya belge onayı oluşturmaz. Gerçek satış ortamında örnek/fixture bileşeni kullanılamaz. İç içe setler desteklenmediği için ödeme başlamadan reddedilir.

Tüm sepet setlerinin fiziksel kayıtları tek sorguda ürün/SKU sırasıyla paylaşılmış satır kilidine alınır. Ülke ve eşleşen belge satırları da transaction süresince paylaşılmış kilitle korunur. Mevcut deadlock/serialization tekrar kuralı devam eder. Stok rezervasyonu, lot/FEFO tahsisi, para hesabı ve değişmez sipariş bileşen snapshot'ı aynı kaynaklardan beslenir.

Belge doğrulaması kayıtların kapsamını ve yürürlük tarihini kontrol eder; üreticinin belgesini dış bir sistemde doğrulamış gibi davranmaz. İnceleme ve gerçek belge kabulü yetkili operasyonun sorumluluğundadır. Fiziksel ambalaj içinde doğru SKU/lot bulunduğunun barkodla doğrulanması ayrı depo işidir.

İzole doğrulama: `npx tsx --env-file=.env.local scripts/operations-integration.ts`. Yeni belge senaryosu düzeltme öncesinde, ülke onayı olmayan bileşenle başarılı checkout oluştuğu için **Missing expected rejection** ile RED verdi. Test ayrıca geçerli belgesi olan taslak bileşenin set içinde kullanılmasını, inaktif/belgesi eksik bileşenin reddini, iç içe set sınırını ve production ortam benzetiminde gizli fixture bileşeninin reddini kapsar. Ortam benzetimi yalnız rastgele oluşturulup silinen yerel operations_test veritabanındadır; gerçek ödeme sağlayıcısına veya production verisine bağlanmaz.

## Yeni fazın yerel test kanıtı

11 Kasım 2026: yeni `scripts/bundle-integration.ts` ilk çalışmada yayındaki ürünün tanım değişiminden sonra hâlâ `published` kalmasını yakaladı: beklenen `review`, gerçekleşen `published` (RED). Son inceleme ayrıca mevcut set üst koduna doğrudan stok girişinin kabul edildiğini **Missing expected rejection** ile gösterdi. Ortak guard sonrası benzersiz oluşturulup silinen yerel `sexsogate_<rastgele>_bundle_test` veritabanında **16/16** geçti. Testler sürüm yarışı, kaldırılan eski bileşende checkout kilidi, immutable eski sipariş, yazmayan önizleme, rol/MFA, stok ve satın alma kabulü yarışları, karma kabul rollback’i, fiziksel satış geçmişi ve eski tutarsız iade reddini kapsar. Ana geliştirme veya ortak test DB'si sıfırlanmaz.

- `npx tsx --env-file=.env.local scripts/bundle-integration.ts` — 16/16 PASS; 001–024 migration'ları izole DB'de uygulandı.
- `npx vitest run tests/unit/bundle-management.test.ts` — modül yokken RED, adet farkı hesabı eklendikten sonra 5/5 PASS.
- `npx tsx --env-file=.env.local scripts/operations-integration.ts` — 16/16 PASS; ön onaylar gerçek `complianceAction`, adres profili yalnız izole fixture helper'ı ile hazırlanır.
- `npx tsx --env-file=.env.local scripts/lot-integration.ts` — 11/11 PASS; lot ve bileşen stok davranışları korunur.
- Hedefli ESLint ve global `npx tsc --noEmit` — PASS.

`tests/e2e/bundles.spec.ts` katalog/MFA oturumunda arama → bileşen/adet → önizleme → sürümlü kayıt, yeniden açma, depo yazma reddi ve 390/masaüstü görüntülerini doğruladı: Chromium ve WebKit **2/2 PASS**. İlk koşudaki tekrarlanan fixture hareket referansı düzeltildi; kabul testinin rol veya stok sınırı gevşetilmedi. Son optimize toplu koşu **94/94 E2E (47 Chromium + 47 WebKit)** geçti; güncel 246 birim/232 DB ve build kanıtı [test-evidence.md](test-evidence.md), kapsam ve açık dış koşullar [progress.md](progress.md) içindedir. `admin-bundles-desktop-{chromium,webkit}.png` ve `admin-bundles-mobile-{chromium,webkit}.png` ekranları `docs/screenshots/` altında üretildi. Bu sonuç fiziksel depo veya gerçek cihaz kabulü değildir.

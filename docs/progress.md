# İlerleme — 11 Kasım 2026

Tamamen yerel geliştirme. Kullanıcının 29 bölümlük kapsamının tamamı bitmedi; canlı satış kapalı. Production/staging dağıtımı, gerçek tahsilat veya DNS/alan adı işlemi yapılmadı. Kullanıcı aynı GitHub deposunun eski içeriğini SEXSOGATE kaynaklarıyla değiştirmeyi sonradan açıkça yetkilendirdi; kaynak aktarımı ve CI durumu aşağıdaki Git kaydında izlenir.

## Son test edilmiş sürüm — 09:19 İstanbul

022–025, ödeme öncesi sunucu toplamı ve oturum yarış düzeltmesi dahil **246/246 birim, 232/232 PostgreSQL kontrolü ve 94/94 E2E PASS**. Birim testler 29 dosya; DB kontrolleri 19 komut; E2E Chromium 47 + WebKit 47, tek worker, retry 0, 4,7 dakika. Lint, strict typecheck, uyarısız optimize build ve `verify:artifact` PASS. Tam bağımlılık taraması `npm audit --audit-level=low`: sıfır bilinen açık.

AES256-GCM yedeği gerçek yeni izole DB'ye geri yüklendi; **33 tablo count/hash** ve ayrı örnek medya SHA256 eşleşti. Bazı tablolar kaynak test DB'sinde boş; gerçek staging/tüm medya veya üretim RPO/RTO tatbikatı değildir.

Kaynak/varlık/test/config **320 dosya** manifesti SHA256 `53849dbe305cd6c0466dfded498e4de0c6f1e4265cdede1344720fe53866a0bc`; `.local/owner-snapshot.json`. Manifestteki dosyalar son koşudan sonra yeniden karşılaştırıldı, değişiklik yok. Belgeler manifest dışında güncellenir. Bu kayıt Git commit'i değildir. Komutlar, loglar ve başarısız koşuların geçmişi [test-evidence.md](test-evidence.md) içindedir. Önceki 06:37 çekirdek, 07:34 modül ve 08:46 ilk PO/quote sonuçları tarihsel kontrol noktalarıdır.

## Bu devam çalışmasında kapanan akışlar

- **Ödeme öncesi gerçek toplam:** ürün, kupon, kargo, dahil vergi ve teslimat koşulu aynı sunucu hesaplayıcısından gelir. Teklif yazmasız, sepete/sahibe bağlı ve beş dakika imzalıdır. Checkout kilit altında yeniden hesaplar; koşul değişince yeni özet gösterilir ve müşterinin tekrar tıklaması gerekir. Teklif rezervasyon veya fiyat garantisi değildir; yeni teklif aynı idempotency anahtarında ikinci sipariş üretmez.
- **Oturum ve geciken yanıtlar:** eski `/api/session` yanıtının yeni hesabı ekrana geri yazdığı gerçek RED yakalandı. Oturum/sepet istek nesilleri ve iptal koruması, checkout/test ödeme ekranından ayrıldıktan sonraki eski yönlendirmelerle birlikte iki tarayıcıda geçti. İstek iptali sunucuda oluşmuş siparişi iptal etmiş sayılmaz.
- **025 lotlu satın alma kabulü:** aynı PO'nun kısmi kalan miktarı birden fazla üretici lotuna bölünerek alınır. Normal ve lotlu SKU tek transaction'da, kaynak belgesi ve karantina ayrımıyla işlenir. Yanlış lot toplamı, fazla kabul, set üst SKU'suna stok ve mükerrer hareket engellenir. Sonucu belirsiz ağ yanıtında aynı anahtar/gövde güvenle tekrar edilir. Lot ekranı ilişkili satın alma/teslim belgesi kaynaklarını maliyetsiz, yetkili ve sayfalı gösterir. Fiziksel paket-lot eşleştirmesi bu kabulün parçası değildir.

- **İnceleme sonrası sahiplik düzeltmesi:** sepet okuma, değiştirme/silme ve checkout sahibi verinin okunduğu snapshot/kilit içinde doğrular. Hesap birleşmesinin anonimleştirdiği eski sepetten geçmiş üye siparişinin tekrar yanıtı ayrıca sipariş sahibiyle korunur. Gerçek eski-kod RED'lerinden sonra boundary10 ve quote13 kontrolleri geçti; yeni genel94 bu kaynağı da kapsar.
- **Belirsiz kabul sonucu:** bozuk/boş JSON ve gerekli sonuç alanları eksik başarılı yanıt başarı sayılmaz. Önizleme/UUID aynı denemede korunur. Gerçek sunucu200 sonrasında ağ kesilmesi, kesik JSON, eksik kimlik ve eksik sonuç üretilerek aynı anahtarlı beş denemede tek kabul/stok yazımı doğrulandı. Genel API hata ayrıntıları sızdırılmaz; eski idempotent tekrar sözleşmesi korunur.

Kullanım: [checkout](checkout-guide.md), [lotlu satın alma](purchase-lot-guide.md), [yönetim](admin-guide.md). Yeni masaüstü/mobil görüntüler [görsel inceleme](visual-review.md) içinde bağlıdır.

İlk quote 90 koşusu 80 PASS/10 FAIL; sonraki 88 PASS/2 FAIL oldu. Seçiciler, gerçek checkbox taşması ve yalnız özel fixture ülkesinin eksik vergi kaydı düzeltildi. Son iki WebKit hatası gerçek giriş HTTP429 penceresiydi; test resmi retry başlığını sınırlı bekler, uygulama kotası değişmedi. Eski session yarışına ait ayrı gerçek RED korunur. Önce hedef14/14 ve ilk genel94/94 geçti; son inceleme sonrası yeni246/232 kontrolleri ve yeni genel94/94 ayrıca çalıştırıldı. Başarısız koşular PASS sayılmadı.

## Çalışan modüller ve sınırlar

- Katalog/varyant → stok hareketi → ayrı uygunluk incelemesi/yayın → sunucu sepeti → teklif → rezervasyon → imzalı yerel test ödeme → değişmez sipariş/takip/PDF/JSON. Son adet, set bileşeni/lot, kupon, karma vergi, tekrar/yanlış bildirim ve geç başarı istisnaları test edildi. Gerçek katalog veya tahsilat yok.
- 018 FEFO/lot/son kullanım/recall; 019 gruplu CSV/XLSX inceleme ve güvenli import; 020 yapısal TR/EN CMS/sürüm/zamanlı yayın; 021 ayrı veri sorumlusu, ülke SLA/saklama ve manuel doğrulanmış ilgili kişi başvurusu.
- 022 sürümlü set önizleme/editör, eski düzenlemede 409, değişmez geçmiş bileşenler. Logical üst SKU'ya mal kabulü/karantina yazımı ve fiziksel geçmişli SKU'nun sete dönüşümü kapalı; stok↔set yarışları test edildi.
- 023 katalog belge/teknik alanları, yönetici belge/ülke uygunluk onayı/iptali, kaynak incelemesiyle üretici iletişimi. Yayın onay üretmez; onay aktörü olmayan eski boolean kabul edilmez. Public teknik DTO açık whitelist'tir. Ham belge yükleme/antivirüs veya gerçek hukuk kabulü değildir.
- 024 onaylı/sürümlü ülke adres alanları; checkout ve hesap ortak doğrular. Sahiplikli CRUD, geciken GET koruması, eski sipariş adres/profil snapshot'ı ve production fixture reddi test edildi. Profil ülkeye satış açmaz.
- Gerçek ürün/SKU/fiyat/CMS kaydından yedi açık/koyu sosyal SVG ailesi indirilir. Font/logo lisansı, raster fotoğraf açıklaması ve sınırlı dosya okuma vardır. Sosyal hesapta yayın veya reklam yapılmaz.
- Oturuma bağlı MFA/roller ve private/no-store; manuel gerçek takipli kısmi sevk, barkod/SKU toplama-paketleme, iade/karantina/QC ve dış fatura referansı var. Sipariş PDF'si resmî fatura değildir.
- TR/EN vitrin ve yayın/dil/para ayrımı, SSR/slug/canonical/hreflang/sitemap/SEO editörü ve raporu. Fuzzy arama, genel crawler ve gerçek Search Console/Bing hesabı yok. de/ru/ar yayında değil, RTL altyapısı test içindir. Slug editörü mevcut ASCII sınırındadır; özgün Türkçe ad/içerik korunur.

## Ortam ve devam komutları

Bu klasörde bağımsız `codex/local-commerce` Git deposu var; başka işletmenin ortamı bağlanmadı. PostgreSQL 18.6 yalnız `.local` ve 127.0.0.1:55432; development/test DB ayrı. Ana development şeması 001–006, 010–025 uygulanmış durumda. Uygulanmış migration baytlarını değiştirmeyin. Docker Desktop başlangıç hatası nedeniyle OS ayarları değiştirilmedi; Compose config geçmesi çalışan container kanıtı değildir.

**Çalışan optimize önizleme:** http://127.0.0.1:3000; yönetim http://127.0.0.1:3000/yonetim. Health: `{"status":"ok","sales":"closed"}`. Son standalone oturum kimliği 3739; terminal kapanmışsa yeniden başlatma:

```powershell
node scripts/native-postgres.mjs
node --env-file=.env.local scripts/start.mjs --port 3000
```

Worker/scheduler sürekli çalışan servis olarak kurulmadı. Ayrı terminalde `npm run worker` ve `npx tsx --env-file=.env.local scripts/scheduler.ts`; önce yapılandırma rehberini okuyun. Gerçek SMTP teslimatı veya Stripe bağlantısı doğrulanmadı. `.env.local` ve `.local/admin-access.txt` Git dışında; değerlerini yazdırmayın. Yönetici yerelde MFA kurmalıdır.

Yeni kaynak değişirse kendi standalone sunucusunu Ctrl+C ile durdurun; `npm run build`, `npm run verify:artifact`, sunucuyu başlatıp tek `npm run test:e2e` runner'ı kullanın. Windows çalışan standalone klasörünü kilitler. `npm run dev` Webpack ve `.next-local`, optimize build Turbopack ve `.next` kullanır. DB komutlarının tam sırası README/test kanıtındadır; aynı test DB'sini sıfırlayan işlemleri paralel çalıştırmayın.

Başlangıçtaki boş projede marka JPG ve 12 sayfalık PDF incelendi; rapor iddiaları kanıt sayılmadı. SVG'ler referansın düzenlenebilir yorumudur; birebir kaynak vektör veya gerçek katalog fotoğrafı değildir. NDECOR başlık biçimi karşılaştırması açık; bu nedenle başka depo açılmadı.

Kullanıcı 11 Kasım 2026'da `https://github.com/hamzaozbalkansahsi-bot/sogate` adresini verdi. Bağlı GitHub hesabı aynı kullanıcı adı ve 240751698 hesap numarası ile doğrulandı. Yalnız bu depoda Git yazarı `hamzaozbalkansahsi-bot`, GitHub'ın ID tabanlı noreply adresi olarak ayarlandı; özel e-posta yeni commitlere eklenmez. `origin` verilen adrese bağlandı ve yalnız okuma amaçlı fetch yapıldı.

**GitHub kaynak aktarımı:** kullanıcı eski deponun dosyalarının yeni çalışmayla değiştirilmesini açıkça istedi. Önceki `origin/main` yalnız Lyvora README'si içeriyordu (`85aaa5c691fea53a803729f6f1cba140f14f9d21`); eski etiketler aynı commit'e bağlıdır. Doğrulanmış tam Git bundle ve refs yedeği `.local/repository-backups` altında alındı. SEXSOGATE dosya ağacı korunup eski main yalnız Git geçmişine bağlanarak normal push hazırlanır; başka işletmenin uygulama/veritabanı/ortam verisi alınmaz. Force-push veya canlı dağıtım yoktur. Tam kayıt [git-workflow.md](git-workflow.md).

Aktarım hazırlığından önce 320 çalışma kaynağı son test manifestiyle birebir aynıydı; yalnız AGENTS.md depo/push yetkisi ve Git belgeleri bu aşamada güncellendi. Uygulama kaynakları ve iş kuralları değişmedi. Git index kontrolünde yalnız 138 metin dosyasının standart CRLF→LF normalizasyonu var; migration bayt değişimi 0, beklenmeyen içerik farkı 0. Yerel secret/DB/backup/test raporları dışarıda. Ayrıntılı Git durumu ve commit sonucu [git-workflow.md](git-workflow.md) içinde kaydedilir.

## Açık işler ve dış engeller

1. **Sıradaki bağımsız kod işi:** fiziksel paket-lot doğrulaması. Önce `src/server/commerce/staff-orders.ts`, `src/server/commerce/lots.ts`, `scripts/staff-orders-integration.ts` ve `staff-order-guide.md` okunmalı; mevcut sipariş tahsislerini tekrar stok düşmeden doğrulayan başarısız regresyon hazırlanmalı. Lotlu PO kabulünü yeniden yazmak veya geçmiş migration'ı değiştirmek gerekmiyor. Lotu bilinmeyen iadenin yeniden atfı/imhası ve çok depo/transfer ayrıca açık.
2. Veri sınıfına göre otomatik saklama/silme/anonimleştirme/taşınabilirlik motoru ve dış sistem/backup etkisi; mevcut privacy manuel kanıtlı süreçtir.
3. Tedarikçi XML/API inceleme, gerçek kanal SKU/fiyat/stok/sipariş/mutabakat; fuzzy arama, kalan CMS yönetişimi ve genel SEO crawler. Kur kaynağı/tampon/yuvarlama operasyonu tamamlanmadı.
4. Gerçek satıcı/vergi/adres/banka/destek ve veri sorumlusu, gerçek SKU/stok/görsel hakları/belgeler, onaylı hukuk/vergi/ülke kuralları sağlanmadı. Geliştirici/tasarımcı kredisi bunları doldurmaz.
5. Stripe işletme/hesap ülkesi/kategori kabulü ve gerçek sandbox anahtarları; SMTP/S3, taşıyıcı/desi tarifesi/e-Fatura ve pazaryeri erişimi bekliyor. Adaptör kodu gerçek bağlantı değildir; desteklenmeyen operasyon başarı gösterilmez.
6. Gerçek cihaz/ekran okuyucu, saha p75 Core Web Vitals, tam medya yedeği/uzak şifreli saklama, gerçek staging restore, container çalıştırma ve remote CI tamamlanmadı. Alan adı/DNS/marka tescili varsayılmadı.

[Modül durum tablosu](module-status.md) yerel çalışan kapsam ve gerçek ortam engellerini ayırır. Kaynak devamı [implementation-plan.md](implementation-plan.md), entegrasyon durumu [integrations.md](integrations.md), canlı koşulları [launch-checklist.md](launch-checklist.md). Tüm kapsam bitmiş değildir.

Sıradaki kod inceleme komutu (mevcut çalışan sürümü değiştirmez):

```powershell
rg -n "pick|pack|lot|reservation" src/server/commerce/staff-orders.ts src/server/commerce/lots.ts scripts/staff-orders-integration.ts
```

Son bütünlük özeti `.local/owner-validation-summary.json`: 320 kaynak dosyasında değişen/ekstra dosya yok; 246 birim, 19 komutta232DB ve94E2E loglardan tekrar sayıldı. Belge yerel bağlantıları/UTF-8 ve kaynak diff whitespace kontrolü geçti; orijinal OFL lisansları whitespace dönüşümünün dışında tutuldu.

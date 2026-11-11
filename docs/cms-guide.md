# Vitrin ve içerik yönetimi

Yerel yönetim adresi: `/yonetim/content`. Yönetici ve pazarlama rolü, oturuma bağlı güncel iki adımlı doğrulama ile erişir. Katalog, depo, finans ve müşteri rolleri yeni CMS taslaklarını veya önizlemelerini okuyamaz. Hukuk metinleri bu ekranın kapsamına girmez; `/yonetim/legal` sürüm ve onay akışı korunur.

## Vitrin alanları

İçerik alanından “Kampanya, koleksiyon ve bağlantılar”ı ve ardından dili seçin. Türkçe ve İngilizce ayrı kaydedilir; bir dilin taslağı diğer dilde yayımlanmaz.

1. “Yeni vitrin içeriği” ile ana kampanya, menü, alt bilgi veya koleksiyon seçin.
2. Kampanyada üst başlık, başlık, vurgulu satır, açıklama ve düğmeyi doldurun. Görsel isteğe bağlıdır.
3. Menüde görünen metin ve mağaza bağlantılarını; alt bilgide açıklamayı ve en fazla iki bağlantı sütununu düzenleyin. Gizlilik/çerez kontrolleri ile `Geliştirici: PTYS Technoligess LLC` ve `Tasarım: Hamza ÖZBALKAN` kredileri içerikten bağımsız korunur. Bunlar hukuki satıcı bilgileri değildir.
4. Koleksiyona benzersiz bağlantı adı, başlık, açıklama ve görsel ekleyin. Ürünleri ad veya stok koduyla arayıp seçin. “Ana sayfada göster” seçeneği ana sayfadaki koleksiyon kartlarında kullanılmasını sağlar. Yayındaki koleksiyon `/koleksiyonlar?collection=<bağlantı-adı>` adresinde gerçek ürün ve seçili para birimi fiyatlarıyla açılır. Ürünler 24'er sayfalanır.
5. “Taslak sürümü kaydet” mevcut yayını değiştirmez. “Önizle” yalnız yetkili oturumda açılır; önizleme bağlantısı müşteriye taslak erişimi sağlamaz.
6. “Yayınla” ile hemen yayınlayın veya yerel tarih/saat girin. Tarih sunucuya UTC olarak gönderilir. Gelecekteki sürüm zamanı gelene kadar mevcut yayın gösterilir. Ayrı bir tarayıcının açık kalması gerekmez; sunucu her okumada zamanı çözer.

Görsel önce medya kütüphanesinde hak kaynağıyla yüklenmelidir. Yazılım hak referansının kaydedilmiş olmasını denetler; lisansın kapsamı ve geçerliliğini sorumlu kişi ayrıca doğrulamalıdır. Yalnız doğrulanmış yerel WebP yüklemesi veya projenin güvenilir marka varlıkları kabul edilir. Altı `/media/atelier-0*.svg` illüstrasyonu yalnız “Yerel örnek içerik” işaretli geliştirme/test kaydında kullanılabilir. Bu işaret daha sonra değiştirilemez ve production'da yayın engellenir. Taslak, gelecek tarihli veya yayından kaldırılmış bir CMS sürümü yüklenmiş medyayı anonim erişime açmaz.

Koleksiyon yayınında bütün üyelerin ilgili dilde yayımlanmış, etkin varyantlı ve etkin kategorili olması denetlenir. Sonradan kapanan veya bu dilde eksilen ürün genel koleksiyondan düşer. Ürünlerin tamamı uygunluğunu yitirirse koleksiyon gösterilmez. Bu kontrol ülke, stok, ödeme veya checkout onaylarını değiştirmez.

## Rehber ve sık sorulan sorular

“Rehber ve sık sorulan sorular” alanında “Yeni rehber veya soru”yu açın. Rehberde başlık ve metni; soruda başlık alanına soruyu, metne yanıtı yazın. Ayrı paragrafta `## ` ile başlayan satırlar güvenli başlık olarak gösterilir. HTML, SVG, JavaScript veya çalıştırılabilir içerik kabul edilmez.

Taslak kaydından sonra “Sürümler ve yayın”ı açın; kaydı önizleyip hemen veya zamanlı yayımlayın. Eski sürüm “Yeni sürüme kopyala” ile yeniden taslak yapılabilir. Yayındaki sürümün metni yerinde değiştirilmez. Rehberler `/rehber` listesinde ve `/rehber/<bağlantı-adı>` sayfasında; sorular `/sss` ekranında görünür. Sorular rehber listesine karışmaz. “Yayından kaldır” geçmişi silmez, önceki bir yayını kendiliğinden geri getirmez ve planlanmış sayfa yayınlarını iptal eder.

Rehber ve SSS için ikinci bir içerik tablosu oluşturulmadı. Mevcut `content_pages` ve `content_revisions` tek kaynaktır. Eski `/api/admin/content` yazıcısı aynı revision kaynağıyla uyumludur; taslağı yayından kaldırmak için yeni ekranın açık arşivleme işlemi kullanılmalıdır. `/api/content` aynı `{page}` veya `{pages}` yanıtını yayımlanmaya uygun sürümlerden üretir. Genel liste mevcut sözleşmeyle en son 30 içerikle sınırlıdır.

## Varsayılan davranış ve sınırlar

Ana sayfa, menü ve footer yayımlanmış CMS snapshot’ıyla ilk sunucu HTML yanıtında oluşturulur. Aynı istekte React.cache ile aynı snapshot paylaşılır; istekler arası kalıcı CMS önbelleği yoktur. Yayımlanmış yapısal kayıt yoksa mevcut yazılı marka kimliği, navigasyon, kategori kartları ve footer kullanılır. Ana kampanyada öncelik: yapısal kampanya → eski `home-campaign` içeriği → marka metni. Yayımlanmış CMS sorusu yoksa mevcut temel kullanım yanıtları gösterilir; ilk yayımlanmış soru o dilin SSS listesini CMS'den besler. Ana sayfa rehber bağlantıları gerçek yayınlardan gelir; veri yoksa boş durum gösterilir. Örnek müşteri yorumu, satış sayısı veya kıtlık mesajı üretilmez.

Önizleme yapısal içeriği güvenli React bileşenleriyle gösterir; tüm sayfa, cihaz, görsel hakları veya hukuk onayı simülasyonu değildir. Formlar Türkçedir; müşteri yayını için TR/EN metni editör ayrı girer. Otomatik çeviri, zengin HTML editörü, harici görsel indirme, çok aşamalı editör onay zinciri ve yayın bildirim servisi eklenmedi. Geleceğe en fazla bir yıllık yayın planlanabilir.

## Teknik girişler ve doğrulama

- `GET /api/cms?locale=tr&currency=TRY`: yalnız yürürlükteki genel bölgeler ve koleksiyonlar.
- `GET /api/cms?collection=<anahtar>&locale=en&currency=EUR&page=1`: koleksiyon ve gerçek fiyat projection'ı.
- `GET /api/cms?view=admin|history|preview`: MFA ve içerik yazma yetkisi gerektirir; `history/preview` için `id`, sayfa sürümleri için `pageContent=1`.
- `POST /api/cms`: `draft`, `publish`, `archive`, `pageDraft`, `pagePublish`, `pageArchive` işlemleri. Mutasyonlar aynı origin ve sınırlı UTF-8 JSON gövdesi gerektirir. Her değişiklik işlem kaydına yazılır.
- `migrations/020_content_regions.sql`: migration checksum'u sabittir; root tarafından yerel geliştirme veritabanına uygulandı.

11 Kasım 2026 son hedef kanıtları:

| Komut / kontrol | Gerçek sonuç |
| --- | --- |
| `npx vitest run tests/unit/cms.test.ts` | 14/14 PASS; bozuk URL 400 regression'ı RED→GREEN |
| `npx tsx --env-file=.env.local scripts/cms-integration.ts` | Benzersiz yeni yerel veritabanında 16/16 PASS; bulunmayan archive ID 404, boş DB seed ve 1002 kayıtlı SEO indeksi regression'ları RED→GREEN |
| `npx playwright test tests/e2e/cms.spec.ts --output=.local/cms-ui-final-html --reporter=line` | Chromium/WebKit 2/2 PASS, 30,4 saniye, retry 0 |
| `npx playwright test tests/e2e/cms.spec.ts --grep 'guide HTML' --output=.local/cms-seo-article-final --reporter=line` | Chromium/WebKit 2/2 PASS, 4,4 saniye; gerçek SSR metin/metaveri, gelecek→yürürlük, 404 ve yalnız mevcut çeviri alternatifleri |
| `npx tsx --env-file=.env.local scripts/seo-integration.ts` | İzole yeni veritabanında 8/8 PASS; zamanlanan rehbere yönlendirme ve arşiv/örnek veri engeli dahil |
| Önceki tam CMS UI hedefi | İki motor 2/2 PASS, 33,7 saniye; ilk HTML öğe kontrolleri ardından sıkılaştırıldı |
| CMS kaynaklarının hedefli ESLint kontrolü | PASS, sıfır hata/uyarı |
| `npm run typecheck` | PASS, strict TypeScript sıfır hata |

Entegrasyon; yetki/MFA, taslak gizliliği, dil bağımsızlığı, zamanlama, eşzamanlı sürüm, ürün/görsel uygunluğu, eski yazıcı, production örnek veri engeli, medya erişimi ve arşiv davranışını doğrular. Veritabanı test sonunda silinir; geliştirme kataloğu bu scriptle değiştirilmez.

UI hedefi gerçek pazarlama MFA oturumu ve formlarla koleksiyon taslağı → yetkili önizleme → yayın → müşteri ürün listesi; yapılandırılmış kampanya/menü/footer'ın gerçek `<h1>`, `<a>` ve `<p>` ilk HTML öğelerinde bulunması; SSS formu/sürümü/yayını ile rehber listesi ve detayını doğrular. Anonim taslak önizlemesi 401'dir, SSS rehber listesine karışmaz, mobil sayfa yatay taşmaz ve sabit marka kredileri korunur. Test yalnız kendi aktörü ve `fixture=true` kayıtlarını temizler; mevcut İngilizce marka bölgeleri varsa onları değiştirmek yerine güvenli biçimde atlanır. Son koşuda atlama yoktur.

Önceki başarısız denemeler saklandı: aktif geliştirmede Fast Refresh formu sıfırladı; select için exact `getByLabel` option metinlerine takıldı ve rol/combobox seçicisine düzeltildi. Gerçek ürün seçimi ise checkbox'ı seçim anında DOM'dan kaldırıyordu; seçili checkbox yerinde korunarak klavye odağı ve gerçek checked durumu düzeltildi. Son hedef bu akışı iki motorda geçti. Bunlar tüm projenin yeni toplu build/E2E onayı sayılmaz; kök ilerleme kaydındaki son toplu sonuç ayrıca esas alınır.

## Rehber SEO ve yeni kurulum

Rehber detayında başlık ve gövde ilk HTML'de sunulur. Canonical ve OG aynı yürürlükteki sürümden gelir. Yayımlanmamış, eksik veya arşivlenmiş rehber 404 döner. TR/EN alternatif yalnız aynı bağlantı adında gerçekten yayımlanmış diğer dil kaydı varsa eklenir; eksik çeviriye bağlantı üretilmez. Tek İngilizce kayıtta varsayılan dil bağlantısı da mevcut İngilizce yola gider.

SEO indeksi `publicContentIndex()` ile aynı etkin revision seçimini kullanır; 30 veya 10000 kayıt sınırında sessizce kesilmez. Örnek kayıtlar, SSS/kampanya türleri ve ayrılmış sayfa adları rehber sitemap'ine girmez. Gerçek içerik sitemap'leri 1000 kayıtlık `/sitemaps/content`, `/sitemaps/content-1` gibi parçalara bölünür. Gelecekteki yayın erken listelenmez; zamanı gelen yayın eski `content_pages` görünümü taslak olsa da görünür. Yönlendirme hedefi de aynı resolver ile kontrol edilir.

Kurulumun içerik yükleyicisi başlangıç `content_revisions` kaydını, doğru içerik türünü ve `fixture=true` işaretini birlikte oluşturur. Tekrar yükleme mevcut metni veya sürümü ezmez. Genel seed girişindeki ortam, veritabanı adı ve stok kısıtları değiştirilmedi. Yeni boş veritabanı ve tekrar yükleme ayrı entegrasyon kontrolünde doğrulandı.

Son CMS/SEO dört hedefli koşuda ana CMS iki motor 2/2 geçti; yeni makale testi ham HTML'deki `hrefLang` yazımını büyük/küçük harfe duyarlı aradığı için iki hata verdi. Gerçek `<link>` öğeleri standart HTML attribute eşlemesiyle ayrıştırılacak şekilde test düzeltildi; URL değerleri sıkı eşitlikle doğrulanmaya devam etti. Son makale hedefi iki motor 2/2 geçti. Uygulama metaverisi bu seçici düzeltmesi için değiştirilmedi; önceki hata çıktıları `.local/cms-seo-final` altında korunur. Tek yeni toplu proje koşusu ve optimize derleme bu hedef kanıtlarından ayrıdır.

Son küçük HTTP dil kontrolü: `GET /api/cms?locale=en&currency=BAD`, `locale=en&page=Infinity` ve `locale=tr&currency=BAD` için 3/3 gerçek 400 yanıtı doğrulandı. İngilizce genel hata metni İngilizcedir, Türkçe metin korunur; tümünde `Cache-Control: private, no-store` vardır. Yönetim hataları Türkçe kalır. Bu düzenlemeden sonra hedefli ESLint ve tüm proje strict typecheck sıfır hatayla geçti; uygulama, script ve test kaynakları donduruldu.

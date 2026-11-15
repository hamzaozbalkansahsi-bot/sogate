# Çalışma Akışı

- Tüm tasarım, geliştirme ve değişiklikler önce yerel ortamda yapılır.
- 15 Kasım kaynak katalog kararı: xShopum1.022/46, Liona544/75, Sistina628/49 ürün/kategori kaydı özel PHP incelemesine alınır; kamu fiyatı bayi maliyeti, gözlenen bulunabilirlik depo stoğu değildir. Kanonik durum `docs/php-supplier-research.md`, kullanım `docs/php-shopping-guide.md`. Sosyal medya bağlantıları yalnız ikon; görünür ad/ok/tooltip yok, erişilebilir adlar ve azaltılmış hareket korunur.
- 14 Kasım son logo/menü kararı: simge yazının üstünde ortalı kalır; footer logo bütünü ortalı, header logo bütünü soldadır. Sosyal bağlantılar ikonlu, hover/odak hareketli ve azaltılmış hareket tercihine uyumludur. Mobil Kategoriler doğrudan görselli tam sayfayı açar; alt menü Ana sayfa/Kategoriler/Favorilerim/Sepetim/Hesabım sırasındadır. xShopum, Liona, Sistina kapsamı `docs/php-supplier-research.md` içinde gerçek erişim durumlarıyla izlenir.
- 14 Kasım son kapsam: kullanıcı NODENO'nun bütün menü/kategori/ürün/sepet/blog/öneri yapısını SEXOGATE'e uyarlamayı istedi. PHP müşteri katmanı için `docs/php-nodeno-parity.md` kabul matrisidir. NODENO yalnız okunur; işletme/müşteri/ürün/secret verisi ve sektöre özgü vergisi taşınmaz. İletişimde şimdilik yalnız mail gösterilir. Hijyen iade metni, açılmış koruyucu unsur istisnası ve ayıplı ürün haklarını ayrı korur.
- Değişiklikler yerelde çalıştırılır, incelenir ve ilgili testlerle doğrulanır.
- Canlıya geçiş, yerel çalışma ve doğrulamalar tamamlandıktan sonra ayrı bir aşama olarak ele alınır.

- Marka adı SEXSOGATE, sloganı “Tutkunu Keşfet.”; başka işletmenin ortamına bağlanma.
- Başlangıçta docs/product-spec.md, docs/architecture.md ve docs/progress.md oku. Tasarım için docs/design-system.md esas alınır.
- İlerlemeyi ve gerçek test sonuçlarını docs/progress.md içinde güncelle. Çalıştırılmayan kontrolü başarılı sayma.
- Para ve stok kararları sunucuda, işlemsel olarak alınır. İstemciden fiyat veya yetki kabul etme.
- Yerel örnek veri production'a taşınamaz. Eksik ülke, ödeme, belge ve hukuk onaylarında satış kapalıdır.
- Gizli değerleri yazdırma veya Git'e ekleme. Kullanıcının 11 Kasım 2026 tarihli açık talebiyle yalnız `hamzaozbalkansahsi-bot/sogate` deposundaki eski dosyaların SEXSOGATE kaynaklarıyla değiştirilmesi ve normal Git push yetkilidir. Önce yerel yedek ve kontroller; force-push/geçmiş silme, canlı dağıtım, gerçek tahsilat ve DNS değişikliği yetkili değildir.
- Geliştirici gösterimi PTYS Technoligess LLC, tasarım Hamza ÖZBALKAN; satıcı/veri sorumlusu bunlardan çıkarılamaz. Elle yazılmış yorum destekleyen kaynaklarda kullanıcı standardı Türkçe dosya başlığı kullan; üretilmiş/vendor dosyalara dokunma.
- Stripe öncelikli adaptördür; işletme, hesap ülkesi, kategori kabulü ve gerçek test olmadan canlı açılmaz. Hukuk sürümleri sipariş snapshot'ında korunur. Ana kapsamın güncel sürümü 29 bölümlük kullanıcı talimatıdır.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

<!-- BEGIN PHP_SOURCE_API_20261115 -->
- PHP kaynak API kuralları `docs/php-supplier-api-guide.md`: yalnız tam/başarılı snapshot incelemede görünür; yarım/başarısız katalog eskisini ezmez. Kamu fiyatı bayi maliyeti, bulunabilirlik fiziksel depo stoğu değildir. Hosting HTTP401/403 alırsa otomatik bağlantı kapanır; yerel dosya yüklemesi sunucudan başarılı API bağlantısı sayılmaz. Liona/Sistina onaylı bayi erişimi olmadan bağlı gösterilemez.
<!-- END PHP_SOURCE_API_20261115 -->

<!-- BEGIN NATIVE_DIRECT_COPY_20261115 -->
- 15 Kasım son kullanıcı kararı: önce NODENO uygulaması bütün kaynak/modülleriyle doğrudan alınır, yeniden/parçalı arayüz uyarlaması yapılmaz. Yeni temel `native-store/upstream`, marka/renk/font/varlık katmanı `native-store/theme`; kanonik kayıt `docs/native-store-transfer.md`. Kaynak çekirdek byte olarak korunur; sır/müşteri/sipariş/NODENO ticari kataloğu taşınmaz. Yerel Native PHP/SQLite kopyası ile mevcut MySQL `/test` yayını ayrı durumdur; eski yayın henüz değiştirilmedi.
- Kaynak testlerindeki üç açık sahte Stripe sabiti için tek istisna `scripts/native_fixture_safety.py` ve manifest'teki özgün/güvenli hash çiftleridir; özgün52 PHP/61 JS uygulama motoru değiştirilmez. Bu istisnayı kaldırıp ham sabitleri Git'e geri koyma.
<!-- END NATIVE_DIRECT_COPY_20261115 -->

<!-- BEGIN NATIVE_TEST_ADULT_RELEASE_20261115 -->
## 15 Kasım Native PHP yayın kararı

- Güncel test runtime `native-store/` içindeki korunmuş NODENO kaynağının SEXOGATE derlemesidir; yalnız `https://sexogate.com/test`. Ayrıntı `docs/native-test-deployment.md`; son kanıt `docs/native-deployment-report.json` ve `docs/progress.md`.
- NODENO katalog/ürün/müşteri/işletme verisi taşınmaz. Mobilya, kurulum, haritalı karşılama veya başka işletmenin satıcı unvanı SEXOGATE müşteri ekranına konmaz. 18+ marka bildirimi ve onaydan sonra üyelik istemeyen gezinti korunur; ülke bazlı gerçek yaş kabulü ayrıca gerekir.
- Sunucuda Node çalıştırılmaz. PHP/SQLite özel state web kökü dışındadır; legacy MySQL verisi korunur. Gerçek tahsilat teknik olarak kapalıdır; boş katalog medya/sağlayıcı kabulü geçmiş sayılmaz. Ana site/DNS/gerçek tahsilat bu yayın yetkisinin dışındadır.
<!-- END NATIVE_TEST_ADULT_RELEASE_20261115 -->

# Kasım kampanyası ve kolay iade merkezi

16 Kasım 2026. Hedef mevcut PHP/SQLite mağazası ve yalnız `/test`; ana hazırlanıyor sayfası ve korunan `native-store/upstream` değiştirilmez. Kullanıcı NODENO’daki Büyük Kasım kampanyasını ve iade/finans/fatura akışını istedi. NODENO salt okunur incelendi; başka işletmenin ürün, müşteri, fiyat geçmişi, şirket veya sırları aktarılmaz.

## Kararlar

- Güncel fiyat kararı: kaynak indirimsiz tutar +%15 **nihai satış fiyatıdır**. Önceki NODENO %20 Kasım indirimi yeni ürünlere eklenmez. Kaynak mağazanın indirim/ücretsiz kargo geçmişi veya taahhüdü taşınmaz. Gerçek tahsilat kapalıdır.
- İade başvurusu ve kargo gönderi kodu ayrı kimliklerdir. SGR numarası sistemde anında ve tekil oluşturulur; taşıyıcının gerçek kodu entegrasyon veya denetlenmiş manuel kayıtla eklenir. SGR kodu tek başına müşteri verisine erişim sağlamaz.
- Sipariş sahibi oturum veya güvenli sipariş bağlantısı gerekir. Ürün/beden/renk, adet ve ödenmiş fiyat sipariş snapshot’ından alınır. Kısmi/tekrarlı iadeler toplam satılmış adedi ve tahsilatı aşamaz. Mükerrer istek aynı sonucu döndürür.
- Başvuru → değerlendirme → gönderim → kabul/karantina → kontrol → ödeme iadesi → mali belge düzeltmesi ayrı izlenir. Ayıplı/yanlış/eksik ürün hakkı ile cayma ve açılmış hijyen koruyucusu ayrı değerlendirilir. Fotoğraf veya açıklama, cayma bildirimini zorunlu koşula bağlamaz.
- Müşteri ürünü sağlam ve uygun paketleyip belirtilen taşıyıcıya zamanında teslim eder; bu, kargo ücretinin otomatik müşteriye ait olması veya bütün hasarlardan kusursuz sorumluluğu anlamına gelmez. Siparişteki ülke/politika sürümü korunur. Belirsiz tarih/ülke, otomatik hak kaybı yerine incelemeye gider.
- Mali kayıtlar silinmez: kabulde iade karşılığı ve satış düzeltmesi; sağlayıcı teyidinde nakit çıkışı. Vergi düzeltmesi resmi belge teyidine kadar bekler. Kargo/komisyon gibi gerçekleşmiş giderler otomatik sıfırlanmaz; belgeli geri kazanım ayrı kayıttır. Katkı, net işletme kârı diye gösterilmez.
- Faturanın tamamı kısmi iadede iptal edilmez. İptal, iade faturası/düzeltme belgesi veya uzman incelemesi türüne/süresine/sağlayıcısına göre ayrı iş oluşturur. Harici sağlayıcı teyidi olmadan “iptal edildi” denmez. Sipariş PDF’si resmî fatura değildir.

## Resmî kaynak incelemesi

Kontrol: 16–17 Kasım 2026. Aşağıdaki akışlar referanstır; başka mağazanın hizmeti, süresi veya taşıyıcı anlaşması SEXOGATE’e otomatik uygulanmaz.

- [Trendyol iade](https://www.trendyol.com/s/trendyol-iade): siparişten ürün/adet/neden, iade yöntemi ve kod, paket teslimi ve takip. Çok satıcılı mağaza/puan alanı alınmaz.
- [Hepsiburada kolay iade](https://www.hepsiburada.com/kolay-iade): siparişten talep, uygun teslim yöntemi, kargo kodu ve talebin durumu. Adresten alma/teslim noktası yalnız gerçek hizmet bağlantısıyla sunulur.
- [Ticaret Bakanlığı indirim düzenlemesi](https://ab.ticaret.gov.tr/haberler/ticaret-bakanligindan-indirimli-satis-reklamlarinda-seffafligi-artiracak-yeni-duzenleme): Önceki fiyat dönemi güncel resmî mevzuat ve işletme/hukuk incelemesiyle doğrulanır; sayfanın17Kasım ayrıntı okuması zaman aşımı verdi. Onaylı süre varsayılmaz ve kaynak işletmenin referans fiyatı SEXOGATE geçmişi yapılmaz. Yeni+%15 ürünlerde indirim/önceki fiyat iddiası yoktur.
- [24 Mayıs 2025 değişikliği](https://www.resmigazete.gov.tr/eskiler/2025/05/20250524-2.htm), 1 Ocak 2026 yürürlük: arama kaydında doğrulandı; doğrudan sayfa okuması zaman aşımı verdi. Kargo masrafı için bu eksik okuma tek başına hukuk onayı sayılmaz. Güncel konsolide kaynak ve işletme/hukuk incelemesi tamamlanmadan ülke politikası onaylanmaz.
- [GİB e-Arşiv iptal/itiraz kılavuzu](https://ebelge.gib.gov.tr/dosyalar/kilavuzlar/e-Arsiv_Uygulamalari_Iptal_Ihtar_Itiraz_Bildirim_Kilavuzu_V.1.0.pdf) ve [teknik kılavuz 1.18](https://ebelge.gib.gov.tr/dosyalar/kilavuzlar/e-Arsiv_Teknik_Kilavuzu_V.1.18.pdf): talep, onay ve resmî belge sonucu ayrıdır. Belgeler arası iade ilişkisi gerçek numara/UUID ile kaydedilir; mevzuat ve muhasebeci incelemesi yerine geçmez.

## Kullanım ve gerçek durum

Müşteri: `/test/?page=return-center&lang=tr` veya `lang=en`; footer bağlantısından açılır. Üyeye yalnız kendi ödenmiş siparişleri sunulur; misafir güvenli sipariş bağlantısını kullanır. Ürün ve adet → neden → sunucuda hesaplanmış tutar → SGR kodu/takip. İlk başvuru için fotoğraf, ek açık rıza veya zorunlu paketleme kutusu yoktur. Paketleme ve taşıyıcıya teslim yükümlülüğü açıklanır; kanuni haklar korunur.

Yönetim: `/test/yonetim/iade-merkezi`; mevcut MFA oturumu ve API rolü gerekir. Depo operasyonu tutar/komisyon/mali işleri alamaz. Gerçek taşıyıcı kodu, teslim/karantina, kontrol tutanağı, finans kabulü ve harici mali belge teyidi ayrı işlemlerdir. Kod gerçek kargo etiketi değildir. Mali belgede operatör teyidi API’de de zorunludur. Yerel örneklerin kodları gerçek taşıyıcı veya GİB işlemi değildir.

Çekirdek `native-store/returns`; additive migration `sg-returns-001.sql`, resmî Stripe PHP23.0.0 SDK ve kilitli Composer. Kurulum: `composer install --working-dir=native-store/returns --no-dev --no-interaction --no-plugins --no-scripts --prefer-dist`. Sunucuda Node yok; Python/Node yalnız yerel derleme ve testte kullanılır. Vendor özel pakete alınır, web köküne veya Git’e konmaz. Yeni ödeme kapalıyken geçmiş ödeme iadesi prensipte ayrı yetkilendirilir; bu `/test` dağıtımında gerçek sağlayıcı teknik olarak **daima kapalıdır**. SDK timeout/lease ve kalıcı idempotency anahtarı vardır.

Önceki tarihsel yerel doğrulama `263190861527a68ab3ed24ab`: kaynak korunumu771 dosya; paket2.492 dosya,82 JavaScript modülü. Derleme/syntax geçti. İzole PHP48 kontrol; aynı testin upstream primitives ile `--source` koşusu48; mevcut JavaScript38 regresyon kontrolü geçti. Gerçek HTTPS üzerinden Chromium ve WebKit: kısmi iade/önizleme, mükerrerlik, iptal/geçmiş, beden/renk, CSRF/Origin, oturum ve sipariş sahipliği, depo/finans sınırı, MFA, karantina, harici mali teyit ayrımı, test siparişinin canlı rapordan dışlanması, TR/EN, RTL dil seçimi, private/no-store/noindex ve360/390/430/768/1440px geçti. Kanıt `native-returns-local-results.json`; ekranlar `screenshots/native-store-returns-local/`. Fiziksel iPhone ve tam WCAG denetimi değildir.

İlk derleme Node dosya kopyasında kapandı; Python kontrollü kopyasıyla düzeldi. HTTP testleri alt yol eki ve eşzamanlı oturum/CSRF başlangıç hatalarını yakaladı, giderildi; ilk başarısız loglar Git dışı korunur. Sonraki iki hata testin varsaydığı düğme seçicisi/iptal metniydi; gerçek arayüze göre düzeltildi. Test kapısı kapatılmadı.

**17 Kasım ilk test yayını — tarihsel:** `b5e7e6913484a652360a2097` yalnız `https://sexogate.com/test` üzerinde yayımlandı; daha sonra yerini aşağıdaki güncel sürüm aldı. Bu ilk sürümde yerel14 ve sunucu önizlemesi13 kabul grubu geçti; etkin adreste iki tarayıcı/MFA ve mahrem iade girişi yeniden doğrulandı. Yerel fixture sipariş/kullanıcıları hiçbir pakette yoktur. Gerçek Stripe iadesi, taşıyıcı API’si/etiketi ve fatura iptal API’si çalıştırılmadı. İşler yönetimde blocked olarak izlenir; manuel harici sonuç kaydı resmî API entegrasyonu sayılmaz. Ayrı ücretli kargo/vergi snapshot’ı bulunmayan geçmiş siparişler otomatik tahsis yerine inceleme engeli verir. Tam medya geri yükleme ve sağlayıcı kesinti/gerçek hesap kabulü açıktır. Diğer dillerde eksik hukuk/işlem çevirisi yayımlanmaz; açık TR/EN dil seçimi gösterilir.

## Son kampanya fiyat kararı

Kullanıcı kaynak indirimsiz1.000 TL → **1.150 TL nihai** seçti. NODENO’daki ek%20 Kasım fiyat indirimi yeni ürünlere uygulanmaz. Eski kaynak fiyatı SEXOGATE fiyat geçmişi veya indirim kanıtı yapılmaz. Başka işletmenin ücretsiz kargo taahhüdü taşınmaz.

## Son düzeltmeler ve yayın kapısı

16 Kasım kaynak kontrolleri: izole çekirdek 53/53, sağlayıcı gözlem sırası/kuyruk sahipliği 17/17. API sorgusunun gözlem zamanı, iadenin eski oluşturulma zamanından ayrıdır; geç pending olayı tamamlanan iade durumunu geri alamaz. İş sonucu uygulanırken lease sahipliği ve süresi aynı veritabanı işlemi içinde denetlenir. İlk sağlayıcı gönderim niyeti ağ çağrısından önce kalıcıdır; referansı bilinmeyen işlem 20 saat sonra yeni create yerine mutabakat engeline girer. Bu koruma, resmî [Stripe idempotency](https://docs.stripe.com/api/idempotent_requests) saklama sınırına karşı ihtiyatlıdır; gerçek hesap testi sayılmaz.

Mükerrer mali belge referansı başka iadeye bağlanamaz. Aynı gider anahtarının değişmiş içeriği reddedilir. Test işleri ve test tutarları canlı rapora girmez. Son paket için bağımsız kaynak testleri, kurucu sınırları, iki tarayıcıda iade ve katalog kabulü yeniden çalıştırılır. Güncel sonuçlar `native-marketplace-source-local-results.json`, `native-marketplace-local-results.json` ve `native-returns-local-results.json` içindedir. Başarılı eski sürüm, yeni sürümün kanıtı olarak kullanılmaz.

Yerel ücretli fixture E2E kanıtı güncel `native-returns-local-results.json` içindedir. İlk b5 sürümünün tarihsel2veritabanı/52tablo/12.460satır restore sonucu `native-deployment-history-b5e7e691-20261117.json` içinde korunur.

**Güncel 17 Kasım sürümü:** `e7f4feeb57497118bdaf4dd3`, yalnız `/test`; yerel15/önizleme14 kabul kapısı ve etkin adreste iki motorun iade girişi geçti. Güncel şifreli yedek gerçekten açılıp2veritabanı/52tablo/22.873satır/FK denetlendi; mevcut PHP CLI cron işleri korunup aynı sürümün worker kalp atışı doğrulandı. Gerçek sağlayıcılar kapalıdır. Katalog genişletme kararları `native-marketplace-expansion.md`, tam yayın/test kanıtı `native-deployment-report.json` içindedir.

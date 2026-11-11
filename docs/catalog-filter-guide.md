# Katalog filtreleri

Bu modül yerel geliştirmededir. Bu belgedeki test kaydı yalnız belirtilen komutların çalıştırıldığı sürümü kapsar; genel sürüm kabulü, staging ve canlı onayı yerine geçmez.

## Veri ve filtre sözleşmesi

`src/server/commerce/catalog.ts` tek sunucu doğrulama ve arama kaynağıdır. `listProducts` eski ürün dizisi sözleşmesini korur; `searchCatalog` aynı ürünlerle birlikte `facets`, `total`, `page`, `pageSize` döndürür. Ürün yanıtında maliyet, tedarikçi iletişim bilgisi veya özel belge içerikleri yoktur.

Desteklenen sorgular: `q`, `category`, `min`, `max`, `material`, `brand`, `size`, `color`, `power`, `features`, `available`, `sort`, `page`, `locale`, `currency`. Fiyat sınırları seçili gösterim para biriminin alt birimidir. Min/max 0–9.000.000.000.000 arasında tam sayı, sayfa 1–100.000 arasında tam sayıdır. Ters fiyat aralığı reddedilir. `available=1` stoktakileri, `0` tüm uygun kayıtları seçer. `sort`: `newest`, `price_asc`, `price_desc`, `name`; eski `price-asc/price-desc` bağlantıları kabul edilip normalize edilir. Dil tr/en, gösterim para birimi TRY/EUR/USD/GBP ile sınırlıdır.

Doğrudan API'de bilinmeyen anahtar, yinelenen tekil alan, kontrol karakteri, aşırı uzun değer, geçersiz özellik veya sayı 400 hatasıdır. `features` dışında alanlar tekildir. `features=liquid&features=hygiene-sealed` iki özelliği birlikte ister; aynı değer tekrarlanamaz. UI/SSR, dil değiştirirken korunabilen `selection` gibi ilgisiz URL parametrelerini filtre API'sine taşımaz. Arama sorguları loglanmaz.

Marka/malzeme ürün kaydından, beden/renk/güç varyant kaydından alınır. `power` gerçek `battery_type` metnidir. Li-ion veya başka pil adından şarj edilebilirlik çıkarılmaz. Özellikler yalnız verideki `liquid` (sıvı ürün) ve `hygiene_sealed` (hijyen mührü) işaretleridir. Su geçirmezlik, tıbbi malzeme, sertifika veya garanti iddiası eklenmez. Fiyat, beden, renk, güç, özellik ve bulunabilirlik aynı aktif varyantta karşılanır; ürünün farklı seçenekleri birlikte yanlış eşleşme üretemez.

Facetler yalnız yayımlanmış ürün/aktif kategori/aktif varyantlardan, seçili dilin yayın koşullarına ve çalışma ortamının fixture sınırına göre hesaplanır. Arama, fiyat aralığı ve stok filtresi facet bağlamıdır; diğer facet seçimleri seçenek listesini yok etmez. Her seçeneğin sayısı farklı ürün sayısıdır. Boş kaynak alanları seçenek üretmez. Gerçek Türkçe etiketler korunur; arama için normalizasyon saklanan metni değiştirmez. Bu sürüm yazım hatası önerisi veya fuzzy arama içermez.

## Stok ve para sınırı

Katalog sorgusu ürünleri, seçenekleri, toplamı ve sayfayı tek PostgreSQL okuma snapshot'ında hesaplar. Sayfa 24 üründür. Aktif rezervasyonlar, güvenlik payı, lot karantina/geri çağırma/son kullanma koşulları ve set bileşeni adetleri hesaba katılır. Stok filtresi LIMIT/OFFSET öncesindedir. İlk etapta checkout ile aynı `main` sevk deposu kullanılır; yalnız diğer depoda bulunan stok vitrinde satılabilir sayılmaz. Ortak `variantAvailability` helper'ı da aynı depo sınırını uygular. Çok depolu sevk tahsisi bu geliştirmeyle açılmaz. Checkout kendi kilitli doğrulamasını tekrar uygular; katalog sonucu rezervasyon garantisi değildir.

Gösterim fiyat listesi yoksa rastgele kur veya TRY fiyatı başka para birimi etiketiyle sunulmaz. Ürün fiyatı bulunamıyor durumu gösterilir; seçili para biriminde fiyat filtresi istenirse eksik fiyatlı varyant eşleşmez. Ülke, belge, ödeme ve taşıma onayları bu filtreyle verilmez.

## Doğrulama kaydı

- 11 Kasım 2026 ilk RED: `npx vitest run tests/unit/catalog-filters.test.ts` — yeni parser olmadığı için 5 başarısız test.
- İlk GREEN: aynı komut — 23/23 PASS.
- `npx tsx --env-file=.env.local scripts/catalog-filters-integration.ts` — ilk yeni fonksiyon yokken RED; ilk backend sürümünde 12 kontrol PASS. İlk sürümde eski helper ile aynı biçimde diğer depolar da toplandı. Ana sevk deposu düzeltmesinin yeni kabulü önce testte eklenerek `6 !== 3` RED gözlendi; iki okuma yolu `main` ile sınırlandıktan sonra **13/13 PASS**. Yalnız ikinci depoda stoklu varyantın stoktakiler filtresine girmediği ayrıca doğrulandı.
- `npx tsx --env-file=.env.local scripts/turkish-locale-integration.ts` — 5 kontrol PASS. Bilinmeyen sort artık açık doğrulama hatasıdır; SQL enjeksiyonunun tabloyu etkilemediği kontrolü korunur.
- `npm test` — **17 dosya, 137/137 PASS** (11 Kasım 2026 05:47).
- `npm run typecheck` — çıkış 0. Dokuz değişen TypeScript/TSX dosyasının hedefli ESLint kontrolü — çıkış 0.
- Yerel HTTP smoke: `/api/catalog` 200 ve gerçek `total/facets`; `page=NaN`, `page=Infinity`, bilinmeyen sort/özellik/alan ve yinelenen marka alanı **6×400**. `/urunler` ve ilgisiz `selection` parametresi taşıyan `/en/urunler` SSR yanıtları 200; İngilizce başlık mevcut.
- `tests/e2e/catalog-filters.spec.ts` hazırdır: masaüstü çoklu filtre, aynı varyant, URL/yenileme, 390px çekmece, Tab/Escape/odağın geri gelmesi, Axe, Türkçe ve İngilizce akış; Chromium/WebKit projelerinde çalışacaktır. Root kararıyla eşzamanlı geliştirme sırasında dev HMR koşusu yapılmadı. **Bu yeni UI testine henüz PASS sonucu yazılamaz**; son optimize build ve toplu runner root tarafından çalıştırılacaktır. Bu testin ekran görüntüleri de çalıştırıldıktan sonra incelenmelidir.

Bağımsız DB testleri yalnız yerel `*_test` bağlantısından rastgele adlı yeni veritabanı oluşturur, migration'ları uygular ve sonunda yalnız oluşturdukları DB'yi kaldırır. UI testi ayrıca development/test ve proje localhost DB guardı altında yalnız kendi benzersiz geçici ürün/varyant kayıtlarını temizler.

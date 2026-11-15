# Configurable furniture sets implementation plan

> Execute natively using executing-plans and TDD. Existing implementation/publication authorization applies.

Goal: katalogla doğrulanmış seçilebilir takımları Türkiye sepeti ve adet/takım bazlı yurt dışı teklifine bağlamak.
Architecture: hash doğrulanmış katalog tanımları, paylaşılan saf takım hesaplaması, mevcut sepet kuyruğuna atomik ekleme ve sunucuda yeniden açılan RFQ içeriği.
Tech stack: vanilla JS/CSS, PHP SQLite, Node tests, Python/Playwright/PyMuPDF.
Spec: `docs/superpowers/specs/2026-11-01-configurable-furniture-sets-design.md`

## Global constraints

- TR/EN/RU/AR ve RTL; marka, onaylı görseller ve gerçek fiyatlar korunur.
- Katalogdaki 5 eksik kod oluşturulmaz, kapak/gövde komple dolap diye sunulmaz.
- Perakende sınırları99 adet/100kalem; atomik ekleme, gizli müşteri verisi ve gönderim kilidi.
- Ödeme/fiscal/provider açılmaz; ilgisiz medya/PDF değişiklikleri korunur.

## Review focus

1. Seçilmeyen baza/karyola sepete/teklife sızmamalı.
2. Aynı SKU mevcut sepette99 sınırını veya50 SKU RFQ sınırını aşarsa kısmi işlem olmamalı.
3. Katalogdan kalkan ya da başka takıma ait parça özel takımda kabul edilmemeli.
4. On takımın iki komodini20SKU adedi olmalı; sabit bir SKU takım ayrıca parçalanmamalı.
5. Bekleyen istek, hesap/dil değişimi ve iki farklı takım içeriği birbirini ezmemeli.

## Task 1: Kanıtlı tanımlar ve takım hesaplama

Files: `scripts/import-furniture-sets.py`, `data/furniture-sets.json`, `lib/furniture-sets.mjs`, `web/furniture-set-core.js`, `tests/furniture-sets.test.mjs`, build.
Produces: `applyFurnitureSets(catalog,mapping,hashes)`, `resolveFurnitureSet(catalog,setId,components,multiplier)`, `mergeFurnitureSetCart(cart,selection,products)`.
- [x] RED: gerçek Bohera tanımı 4911 komodin içerir; `1 dolap+2 komodin+1 şifonyer` açılımı4ürün; yatak bulunmaz; kaynak/PDF hash uyuşmazlığı ve99 sınırı reddedilir.
- [x] GREEN: yalnız PDF kod eşliği ile17 grup, eksik kod raporu, saf doğrulama ve atomik birleştirme.
- [x] `node --test tests/furniture-sets.test.mjs`; ilgili dosyaları commit et.

## Task 2: Adet/takım RFQ ve özel anlık kayıt

Files: `hosting/wholesale.php`, `tests/wholesale.test.mjs`, `tests/furniture-set-rfq.test.mjs`.
Consumes catalogue definitions, produces validated `piece|set` lines and immutable set component snapshots.
- [x] RED:10takım →10dolap/20komodin/10şifonyer; dış SKU/tekrar/fiyat enjeksiyonu/eski tanım ve pack/pallet reddi; geçmiş kayıt değişmez.
- [x] GREEN: SKU miktarlarını yeniden hesapla, doğrulanmış kademe varsa uygula, eksik/farklı para birimini toplam gibi gösterme, APIyecompositionVersion ekle.
- [x] gerçek PHP/SQLite testleri; commit.

## Task 3: Ortak takım kurucu ve mağaza bağlantıları

Files: `web/furniture-sets.js`, `web/furniture-sets.css`, `web/furniture-set-i18n.js`, `web/app.js`, `web/wholesale.js`, i18n, SEOJS/PHP, `tests/browser/furniture-sets.py`.
- [x] RED: ilk takım seçim ekranı, kullanıcı örneği, atomik guest/logged-in sepet, toptan takım tekrarı ve pending gönderim gerçek browser kabulü.
- [x] GREEN:17oda seçimi, model/renk/adet/çıkar, gerçek toplam, sepete toplu ekleme, adet ve takım RFQ listesi. Mobil/RTL taşma ve form koruması.
- [x] SSR/canonical/hreflang/sitemap, adet/takım metinleri, cache sürümleri; gerçek paket tarayıcı kabulü.

## Task 4: İnceleme, kılavuz ve canlı

- [x] Tek taze reviewer; önemli bulgulara RED→GREEN tek düzeltme geçişi.
- [x] Tam kaynak/dağıtım testleri ve paket doğrulama; tüm ilgili kılavuzları güncelle.
- [x] Zorunlu medya denetimi ve yedekli canlı yayın; dört alan adı ve canlı UI/SEO/özel sınır kabulü, test alıcı kaydı yok.

Ledger: `docs/furniture-sets-ledger.md`. Interface ruling: uygulama aynı bağlı `codex/control-seo` dalında yürür; ayrı müşteri stok/ödeme mimarisi kurulmaz.

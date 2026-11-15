# NODENO Control and SEO Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gerçek uluslararası SEO ile güvenli ve kalıcı mağaza yönetimini Turhost üzerinde çalıştırmak.

**Architecture:** Özel PHP modülleri ve kalıcı SQLite çalışma katmanı; ayrı yönetici kimliği/oturumu ve rol izinleri. Genel SEO çıktısı, genel katalog ve vitrin aynı yayımlanmış veriyi kullanır; mevcut storefront geliştirilir, değiştirilip başka platforma taşınmaz.

**Tech Stack:** PHP 8.x, PDO SQLite/WAL, OpenSSL, vanilla JS/CSS, Node built-in tests, Python Playwright.

**Spec:** `docs/superpowers/specs/2026-11-01-control-and-seo-design.md`

## Global Constraints

- Çalışma deposu `C:/Users/Hamza ÖZBALKAN/Desktop/Nodeno`; diğer projeler değişmez.
- Mevcut yayın dilleri `tr`, `en`, `ru`, `ar` ve RTL korunur.
- Yalnız onaylı 5.129 medya referansı yayımlanır.
- Fiyat, stok, değerlendirme, indirim, sipariş, kargo, analiz ve bağlantı başarıları uydurulmaz.
- Müşteri oturumu yönetici yetkisi vermez.
- Ödeme/yasal firma ve gerçek Google/Apple etkinleştirmesi önceki kullanıcı kararıyla kapalıdır.

## Review Focus

1. Yeni fiyat yayını sonrasında HTML/JSON-LD/API/sepet önizlemesinin aynı sürüm ve kuruş değerini kullanması. Test: `published price reaches all public projections` (Task 3/7).
2. Özel sayfa, geçersiz ürün ve filtre URL'lerinde JS sonrası eski canonical/index bilgisinin kalmaması. Test: `navigation clears stale product metadata` (Task 1/7).
3. Müşteri oturumu, eski personel yetkisi, çalınmış CSRF veya iki eşzamanlı sahip kurulumunun yetki yükseltememesi. Test: `customer cannot administer`, `revoked role loses access`, `bootstrap race has one owner` (Task 2).
4. Eşzamanlı durum/fiyat/kupon güncellemesinin para, geçmiş veya kayıt kaybettirmemesi. Test: `stale version conflicts`, `duplicate operation is idempotent`, `campaign boundaries use server time` (Task 3/4).
5. Onay verilmeden/geri çekildikten sonra olay gönderilmemesi; panel ve önerilerde sahte ülke/başarı veya özel veri bulunmaması. Test: `consent gates collection`, `telemetry rejects personal payload`, `ranking uses eligible real aggregates` (Task 5).

## Task 1: Tarayıcı ve sunucu SEO sözleşmesi

**Files:** Create `lib/seo.mjs`, `hosting/seo.php`, `tests/seo.test.mjs`, `tests/fixtures/seo-runtime.php`. Modify `lib/server.mjs`, `scripts/build.mjs`, `hosting/index.php`, `web/app.js`.

**Interfaces:** JS `seoPage(catalog, config, URL)` returns `{status,title,description,canonical,alternates,indexable,jsonld,body,locale,kind}`; PHP `nodenoSeoPage(array $catalog,array $config,array $query):array` aynı sözleşmeyi üretir. `seoRobots(origin)` / `nodenoSeoRobots()` ve sitemap üreticileri. HTML gömme işlevleri düz değerleri kaçışlar; JSON-LD `<` karakteri güvenle kodlanır.

- [ ] Red test: `assert.equal(seoPage(catalog, config, new URL('https://nodenohome.com/?lang=en&product=p1')).status,200)`; canonical aynı locale/variant, dört karşılıklı dil bağlantısı, gerçek SKU/fiyat/renk; `product=missing` 404; `page=cart` noindex; `q` noindex; stok ve puan yoksa JSON-LD'de bulunmaz.
- [ ] Run `node --test tests/seo.test.mjs`; expect missing-module failure first, then behavior assertions.
- [ ] Implement pure metadata, gerçek SSR ürün/kategori bağlantıları/teknik veri, robots ve sitemap. Worker bundle içine SEO kaynağını kontrollü ekle; PHP aynı bağlamı kullanır. Başlangıç SSR içerik yükleme sırasında korunur; SPA geçişleri meta bilgiyi günceller.
- [ ] Verify PHP/JS parity, escaped hostile text, unknown routes, image crawling and canonical sitemap entries; run source suite after build/package.
- [ ] Commit only this task's files; append result/rulings to ledger.

## Task 2: Kalıcı yönetim kimliği ve izin sınırı

**Files:** Create `hosting/control-store.php`, `hosting/control-auth.php`, `hosting/control-http.php`, `tests/control-auth.test.mjs`, `tests/fixtures/control-runtime.php`, `scripts/provision-admin-cpanel.py`. Modify package/deploy private-file allowlist with these specific files.

**Interfaces:** `nodenoControlDatabase(string $root):PDO`; `nodenoControlSession(PDO $db,string $root):array`; `nodenoControlRequire(array $context,string $permission):array`; `nodenoControlHandle(path,method,catalog,config,storageRoot):bool`. Bootstrap seed is fixed-email/hashed-token/expiry, outside public/release roots. HTTP returns `{data,version}` for resources and stable `{error}` failures.

- [ ] Red test: unauthenticated GET to orders returns 401; customer cookie returns 401; wrong Origin/missing CSRF writes return 403; invalid token does not create owner; two bootstrap completions produce one owner; TOTP replay fails; revoked role fails immediately.
- [ ] Run `node --test tests/control-auth.test.mjs`; expect missing module/routes before implementation.
- [ ] Implement guarded additive schema, password+TOTP/recovery flow, separate secure cookie, timing/attempt limits, role map, reauthentication and redacted append-only audit. No seed is shipped in public/release files.
- [ ] Run real isolated PHP HTTP tests and full suite; prove restart persistence and no auth in public config.
- [ ] Commit scoped files and ledger.

## Task 3: Katalog, fiyat, kampanya ve görünüm çalışma katmanı

**Files:** Create `hosting/control-catalog.php`, `tests/control-catalog.test.mjs`. Extend `control-store.php`, `control-http.php`; integrate read projection in `index.php`.

**Interfaces:** `nodenoControlPublicState(PDO $db,array $catalog,array $config):array` returns `{catalog,config,revision}`; `nodenoControlResource(PDO $db,context,resource,id,method,body):array` dispatches a whitelisted resource definition. Writes require version and idempotency key where operation could duplicate. Publish is a separate audited transition.

- [ ] Red test: no overrides yields unchanged products/prices/media; forbidden SKU/spec/image writes fail; draft is private; publish affects API+SEO projection; stale version returns 409; future/expired campaign does not affect price; fake reference price rejected.
- [ ] Run catalogue tests, observe red; implement validated locale fields, inventory-known flag, integer prices/history, campaigns/coupons/collections and safe storefront settings. Validate category/product/media references against the approved catalogue.
- [ ] Verify price boundaries and concurrency; build/package/full suite; record exact published projection tests.
- [ ] Commit task files and ledger.

## Task 4: Operasyon ve iletişim kayıtları

**Files:** Create `hosting/control-operations.php`, `hosting/control-marketing.php`, `tests/control-operations.test.mjs`, `tests/control-marketing.test.mjs`. Extend store/http and customer order adapter only where needed.

**Interfaces:** resource handlers expose actual orders/drafts, shipping rules/carriers/shipments, invoice/proforma records, customer views, support inbox, templates, outbox and advertising campaign records. `nodenoControlOrderTransition(db,context,key,version,action,body)` enforces state/readiness. `nodenoControlShippingQuote(db,items,country)` derives only configured rules.

- [ ] Red: anonymous/customer cannot enumerate records; paid/shipped/fiscal-issued transitions blocked without readiness/proof; duplicate transition idempotent; customer A never receives B's order; invalid tracking/URL rejected; missing provider cannot mark message sent; marketing without consent rejected.
- [ ] Implement transactional drafts and state machine, real legacy customer-order bridge, packing/proforma documents clearly labeled, shipping quotes and tracking, support forms and message drafts/outbox. Integrations are explicit configured/unverified/connected states; no real external send/charge in tests or deployment.
- [ ] Test UTC campaign/operation boundaries, monetary arithmetic, record versions and CSV injection-safe exports; full suite.
- [ ] Commit and ledger.

## Task 5: Onaylı analiz ve vitrine bağlı gerçek sıralama

**Files:** Create `hosting/control-analytics.php`, `web/store-insights.js`, `web/store-insights.css`, `tests/control-analytics.test.mjs`, `tests/store-insights.test.mjs`. Extend public routing and storefront recommendation load.

**Interfaces:** public consent/event endpoint accepts only whitelisted event/product/locale/device/selected-market values; no raw IP/email/free URL. `nodenoControlRecommendations(db,catalog,context):array` ranks eligible distinct models from real aggregates/config; settings version gates cached results.

- [ ] Red: no consent or withdrawal sends no telemetry; personal/unknown payload rejected; hidden/unapproved/duplicate variant not recommended; zero data produces deterministic category/catalogue fallback; actual event changes ranking without fictitious claims.
- [ ] Implement private bounded event storage, consent UI, real aggregate queries, configurable nonnegative weights and public recommendation feed consumed by home/product shelves. Owner panel visits are not customer analytics.
- [ ] Verify browser storage denied, callback races, bot/rate limiting, reset/withdrawal and real empty dashboard; full suite.
- [ ] Commit and ledger.

## Task 6: İşlevsel yönetim arayüzü

**Files:** Create `web/admin.html`, `web/admin.js`, `web/admin.css`, optionally focused `web/admin-*.js` modules; `tests/browser/control-panel.py`. Add protected shell routes in PHP.

**Interfaces:** UI consumes permission-filtered `/api/admin/session`, `/api/admin/schema`, `/api/admin/{resource}`, publish/transition actions; no private data embedded in HTML. All sections use real response/loading/error/empty states and version-aware save.

- [ ] Red browser: first-setup flow gated by secret+MFA; unsigned user cannot open order contents; analyst cannot see edit action; forms persist after navigation/restart; stale update offers reload; mobile viewport has no page overflow.
- [ ] Implement complete navigation, real tables/search/filter, detail forms/drawers, validation, draft/publish, readiness cards, invoices/packing, messaging, market SEO, theme, analytics/ranking, staff and audit/system views. Canonical brand assets and natural Turkish admin copy; no decorative arrows/emoji.
- [ ] Verify Chromium/Windows WebKit desktop/mobile, keyboard focus, MFA recovery, logout and no secret leaks to HTML/localStorage/screenshot logs. Screenshots use isolated test data; no production demo rows.
- [ ] Commit and ledger.

## Task 7: Yayın entegrasyonu ve SEO bildirimleri

**Files:** Extend `hosting/index.php`, `.htaccess`, `lib/server.mjs`, `scripts/build-cpanel.mjs`, `scripts/deploy-cpanel.py`, private job module, `scripts/provision-admin-cpanel.py`, `tests/control-integration.test.mjs`, SEO browser tests.

**Interfaces:** all source/private file hashes enter release manifest; `storageRoot` survives deployment. `robots/sitemap` and HTML use public projection only. IndexNow job targets only official fixed HTTPS endpoints and canonical owned URLs; response state is queued/submitted/failed, never indexed by assertion.

- [ ] Red: JS-off product/category has actual visible contents; invalid route 404; filters/private routes noindex; SPA clears old schema/canonical; edited price matches HTML/API/JSON-LD; any missing private module blocks packaging; unauthenticated admin reads fail on all aliases.
- [ ] Implement routing, projection/ETag, sitemap boundaries, provider verification values, safe IndexNow ownership/job persistence and private bootstrap provision. Do not weaken CSP or media publication gate.
- [ ] Build/package/validate/secret scan; full source and deployment suites; isolated exact package browser acceptance and durable migration tests. Baseline remains unchanged until explicit panel publish.
- [ ] Commit and ledger.

## Task 8: Taze inceleme, kılavuzlar ve canlı kabul

**Files:** `docs/yonetim-kilavuzu.md`, `docs/seo-kilavuzu.md`, `docs/teslim-durumu.md`; ignored delivery/review artifacts and private owner access file.

- [ ] Prepare whole-branch review package from baseline `853aed8` to completed code, with spec/plan/ledger and Review Focus. Use one fresh reviewer as required by executing-plans; preserve unrelated pre-existing media changes outside review/staging scope. Fix Important/Critical with red→green tests and fresh suite.
- [ ] Finalize operator guide, first-owner setup, roles, backup/recovery, pending services, markets/languages, actual reports and ranking inputs. No invented external service success.
- [ ] Run approved media publication proof, back up Turhost target, publish exact accepted release, provision one-time hashed owner seed outside public root; local plaintext setup code is ignored and never printed.
- [ ] Verify trusted HTTPS for four domains, all public/private manifest hashes/boundaries, JS-off SEO, metadata/robots/sitemaps, anonymous admin denial, real storefront and screenshots. No live demo customer/order/analytics data.
- [ ] If IndexNow enabled and ownership verified, submit only genuinely new/changed canonical URLs and record actual status. Google/Bing/Yandex account ownership actions remain clearly user-authenticated.
- [ ] Record exact live release hash, backup, source commit and test evidence. Deliver management URL and private local setup-file link; disclose only material unconfigured service limits.

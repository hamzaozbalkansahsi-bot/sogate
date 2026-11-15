# Wholesale Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans task by task. Existing user authorization covers implementation and publication; preserve the current checkout and provider deferrals.

**Goal:** Yurt dışı paket/palet tekliflerini gerçek kayıt ve dört dil SEO ile çalıştırmak.
**Architecture:** Mevcut özel PHP yönetimine `wholesale.php` modülü; yayınlanan SKU ambalaj/fiyat ayarı ve özel talep kaydı; bağımsız mağaza JS/CSS ve mevcut SSR politikası.
**Tech Stack:** PHP/PDO SQLite, vanilla JS/CSS, Node tests, Python Playwright.
**Spec:** `docs/superpowers/specs/2026-11-01-wholesale-design.md`

## Global Constraints

- Kaynak katalog, marka ve 5.129 onaylı medya korunur; toptan sayılar/fiyatlar tahmin edilmez.
- TR/EN/RU/AR, RTL, güvenilir HTTPS; müşteri verisi özel kökte kalır.
- Ödeme, gerçek sipariş/fiscal/provider gönderimi açılmaz. Yalnız teklif kaydı oluşturulur.
- Mevcut `codex/control-seo` dalı ve kullanıcının ilgisiz değişiklikleri korunur.

## Review Focus

1. Bir mobilyanın montaj kolileri ticari paket adedi sanılmamalı; ayarsız talepte adet null kalmalı.
2. Eski revizyon veya kullanıcı fiyat enjeksiyonu teklif toplamını etkilememeli.
3. Tekrar gönderim çift talep oluşturmamalı; yetkisiz ID sorgusu özel bilgi açmamalı.
4. Farklı para birimleri karıştırılmamalı; bilinmeyen fiyat toplamı sıfır olmamalı.
5. Mobil yeniden çizim/RTL iletişim alanlarını silmemeli ve sayfayı taşırmamalı.

## Task 1: Gerçek toptan veri ve özel teklif

Files: `hosting/wholesale.php`, `hosting/control-catalog.php`, `hosting/control-http.php`, `hosting/index.php`, build/deploy allowlist; `tests/wholesale.test.mjs`.
Consumes: `nodenoControlResource`, `nodenoControlPublished`, existing auth/rate/audit/transaction.
Produces: `nodenoWholesaleDefinitions($f)`, `nodenoWholesalePrepare($resource,$old,$data,$id)`, `nodenoWholesaleProjection`, `nodenoWholesaleRequest`, `nodenoWholesaleHandle`.

- [x] RED: `assert.equal(nodenoControlDefinitions().wholesale.publish,true)` via PHP process; ayarsız palet talebinin `units === null` olduğunu, idempotency ve yanlış fiyatın reddini test et.
- [x] GREEN: SKU tekilliği, doğrulanmış ambalaj/kademe, revizyonlu snapshot, gizli kayıt, salt okunur request detayları; `node --test tests/wholesale.test.mjs`.
- [x] Testler geçince yalnız ilgili dosyaları commit et.

## Task 2: Mağaza akışı ve SEO

Files: `web/wholesale.js`, `web/wholesale.css`, `web/app.js`, `web/index.html`, `web/seo-core.js`, `hosting/seo.php`, `tests/wholesale-seo.test.mjs`, `tests/browser/wholesale.py`.
Consumes: `catalog`, `config`, public wholesale routes and revision from Task 1.
Produces: `createWholesale({state,esc,loc,image,productName,href,toast})` returning `{render,mount,entry}`, four locale SSR and canonical sitemap entry.

- [x] RED: `seoPage(catalog,config,new URL('https://nodenohome.com/?page=wholesale&lang=en')).status === 200`; four locale canonical/SSR and no fake Offer assertions.
- [x] GREEN: four-language product selection/multi-item request, form preservation, success/error, responsive product hero; attach menu/product entry points and version assets.
- [x] Real browser RED/GREEN: request form, product/colour/pack/pallet count, server stored snapshot, admin visibility, 390/1440 widths, Arabic RTL, Chromium/WebKit.
- [x] Source suite and relevant browser checks; commit actual implementation.

## Task 3: Review, guides and publication

Files: operator/store/SEO guides, delivery/wholesale ledger; exact build and live reports under ignored artifacts.
- [x] `npm test`, deployment tests, `npm run build`, PHP build and artifact validation.
- [x] One fresh final reviewer as required by executing-plans; fix material findings with regression evidence.
- [x] Physical media gate and existing cPanel publish with backup and exact release hash.
- [x] Trusted TLS live SSR/SEO/menus/assets, no production customer records; document actual live hash and remaining business inputs.

Execution ledger: `docs/wholesale-ledger.md`. Spec self-check: no fabricated commercial terms; route/private boundary and existing retail pricing remain separate. External provider settings are unchanged.

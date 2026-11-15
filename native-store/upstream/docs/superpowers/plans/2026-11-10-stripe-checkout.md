# Stripe Checkout Implementation Plan

> **For agentic workers:** Execute task-by-task with TDD and verification-before-completion. Preserve the user's existing working tree; review a scoped baseline rather than committing unrelated changes.

**Goal:** Connect the existing guest checkout to hosted Stripe card payments with real server-confirmed orders.

**Architecture:** Private PHP payment services reuse catalogue quoting, SQLite, account sessions, administrator authentication and encrypted integration storage. A small store module handles review, redirect and verified return status; card details remain on Stripe.

**Tech Stack:** PHP with PDO SQLite/cURL/OpenSSL, native browser modules, Node test runner, existing browser harness.

**Spec:** `docs/superpowers/specs/2026-11-10-stripe-checkout-design.md`

## Global constraints

- Recipient-paid freight is excluded, never free; VAT is 10% finished furniture and 20% doors/fronts, added to the current net prices.
- Initial direct checkout is TRY/TR. Existing international quotation is preserved.
- No credentials, personal banking papers or raw payment payloads enter Git or public files.
- No payment confirmation from a redirect, no fictitious order/stock/shipment/invoice records.
- Keep the media publication gate and existing customer storage location.

## Review focus

1. A retry after a provider timeout must reuse the original Stripe idempotency key and immutable price snapshot.
2. One order cannot be paid by an event for a different account, mode, session, amount or currency.
3. A measured front line must retain its aggregate-area rounding when VAT and Stripe line amounts are computed.
4. Returning in a different account or with a changed basket must not erase someone else's basket.
5. Deactivated/unconfigured credentials and missing seller/terms setup must fail closed.

## Task 1: Deterministic quote and webhook contracts

- [x] Create `tests/payments-core.test.mjs`; use `artifacts/runtime-php/php.exe` and real PHP fixtures.
- [x] Run `node --test tests/payments-core.test.mjs`; observe missing payment module assertions fail.
- [x] Implement `hosting/payment-core.php`: `nodenoPaymentQuote`, `nodenoPaymentContact`, `nodenoPaymentVerifySignature`, `nodenoPaymentEvent`.
- [x] Run the same command; all quote, VAT, freight, signature and matching cases pass.

## Task 2: Private state, Stripe transport and management

- [x] Add failing tests for SQLite idempotency, write-only encrypted keys, owner/elevated permissions and provider error recovery.
- [x] Implement `hosting/payments.php`, `hosting/payment-stripe.php`, `hosting/payment-store.php` and `hosting/payment-admin.php` with the spec's HTTP interfaces.
- [x] Register narrow dispatch hooks in `hosting/index.php` and `hosting/control-http.php`; add pure PHP files to cPanel packaging.
- [x] Run payment runtime tests and existing account/control tests with `PHP_BINARY` pointing at the bundled executable. No skipped required runtime checks.

## Task 3: Store and administrator flow

- [x] Test totals, explicit freight acknowledgement, stale quote handling and confirmed-return basket handling.
- [x] Add `web/payments.js`, four-language copy and an administrator payment panel; patch only the existing checkout and integration mounting points.
- [x] Validate both desktop and mobile, TR/EN/RU/AR, RTL, errors and keyboard flow using the existing browser harness.
- [x] Update `docs/mobile-guest-checkout.md`, `docs/yonetim-kilavuzu.md` and a payment operation guide with the resulting real behaviour.

## Task 4: Provider setup and release

- [x] Review only this task's scoped changes; resolve important security/correctness findings with regression tests.
- [x] Run the full suite with the real PHP binary and inspect all failures; validate the production media/release contract.
- [x] Provision the owner-authorized restricted live credentials through private hosting maintenance; verify the real account and signed live webhook without exposing secrets.
- [x] Complete distinct provider test-mode paid/declined, 3D Secure and partial/full refund checks. Completed after the owner's earlier explicit live activation; no live test charges.
- [x] Publish a reviewed release preserving runtime secrets, customer data and approved media; verify live readiness and screenshots. Report any outstanding external setup without claiming payments are enabled.

## Execution ledger

- 2026-11-10: Read-only account check: Stripe Payments/Payouts active, no active tasks; no payout bank linked.
- 2026-11-10: Owner confirmed recipient-paid courier/freight, net catalogue prices, furniture VAT 10%, doors/fronts VAT 20%.
- Ruling: Work in the supplied dirty worktree, saving a scoped baseline before touching existing files. Do not commit or reset unrelated catalogue/media/supplier changes. Cost if wrong: scoped integration must be re-applied against a changing file.

- 2026-11-10: Core/store/admin/HTTP/UI regressions: 14 payment tests passed; complete Node suite 299/299 and Python 177/177 passed. Twelve desktop/mobile Chromium/WebKit locale scenarios passed on packaged release 6cff5980b90c4bdd520b76e8a6df6e72b4a005029b5eb2ff990fca9820c13cb4. Stripe UI responses were mocked; this is not a provider card test.
- 2026-11-10: Fresh code-review-expert review completed. Mode/account webhook binding, credential rotation, stale review/redirect, terms hash, address newlines and status recovery findings fixed with regression checks. Full media verification and release staging in progress.
- Ruling: First card release uses TRY and Turkey delivery; foreign markets retain RFQ. Cost if wrong: international customers need a separate approved tax/fulfillment card flow.
- Ruling: Stock-controlled products fail closed until reservations are connected. Cost if wrong: these SKUs remain unavailable for card purchase. No stock was invented.
- Current: restricted live API key and live webhook are configured and verified. Exact PHP-generated TRY Checkout creation and immediate expiration passed on the real provider; two signed deliveries returned HTTP 200. Zero card charges and zero NODENO orders. PTYS Turkish tax/invoice arrangement and four-language sale/return documents remain pending; customer checkout stays disabled.

- 2026-11-10: Published disabled-by-default release a554e1db68f0f9bc726642f212e98e7273c8642e2ea98e60b1a6bf35c8d3e4e5 to Turhost with backup/rollback. Four public domain variants report the same release and preserved host, mediaReady=true, checkoutEnabled=false. Three read-only live browser scenarios passed; zero charges and zero orders.
- 2026-11-10: The unchanged-media release reused the existing complete audit only after matching its exact source report/approved metadata and rehashing current original/output bytes plus owner catalogues; 5,129 media references remain approved. No new media was published.
- 2026-11-10: Published private Stripe form compatibility fix 32af0a885e447b77f0c800caaae1348a0e7365377270b222515163e24964bba2. Endive card filter and PHP boolean serialization are verified against the real API. Public assets, accounts, encrypted credentials and media are preserved. A stale local Worker build caused three packaging failures; after regeneration the complete Node suite passed 308/308. Python passed 185/185. Temporary provisioning seeds/timers were removed; encrypted credential backup retained. See artifacts/stripe-checkout-20261110/connection-final-verification.json.
- 2026-11-10: Owner explicitly instructed US PTYS invoices with Türkiye dispatch and requested activation. Billing decision and prior VAT/freight instructions recorded without claiming official tax registration verification. Live provider account was rechecked; final four-language documents and activation saved atomically as configuration version 4. All four domains report enabled live payments and checkout, with matching document hashes and correct TRY quote arithmetic. No card charge or order was created in verification. Current scoped/full checks: Node 314/314, Python 194/194. Test-mode paid/declined provider exercise remains distinct from the actual unpaid live API check and is not claimed completed. Invoice automation is not connected.
- 2026-11-10: Five genuine provider sandbox scenarios passed on exact staged release 737a01736b06e834e3f7c941e35bdb554c442efccb108a8f11c10ffd511b50e4: paid, declined, 3DS success, 3DS failure, partial/full refund. Official temporary Stripe sandbox and loopback-only PHP used isolated private storage; live settings/customer orders untouched. Fixed claimable test-key validation and signed refund reconciliation with duplicate/out-of-order, pending/failure and pre-payment event coverage. Four locale receipt screenshots passed. Payment regressions 32/32; Python 195/195. Broad Node suite 317/320: three packaging tests require a refreshed Worker; the source production build currently stops at the independent missing approved supplier-storefront projection. No media/build gate bypass. Scoped publication uses the already-live supplier release as its immutable base, with fresh media hashes and actual-provider hashes for every changed payment module. Deployment/live acceptance recorded separately after publication.
- 2026-11-10: Scoped payment release published with backup and rollback protection; all four domain aliases confirm the exact release and public module hashes, active live checkout and unchanged seller/terms/TRY/freight. Live webhook now retains four payment events and adds the three refund events. Read-only live browser smoke passed three desktop/mobile locale cases. Four locale sandbox refund receipts visually checked. No real charge, no test order in production, no live key replacement; secret scan clean and all sandbox child processes stopped. Consolidated evidence: artifacts/stripe-sandbox-20261110/acceptance.json.

# NODENO Stripe Checkout

## Confirmed outcome

The existing basket and guest address flow lead to Stripe's hosted card payment page. A return URL never marks an order paid. Only a verified Stripe event matching the saved order, amount, currency, account and environment can confirm payment.

The owner confirmed on 10 November 2026 that freight is recipient-paid directly to the courier or freight carrier. It is excluded from the card charge, is never described as free, and needs an explicit buyer acknowledgement. Current furniture prices exclude VAT: add 10% for finished furniture, 20% for doors and cabinet fronts. Source prices and catalogue facts remain unchanged.

The current US Stripe account shows Payments and Payouts active. A linked payout bank is still absent. Payment acceptance and bank withdrawal are distinct; do not claim that a bank account has been approved or that a transfer has happened.

## Initial supported checkout

- TRY, delivery in Türkiye, TR/EN/RU/AR including RTL. Other destinations retain the existing wholesale inquiry flow until their tax and sale terms are configured.
- Reuse `nodenoCommerceQuote` for prices, variant/measurement validation and door/front minimums. Unpriced, quote-only, unsupported currency/type, hidden and insufficient-minimum lines cannot be charged.
- VAT is rounded once per basket line in minor units. Stripe receives one amount per saved order line so area/quantity rounding cannot change the total.
- Shipping is `{kind: recipient_pays, includedInCharge: false, feeMinor: null}`; only product net value and VAT compose the card total.
- Existing unrelated work, catalogue/source records, media approvals and customer data remain intact.

## Boundaries

`payment-core.php` owns deterministic pricing, address validation, signature checking and event matching. Payment tables in the existing private SQLite database own immutable order snapshots and idempotency. A fixed-origin Stripe transport owns API calls. Public HTTP routes validate origin, CSRF, body size and ownership before creating a session. Admin payment routes use existing owner permissions, elevated authentication, encrypted credentials and audit logging.

Public routes: `GET /api/payments/status`, `POST /api/payments/quote`, `POST /api/payments/checkout`, `GET /api/payments/order/<token>`, `POST /api/payments/stripe/webhook`. Public order status contains no contact/address data or secret credentials. Customer information is not added to URLs or browser storage.

The gateway starts disabled. Activation requires a verified live Stripe key for the intended account, a signing secret for the store webhook, seller details and accepted sale/freight terms. Test and live credentials remain separate. Credentials are entered directly in the administrator's password fields, encrypted outside the web root, and never bundled or printed.

## UI and operations

Preserve NODENO Sans, existing brand colours and the mobile layout. The review shows net products, VAT, card total and the separate carrier payment notice. Loading and failure states preserve the form and checkout idempotency key. Payment success is a server status, not a client assertion. Paid orders are visible to operations; no shipment, invoice or marketing message is invented or automatically sent.

## Acceptance evidence

Real PHP/SQLite tests cover price tampering, measurement/MOQ validation, 10%/20% VAT, recipient-paid freight, unknown/quote products, signature replay/forgery, wrong mode/account/session/amount/currency, duplicate events and concurrent/retried checkout attempts. Browser checks cover mobile/desktop, all four languages, RTL, keyboard and failed payment recovery. Actual provider testing is reported separately from isolated contract tests. Live activation and deployment do not proceed with missing credentials or failed publication checks.

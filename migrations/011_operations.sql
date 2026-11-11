-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/011_operations.sql | Açıklama: Varyant, satın alma, taşıma izni ve iade dağılımı kayıtları.
ALTER TABLE products ADD COLUMN translations jsonb NOT NULL DEFAULT '{}';
ALTER TABLE variants ADD COLUMN name_en text NOT NULL DEFAULT '';
ALTER TABLE variants ADD COLUMN liquid boolean NOT NULL DEFAULT false;
ALTER TABLE categories ADD COLUMN active boolean NOT NULL DEFAULT true;
CREATE TABLE brands (slug text PRIMARY KEY,name text NOT NULL,name_en text NOT NULL,active boolean NOT NULL DEFAULT true);
CREATE TABLE purchase_receipts (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,purchase_id text NOT NULL REFERENCES purchase_orders(id),idempotency_key text NOT NULL UNIQUE,request_hash text NOT NULL,actor_id text NOT NULL,reason text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE purchase_receipt_items (receipt_id text NOT NULL REFERENCES purchase_receipts(id),variant_id text NOT NULL REFERENCES variants(id),quantity integer NOT NULL CHECK(quantity>0),PRIMARY KEY(receipt_id,variant_id));
CREATE TABLE shipping_approvals (variant_id text NOT NULL REFERENCES variants(id),carrier text NOT NULL,country text NOT NULL,accepted boolean NOT NULL DEFAULT false,reviewed_by text NOT NULL,reference text NOT NULL,valid_until timestamptz,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(variant_id,carrier,country));
ALTER TABLE refunds ADD COLUMN tax_minor bigint NOT NULL DEFAULT 0 CHECK(tax_minor>=0);
ALTER TABLE refunds ADD COLUMN discount_minor bigint NOT NULL DEFAULT 0 CHECK(discount_minor>=0);
ALTER TABLE refunds ADD COLUMN restocked_cost_minor bigint NOT NULL DEFAULT 0 CHECK(restocked_cost_minor>=0);
ALTER TABLE invoice_references ADD COLUMN actor_id text;
ALTER TABLE invoice_references ADD COLUMN note text NOT NULL DEFAULT '';
CREATE INDEX purchase_receipts_purchase ON purchase_receipts(purchase_id,created_at DESC);

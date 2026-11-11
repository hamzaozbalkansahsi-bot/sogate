-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/023_product_compliance.sql | Açıklama: SKU belge inceleme izi, ayrı ülke onayı ve kaynaklı işletme iletişim bilgileri.
ALTER TABLE product_documents ADD COLUMN model_reference text NOT NULL DEFAULT '';
ALTER TABLE product_documents ADD COLUMN version integer NOT NULL DEFAULT 1 CHECK(version>0);
ALTER TABLE product_documents ADD COLUMN created_by text;
ALTER TABLE product_documents ADD COLUMN created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE product_documents ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE product_documents ADD COLUMN reviewed_by text;
ALTER TABLE product_documents ADD COLUMN reviewed_at timestamptz;
ALTER TABLE product_documents ADD COLUMN review_note text NOT NULL DEFAULT '';
ALTER TABLE product_documents ADD COLUMN revoked_by text;
ALTER TABLE product_documents ADD COLUMN revoked_at timestamptz;
ALTER TABLE product_documents ADD COLUMN revocation_reason text NOT NULL DEFAULT '';
ALTER TABLE product_eligibility ADD COLUMN approved_by text;
ALTER TABLE product_eligibility ADD COLUMN approved_at timestamptz;
CREATE INDEX product_documents_exact_review ON product_documents(variant_id,country,kind,valid_from,valid_until) WHERE reviewed=true;
CREATE TABLE product_contact_profiles (
 product_id text PRIMARY KEY REFERENCES products(id),manufacturer_address text,manufacturer_email text,
 responsible_name text,responsible_address text,responsible_email text,responsible_country text CHECK(responsible_country IS NULL OR responsible_country~'^[A-Z]{2}$'),
 source_reference text NOT NULL,reviewed boolean NOT NULL DEFAULT false,reviewed_by text,reviewed_at timestamptz,
 updated_by text NOT NULL,updated_at timestamptz NOT NULL DEFAULT now(),version integer NOT NULL DEFAULT 1 CHECK(version>0)
);
CREATE TABLE product_compliance_events (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,variant_id text REFERENCES variants(id),product_id text REFERENCES products(id),
 document_id text REFERENCES product_documents(id),country text,actor_id text NOT NULL,action text NOT NULL,reason text NOT NULL,
 details jsonb NOT NULL DEFAULT '{}',created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX product_compliance_events_variant ON product_compliance_events(variant_id,created_at DESC);
CREATE TABLE compliance_commands (
 idempotency_key text PRIMARY KEY,request_hash text NOT NULL,actor_id text NOT NULL,result jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now()
);

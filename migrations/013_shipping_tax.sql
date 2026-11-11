-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/013_shipping_tax.sql | Açıklama: Ülke ve yürürlük tarihine bağlı doğrulanmış kargo vergi kuralları.
CREATE TABLE shipping_tax_rules (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,country text NOT NULL REFERENCES country_rules(code),
 rate_bps integer NOT NULL CHECK(rate_bps BETWEEN 0 AND 10000),valid_from timestamptz NOT NULL,
 valid_until timestamptz,CHECK(valid_until IS NULL OR valid_until>valid_from),
 reference text NOT NULL,approved boolean NOT NULL DEFAULT false,created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX shipping_tax_current ON shipping_tax_rules(country,valid_from,valid_until) WHERE approved=true;

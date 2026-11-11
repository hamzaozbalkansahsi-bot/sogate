-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/015_tax_class_rules.sql | Açıklama: SKU vergi sınıfı ve kesin ülke/sınıf/yürürlük kuralları.
ALTER TABLE variants ADD COLUMN tax_class text NOT NULL DEFAULT '*'
 CHECK(char_length(tax_class) BETWEEN 1 AND 100 AND tax_class=btrim(tax_class));
ALTER TABLE tax_rules ADD CONSTRAINT tax_rules_class_valid
 CHECK(char_length(product_class) BETWEEN 1 AND 100 AND product_class=btrim(product_class));
ALTER TABLE tax_rules ADD CONSTRAINT tax_rules_period_valid
 CHECK(valid_until IS NULL OR valid_until>valid_from);
CREATE UNIQUE INDEX tax_rules_country_class_start ON tax_rules(country,product_class,valid_from);
CREATE INDEX tax_rules_current_lookup ON tax_rules(country,product_class,valid_from,valid_until);
CREATE INDEX variants_tax_class ON variants(tax_class);

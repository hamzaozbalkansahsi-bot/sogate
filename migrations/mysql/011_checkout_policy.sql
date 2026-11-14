-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/011_checkout_policy.sql
-- Açıklama   : Checkout vergi ve SKU/belge kabul kapılarının MySQL ilişkileri.
CREATE TABLE settings(`key` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PRIMARY KEY,value JSON NOT NULL,updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)) ENGINE=InnoDB;
CREATE TABLE tax_rules(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),country CHAR(2) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 product_class VARCHAR(100) COLLATE utf8mb4_0900_bin NOT NULL DEFAULT '*',rate_bps INT NOT NULL,valid_from DATETIME(3) NOT NULL,valid_until DATETIME(3),fixture BOOLEAN NOT NULL DEFAULT false,
 FOREIGN KEY(country) REFERENCES country_rules(code),CHECK(rate_bps BETWEEN 0 AND 10000),CHECK(fixture IN(0,1)),INDEX current_product_tax(country,product_class,valid_from,valid_until)
) ENGINE=InnoDB;
CREATE TABLE shipping_tax_rules(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),country CHAR(2) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,rate_bps INT NOT NULL,valid_from DATETIME(3) NOT NULL,valid_until DATETIME(3),
 reference TEXT NOT NULL,approved BOOLEAN NOT NULL DEFAULT false,created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 FOREIGN KEY(country) REFERENCES country_rules(code),CHECK(rate_bps BETWEEN 0 AND 10000),CHECK(valid_until IS NULL OR valid_until>valid_from),CHECK(approved IN(0,1)),INDEX current_shipping_tax(country,approved,valid_from,valid_until)
) ENGINE=InnoDB;
CREATE TABLE product_documents(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),variant_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,country CHAR(2) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 kind VARCHAR(100) COLLATE utf8mb4_0900_bin NOT NULL,reference TEXT NOT NULL,valid_from DATE NOT NULL,valid_until DATE,reviewed BOOLEAN NOT NULL DEFAULT false,model_reference TEXT NOT NULL DEFAULT(''),version INT NOT NULL DEFAULT 1,
 created_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 reviewed_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,reviewed_at DATETIME(3),review_note TEXT NOT NULL DEFAULT(''),revoked_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,revoked_at DATETIME(3),revocation_reason TEXT NOT NULL DEFAULT(''),
 FOREIGN KEY(variant_id) REFERENCES variants(id),CHECK(reviewed IN(0,1)),CHECK(version>0),INDEX current_product_document(variant_id,country,kind,reviewed,valid_from,valid_until)
) ENGINE=InnoDB;
CREATE TABLE product_eligibility(
 variant_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,country CHAR(2) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,approved BOOLEAN NOT NULL DEFAULT false,required_document_kind VARCHAR(100) COLLATE utf8mb4_0900_bin,
 review_note TEXT NOT NULL DEFAULT(''),approved_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,approved_at DATETIME(3),PRIMARY KEY(variant_id,country),FOREIGN KEY(variant_id) REFERENCES variants(id),CHECK(approved IN(0,1))
) ENGINE=InnoDB;

-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/004_catalog_markets.sql
-- Açıklama   : Katalog/ülke okuma portunun şeması; tam stok/sipariş şeması değildir.
CREATE TABLE categories(slug VARCHAR(120) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,name TEXT NOT NULL,name_en TEXT NOT NULL,active BOOLEAN NOT NULL DEFAULT true,CHECK(active IN(0,1))) ENGINE=InnoDB;
CREATE TABLE suppliers(id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),name TEXT NOT NULL,lead_days INT NOT NULL DEFAULT 0,contact_email TEXT,archived BOOLEAN NOT NULL DEFAULT false,CHECK(lead_days>=0),CHECK(archived IN(0,1))) ENGINE=InnoDB;
CREATE TABLE products(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),slug VARCHAR(120) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
 name TEXT NOT NULL,name_en TEXT NOT NULL,description TEXT NOT NULL DEFAULT(''),description_en TEXT NOT NULL DEFAULT(''),category VARCHAR(120) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 brand TEXT NOT NULL DEFAULT(''),image TEXT NOT NULL,material TEXT NOT NULL DEFAULT(''),status VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'draft',
 warnings TEXT NOT NULL DEFAULT(''),care TEXT NOT NULL DEFAULT(''),manufacturer TEXT,origin TEXT,fixture BOOLEAN NOT NULL DEFAULT false,
 attributes JSON NOT NULL DEFAULT(JSON_OBJECT()),seo JSON NOT NULL DEFAULT(JSON_OBJECT()),translations JSON NOT NULL DEFAULT(JSON_OBJECT()),supplier_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,
 created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 FOREIGN KEY(category) REFERENCES categories(slug),FOREIGN KEY(supplier_id) REFERENCES suppliers(id),CHECK(status IN('draft','review','published','closed','archived')),CHECK(fixture IN(0,1)),INDEX products_category_status(category,status)
) ENGINE=InnoDB;
CREATE TABLE variants(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),product_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,sku VARCHAR(191) COLLATE utf8mb4_bin NOT NULL UNIQUE,
 name TEXT NOT NULL,name_en TEXT NOT NULL DEFAULT(''),barcode VARCHAR(191) COLLATE utf8mb4_bin UNIQUE,price_minor BIGINT NOT NULL,cost_minor BIGINT NOT NULL DEFAULT 0,currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'TRY',
 color TEXT,size TEXT,weight_grams INT NOT NULL DEFAULT 0,package_dimensions JSON,battery_type TEXT,battery_capacity_mah INT,ingredients TEXT,hygiene_sealed BOOLEAN NOT NULL DEFAULT false,active BOOLEAN NOT NULL DEFAULT true,
 liquid BOOLEAN NOT NULL DEFAULT false,tax_class VARCHAR(100) COLLATE utf8mb4_bin NOT NULL DEFAULT '*',lot_tracking BOOLEAN NOT NULL DEFAULT false,expiry_required BOOLEAN NOT NULL DEFAULT false,bundle_version INT NOT NULL DEFAULT 0,measurements TEXT,
 fulfillment_mode VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'warehouse',created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 FOREIGN KEY(product_id) REFERENCES products(id),CHECK(price_minor BETWEEN 0 AND 9000000000000),CHECK(cost_minor BETWEEN 0 AND 9000000000000),CHECK(currency IN('TRY','EUR','USD','GBP')),CHECK(weight_grams>=0),
 CHECK(hygiene_sealed IN(0,1)),CHECK(active IN(0,1)),CHECK(liquid IN(0,1)),CHECK(lot_tracking IN(0,1)),CHECK(expiry_required IN(0,1)),CHECK(NOT expiry_required OR lot_tracking),CHECK(bundle_version>=0),
 CHECK(CHAR_LENGTH(tax_class) BETWEEN 1 AND 100 AND BINARY tax_class=BINARY TRIM(tax_class)),CHECK(fulfillment_mode IN('warehouse','dropship','hybrid')),INDEX variants_tax_class(tax_class)
) ENGINE=InnoDB;
CREATE TABLE variant_prices(variant_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,amount_minor BIGINT NOT NULL,valid_from DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),valid_until DATETIME(3),PRIMARY KEY(variant_id,currency),FOREIGN KEY(variant_id) REFERENCES variants(id),CHECK(currency IN('TRY','EUR','USD','GBP')),CHECK(amount_minor BETWEEN 0 AND 9000000000000)) ENGINE=InnoDB;
CREATE TABLE country_rules(
 code CHAR(2) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,name TEXT NOT NULL,enabled BOOLEAN NOT NULL DEFAULT false,product_approved BOOLEAN NOT NULL DEFAULT false,age_approved BOOLEAN NOT NULL DEFAULT false,
 payment_approved BOOLEAN NOT NULL DEFAULT false,shipping_approved BOOLEAN NOT NULL DEFAULT false,tax_approved BOOLEAN NOT NULL DEFAULT false,legal_approved BOOLEAN NOT NULL DEFAULT false,
 shipping_minor BIGINT,currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'TRY',delivery_term VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'DAP',restrictions TEXT NOT NULL DEFAULT(''),fixture BOOLEAN NOT NULL DEFAULT false,
 CHECK(CHAR_LENGTH(code)=2),CHECK(shipping_minor>=0),CHECK(enabled IN(0,1)),CHECK(product_approved IN(0,1)),CHECK(age_approved IN(0,1)),CHECK(payment_approved IN(0,1)),CHECK(shipping_approved IN(0,1)),CHECK(tax_approved IN(0,1)),CHECK(legal_approved IN(0,1)),CHECK(fixture IN(0,1))
) ENGINE=InnoDB;
CREATE TABLE country_address_profiles(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),country CHAR(2) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,version INT NOT NULL,fields JSON NOT NULL,
 status VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'draft',fixture BOOLEAN NOT NULL DEFAULT false,reference TEXT NOT NULL,created_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 approved_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,approved_at DATETIME(3),created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 approved_country CHAR(2) CHARACTER SET ascii COLLATE ascii_bin GENERATED ALWAYS AS(CASE WHEN status='approved' THEN country ELSE NULL END) STORED,
 UNIQUE(country,version),UNIQUE(approved_country),FOREIGN KEY(country) REFERENCES country_rules(code),CHECK(version>0),CHECK(JSON_TYPE(fields)='ARRAY' AND JSON_LENGTH(fields) BETWEEN 3 AND 7),CHECK(status IN('draft','approved','archived')),CHECK(fixture IN(0,1))
) ENGINE=InnoDB;
CREATE TABLE country_address_events(id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),profile_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,actor_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,action TEXT NOT NULL,note TEXT NOT NULL,created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),FOREIGN KEY(profile_id) REFERENCES country_address_profiles(id),INDEX profile_events(profile_id,created_at)) ENGINE=InnoDB;
CREATE TABLE product_routes(product_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,locale VARCHAR(2) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,slug VARCHAR(120) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),PRIMARY KEY(product_id,locale),UNIQUE(locale,slug),FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,CHECK(locale IN('tr','en')),CHECK(slug REGEXP '^[a-z0-9]+(-[a-z0-9]+)*$')) ENGINE=InnoDB;
DELIMITER $$
CREATE TRIGGER product_route_insert AFTER INSERT ON products FOR EACH ROW BEGIN
 INSERT INTO product_routes(product_id,locale,slug) VALUES(NEW.id,'tr',NEW.slug),(NEW.id,'en',NEW.slug);
END$$
CREATE TRIGGER address_profile_immutable BEFORE UPDATE ON country_address_profiles FOR EACH ROW BEGIN
 IF NOT(OLD.country<=>NEW.country) OR NOT(OLD.version<=>NEW.version) OR NOT(OLD.fields<=>NEW.fields) OR NOT(OLD.fixture<=>NEW.fixture) OR NOT(BINARY OLD.reference<=>BINARY NEW.reference) OR NOT(OLD.created_by<=>NEW.created_by) OR NOT(OLD.created_at<=>NEW.created_at) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Address profile version is immutable'; END IF;
 IF OLD.status='archived' AND NEW.status<>'archived' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Archived profile cannot reactivate'; END IF;
 IF OLD.status='approved' AND NEW.status NOT IN('approved','archived') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Approved profile cannot return to draft'; END IF;
 IF OLD.approved_by IS NOT NULL AND (NOT(OLD.approved_by<=>NEW.approved_by) OR NOT(OLD.approved_at<=>NEW.approved_at)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Approval is immutable'; END IF;
END$$
DELIMITER ;

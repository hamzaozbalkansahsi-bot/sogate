-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/027_storefront_experience.sql
-- Açıklama   : Sahiplikli alışveriş listeleri, kategori hiyerarşisi ve gerçek varyant medya ilişkileri.
CREATE TABLE shopping_states(
 owner_key VARCHAR(160) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 user_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,
 version INT NOT NULL DEFAULT 0,
 payload JSON NOT NULL,
 updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 expires_at DATETIME(3),
 FOREIGN KEY(user_id) REFERENCES `user`(id),
 CHECK(version>=0),INDEX shopping_expiry(expires_at)
) ENGINE=InnoDB;
ALTER TABLE categories ADD COLUMN parent_slug VARCHAR(120) CHARACTER SET ascii COLLATE ascii_bin,ADD COLUMN image TEXT,ADD COLUMN sort_order INT NOT NULL DEFAULT 0,ADD CONSTRAINT category_parent_fk FOREIGN KEY(parent_slug) REFERENCES categories(slug),ADD CONSTRAINT category_not_own_parent CHECK(parent_slug IS NULL OR parent_slug<>slug);
ALTER TABLE variants ADD UNIQUE KEY variant_product_identity(id,product_id);
CREATE TABLE product_media(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 product_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 variant_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,
 path TEXT NOT NULL,alt_tr TEXT NOT NULL,alt_en TEXT NOT NULL,
 sort_order INT NOT NULL DEFAULT 0,rights_reference TEXT NOT NULL,
 created_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 FOREIGN KEY(product_id) REFERENCES products(id),FOREIGN KEY(variant_id,product_id) REFERENCES variants(id,product_id),INDEX product_media_order(product_id,sort_order,id)
) ENGINE=InnoDB;

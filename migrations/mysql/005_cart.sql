-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/005_cart.sql
-- Açıklama   : Sunucu sepeti ve varyant satırlarının MySQL eşlemesi.
CREATE TABLE carts(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),
 token_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
 user_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,
 currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'TRY',
 created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
) ENGINE=InnoDB;
CREATE TABLE cart_items(
 cart_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 variant_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 quantity INT NOT NULL,PRIMARY KEY(cart_id,variant_id),
 FOREIGN KEY(cart_id) REFERENCES carts(id) ON DELETE CASCADE,
 FOREIGN KEY(variant_id) REFERENCES variants(id),CHECK(quantity>0 AND quantity<=99)
) ENGINE=InnoDB;

-- Proje: SEXOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/mysql/026_cart_experience.sql | Açıklama: Seçili sepet satırları ve süreli, tek kullanımlık geri alma.
ALTER TABLE cart_items ADD COLUMN selected BOOLEAN NOT NULL DEFAULT true;
CREATE TABLE cart_undo(
 token_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 cart_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 before_rows JSON NOT NULL,
 after_revision CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 expires_at TIMESTAMP(3) NOT NULL,
 consumed_at TIMESTAMP(3) NULL,
 created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 FOREIGN KEY(cart_id) REFERENCES carts(id) ON DELETE CASCADE,
 INDEX cart_undo_expiry(expires_at)
) ENGINE=InnoDB;

-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/013_php_account_tokens.sql
-- Açıklama   : Tek kullanımlık hesap token'ları, TOTP tekrar engeli ve ilk yönetici kilidi.
ALTER TABLE `user` ADD COLUMN php_totp_last_step BIGINT NOT NULL DEFAULT 0;
CREATE TABLE php_account_tokens(id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),user_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,kind VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,token_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,expires_at DATETIME(3) NOT NULL,consumed_at DATETIME(3),created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),FOREIGN KEY(user_id) REFERENCES `user`(id),CHECK(kind IN('password-reset','verify-email'))) ENGINE=InnoDB;
INSERT INTO commerce_definition_locks(name) VALUES('php-admin-setup');

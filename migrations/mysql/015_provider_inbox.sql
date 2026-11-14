-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/015_provider_inbox.sql
-- Açıklama   : Sağlayıcı istekleri, imzalı bildirim inbox'ı ve ödeme itirazı kayıtları.
ALTER TABLE payments ADD COLUMN payment_intent VARCHAR(255) COLLATE utf8mb4_0900_bin UNIQUE;
CREATE TABLE payment_attempts(order_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,idempotency_key VARCHAR(191) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,envelope TEXT NOT NULL,session_url TEXT,status VARCHAR(20) NOT NULL DEFAULT 'pending',created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),FOREIGN KEY(order_id) REFERENCES orders(id),CHECK(status IN('pending','created','failed'))) ENGINE=InnoDB;
CREATE TABLE provider_events(id VARCHAR(200) COLLATE utf8mb4_0900_bin PRIMARY KEY,payload_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,payload JSON NOT NULL,status VARCHAR(20) NOT NULL DEFAULT 'pending',last_error VARCHAR(100),created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),processed_at DATETIME(3),CHECK(status IN('pending','processed','rejected'))) ENGINE=InnoDB;
CREATE TABLE payment_disputes(id VARCHAR(200) COLLATE utf8mb4_0900_bin PRIMARY KEY,payment_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,status VARCHAR(64) NOT NULL,amount_minor BIGINT NOT NULL,currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),FOREIGN KEY(payment_id) REFERENCES payments(id),CHECK(amount_minor>=0)) ENGINE=InnoDB;

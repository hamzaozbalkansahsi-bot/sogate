-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/002_outbox.sql
-- Açıklama   : Kalıcı iş kaydı şeması; MySQL worker portunun tamamlandığını ifade etmez.
CREATE TABLE jobs (
  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  type VARCHAR(128) CHARACTER SET ascii NOT NULL,
  payload JSON NOT NULL,
  dedupe_key VARCHAR(255) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
  status VARCHAR(16) NOT NULL DEFAULT 'pending',
  attempts INT NOT NULL DEFAULT 0,
  max_attempts INT NOT NULL DEFAULT 5,
  available_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  lease_until DATETIME(3) NULL,
  last_error VARCHAR(128) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  completed_at DATETIME(3) NULL,
  INDEX jobs_claim(status,available_at),
  CONSTRAINT jobs_status_valid CHECK(status IN ('pending','running','completed','failed')),
  CONSTRAINT jobs_attempts_valid CHECK(attempts>=0 AND max_attempts>0 AND max_attempts<=100)
) ENGINE=InnoDB;

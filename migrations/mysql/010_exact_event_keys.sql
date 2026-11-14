-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/010_exact_event_keys.sql
-- Açıklama   : PostgreSQL işlem/olay anahtarlarında sondaki boşluğu da ayırt eden NO PAD karşılaştırma.
ALTER TABLE orders MODIFY idempotency_key VARCHAR(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin NOT NULL;
ALTER TABLE payment_events MODIFY id VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin NOT NULL;
ALTER TABLE payments MODIFY provider_reference VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;
ALTER TABLE jobs MODIFY dedupe_key VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin NOT NULL;

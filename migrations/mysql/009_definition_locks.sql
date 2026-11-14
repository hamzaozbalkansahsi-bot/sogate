-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/009_definition_locks.sql
-- Açıklama   : PostgreSQL işlem advisory kilitleri için MySQL paylaşımlı/sıralı satır kilitleri.
CREATE TABLE commerce_definition_locks(name VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY) ENGINE=InnoDB;
INSERT INTO commerce_definition_locks(name) VALUES('bundle-definition'),('fulfillment-definition');

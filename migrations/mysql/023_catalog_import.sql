-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/023_catalog_import.sql
-- Açıklama   : Süreli önizleme ve atomik taslak katalog içe aktarma kaydı.
CREATE TABLE import_batches(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 actor_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 file_name VARCHAR(255) NOT NULL,file_sha256 CHAR(64) CHARACTER SET ascii NOT NULL,
 format VARCHAR(8) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,column_mapping JSON NOT NULL,
 payload JSON NOT NULL,error_count INT NOT NULL,status VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'preview',
 created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),expires_at DATETIME(3) NOT NULL,
 committed_at DATETIME(3),CHECK(format IN('csv','xlsx')),CHECK(status IN('preview','committed')),CHECK(error_count>=0),
 INDEX import_owner(actor_id,created_at)
) ENGINE=InnoDB;

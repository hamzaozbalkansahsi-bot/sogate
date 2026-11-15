-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/029_source_catalog_review.sql
-- Açıklama   : Kaynak kataloglarını stok/fiyat/yayın onayı vermeden sürümlü incelemeye alır.
CREATE TABLE source_catalog_batches(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 vendor VARCHAR(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 file_sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 product_count INT NOT NULL DEFAULT 0,category_count INT NOT NULL DEFAULT 0,
 parsed_count INT NOT NULL DEFAULT 0,access_required_count INT NOT NULL DEFAULT 0,
 created_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 CHECK(vendor IN('xshopum','liona','sistina'))
) ENGINE=InnoDB;
CREATE TABLE source_catalog_records(
 batch_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 source_key CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 kind VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 source_url TEXT NOT NULL,title TEXT,payload JSON NOT NULL,
 metadata_state VARCHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 status VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'review',
 product_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,
 PRIMARY KEY(batch_id,source_key),FOREIGN KEY(batch_id) REFERENCES source_catalog_batches(id),FOREIGN KEY(product_id) REFERENCES products(id),
 CHECK(kind IN('product','category')),CHECK(metadata_state IN('indexed','parsed','access_required','error')),CHECK(status IN('review','rejected','drafted')),
 INDEX source_review(batch_id,kind,metadata_state)
) ENGINE=InnoDB;

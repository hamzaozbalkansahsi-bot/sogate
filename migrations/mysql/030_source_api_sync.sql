-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/030_source_api_sync.sql
-- Açıklama   : Kaynak API sayfaları, devre kesmesi ve yalnız tam snapshot yayın işareti.
ALTER TABLE source_catalog_batches ADD status VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'complete',ADD source_method VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'upload',ADD CHECK(status IN('collecting','complete','failed'));
CREATE TABLE source_api_connections(
 vendor VARCHAR(20) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 enabled BOOLEAN NOT NULL DEFAULT false,poll_minutes INT NOT NULL DEFAULT 60,
 active_run_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,
 last_run_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,
 next_run_at DATETIME(3),last_attempt_at DATETIME(3),last_success_at DATETIME(3),
 last_error VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin,updated_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,
 CHECK(vendor IN('xshopum','liona','sistina')),CHECK(enabled IN(0,1)),CHECK(poll_minutes BETWEEN 60 AND 1440)
) ENGINE=InnoDB;
INSERT INTO source_api_connections(vendor,last_error) VALUES('xshopum',NULL),('liona','SOURCE_API_CREDENTIALS_REQUIRED'),('sistina','SOURCE_API_CREDENTIALS_REQUIRED');
CREATE TABLE source_api_runs(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,vendor VARCHAR(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 batch_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
 status VARCHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'running',
 resource VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'categories',page INT NOT NULL DEFAULT 1,
 category_total INT,product_total INT,last_error VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin,
 requested_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 started_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),completed_at DATETIME(3),
 FOREIGN KEY(vendor) REFERENCES source_api_connections(vendor),FOREIGN KEY(batch_id) REFERENCES source_catalog_batches(id),
 CHECK(status IN('running','complete','failed','access_required')),CHECK(resource IN('products','categories')),CHECK(page BETWEEN 1 AND 200),
 INDEX api_run_vendor(vendor,started_at)
) ENGINE=InnoDB;
ALTER TABLE source_api_connections ADD FOREIGN KEY(active_run_id) REFERENCES source_api_runs(id),ADD FOREIGN KEY(last_run_id) REFERENCES source_api_runs(id);
CREATE TABLE source_api_pages(
 run_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,resource VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,page INT NOT NULL,
 sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,row_count INT NOT NULL,total_count INT NOT NULL,
 fetched_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 PRIMARY KEY(run_id,resource,page),FOREIGN KEY(run_id) REFERENCES source_api_runs(id),CHECK(row_count BETWEEN 0 AND 100),CHECK(total_count BETWEEN 0 AND 20000)
) ENGINE=InnoDB;

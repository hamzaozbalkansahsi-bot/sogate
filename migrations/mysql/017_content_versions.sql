-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/017_content_versions.sql
-- Açıklama   : Değişmez içerik sürümleri, zamanlı yayın ve hukuk inceleme referansı.
CREATE TABLE content_entries(id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,kind VARCHAR(30) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,locale VARCHAR(8) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,slug VARCHAR(120) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,current_version INT NOT NULL DEFAULT 0,archived BOOLEAN NOT NULL DEFAULT false,created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),UNIQUE(kind,locale,slug),CHECK(kind IN('guide','faq','collection','hero','navigation','footer','contact')),CHECK(locale IN('tr','en','de','ru','ar')),CHECK(current_version>=0 AND archived IN(0,1))) ENGINE=InnoDB;
CREATE TABLE content_revisions(entry_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,version INT NOT NULL,title TEXT NOT NULL,summary TEXT NOT NULL,body MEDIUMTEXT NOT NULL,metadata JSON NOT NULL,actor_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),PRIMARY KEY(entry_id,version),FOREIGN KEY(entry_id) REFERENCES content_entries(id),CHECK(version>0)) ENGINE=InnoDB;
CREATE TABLE content_publications(entry_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,version INT NOT NULL,publish_at DATETIME(3) NOT NULL,actor_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),PRIMARY KEY(entry_id,version),FOREIGN KEY(entry_id,version) REFERENCES content_revisions(entry_id,version),INDEX publication_due(publish_at)) ENGINE=InnoDB;
ALTER TABLE legal_documents ADD COLUMN review_reference TEXT,ADD COLUMN approved_at DATETIME(3);
INSERT INTO commerce_definition_locks(name) VALUES('php-legal');
DELIMITER $$
CREATE TRIGGER content_revision_immutable BEFORE UPDATE ON content_revisions FOR EACH ROW BEGIN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='CONTENT_REVISION_IMMUTABLE'; END$$
CREATE TRIGGER content_revision_delete BEFORE DELETE ON content_revisions FOR EACH ROW BEGIN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='CONTENT_REVISION_IMMUTABLE'; END$$
DELIMITER ;

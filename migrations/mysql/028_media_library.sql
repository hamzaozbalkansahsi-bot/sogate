-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/028_media_library.sql
-- Açıklama   : Yayın klasörünün dışındaki kalıcı, hak referanslı katalog görselleri.
CREATE TABLE media_assets(
 path VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
 width INT NOT NULL,height INT NOT NULL,bytes INT NOT NULL,
 rights_reference TEXT NOT NULL,created_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 CHECK(width>0 AND height>0 AND bytes>0)
) ENGINE=InnoDB;

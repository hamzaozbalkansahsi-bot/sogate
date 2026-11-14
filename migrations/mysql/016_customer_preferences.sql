-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/016_customer_preferences.sql
-- Açıklama   : Ayrı müşteri iletişim/çerez tercihleri ve sürümlü izin kanıtı.
CREATE TABLE customer_preferences(user_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,marketing BOOLEAN NOT NULL DEFAULT false,analytics BOOLEAN NOT NULL DEFAULT false,private_notifications BOOLEAN NOT NULL DEFAULT true,updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),FOREIGN KEY(user_id) REFERENCES `user`(id),CHECK(marketing IN(0,1) AND analytics IN(0,1) AND private_notifications IN(0,1))) ENGINE=InnoDB;
CREATE TABLE consent_events(id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,user_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,preferences JSON NOT NULL,policy_version VARCHAR(100) NOT NULL,created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),FOREIGN KEY(user_id) REFERENCES `user`(id),INDEX consent_user_date(user_id,created_at)) ENGINE=InnoDB;

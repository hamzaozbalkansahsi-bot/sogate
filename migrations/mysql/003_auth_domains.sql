-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/003_auth_domains.sql
-- Açıklama   : PostgreSQL kimlik alanlarının harf ve boolean sınırlarını MySQL'de korur.
ALTER TABLE `user` MODIFY role VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL;
ALTER TABLE `user` MODIFY email VARCHAR(320) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL;
ALTER TABLE `user` ADD CONSTRAINT user_email_verified_boolean CHECK(emailVerified IN(0,1));
ALTER TABLE `user` ADD CONSTRAINT user_two_factor_boolean CHECK(twoFactorEnabled IN(0,1));
ALTER TABLE two_factor ADD CONSTRAINT two_factor_verified_boolean CHECK(verified IN(0,1));
ALTER TABLE jobs MODIFY status VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'pending';
ALTER TABLE jobs MODIFY type VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL;

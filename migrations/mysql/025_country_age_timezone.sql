-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/025_country_age_timezone.sql
-- Açıklama   : Beyan ile güçlü yaş doğrulamasını ve belge tarihlerinin ülke saat dilimini ayırır.
ALTER TABLE country_rules
 ADD age_method VARCHAR(24) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'unconfigured',
 ADD timezone VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'UTC',
 ADD CHECK(age_method IN('unconfigured','declaration','provider_required'));

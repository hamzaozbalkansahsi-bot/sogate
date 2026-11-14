-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/021_job_generations.sql
-- Açıklama   : Yetkili retry sonrasında eski işçinin yeni denemeyi tamamlamasını engeller.
ALTER TABLE jobs ADD COLUMN generation INT NOT NULL DEFAULT 0,ADD CHECK(generation>=0);

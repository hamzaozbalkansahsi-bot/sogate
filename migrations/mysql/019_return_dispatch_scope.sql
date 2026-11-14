-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/019_return_dispatch_scope.sql
-- Açıklama   : Sevk öncesi iptal edilen adet ile müşteriden dönen adedi ayırır.
ALTER TABLE returns ADD COLUMN undispatched_quantity INT NOT NULL DEFAULT 0,ADD CHECK(undispatched_quantity BETWEEN 0 AND quantity);

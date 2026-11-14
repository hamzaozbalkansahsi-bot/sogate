-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/020_payment_reconciliation.sql
-- Açıklama   : Sınırlı mutabakat turu için ilerleyen tarama, kısa kira ve hata durumu.
ALTER TABLE payments ADD COLUMN reconciled_at DATETIME(3),ADD COLUMN reconcile_after DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),ADD COLUMN reconcile_error VARCHAR(100),ADD INDEX reconciliation_due(provider,reconcile_after,reconciled_at);

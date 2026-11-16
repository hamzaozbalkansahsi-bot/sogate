-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : native-store/returns/sg-returns-001.sql
-- Açıklama   : İade başvurusu, birim tahsisi, mali günlük ve kalıcı dış işlem işlerini kurar.
CREATE TABLE IF NOT EXISTS sg_return_cases (
 code TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES payment_orders(id), actor_hash TEXT NOT NULL,
 reason TEXT NOT NULL, note_envelope TEXT NOT NULL, locale TEXT NOT NULL, currency TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'requested' CHECK(status IN('requested','awaiting_dispatch','in_transit','received','approved','rejected','cancelled','closed')),
 version INTEGER NOT NULL DEFAULT 1, gross_minor INTEGER NOT NULL CHECK(gross_minor>0), net_minor INTEGER NOT NULL CHECK(net_minor>=0), vat_minor INTEGER NOT NULL CHECK(vat_minor>=0), shipping_minor INTEGER NOT NULL DEFAULT 0,
 policy_json TEXT NOT NULL, review_flags_json TEXT NOT NULL, shipping_json TEXT NOT NULL DEFAULT '{}', qc_json TEXT NOT NULL DEFAULT '{}',
 refund_state TEXT NOT NULL DEFAULT 'none', fiscal_state TEXT NOT NULL DEFAULT 'none', requested_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
 CHECK(gross_minor=net_minor+vat_minor)
);
CREATE INDEX IF NOT EXISTS sg_return_orders ON sg_return_cases(order_id,requested_at);
CREATE TABLE IF NOT EXISTS sg_return_lines (
 case_code TEXT NOT NULL REFERENCES sg_return_cases(code), line_key TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0), units_json TEXT NOT NULL, snapshot_json TEXT NOT NULL,
 gross_minor INTEGER NOT NULL, net_minor INTEGER NOT NULL, vat_minor INTEGER NOT NULL,
 PRIMARY KEY(case_code,line_key), CHECK(gross_minor=net_minor+vat_minor)
);
CREATE TABLE IF NOT EXISTS sg_return_commands(key_hash TEXT PRIMARY KEY,request_hash TEXT NOT NULL,response_json TEXT NOT NULL,created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS sg_return_events(id INTEGER PRIMARY KEY AUTOINCREMENT,case_code TEXT NOT NULL REFERENCES sg_return_cases(code),kind TEXT NOT NULL,actor TEXT NOT NULL,details_json TEXT NOT NULL,created_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS sg_return_timeline ON sg_return_events(case_code,id);
CREATE TABLE IF NOT EXISTS sg_return_jobs(
 id TEXT PRIMARY KEY,case_code TEXT NOT NULL REFERENCES sg_return_cases(code),kind TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'queued',
 amount_minor INTEGER NOT NULL,currency TEXT NOT NULL,request_json TEXT NOT NULL,provider_ref TEXT UNIQUE,
 attempts INTEGER NOT NULL DEFAULT 0,next_at INTEGER NOT NULL,lease_until INTEGER NOT NULL DEFAULT 0,lease_token TEXT,error_code TEXT,
 created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,UNIQUE(case_code,kind)
);
CREATE INDEX IF NOT EXISTS sg_return_job_due ON sg_return_jobs(status,next_at,lease_until);
CREATE TABLE IF NOT EXISTS sg_return_journal(
 event_key TEXT PRIMARY KEY,case_code TEXT REFERENCES sg_return_cases(code),order_id TEXT NOT NULL REFERENCES payment_orders(id),currency TEXT NOT NULL,
 kind TEXT NOT NULL,entries_json TEXT NOT NULL,reference TEXT NOT NULL,created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS sg_return_journal_currency ON sg_return_journal(currency,created_at);
CREATE TABLE IF NOT EXISTS sg_return_fiscal(
 case_code TEXT PRIMARY KEY REFERENCES sg_return_cases(code),operation TEXT NOT NULL,original_ref TEXT NOT NULL,corrective_ref TEXT NOT NULL UNIQUE,
 evidence_ref TEXT NOT NULL,actor TEXT NOT NULL,confirmed_at INTEGER NOT NULL,origin TEXT NOT NULL DEFAULT 'manual_external_confirmation'
);
CREATE TABLE IF NOT EXISTS sg_return_migrations(version INTEGER PRIMARY KEY,applied_at INTEGER NOT NULL);
INSERT OR IGNORE INTO sg_return_migrations(version,applied_at)VALUES(1,strftime('%s','now'));

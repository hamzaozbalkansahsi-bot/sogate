-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : native-store/storefront/product-feedback-001.sql
-- Açıklama   : Ürün geri bildirimi ve personele ait inceleme olaylarını kalıcı, eklemeli şemayla saklar.
CREATE TABLE IF NOT EXISTS sg_product_feedback(
 id TEXT PRIMARY KEY,product_id TEXT NOT NULL,reason TEXT NOT NULL CHECK(reason IN('title','description','specification','price','category','image','image_mismatch','safety','variant','other')),
 note_envelope TEXT NOT NULL,owner_hash TEXT NOT NULL,request_hash TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'new' CHECK(status IN('new','reviewing','resolved','rejected')),
 version INTEGER NOT NULL DEFAULT 1,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS sg_product_feedback_status ON sg_product_feedback(status,created_at,id);
CREATE INDEX IF NOT EXISTS sg_product_feedback_duplicates ON sg_product_feedback(owner_hash,request_hash,created_at);
CREATE TABLE IF NOT EXISTS sg_product_feedback_commands(
 key_hash TEXT PRIMARY KEY,request_hash TEXT NOT NULL,feedback_id TEXT NOT NULL REFERENCES sg_product_feedback(id),created_at INTEGER NOT NULL,expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sg_product_feedback_rates(key_hash TEXT PRIMARY KEY,window_start INTEGER NOT NULL,count INTEGER NOT NULL,expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS sg_product_feedback_events(
 id INTEGER PRIMARY KEY AUTOINCREMENT,feedback_id TEXT NOT NULL REFERENCES sg_product_feedback(id),
 status TEXT NOT NULL CHECK(status IN('new','reviewing','resolved','rejected')),note_envelope TEXT NOT NULL,actor_id TEXT NOT NULL,created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS sg_product_feedback_timeline ON sg_product_feedback_events(feedback_id,id);

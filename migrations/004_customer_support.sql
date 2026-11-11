-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/004_customer_support.sql | Açıklama: Müşteri başvuru ve özel medya kayıtları.
CREATE TABLE contact_requests (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,user_id text,email text NOT NULL,kind text NOT NULL,
 message text NOT NULL,status text NOT NULL DEFAULT 'new',assigned_to text,due_at timestamptz,created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE media_assets (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,object_key text NOT NULL UNIQUE,mime_type text NOT NULL,
 size_bytes integer NOT NULL CHECK(size_bytes>0 AND size_bytes<=8388608),sha256 text NOT NULL,rights_reference text,
 actor_id text NOT NULL,created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE redirect_rules (source_path text PRIMARY KEY,target_path text NOT NULL,status_code integer NOT NULL CHECK(status_code IN(301,308)),created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE import_preview (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,actor_id text NOT NULL,rows jsonb NOT NULL,errors jsonb NOT NULL,sha256 text NOT NULL,status text NOT NULL DEFAULT 'preview',created_at timestamptz NOT NULL DEFAULT now());

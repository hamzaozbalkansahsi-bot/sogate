-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/003_legal_seo.sql | Açıklama: Sürümlü hukuk ve sipariş sözleşmesi kayıtları.
CREATE TABLE legal_documents (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,kind text NOT NULL,locale text NOT NULL,title text NOT NULL,body text NOT NULL,version integer NOT NULL,
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','approved','effective','archived')),
 body_hash text NOT NULL,approved_by text,approved_at timestamptz,effective_at timestamptz,fixture boolean NOT NULL DEFAULT false,
 created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(kind,locale,version)
);
CREATE UNIQUE INDEX legal_one_effective ON legal_documents(kind,locale) WHERE status='effective';
CREATE TABLE order_agreements (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,order_id text NOT NULL REFERENCES orders(id),document_id text NOT NULL REFERENCES legal_documents(id),kind text NOT NULL,version integer NOT NULL,locale text NOT NULL,title text NOT NULL,body text NOT NULL,body_hash text NOT NULL,accepted_at timestamptz NOT NULL,UNIQUE(order_id,kind));
ALTER TABLE products ADD COLUMN seo jsonb NOT NULL DEFAULT '{}';
CREATE TABLE legal_approval_log (id text PRIMARY KEY DEFAULT gen_random_uuid()::text,document_id text NOT NULL REFERENCES legal_documents(id),actor_id text NOT NULL,from_status text NOT NULL,to_status text NOT NULL,note text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());

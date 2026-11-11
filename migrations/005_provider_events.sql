-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/005_provider_events.sql | Açıklama: İmzalı sağlayıcı olayları ve süreli istek kotaları.
CREATE TABLE provider_events (id text PRIMARY KEY,provider text NOT NULL,type text NOT NULL,payload_hash text NOT NULL,normalized jsonb NOT NULL,status text NOT NULL DEFAULT 'pending',created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE request_limits (key text PRIMARY KEY,count integer NOT NULL,window_start timestamptz NOT NULL,expires_at timestamptz NOT NULL);

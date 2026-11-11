-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/022_bundle_management.sql | Açıklama: Set tanımı için iyimser sürüm ve değişmez düzenleme geçmişi.
ALTER TABLE variants ADD COLUMN bundle_version integer NOT NULL DEFAULT 0 CHECK(bundle_version>=0);
CREATE TABLE bundle_changes (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,variant_id text NOT NULL REFERENCES variants(id),
 version integer NOT NULL CHECK(version>0),previous_components jsonb NOT NULL,components jsonb NOT NULL,
 reason text NOT NULL,actor_id text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(variant_id,version)
);

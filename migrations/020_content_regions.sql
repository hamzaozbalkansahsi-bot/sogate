-- Proje      : SEXSOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/020_content_regions.sql
-- Açıklama   : Yapısal vitrin bölgeleri ve mevcut içerik kaynağında taslak, sürüm ve zamanlı yayın.
CREATE TABLE cms_regions (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,
 key text NOT NULL CHECK(key ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
 locale text NOT NULL CHECK(locale IN ('tr','en')),
 kind text NOT NULL CHECK(kind IN ('hero','navigation','footer','collection')),
 active boolean NOT NULL DEFAULT false,
 fixture boolean NOT NULL DEFAULT false,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(key,locale),
 CHECK(kind='collection' OR key=kind)
);
CREATE TABLE cms_region_revisions (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,
 region_id text NOT NULL REFERENCES cms_regions(id),
 version integer NOT NULL CHECK(version>0),
 payload jsonb NOT NULL CHECK(jsonb_typeof(payload)='object'),
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','published','archived')),
 publish_at timestamptz,
 actor_id text NOT NULL,
 published_by text,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(region_id,version)
);
CREATE INDEX cms_effective_revision ON cms_region_revisions(region_id,version DESC) WHERE status='published';
ALTER TABLE content_pages ADD COLUMN kind text NOT NULL DEFAULT 'guide' CHECK(kind IN ('guide','faq','campaign','page'));
ALTER TABLE content_pages ADD COLUMN fixture boolean NOT NULL DEFAULT false;
UPDATE content_pages SET kind=CASE WHEN slug='home-campaign' THEN 'campaign' WHEN slug='sss' OR slug LIKE 'faq-%' THEN 'faq' ELSE 'guide' END;
ALTER TABLE content_revisions ADD COLUMN status text CHECK(status IN ('draft','published','archived'));
ALTER TABLE content_revisions ADD COLUMN publish_at timestamptz;
ALTER TABLE content_revisions ADD COLUMN kind text CHECK(kind IN ('guide','faq','campaign','page'));
ALTER TABLE content_revisions ADD COLUMN published_by text;
UPDATE content_revisions r SET status=CASE WHEN r.version=p.version THEN p.status ELSE 'archived' END,publish_at=p.publish_at,kind=p.kind FROM content_pages p WHERE p.id=r.page_id;
INSERT INTO content_revisions(page_id,version,title,body,status,publish_at,kind)
 SELECT id,version,title,body,status,publish_at,kind FROM content_pages p WHERE NOT EXISTS(SELECT 1 FROM content_revisions r WHERE r.page_id=p.id AND r.version=p.version);
-- Eski içerik yazıcısının aynı kaynağı kullanması sürdürülür. Yeni CMS açık sürüm durumu gönderir.
CREATE FUNCTION cms_content_revision_defaults() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 SELECT coalesce(NEW.status,p.status),coalesce(NEW.kind,p.kind) INTO NEW.status,NEW.kind FROM content_pages p WHERE p.id=NEW.page_id;
 RETURN NEW;
END $$;
CREATE TRIGGER cms_content_revision_defaults BEFORE INSERT ON content_revisions FOR EACH ROW EXECUTE FUNCTION cms_content_revision_defaults();
CREATE INDEX content_effective_revision ON content_revisions(page_id,version DESC) WHERE status='published';

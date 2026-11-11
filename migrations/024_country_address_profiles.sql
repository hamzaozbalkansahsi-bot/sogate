-- Proje      : SEXSOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/024_country_address_profiles.sql
-- Açıklama   : Ülkeye göre sürümlü adres alanı onayı ve sipariş anındaki profil bağlantısı.
CREATE TABLE country_address_profiles (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,country text NOT NULL REFERENCES country_rules(code),
 version integer NOT NULL CHECK(version>0),fields jsonb NOT NULL CHECK(jsonb_typeof(fields)='array' AND jsonb_array_length(fields) BETWEEN 3 AND 7),
 status text NOT NULL DEFAULT 'draft' CHECK(status IN('draft','approved','archived')),
 fixture boolean NOT NULL DEFAULT false,reference text NOT NULL,created_by text NOT NULL,
 approved_by text,approved_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(country,version)
);
CREATE UNIQUE INDEX country_address_current ON country_address_profiles(country) WHERE status='approved';
CREATE TABLE country_address_events (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,profile_id text NOT NULL REFERENCES country_address_profiles(id),
 actor_id text NOT NULL,action text NOT NULL,note text NOT NULL,created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX country_address_events_profile ON country_address_events(profile_id,created_at);
ALTER TABLE orders ADD COLUMN address_profile_id text REFERENCES country_address_profiles(id);
CREATE INDEX orders_address_profile ON orders(address_profile_id) WHERE address_profile_id IS NOT NULL;
ALTER TABLE customer_addresses ADD COLUMN address_profile_id text REFERENCES country_address_profiles(id);
CREATE INDEX customer_addresses_profile ON customer_addresses(address_profile_id) WHERE address_profile_id IS NOT NULL;
CREATE FUNCTION sg_address_profile_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF ROW(OLD.country,OLD.version,OLD.fields,OLD.fixture,OLD.reference,OLD.created_by,OLD.created_at)
  IS DISTINCT FROM ROW(NEW.country,NEW.version,NEW.fields,NEW.fixture,NEW.reference,NEW.created_by,NEW.created_at)
 THEN RAISE EXCEPTION 'Address profile version is immutable'; END IF;
 IF OLD.status='archived' AND NEW.status<>'archived' THEN RAISE EXCEPTION 'Archived address profile cannot reactivate'; END IF;
 IF OLD.status='approved' AND NEW.status NOT IN('approved','archived') THEN RAISE EXCEPTION 'Approved address profile cannot return to draft'; END IF;
 IF OLD.approved_by IS NOT NULL AND ROW(OLD.approved_by,OLD.approved_at) IS DISTINCT FROM ROW(NEW.approved_by,NEW.approved_at)
 THEN RAISE EXCEPTION 'Address profile approval is immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER address_profile_immutable BEFORE UPDATE ON country_address_profiles FOR EACH ROW EXECUTE FUNCTION sg_address_profile_immutable();

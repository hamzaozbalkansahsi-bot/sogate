-- Proje      : SEXSOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/021_privacy_requests.sql
-- Açıklama   : Ayrı veri sorumlusu kimliği, sürümlü süre politikası ve özel ilgili kişi başvuruları.
CREATE TABLE privacy_controllers (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,version integer NOT NULL UNIQUE,
 legal_name text NOT NULL,address text NOT NULL,email text NOT NULL,evidence text NOT NULL,
 status text NOT NULL CHECK(status IN('draft','approved','archived')),
 fixture boolean NOT NULL DEFAULT false,created_by text NOT NULL,created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX privacy_current_controller ON privacy_controllers(status) WHERE status='approved';
CREATE TABLE privacy_policies (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,controller_id text REFERENCES privacy_controllers(id),country text NOT NULL CHECK(country~'^[A-Z]{2}$'),version integer NOT NULL,
 unit text NOT NULL CHECK(unit IN('days','months')),period_count integer NOT NULL CHECK(period_count BETWEEN 1 AND 366),time_zone text NOT NULL,
 source text NOT NULL,evidence text NOT NULL,retention_note text NOT NULL,
 approved boolean NOT NULL DEFAULT false,fixture boolean NOT NULL DEFAULT false,
 approved_by text,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(country,version)
);
CREATE UNIQUE INDEX privacy_one_approved_policy ON privacy_policies(country) WHERE approved=true;
CREATE SEQUENCE privacy_request_reference;
CREATE TABLE privacy_requests (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,
 reference text NOT NULL UNIQUE DEFAULT('PR-'||to_char(current_date,'YYYY')||'-'||lpad(nextval('privacy_request_reference')::text,6,'0')),
 customer_id text REFERENCES "user"(id) ON DELETE SET NULL,email text NOT NULL,
 type text NOT NULL CHECK(type IN('access','correction','erasure','objection','portability','consent_withdrawal','other')),
 summary text NOT NULL,country text CHECK(country~'^[A-Z]{2}$'),locale text NOT NULL CHECK(locale IN('tr','en')),
 tracking_hash text NOT NULL,policy_id text REFERENCES privacy_policies(id),due_at timestamptz,
 identity_status text NOT NULL DEFAULT 'pending' CHECK(identity_status IN('pending','verified')),
 status text NOT NULL DEFAULT 'received' CHECK(status IN('received','in_review','responded','rejected')),
 assigned_to text,received_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX privacy_requests_queue ON privacy_requests(status,due_at,received_at);
CREATE INDEX privacy_requests_customer ON privacy_requests(customer_id,received_at DESC);
CREATE TABLE privacy_request_events (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,request_id text NOT NULL REFERENCES privacy_requests(id) ON DELETE CASCADE,
 actor_id text NOT NULL,type text NOT NULL,reference text NOT NULL DEFAULT '',created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE privacy_responses (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,request_id text NOT NULL UNIQUE REFERENCES privacy_requests(id) ON DELETE CASCADE,
 actor_id text NOT NULL,body text NOT NULL,outcome text NOT NULL CHECK(outcome IN('fulfilled','partially_fulfilled','rejected')),
 external_reference text NOT NULL,created_at timestamptz NOT NULL DEFAULT now()
);
CREATE FUNCTION sg_privacy_deadline(received timestamptz,policy text) RETURNS timestamptz LANGUAGE sql STABLE AS $$
 SELECT CASE unit WHEN 'days' THEN((received AT TIME ZONE time_zone)+make_interval(days=>period_count)) AT TIME ZONE time_zone
  WHEN 'months' THEN((received AT TIME ZONE time_zone)+make_interval(months=>period_count)) AT TIME ZONE time_zone END
 FROM privacy_policies WHERE id=policy;
$$;

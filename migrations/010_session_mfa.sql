-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/010_session_mfa.sql | Açıklama: Doğrulamayı hesaba değil geçerli oturuma bağlar.
CREATE TABLE session_mfa (session_id text PRIMARY KEY REFERENCES session(id) ON DELETE CASCADE,user_id text NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,verified_at timestamptz NOT NULL DEFAULT now());

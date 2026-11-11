-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/014_turkish_search.sql | Açıklama: Özgün metni değiştirmeden Türkçe arama normalizasyonu.
CREATE FUNCTION sg_search_normalize(value text) RETURNS text
LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
AS $$ SELECT lower(translate(value,'ıİğĞüÜşŞöÖçÇ','iigguussoocc')) $$;

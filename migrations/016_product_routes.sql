-- Proje      : SEXSOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/016_product_routes.sql
-- Açıklama   : Ürünlerin dil bazlı tekil URL'leri ve denetlenebilir genel yönlendirmeleri.
CREATE TABLE product_routes (
 product_id text NOT NULL REFERENCES products(id) ON DELETE CASCADE,
 locale text NOT NULL CHECK(locale IN('tr','en')),
 slug text NOT NULL CHECK(length(slug)<=120 AND slug~'^[a-z0-9]+(-[a-z0-9]+)*$'),
 updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(product_id,locale), UNIQUE(locale,slug)
);
INSERT INTO product_routes(product_id,locale,slug)
 SELECT p.id,l.locale,p.slug FROM products p CROSS JOIN(VALUES('tr'),('en'))l(locale);
CREATE FUNCTION sg_create_product_routes() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 INSERT INTO product_routes(product_id,locale,slug) VALUES(NEW.id,'tr',NEW.slug),(NEW.id,'en',NEW.slug);
 RETURN NEW;
END;
$$;
CREATE TRIGGER sg_product_route_insert AFTER INSERT ON products FOR EACH ROW EXECUTE FUNCTION sg_create_product_routes();
CREATE TABLE public_redirects (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,
 from_path text NOT NULL UNIQUE CHECK(length(from_path)<=350),
 to_path text NOT NULL CHECK(length(to_path)<=350 AND from_path<>to_path),
 active boolean NOT NULL DEFAULT true,
 reason text NOT NULL,created_by text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now()
);

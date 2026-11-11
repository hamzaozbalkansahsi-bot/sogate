-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/019_catalog_import_fields.sql
-- Açıklama: Sürümlü katalog önizlemesi ve onaysız mevcut belge referansları.
ALTER TABLE import_preview ADD COLUMN format_version integer NOT NULL DEFAULT 1;
ALTER TABLE import_preview ADD COLUMN source_environment text NOT NULL DEFAULT 'legacy';
ALTER TABLE products ADD COLUMN supplier_id text REFERENCES suppliers(id);
ALTER TABLE variants ADD COLUMN measurements text;
CREATE TABLE catalog_import_document_links (
 variant_id text NOT NULL REFERENCES variants(id),
 document_id text NOT NULL REFERENCES product_documents(id),
 preview_id text NOT NULL REFERENCES import_preview(id),
 status text NOT NULL DEFAULT 'review_required' CHECK(status='review_required'),
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(variant_id,document_id)
);

-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/012_return_stock_lines.sql | Açıklama: Satış snapshot'ından iade bileşen stokları.
CREATE TABLE return_stock_lines (
 return_id text NOT NULL REFERENCES returns(id),variant_id text NOT NULL REFERENCES variants(id),
 warehouse_id text NOT NULL REFERENCES warehouses(id),quantity integer NOT NULL CHECK(quantity>0),
 PRIMARY KEY(return_id,variant_id,warehouse_id)
);
-- Older bundle returns used parent stock. Stop for explicit reconciliation instead
-- of inventing component inventory or concealing an existing stock discrepancy.
DO $$ BEGIN
 IF EXISTS (
  SELECT 1 FROM returns r JOIN order_items i ON i.order_id=r.order_id AND i.variant_id=r.variant_id
  WHERE r.status IN('received','inspected','refund_pending','refunded','refund_failed')
  AND CASE WHEN jsonb_typeof(i.snapshot->'bundleComponents')='array'
      THEN jsonb_array_length(i.snapshot->'bundleComponents') ELSE 0 END>0
 ) THEN RAISE EXCEPTION 'Legacy received bundle returns require explicit inventory reconciliation before migration 012';
 END IF;
END $$;
-- Existing regular-item returns already changed this exact SKU; backfill links only.
INSERT INTO return_stock_lines(return_id,variant_id,warehouse_id,quantity)
 SELECT id,variant_id,'main',quantity FROM returns
 WHERE status IN('received','inspected','refund_pending','refunded','refund_failed');
CREATE INDEX return_stock_lines_variant ON return_stock_lines(variant_id,warehouse_id);

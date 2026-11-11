-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/025_purchase_lot_receipts.sql | Açıklama: Satın alma kabulünü gerçek lot ve tekil stok hareketine bağlar.
ALTER TABLE purchase_receipts ADD COLUMN source_reference text;
ALTER TABLE purchase_receipts ADD COLUMN request_version smallint NOT NULL DEFAULT 1 CHECK(request_version IN(1,2));
ALTER TABLE purchase_receipts ADD CONSTRAINT purchase_receipt_source CHECK(request_version=1 OR(source_reference IS NOT NULL AND length(trim(source_reference)) BETWEEN 5 AND 1000));
ALTER TABLE purchase_items ADD CONSTRAINT purchase_received_bounds CHECK(received>=0 AND received<=quantity);
ALTER TABLE inventory_lots ADD CONSTRAINT inventory_lot_identity UNIQUE(id,variant_id);
ALTER TABLE inventory_movements ADD CONSTRAINT inventory_movement_lot_identity UNIQUE(id,variant_id,lot_id);
CREATE TABLE purchase_receipt_lots (
 receipt_id text NOT NULL,variant_id text NOT NULL,lot_id text NOT NULL,movement_id text NOT NULL UNIQUE,
 quantity integer NOT NULL CHECK(quantity>0),quarantine_quantity integer NOT NULL CHECK(quarantine_quantity>=0 AND quarantine_quantity<=quantity),
 source_reference text NOT NULL CHECK(length(trim(source_reference)) BETWEEN 5 AND 1000),
 PRIMARY KEY(receipt_id,variant_id,lot_id),
 FOREIGN KEY(receipt_id,variant_id) REFERENCES purchase_receipt_items(receipt_id,variant_id),
 FOREIGN KEY(lot_id,variant_id) REFERENCES inventory_lots(id,variant_id),
 FOREIGN KEY(movement_id,variant_id,lot_id) REFERENCES inventory_movements(id,variant_id,lot_id)
);
CREATE INDEX purchase_receipt_lots_source ON purchase_receipt_lots(lot_id,receipt_id);

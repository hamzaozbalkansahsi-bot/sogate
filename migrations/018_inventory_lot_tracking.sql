-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/018_inventory_lot_tracking.sql | Açıklama: Mevcut lot kimliğine bağlı stok ve rezervasyon izlenebilirliği.
ALTER TABLE variants ADD COLUMN lot_tracking boolean NOT NULL DEFAULT false;
ALTER TABLE variants ADD COLUMN expiry_required boolean NOT NULL DEFAULT false;
ALTER TABLE variants ADD CONSTRAINT variant_expiry_requires_tracking CHECK(NOT expiry_required OR lot_tracking);
ALTER TABLE inventory_lots ADD COLUMN source_reference text NOT NULL DEFAULT '';
ALTER TABLE inventory_lots ADD COLUMN created_at timestamptz NOT NULL DEFAULT now();
CREATE TABLE inventory_lot_balances (
 lot_id text NOT NULL REFERENCES inventory_lots(id),warehouse_id text NOT NULL REFERENCES warehouses(id),
 on_hand integer NOT NULL DEFAULT 0 CHECK(on_hand>=0),quarantine integer NOT NULL DEFAULT 0 CHECK(quarantine>=0),
 PRIMARY KEY(lot_id,warehouse_id)
);
CREATE TABLE reservation_lots (
 reservation_id text NOT NULL REFERENCES reservations(id),lot_id text NOT NULL REFERENCES inventory_lots(id),
 quantity integer NOT NULL CHECK(quantity>0),PRIMARY KEY(reservation_id,lot_id)
);
CREATE INDEX reservation_lots_lot ON reservation_lots(lot_id,reservation_id);
CREATE INDEX inventory_lots_fefo ON inventory_lots(variant_id,expires_at,id) WHERE quarantined=false AND recall_reference IS NULL;
CREATE TABLE lot_operations (
 idempotency_key text PRIMARY KEY,request_hash text NOT NULL,action text NOT NULL,lot_id text REFERENCES inventory_lots(id),
 actor_id text NOT NULL,result jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now()
);

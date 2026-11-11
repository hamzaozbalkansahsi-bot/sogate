-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/017_staff_fulfillment.sql
-- Açıklama: Ödenmiş siparişlerin doğrulamalı toplama ve paketleme kayıtları.
CREATE TABLE fulfillment_tasks (
 id text PRIMARY KEY DEFAULT gen_random_uuid()::text,
 order_id text NOT NULL REFERENCES orders(id),
 status text NOT NULL DEFAULT 'picking' CHECK(status IN('picking','packing','packed','shipped','cancelled')),
 shipment_id text REFERENCES shipments(id),
 created_by text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK((status='shipped')=(shipment_id IS NOT NULL))
);
CREATE INDEX fulfillment_tasks_order_status ON fulfillment_tasks(order_id,status);
CREATE TABLE fulfillment_task_items (
 task_id text NOT NULL REFERENCES fulfillment_tasks(id),
 variant_id text NOT NULL REFERENCES variants(id),
 quantity integer NOT NULL CHECK(quantity>0 AND quantity<=999),
 picked_quantity integer NOT NULL DEFAULT 0 CHECK(picked_quantity>=0 AND picked_quantity<=quantity),
 packed_quantity integer NOT NULL DEFAULT 0 CHECK(packed_quantity>=0 AND packed_quantity<=picked_quantity),
 PRIMARY KEY(task_id,variant_id)
);
CREATE TABLE fulfillment_commands (
 order_id text NOT NULL REFERENCES orders(id),
 request_key text NOT NULL,
 request_hash text NOT NULL,
 task_id text NOT NULL REFERENCES fulfillment_tasks(id),
 action text NOT NULL CHECK(action IN('create','pick','pack','ship','cancel')),
 actor_id text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(order_id,request_key)
);

-- Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
-- Dosya: migrations/006_commerce_safety.sql | Açıklama: Sevkiyat tekrarlarında içerik eşleşmesi.
ALTER TABLE shipments ADD COLUMN request_hash text;
CREATE TABLE coupon_usage (coupon_id text NOT NULL REFERENCES coupons(id),order_id text NOT NULL UNIQUE REFERENCES orders(id),status text NOT NULL DEFAULT 'reserved' CHECK(status IN('reserved','consumed','released')),PRIMARY KEY(coupon_id,order_id));

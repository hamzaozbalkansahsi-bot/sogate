-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/007_supplier_availability.sql
-- Açıklama   : Mevcut hibrit gönderimin ayrı tedarikçi bildirim/tahsis okuma şeması.
CREATE TABLE supplier_fulfillment_profiles(
 supplier_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,enabled BOOLEAN NOT NULL DEFAULT false,
 contract_reference TEXT NOT NULL,privacy_reference TEXT NOT NULL,packaging_reference TEXT NOT NULL,return_reference TEXT NOT NULL,
 approved_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,fixture BOOLEAN NOT NULL DEFAULT false,updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 FOREIGN KEY(supplier_id) REFERENCES suppliers(id),CHECK(enabled IN(0,1)),CHECK(fixture IN(0,1))
) ENGINE=InnoDB;
CREATE TABLE supplier_shipping_routes(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),supplier_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,country CHAR(2) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,shipping_minor BIGINT NOT NULL,handling_minor BIGINT NOT NULL DEFAULT 0,min_days INT NOT NULL,max_days INT NOT NULL,
 approved BOOLEAN NOT NULL DEFAULT false,reference TEXT NOT NULL,approved_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),carrier VARCHAR(191) COLLATE utf8mb4_bin NOT NULL DEFAULT '',
 UNIQUE(supplier_id,country,currency),FOREIGN KEY(supplier_id) REFERENCES suppliers(id),FOREIGN KEY(country) REFERENCES country_rules(code),
 CHECK(currency IN('TRY','EUR','USD','GBP')),CHECK(shipping_minor BETWEEN 0 AND 9000000000000),CHECK(handling_minor BETWEEN 0 AND 9000000000000),CHECK(min_days>=0),CHECK(max_days>=min_days AND max_days<=365),CHECK(approved IN(0,1))
) ENGINE=InnoDB;
CREATE TABLE supplier_offers(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),supplier_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,variant_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,supplier_sku VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
 currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,cost_minor BIGINT NOT NULL,reported_quantity INT NOT NULL DEFAULT 0,safety_stock INT NOT NULL DEFAULT 0,
 observed_at DATETIME(3) NOT NULL,valid_until DATETIME(3) NOT NULL,source_reference TEXT NOT NULL,approved BOOLEAN NOT NULL DEFAULT false,approved_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 UNIQUE(supplier_id,variant_id,currency),UNIQUE(supplier_id,supplier_sku,currency),FOREIGN KEY(supplier_id) REFERENCES suppliers(id),FOREIGN KEY(variant_id) REFERENCES variants(id),
 CHECK(currency IN('TRY','EUR','USD','GBP')),CHECK(cost_minor BETWEEN 0 AND 9000000000000),CHECK(reported_quantity BETWEEN 0 AND 1000000),CHECK(safety_stock BETWEEN 0 AND 1000000),CHECK(valid_until>observed_at),CHECK(approved IN(0,1))
) ENGINE=InnoDB;
CREATE TABLE supplier_reservations(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),order_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,variant_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,offer_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 quantity INT NOT NULL,status VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'active',expires_at DATETIME(3) NOT NULL,reconciliation_reference TEXT,created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 UNIQUE(order_id,variant_id),FOREIGN KEY(order_id) REFERENCES orders(id),FOREIGN KEY(variant_id) REFERENCES variants(id),FOREIGN KEY(offer_id) REFERENCES supplier_offers(id),CHECK(quantity>0),CHECK(status IN('active','allocated','reconciled','released','expired')),INDEX supplier_reservation_offer(offer_id,status,expires_at)
) ENGINE=InnoDB;
CREATE TABLE shipping_approvals(
 variant_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,carrier VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,country CHAR(2) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,accepted BOOLEAN NOT NULL DEFAULT false,
 reviewed_by VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,reference TEXT NOT NULL,valid_until DATETIME(3),created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 PRIMARY KEY(variant_id,carrier,country),FOREIGN KEY(variant_id) REFERENCES variants(id),CHECK(accepted IN(0,1))
) ENGINE=InnoDB;
CREATE SQL SECURITY INVOKER VIEW supplier_offer_availability AS
 SELECT o.*,r.id route_id,r.country,r.shipping_minor,r.handling_minor,r.min_days,r.max_days,r.reference route_reference,
 p.fixture,p.contract_reference,p.privacy_reference,p.packaging_reference,p.return_reference,
 GREATEST(0,o.reported_quantity-o.safety_stock-COALESCE(h.quantity,0)) available,r.carrier
 FROM supplier_offers o JOIN suppliers s ON s.id=o.supplier_id AND s.archived=false
 JOIN variants v ON v.id=o.variant_id
 JOIN supplier_fulfillment_profiles p ON p.supplier_id=o.supplier_id AND p.enabled=true
 JOIN supplier_shipping_routes r ON r.supplier_id=o.supplier_id AND r.currency=o.currency AND r.approved=true
 LEFT JOIN(SELECT offer_id,SUM(quantity) quantity FROM supplier_reservations WHERE status='allocated' OR(status='active' AND expires_at>CURRENT_TIMESTAMP(3)) GROUP BY offer_id)h ON h.offer_id=o.id
 WHERE o.approved=true AND o.observed_at<=CURRENT_TIMESTAMP(3) AND o.valid_until>CURRENT_TIMESTAMP(3)
 AND((COALESCE(v.battery_type,'')='' AND v.liquid=false) OR(r.carrier<>'' AND EXISTS(
 SELECT 1 FROM shipping_approvals a WHERE a.variant_id=v.id AND a.country=r.country AND a.carrier=LOWER(r.carrier) AND a.accepted=true AND(a.valid_until IS NULL OR a.valid_until>CURRENT_TIMESTAMP(3)))));

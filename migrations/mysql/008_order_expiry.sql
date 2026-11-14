-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/008_order_expiry.sql
-- Açıklama   : Süre bitimindeki kupon bırakma ve sipariş geçiş geçmişinin ilişkileri.
CREATE TABLE coupons(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),code VARCHAR(191) COLLATE utf8mb4_bin NOT NULL UNIQUE,
 discount_bps INT NOT NULL,minimum_minor BIGINT NOT NULL DEFAULT 0,max_uses INT NOT NULL,used_count INT NOT NULL DEFAULT 0,minimum_contribution_minor BIGINT NOT NULL DEFAULT 0,
 expires_at DATETIME(3) NOT NULL,active BOOLEAN NOT NULL DEFAULT true,CHECK(discount_bps>0 AND discount_bps<=10000),CHECK(max_uses>0),CHECK(used_count>=0),CHECK(active IN(0,1))
) ENGINE=InnoDB;
CREATE TABLE coupon_usage(
 coupon_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,order_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
 status VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL DEFAULT 'reserved',PRIMARY KEY(coupon_id,order_id),
 FOREIGN KEY(coupon_id) REFERENCES coupons(id),FOREIGN KEY(order_id) REFERENCES orders(id),CHECK(status IN('reserved','consumed','released'))
) ENGINE=InnoDB;
CREATE TABLE order_history(
 id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT(UUID()),order_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 type VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,from_status VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin,to_status VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin,
 actor_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin,details JSON NOT NULL DEFAULT(JSON_OBJECT()),created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 FOREIGN KEY(order_id) REFERENCES orders(id),INDEX history_order_created(order_id,created_at)
) ENGINE=InnoDB;

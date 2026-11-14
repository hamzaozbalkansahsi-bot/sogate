-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/022_supplier_operations.sql
-- Açıklama   : Manuel dış sipariş teyidi ve depo hareketi oluşturmayan tedarikçi iade kanıtları.
ALTER TABLE order_fulfillment_groups ADD external_order_reference VARCHAR(500),ADD accepted_at DATETIME(3);
CREATE TABLE supplier_return_evidence(
 return_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 stage VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 reference VARCHAR(1000) NOT NULL,actor_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 PRIMARY KEY(return_id,stage),FOREIGN KEY(return_id) REFERENCES returns(id),CHECK(stage IN('receipt','inspection'))
) ENGINE=InnoDB;

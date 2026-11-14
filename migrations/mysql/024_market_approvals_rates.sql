-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/024_market_approvals_rates.sql
-- Açıklama   : Değişen ülke koşullarına bağlı süreli onay geçmişi ve kaynaklı tamsayı kur kayıtları.
ALTER TABLE country_rules ADD review_generation INT NOT NULL DEFAULT 0,ADD CHECK(review_generation>=0);
CREATE TABLE market_approvals(
 id BIGINT PRIMARY KEY AUTO_INCREMENT,country CHAR(2) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 country_version INT NOT NULL,gate VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 approved BOOLEAN NOT NULL,reference VARCHAR(1000) NOT NULL,valid_until DATETIME(3) NOT NULL,
 actor_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 FOREIGN KEY(country) REFERENCES country_rules(code),CHECK(country_version>=0),CHECK(approved IN(0,1)),
 CHECK(gate IN('product','age','payment','shipping','tax','legal')),INDEX market_current(country,country_version,gate,id)
) ENGINE=InnoDB;
CREATE TABLE exchange_rates(
 id BIGINT PRIMARY KEY AUTO_INCREMENT,base_currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 quote_currency CHAR(3) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,rate_numerator BIGINT NOT NULL,rate_denominator BIGINT NOT NULL,
 buffer_bps INT NOT NULL,rounding VARCHAR(8) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 observed_at DATETIME(3) NOT NULL,valid_until DATETIME(3) NOT NULL,reference VARCHAR(1000) NOT NULL,
 actor_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
 CHECK(base_currency IN('TRY','EUR','USD','GBP')),CHECK(quote_currency IN('TRY','EUR','USD','GBP')),CHECK(base_currency<>quote_currency),
 CHECK(rate_numerator BETWEEN 1 AND 9000000000000),CHECK(rate_denominator BETWEEN 1 AND 100000000),
 CHECK(buffer_bps BETWEEN 0 AND 5000),CHECK(rounding IN('nearest','up','down')),CHECK(valid_until>observed_at),
 INDEX exchange_current(base_currency,quote_currency,observed_at,id)
) ENGINE=InnoDB;

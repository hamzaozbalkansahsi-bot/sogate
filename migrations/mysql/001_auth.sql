-- Proje      : SEXOGATE
-- Geliştirici: PTYS Technoligess LLC
-- Tasarım    : Hamza ÖZBALKAN
-- Dosya      : migrations/mysql/001_auth.sql
-- Açıklama   : Better Auth 1.7.20 alanlarının MySQL eşlemesi; ayrı ve boş kimlik şeması.

CREATE TABLE `user` (
  id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(320) NOT NULL UNIQUE,
  emailVerified BOOLEAN NOT NULL,
  image TEXT NULL,
  createdAt DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  twoFactorEnabled BOOLEAN NULL,
  role VARCHAR(32) NOT NULL,
  CONSTRAINT user_role_valid CHECK (role IN ('customer','admin','catalog','warehouse','support','finance','marketing'))
) ENGINE=InnoDB;

CREATE TABLE session (
  id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  expiresAt DATETIME(3) NOT NULL,
  token VARCHAR(255) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
  createdAt DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt DATETIME(3) NOT NULL,
  ipAddress VARCHAR(45) NULL,
  userAgent TEXT NULL,
  userId VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  UNIQUE KEY session_owner (id,userId),
  INDEX session_userId_idx(userId),
  CONSTRAINT session_user_fk FOREIGN KEY (userId) REFERENCES `user`(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE account (
  id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  accountId VARCHAR(255) NOT NULL,
  providerId VARCHAR(255) NOT NULL,
  userId VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  accessToken TEXT NULL, refreshToken TEXT NULL, idToken TEXT NULL,
  accessTokenExpiresAt DATETIME(3) NULL, refreshTokenExpiresAt DATETIME(3) NULL,
  scope TEXT NULL, password TEXT NULL,
  createdAt DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt DATETIME(3) NOT NULL,
  INDEX account_userId_idx(userId),
  CONSTRAINT account_user_fk FOREIGN KEY (userId) REFERENCES `user`(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE verification (
  id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  identifier VARCHAR(255) NOT NULL,
  value TEXT NOT NULL,
  expiresAt DATETIME(3) NOT NULL,
  createdAt DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updatedAt DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  INDEX verification_identifier_idx(identifier)
) ENGINE=InnoDB;

CREATE TABLE two_factor (
  id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  secret TEXT NOT NULL,
  backupCodes TEXT NOT NULL,
  userId VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  verified BOOLEAN NULL,
  failedVerificationCount INT NULL,
  lockedUntil DATETIME(3) NULL,
  INDEX twoFactor_secret_idx(secret(191)),
  INDEX twoFactor_userId_idx(userId),
  CONSTRAINT twoFactor_user_fk FOREIGN KEY (userId) REFERENCES `user`(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE rate_limit (
  id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  `key` VARCHAR(255) COLLATE utf8mb4_bin NOT NULL UNIQUE,
  count INT NOT NULL,
  lastRequest BIGINT NOT NULL,
  CONSTRAINT rateLimit_count_valid CHECK(count>=0),
  CONSTRAINT rateLimit_time_valid CHECK(lastRequest BETWEEN 0 AND 9007199254740991)
) ENGINE=InnoDB;

CREATE TABLE session_mfa (
  session_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  user_id VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  verified_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT session_mfa_owner_fk FOREIGN KEY (session_id,user_id) REFERENCES session(id,userId) ON DELETE CASCADE
) ENGINE=InnoDB;

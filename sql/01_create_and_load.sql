-- Create the database and load data/creditcard.csv.
-- Run from the repo root:  mysql --local-infile=1 -u root < sql/01_create_and_load.sql
-- The server must allow it too: SET GLOBAL local_infile = 1;

CREATE DATABASE IF NOT EXISTS fraud;
USE fraud;

DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
  id      INT AUTO_INCREMENT PRIMARY KEY,
  time_s  INT NOT NULL,              -- seconds since the first transaction in the file
  v1 DOUBLE, v2 DOUBLE, v3 DOUBLE, v4 DOUBLE, v5 DOUBLE, v6 DOUBLE, v7 DOUBLE,
  v8 DOUBLE, v9 DOUBLE, v10 DOUBLE, v11 DOUBLE, v12 DOUBLE, v13 DOUBLE, v14 DOUBLE,
  v15 DOUBLE, v16 DOUBLE, v17 DOUBLE, v18 DOUBLE, v19 DOUBLE, v20 DOUBLE, v21 DOUBLE,
  v22 DOUBLE, v23 DOUBLE, v24 DOUBLE, v25 DOUBLE, v26 DOUBLE, v27 DOUBLE, v28 DOUBLE,
  amount  DECIMAL(10,2) NOT NULL,
  class   TINYINT NOT NULL,          -- 1 = fraud
  hour_of_day TINYINT AS (FLOOR(time_s / 3600) % 24) STORED,
  day_no      TINYINT AS (FLOOR(time_s / 86400) + 1) STORED,
  INDEX idx_class (class),
  INDEX idx_hour (hour_of_day)
);

LOAD DATA LOCAL INFILE 'data/creditcard.csv'
INTO TABLE transactions
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@t, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14,
 v15, v16, v17, v18, v19, v20, v21, v22, v23, v24, v25, v26, v27, v28, amount, @c)
SET time_s = ROUND(@t), class = CAST(TRIM(BOTH '"' FROM TRIM(TRAILING '\r' FROM @c)) AS UNSIGNED);

SELECT COUNT(*) AS rows_loaded, SUM(class) AS frauds FROM transactions;

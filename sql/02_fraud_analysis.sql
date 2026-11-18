-- Fraud pattern queries. Run after 01_create_and_load.sql.
-- Note: "hour" is hours since the first transaction, mod 24. The dataset has no
-- real clock time, so hour 0 is the hour the data starts, not midnight.
USE fraud;

-- Q1. Overall fraud rate
SELECT COUNT(*) AS transactions,
       SUM(class) AS frauds,
       ROUND(100 * AVG(class), 3) AS fraud_rate_pct
FROM transactions;

-- Q2. Fraud rate by amount band
SELECT CASE
         WHEN amount = 0     THEN '0. Zero'
         WHEN amount < 10    THEN '1. Under 10'
         WHEN amount < 50    THEN '2. 10-50'
         WHEN amount < 100   THEN '3. 50-100'
         WHEN amount < 500   THEN '4. 100-500'
         WHEN amount < 1000  THEN '5. 500-1000'
         ELSE                     '6. 1000+'
       END AS amount_band,
       COUNT(*) AS transactions,
       SUM(class) AS frauds,
       ROUND(100 * AVG(class), 3) AS fraud_rate_pct
FROM transactions
GROUP BY amount_band
ORDER BY amount_band;

-- Q3. Fraud rate by hour of day
SELECT hour_of_day,
       COUNT(*) AS transactions,
       SUM(class) AS frauds,
       ROUND(100 * AVG(class), 3) AS fraud_rate_pct
FROM transactions
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Q4. Night vs day (hours 0-6 of each day are the quiet, low-volume hours)
SELECT CASE WHEN hour_of_day BETWEEN 0 AND 6 THEN 'Quiet hours (0-6)' ELSE 'Busy hours (7-23)' END AS period,
       COUNT(*) AS transactions,
       SUM(class) AS frauds,
       ROUND(100 * AVG(class), 3) AS fraud_rate_pct
FROM transactions
GROUP BY period;

-- Q5. Fraud by day (the data covers two days)
SELECT day_no,
       COUNT(*) AS transactions,
       SUM(class) AS frauds,
       ROUND(100 * AVG(class), 3) AS fraud_rate_pct
FROM transactions
GROUP BY day_no;

-- Q6. Amount profile: fraud vs normal
SELECT CASE class WHEN 1 THEN 'Fraud' ELSE 'Normal' END AS type,
       COUNT(*) AS transactions,
       ROUND(AVG(amount), 2) AS avg_amount,
       ROUND(MIN(amount), 2) AS min_amount,
       ROUND(MAX(amount), 2) AS max_amount,
       ROUND(SUM(amount), 2) AS total_amount
FROM transactions
GROUP BY class;

-- Q7. Top 5 hours by fraud rate (with at least 1,000 transactions)
SELECT hour_of_day,
       COUNT(*) AS transactions,
       SUM(class) AS frauds,
       ROUND(100 * AVG(class), 3) AS fraud_rate_pct
FROM transactions
GROUP BY hour_of_day
HAVING COUNT(*) >= 1000
ORDER BY fraud_rate_pct DESC
LIMIT 5;

-- Q8. Features that separate fraud most (difference in means, top PCA features)
SELECT 'v14' AS feature, ROUND(AVG(CASE WHEN class=1 THEN v14 END), 2) AS fraud_mean, ROUND(AVG(CASE WHEN class=0 THEN v14 END), 2) AS normal_mean FROM transactions
UNION ALL SELECT 'v17', ROUND(AVG(CASE WHEN class=1 THEN v17 END), 2), ROUND(AVG(CASE WHEN class=0 THEN v17 END), 2) FROM transactions
UNION ALL SELECT 'v12', ROUND(AVG(CASE WHEN class=1 THEN v12 END), 2), ROUND(AVG(CASE WHEN class=0 THEN v12 END), 2) FROM transactions
UNION ALL SELECT 'v10', ROUND(AVG(CASE WHEN class=1 THEN v10 END), 2), ROUND(AVG(CASE WHEN class=0 THEN v10 END), 2) FROM transactions
UNION ALL SELECT 'v4',  ROUND(AVG(CASE WHEN class=1 THEN v4  END), 2), ROUND(AVG(CASE WHEN class=0 THEN v4  END), 2) FROM transactions;

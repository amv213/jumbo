WITH f1 AS (
    SELECT "unix timestamp", "new center freq"
    FROM servo_data
    WHERE servo = 1 AND "unix timestamp" > (SELECT EXTRACT(EPOCH FROM TIMESTAMP '2020-03-10 09:00:00'))
),
     f2 AS (
    SELECT "unix timestamp", "new center freq"
    FROM servo_data
    WHERE servo = 2 AND "unix timestamp" > (SELECT EXTRACT(EPOCH FROM TIMESTAMP '2020-03-10 09:00:00'))
     )
SELECT (f1."unix timestamp" + f2."unix timestamp") / 2 AS average_timestamp,
       (f1."new center freq" - f2."new center freq")/2 AS splitting
FROM f1, f2
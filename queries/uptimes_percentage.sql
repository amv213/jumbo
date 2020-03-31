SELECT locked,
       count(locked) * 100.0 / (SELECT count(*) FROM servo_data WHERE "unix timestamp" < extract(epoch from now()) AND "unix timestamp" > (extract(epoch from now()) - 21600)) AS locked_percent
FROM servo_data
WHERE "unix timestamp" < extract(epoch from now()) AND "unix timestamp" > (extract(epoch from now()) - 21600)
GROUP BY locked;
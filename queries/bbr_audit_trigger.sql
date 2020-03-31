-- Make sure to change console dialect in DataGrip to PostgreSQL

-- Create table to hold dispatched data
CREATE TABLE IF NOT EXISTS bbr_logs_last AS
    SELECT * FROM bbr_logs LIMIT 1;

-- Give ALL on audit table to user writing data to the triggering table
-- Give SELECT on audit table to users needing to fetch the audit entry
-- (here give permissions on all tables just in case)
GRANT ALL ON ALL TABLES IN SCHEMA public TO leichtenstein;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO lienz;

-- Drop TRIGGER if need to reapply-it
DROP TRIGGER bbr_table_changed ON bbr_logs;
-- Set trigger channel name for clients to LISTEN on
CREATE TRIGGER bbr_table_changed
BEFORE INSERT
ON bbr_logs
FOR EACH ROW
EXECUTE PROCEDURE notify_bbr_update();

-- Define procedure on trigger, might need to force execution on DataGrip as it will warn about UPDATE with no WHERE
CREATE OR REPLACE FUNCTION notify_bbr_update()
RETURNS trigger AS $$
BEGIN

    -- update all rows in the table (there is only one) with NEW values
    UPDATE bbr_logs_last
    SET unix_timestamp = NEW.unix_timestamp,
        iso_timestamp = NEW.iso_timestamp,
        device = NEW.device,
        channel = NEW.channel,
        label = NEW.label,
        calibrated_temperature = NEW.calibrated_temperature,
        calibration_applied = NEW.calibration_applied;


    -- Can add payload string to NOTIFY but here we do payload free for speed
    -- PERFORM pg_notify('table_changed', 'a random payload');
    NOTIFY bbr_table_changed;

    -- Return NEW if TRIGGER is BEFORE <INSERT/UPDATE/...> ; Else return NULL.
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
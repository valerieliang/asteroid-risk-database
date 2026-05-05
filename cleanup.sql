-- cleanup.sql
-- Remove all tables created by setup.sql for NEO Hazard Assessment Database

-- Disable foreign key checks to avoid constraint errors during drop
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tables in reverse order of dependency
DROP TABLE IF EXISTS PredictedPHAs;
DROP TABLE IF EXISTS OrbitalAnomalies;
DROP TABLE IF EXISTS ObservationRecord;
DROP TABLE IF EXISTS OrbitalElements;
DROP TABLE IF EXISTS PhysicalProperties;
DROP TABLE IF EXISTS NEO;


-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;
-- load.sql
-- Load cleaned CSV files into NEO Hazard Assessment Database

LOAD DATA LOCAL INFILE 'data/neo_cleaned.csv'
INTO TABLE NEO
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS (spkid, full_name, pha, class);

LOAD DATA LOCAL INFILE 'data/physical_properties_cleaned.csv'
INTO TABLE PhysicalProperties
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS (spkid, H, diameter);

LOAD DATA LOCAL INFILE 'data/orbital_elements_cleaned.csv'
INTO TABLE OrbitalElements
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS (spkid, e, q, i, moid, moid_ld);

LOAD DATA LOCAL INFILE 'data/observation_record_cleaned.csv'
INTO TABLE ObservationRecord
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS (spkid, data_arc, condition_code);
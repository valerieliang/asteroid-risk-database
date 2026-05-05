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

-- Load predictions from Random Forest inference 
LOAD DATA LOCAL INFILE './data/predictions_unlabelled.csv'
INTO TABLE PredictedPHAs
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(spkid, pred_pha, pha_prob);

-- Load predicted anomaly flags from anomaly flagger
LOAD DATA LOCAL INFILE './data/anomalies_only.csv'
INTO TABLE OrbitalAnomalies
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(spkid, class, moid_anomaly, e_anomaly, i_anomaly, anomaly_flag);
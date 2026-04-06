-- ---------------------------------------------------------------
-- 1. NEOs
-- ---------------------------------------------------------------
LOAD DATA LOCAL INFILE './data/neos.csv'
INTO TABLE NEOs
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(id, name, potentially_hazardous, num_satellites);

-- ---------------------------------------------------------------
-- 2. PhysicalInfo
-- ---------------------------------------------------------------
LOAD DATA LOCAL INFILE './data/physical_info.csv'
INTO TABLE PhysicalInfo
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(id, diameter, absolute_magnitude, slope_parameter, albedo, 
 rotational_period_hrs, gravitational_param, spectral_class_b, spectral_class_t);

-- ---------------------------------------------------------------
-- 3. OrbitalData
-- ---------------------------------------------------------------
LOAD DATA LOCAL INFILE './data/orbital_data.csv'
INTO TABLE OrbitalData
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(id, eccentricity, inclination, orbital_period, orbit_class, earth_moid);

-- ---------------------------------------------------------------
-- 4. ObservationRecord
-- ---------------------------------------------------------------
LOAD DATA LOCAL INFILE './data/observation_records.csv'
INTO TABLE ObservationRecord
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(observation_id, id, discovering_org, first_obs, latest_obs, num_obs);

-- ---------------------------------------------------------------
-- 5. CloseApproaches
-- ---------------------------------------------------------------
LOAD DATA LOCAL INFILE './data/close_approaches.csv'
INTO TABLE CloseApproaches
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(approach_id, id, close_approach_date, miss_distance, relative_velocity, v_infinity);

-- ---------------------------------------------------------------
-- Row counts
-- ---------------------------------------------------------------
SELECT 'NEOs' AS tbl, COUNT(*) FROM NEOs UNION ALL
SELECT 'PhysicalInfo', COUNT(*) FROM PhysicalInfo UNION ALL
SELECT 'OrbitalData', COUNT(*) FROM OrbitalData UNION ALL
SELECT 'CloseApproaches', COUNT(*) FROM CloseApproaches UNION ALL
SELECT 'ObservationRecord', COUNT(*) FROM ObservationRecord;
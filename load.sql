-- ---------------------------------------------------------------
-- 1. NEOs
-- NOT NULL cols: id, name, potentially_hazardous, num_satellites
-- No nullable cols → no SET clause needed
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
-- NOT NULL: id
-- NULLABLE: diameter, absolute_magnitude, slope_parameter, albedo,
--           rotational_period_hrs, gravitational_param,
--           spectral_class_b, spectral_class_t
-- ---------------------------------------------------------------
LOAD DATA LOCAL INFILE './data/physical_info.csv'
INTO TABLE PhysicalInfo
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(id,
 @diameter, @absolute_magnitude, @slope_parameter, @albedo,
 @rotational_period_hrs, @gravitational_param,
 @spectral_class_b, @spectral_class_t)
SET
    diameter              = NULLIF(TRIM(@diameter),              ''),
    absolute_magnitude    = NULLIF(TRIM(@absolute_magnitude),    ''),
    slope_parameter       = NULLIF(TRIM(@slope_parameter),       ''),
    albedo                = NULLIF(TRIM(@albedo),                ''),
    rotational_period_hrs = NULLIF(TRIM(@rotational_period_hrs), ''),
    gravitational_param   = NULLIF(TRIM(@gravitational_param),   ''),
    spectral_class_b      = NULLIF(TRIM(@spectral_class_b),      ''),
    spectral_class_t      = NULLIF(TRIM(@spectral_class_t),      '');

-- ---------------------------------------------------------------
-- 3. OrbitalData
-- NOT NULL: id
-- NULLABLE: eccentricity, inclination, orbital_period,
--           orbit_class, earth_moid
-- ---------------------------------------------------------------
LOAD DATA LOCAL INFILE './data/orbital_data.csv'
INTO TABLE OrbitalData
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(id,
 @eccentricity, @inclination, @orbital_period,
 @orbit_class, @earth_moid)
SET
    eccentricity   = NULLIF(TRIM(@eccentricity),   ''),
    inclination    = NULLIF(TRIM(@inclination),    ''),
    orbital_period = NULLIF(TRIM(@orbital_period), ''),
    orbit_class    = NULLIF(TRIM(@orbit_class),    ''),
    earth_moid     = NULLIF(TRIM(@earth_moid),     '');

-- ---------------------------------------------------------------
-- 4. ObservationRecord
-- NOT NULL: observation_id (AUTO_INCREMENT, not in column list),
--           id
-- NULLABLE: discovering_org, first_obs, latest_obs, num_obs
-- ---------------------------------------------------------------
LOAD DATA LOCAL INFILE './data/observation_records.csv'
INTO TABLE ObservationRecord
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(observation_id, id,
 @discovering_org, @first_obs, @latest_obs, @num_obs)
SET
    discovering_org = NULLIF(TRIM(@discovering_org), ''),
    first_obs       = NULLIF(TRIM(@first_obs),       ''),
    latest_obs      = NULLIF(TRIM(@latest_obs),      ''),
    num_obs         = NULLIF(TRIM(@num_obs),         '');

-- ---------------------------------------------------------------
-- 5. CloseApproaches
-- NOT NULL: approach_id (AUTO_INCREMENT, not in column list),
--           id, close_approach_date
-- NULLABLE: miss_distance, relative_velocity, v_infinity
-- ---------------------------------------------------------------
LOAD DATA LOCAL INFILE './data/close_approaches.csv'
INTO TABLE CloseApproaches
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(approach_id, id, close_approach_date,
 @miss_distance, @relative_velocity, @v_infinity)
SET
    miss_distance     = NULLIF(TRIM(@miss_distance),     ''),
    relative_velocity = NULLIF(TRIM(@relative_velocity), ''),
    v_infinity        = NULLIF(TRIM(@v_infinity),        '');
-- ---------------------------------------------------------------
-- NEOs  (central entity)
--   id                : JPL small-body ID (spkid in source CSV)
--   name              : common name, e.g. "Eros"
--   potentially_hazardous : true when PHA flag = 'Y'
--   num_satellites    : count of known moons/satellites
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS NEOs (
    id                    INT             NOT NULL,
    name                  VARCHAR(120)    NOT NULL,
    potentially_hazardous BOOLEAN         NOT NULL DEFAULT FALSE,
    num_satellites        TINYINT UNSIGNED NOT NULL DEFAULT 0,
    CONSTRAINT pk_neos PRIMARY KEY (id),
    CONSTRAINT chk_neos_satellites CHECK (num_satellites >= 0)
);

-- ---------------------------------------------------------------
-- PhysicalInfo  (1-to-0..1 with NEOs)
--   diameter              : effective diameter in km
--   absolute_magnitude    : H magnitude (brightness at standard dist.)
--   slope_parameter       : G parameter for H-G magnitude system
--   albedo                : geometric albedo (0-1)
--   rotational_period_hrs : synodic rotation period in hours
--   gravitational_param   : GM in km^3/s^2
--   spectral_class_b      : SMASS / Tholen Bus taxonomy
--   spectral_class_t      : Tholen taxonomy
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS PhysicalInfo (
    id                    INT             NOT NULL,
    diameter              DECIMAL(10, 4)  NULL,
    absolute_magnitude    DECIMAL(6, 3)   NULL,
    slope_parameter       DECIMAL(6, 3)   NULL,
    albedo                DECIMAL(6, 4)   NULL,
    rotational_period_hrs DECIMAL(12, 5)  NULL,
    gravitational_param   DECIMAL(16, 8)  NULL,
    spectral_class_b      VARCHAR(10)     NULL,
    spectral_class_t      VARCHAR(10)     NULL,
    CONSTRAINT pk_physinfo PRIMARY KEY (id),
    CONSTRAINT fk_physinfo_neo FOREIGN KEY (id)
        REFERENCES NEOs (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_physinfo_diameter  CHECK (diameter > 0),
    CONSTRAINT chk_physinfo_albedo    CHECK (albedo IS NULL OR (albedo >= 0 AND albedo <= 1))
);

-- ---------------------------------------------------------------
-- OrbitalData  (1-to-0..1 with NEOs)
--   eccentricity  : orbital eccentricity (e)
--   inclination   : orbital inclination in degrees (i)
--   orbital_period: sidereal period in years (per_y from source)
--   orbit_class   : JPL orbit class code, e.g. "AMO", "APO", "ATE"
--   earth_moid    : minimum orbit intersection distance with Earth in AU
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS OrbitalData (
    id              INT             NOT NULL,
    eccentricity    DECIMAL(14, 10) NULL,
    inclination     DECIMAL(10, 6)  NULL,
    orbital_period  DECIMAL(14, 6)  NULL,
    orbit_class     CHAR(3)         NULL,
    earth_moid      DECIMAL(12, 8)  NULL,
    CONSTRAINT pk_orbdata PRIMARY KEY (id),
    CONSTRAINT fk_orbdata_neo FOREIGN KEY (id)
        REFERENCES NEOs (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_orbdata_eccentricity CHECK (eccentricity IS NULL OR eccentricity >= 0),
    CONSTRAINT chk_orbdata_inclination  CHECK (inclination  IS NULL OR (inclination >= 0 AND inclination <= 180)),
    CONSTRAINT chk_orbdata_period       CHECK (orbital_period IS NULL OR orbital_period > 0),
    CONSTRAINT chk_orbdata_moid         CHECK (earth_moid IS NULL OR earth_moid >= 0)
);

-- ---------------------------------------------------------------
-- CloseApproaches  (1-to-many with NEOs)
--   approach_id      : synthetic surrogate PK (auto-increment)
--   id               : FK to NEOs
--   close_approach_date : calendar date of closest approach
--   miss_distance    : miss distance in AU
--   relative_velocity: relative velocity at closest approach in km/s
--   v_infinity       : hyperbolic excess speed in km/s
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS CloseApproaches (
    approach_id         INT             NOT NULL AUTO_INCREMENT,
    id                  INT             NOT NULL,
    close_approach_date DATE            NOT NULL,
    miss_distance       DECIMAL(16, 10) NULL,
    relative_velocity   DECIMAL(12, 6)  NULL,
    v_infinity          DECIMAL(12, 6)  NULL,
    CONSTRAINT pk_closeapproach PRIMARY KEY (approach_id),
    CONSTRAINT fk_closeapproach_neo FOREIGN KEY (id)
        REFERENCES NEOs (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_closeapproach_miss_dist CHECK (miss_distance IS NULL OR miss_distance >= 0),
    CONSTRAINT chk_closeapproach_relvel    CHECK (relative_velocity IS NULL OR relative_velocity >= 0),
    CONSTRAINT chk_closeapproach_vinf      CHECK (v_infinity IS NULL OR v_infinity >= 0)
);

-- ---------------------------------------------------------------
-- ObservationRecord  (1-to-many with NEOs)
--   observation_id : synthetic surrogate PK (auto-increment)
--   id             : FK to NEOs
--   discovering_org: organization or producer of the orbit solution
--   first_obs      : date of first observation used in solution
--   latest_obs     : date of most recent observation used
--   num_obs        : total number of observations used
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ObservationRecord (
    observation_id  INT             NOT NULL AUTO_INCREMENT,
    id              INT             NOT NULL,
    discovering_org VARCHAR(120)    NULL,
    first_obs       DATE            NULL,
    latest_obs      DATE            NULL,
    num_obs         INT UNSIGNED    NULL,
    CONSTRAINT pk_obsrec PRIMARY KEY (observation_id),
    CONSTRAINT fk_obsrec_neo FOREIGN KEY (id)
        REFERENCES NEOs (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_obsrec_dates CHECK (first_obs IS NULL OR latest_obs IS NULL OR first_obs <= latest_obs),
    CONSTRAINT chk_obsrec_numobs CHECK (num_obs IS NULL OR num_obs >= 0)
);

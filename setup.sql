CREATE TABLE NEOs (
    neo_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    discovery_date DATETIME NOT NULL,
    potentially_hazardous BOOLEAN NOT NULL
);

CREATE TABLE Observatory (
    observatory_code VARCHAR(50) PRIMARY KEY,
    observatory_name VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    elevation FLOAT,
    CHECK (latitude BETWEEN -90 AND 90),
    CHECK (longitude BETWEEN -180 AND 180)
);

CREATE TABLE PhysicalInfo (
    neo_id VARCHAR(50) PRIMARY KEY,
    diameter FLOAT NOT NULL,
    absolute_magnitude FLOAT NOT NULL,
    albedo FLOAT,
    spectral_class CHAR(1),
    FOREIGN KEY (neo_id) REFERENCES NEOs(neo_id)
        ON DELETE CASCADE,
    CHECK (diameter > 0),
    CHECK (albedo IS NULL OR (albedo BETWEEN 0 AND 1)),
    CHECK (spectral_class IN ('C','S','X') OR spectral_class IS NULL)
);

CREATE TABLE OrbitalData (
    neo_id VARCHAR(50) PRIMARY KEY,
    eccentricity FLOAT NOT NULL,
    inclination FLOAT NOT NULL,
    orbital_period FLOAT NOT NULL,
    orbit_class VARCHAR(20) NOT NULL,
    moid FLOAT NOT NULL,
    FOREIGN KEY (neo_id) REFERENCES NEOs(neo_id)
        ON DELETE CASCADE,
    CHECK (eccentricity BETWEEN 0 AND 1),
    CHECK (orbital_period > 0),
    CHECK (moid >= 0),
    CHECK (orbit_class IN ('Aten','Apollo','Amor','Atira'))
);

CREATE TABLE Observation (
    observation_id VARCHAR(50) PRIMARY KEY,
    neo_id VARCHAR(50) NOT NULL,
    observatory_code VARCHAR(50) NOT NULL,
    observation_date DATETIME NOT NULL,
    snr FLOAT,
    FOREIGN KEY (neo_id) REFERENCES NEOs(neo_id)
        ON DELETE CASCADE,
    FOREIGN KEY (observatory_code) REFERENCES Observatory(observatory_code)
        ON DELETE CASCADE,
    CHECK (snr IS NULL OR snr >= 0)
);

CREATE TABLE CloseApproaches (
    approach_id VARCHAR(50) PRIMARY KEY,
    neo_id VARCHAR(50) NOT NULL,
    close_approach_date DATETIME NOT NULL,
    miss_distance FLOAT NOT NULL,
    relative_velocity FLOAT NOT NULL,
    impact_probability FLOAT,
    FOREIGN KEY (neo_id) REFERENCES NEOs(neo_id)
        ON DELETE CASCADE,
    CHECK (miss_distance >= 0),
    CHECK (relative_velocity >= 0),
    CHECK (impact_probability IS NULL OR (impact_probability BETWEEN 0 AND 1))
);
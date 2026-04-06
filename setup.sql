-- Create NEOs table
CREATE TABLE NEOs (
    neo_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    discovery_date DATE,
    potentially_hazardous BOOLEAN DEFAULT FALSE
);

-- Create PhysicalInfo table
CREATE TABLE PhysicalInfo (
    neo_id VARCHAR(50) PRIMARY KEY,
    diameter FLOAT,  -- in km
    absolute_magnitude FLOAT,
    albedo FLOAT,    -- NULL if unknown
    spectral_class CHAR(1),  -- C, S, X, etc.
    FOREIGN KEY (neo_id) REFERENCES NEOs(neo_id) ON DELETE CASCADE
);

-- Create OrbitalData table
CREATE TABLE OrbitalData (
    neo_id VARCHAR(50) PRIMARY KEY,
    eccentricity FLOAT CHECK (eccentricity >= 0 AND eccentricity <= 1),
    inclination FLOAT,  -- degrees
    orbital_period FLOAT,  -- years
    orbit_class VARCHAR(20),  -- Atira, Aten, Apollo, Amor, etc.
    moid FLOAT,  -- Minimum Orbit Intersection Distance (AU)
    FOREIGN KEY (neo_id) REFERENCES NEOs(neo_id) ON DELETE CASCADE
);

-- Create CloseApproaches table
CREATE TABLE CloseApproaches (
    approach_id INT AUTO_INCREMENT PRIMARY KEY,
    neo_id VARCHAR(50) NOT NULL,
    close_approach_date DATETIME,
    miss_distance FLOAT,  -- AU
    relative_velocity FLOAT,  -- km/s
    v_infinity FLOAT,  -- km/s (velocity relative to massless body)
    FOREIGN KEY (neo_id) REFERENCES NEOs(neo_id) ON DELETE CASCADE
);
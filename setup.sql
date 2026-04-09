-- setup.sql  
-- Create the four observation tables for NEO Hazard Assessment Database

-- NEO Identity
CREATE TABLE IF NOT EXISTS NEO (
    spkid INT NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    pha CHAR(1) NOT NULL DEFAULT 'N',
    class VARCHAR(10) NOT NULL,
    PRIMARY KEY (spkid)
);

-- Physical properties 
CREATE TABLE IF NOT EXISTS PhysicalProperties (
    spkid INT NOT NULL,
    H DOUBLE DEFAULT NULL,
    diameter DOUBLE DEFAULT NULL,
    PRIMARY KEY (spkid),
    FOREIGN KEY (spkid) REFERENCES NEO (spkid)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Orbital elements 
CREATE TABLE IF NOT EXISTS OrbitalElements (
    spkid INT NOT NULL,
    e DOUBLE DEFAULT NULL,
    q DOUBLE DEFAULT NULL,
    i DOUBLE DEFAULT NULL,
    moid DOUBLE DEFAULT NULL,
    moid_ld DOUBLE DEFAULT NULL,
    PRIMARY KEY (spkid),
    FOREIGN KEY (spkid) REFERENCES NEO (spkid)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Observation quality 
CREATE TABLE IF NOT EXISTS ObservationRecord (
    spkid INT NOT NULL,
    data_arc INT DEFAULT NULL,
    condition_code INT DEFAULT NULL,
    PRIMARY KEY (spkid),
    FOREIGN KEY (spkid) REFERENCES NEO (spkid)
        ON DELETE CASCADE ON UPDATE CASCADE
);
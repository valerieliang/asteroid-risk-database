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

-- PredictedPHAs
-- This table is separate from the main NEO table because predicted PHA status
-- represents model inference, not ground truth, and maintains a clean audit trail of
-- which objects have been classified by the ML model vs. official sources.
CREATE TABLE IF NOT EXISTS PredictedPHAs (
    spkid INT NOT NULL,  -- Changed to INT to match NEO table
    pred_pha CHAR(1) NOT NULL CHECK (pred_pha IN ('Y', 'N')),
    pha_prob DECIMAL(5,4) NOT NULL CHECK (pha_prob >= 0 AND pha_prob <= 1),
    PRIMARY KEY (spkid),
    FOREIGN KEY (spkid) REFERENCES NEO(spkid) ON DELETE CASCADE
);

-- OrbitalAnomalies
-- This table is separate from the orbital elements table to maintain a clean separation 
-- between raw orbital data and derived anomaly flags.
CREATE TABLE OrbitalAnomalies (
    spkid INT NOT NULL,
    class VARCHAR(20) NOT NULL,
    moid_anomaly_yn CHAR(1) NOT NULL CHECK (moid_anomaly_yn IN ('Y', 'N')),
    e_anomaly_yn CHAR(1) NOT NULL CHECK (e_anomaly_yn IN ('Y', 'N')),
    i_anomaly_yn CHAR(1) NOT NULL CHECK (i_anomaly_yn IN ('Y', 'N')),
    anomaly_flag CHAR(1) NOT NULL CHECK (anomaly_flag IN ('Y', 'N')),
    PRIMARY KEY (spkid),
    FOREIGN KEY (spkid) REFERENCES NEO(spkid) ON DELETE CASCADE
);
-- ============================================================
-- Query 1
-- Which asteroids are classified as Potentially Hazardous and
-- have a diameter greater than 1 km, sorted by MOID ascending?
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    pp.diameter,
    oe.moid,
    oe.moid_ld
FROM NEO n
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
WHERE n.pha = 'Y'
    AND pp.diameter > 1.0
ORDER BY oe.moid ASC;


-- ============================================================
-- Query 2
-- How many NEOs exist per orbital class, and what fraction
-- of each class is classified as Potentially Hazardous?
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS total_count,
    SUM(CASE WHEN n.pha = 'Y' THEN 1 ELSE 0 END) AS pha_count,
    ROUND(
        100.0 * SUM(CASE WHEN n.pha = 'Y' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS pha_pct
FROM NEO n
GROUP BY n.class
ORDER BY total_count DESC;


-- ============================================================
-- Query 3
-- List all NEOs by orbital class with their average diameter
-- and average MOID per class, ordered by average MOID ascending.
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS neo_count,
    AVG(pp.diameter) AS avg_diameter_km,
    AVG(oe.moid) AS avg_moid_au,
    AVG(oe.moid_ld) AS avg_moid_ld
FROM NEO n
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
WHERE pp.diameter IS NOT NULL
    AND oe.moid IS NOT NULL
GROUP BY n.class
ORDER BY avg_moid_au ASC;


-- ============================================================
-- Query 4
-- Which 10 NEOs have the smallest absolute magnitude (H) (so
-- they are potentially the largest/brightest objects) and what
-- are their key physical and orbital properties?
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha,
    pp.H,
    pp.diameter,
    oe.moid,
    oe.e,
    oe.i
FROM NEO n
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
WHERE pp.H IS NOT NULL
ORDER BY pp.H ASC
LIMIT 10;


-- ============================================================
-- Query 5
-- Which asteroids have the best-determined orbits?
-- List NEOs with the smallest condition_code (best quality)
-- along with their observation arc length and MOID.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha,
    ob.condition_code,
    ob.data_arc AS observation_days,
    oe.moid,
    pp.diameter
FROM NEO n
JOIN ObservationRecord ob ON n.spkid = ob.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
WHERE ob.condition_code < 2
ORDER BY ob.condition_code ASC;

-- ============================================================
-- Query 6
-- Which asteroids have a MOID < 0.05 AU AND an estimated
-- diameter > 0.14 km (the 140-m city-killer threshold)?
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.pha,
    n.class,
    pp.diameter,
    oe.moid,
    oe.moid_ld,
    ob.data_arc
FROM NEO n
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
JOIN ObservationRecord ob ON n.spkid = ob.spkid
WHERE oe.moid < 0.05
    AND pp.diameter > 0.14
ORDER BY oe.moid ASC, pp.diameter DESC;


-- ============================================================
-- Query 7
-- Identify NEOs with poor observational quality (condition_code
-- >= 7) that are still flagged as Potentially Hazardous -- these
-- represent the highest-uncertainty threats.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    ob.condition_code,
    ob.data_arc,
    oe.moid,
    pp.diameter,
    pp.H
FROM NEO n
JOIN ObservationRecord ob ON n.spkid = ob.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
WHERE n.pha = 'Y'
    AND ob.condition_code >= 7
ORDER BY ob.condition_code DESC, oe.moid ASC;


-- ============================================================
-- Query 8
-- Which asteroids have the longest observational arcs
-- (data_arc in days), and what are their orbital properties?
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha,
    ob.data_arc,
    ob.condition_code,
    oe.e,
    oe.i,
    oe.moid
FROM NEO n
JOIN ObservationRecord ob ON n.spkid = ob.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
WHERE ob.data_arc IS NOT NULL
ORDER BY ob.data_arc DESC
LIMIT 50;


-- ============================================================
-- Query 9
-- What is the distribution of perihelion distance (q) across
-- NEO classes? Identify which classes contain Sun-approaching
-- objects (q < 0.3 AU) vs. more typical Earth-crossers.
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS neo_count,
    MIN(oe.q) AS min_q_au,
    MAX(oe.q) AS max_q_au,
    AVG(oe.q) AS avg_q_au,
    SUM(CASE WHEN oe.q < 0.3 THEN 1 ELSE 0 END) AS sun_approaching_count,
    SUM(CASE WHEN oe.q BETWEEN 0.3 AND 1.0 THEN 1 ELSE 0 END) AS earth_crosser_count
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
WHERE oe.q IS NOT NULL
GROUP BY n.class
ORDER BY avg_q_au ASC;


-- ============================================================
-- Query 10
-- For each orbital class with more than 10 known members,
-- compute the average diameter and average absolute magnitude
-- (H) of the objects within the class.
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS member_count,
    AVG(pp.diameter) AS avg_diameter_km,
    AVG(pp.H) AS avg_magnitude_H
FROM NEO n
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
WHERE pp.diameter IS NOT NULL
    AND pp.H IS NOT NULL
GROUP BY n.class
HAVING COUNT(*) > 10
ORDER BY member_count DESC;


-- ============================================================
-- Query 11
-- Which PHA asteroids have the smallest MOID (top 20 closest
-- Earth-approachers by orbit geometry)?
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    oe.moid,
    oe.moid_ld,
    pp.diameter,
    pp.H,
    ob.data_arc,
    ob.condition_code
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN ObservationRecord ob ON n.spkid = ob.spkid
WHERE n.pha = 'Y'
ORDER BY oe.moid ASC
LIMIT 20;


-- ============================================================
-- Query 12
-- What is the distribution of orbital eccentricity across
-- all NEO classes? Return min, max, mean, and std-dev per class.
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS neo_count,
    MIN(oe.e) AS min_e,
    MAX(oe.e) AS max_e,
    AVG(oe.e) AS mean_e,
    STDDEV_POP(oe.e) AS stddev_e,
    AVG(oe.i) AS mean_incl_deg,
    STDDEV_POP(oe.i) AS stddev_incl_deg
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
WHERE oe.e IS NOT NULL
    AND oe.i IS NOT NULL
GROUP BY n.class
ORDER BY mean_e DESC;


-- ============================================================
-- Query 13
-- Find asteroids with very high eccentricity (e > 0.9) that
-- are also potentially hazardous -- possible cometary or
-- highly perturbed objects.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha,
    oe.e,
    oe.i,
    oe.q,
    oe.moid,
    pp.diameter,
    pp.H
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
WHERE oe.e > 0.9
ORDER BY oe.e DESC, oe.moid ASC;


-- ============================================================
-- Query 14
-- What fraction of each orbital class is classified as PHA?
-- Return class, total count, PHA count, and PHA percentage.
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS total_neos,
    SUM(CASE WHEN n.pha = 'Y' THEN 1 ELSE 0 END) AS pha_count,
    ROUND(
        100.0 * SUM(CASE WHEN n.pha = 'Y' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS pha_pct
FROM NEO n
GROUP BY n.class
ORDER BY pha_pct DESC;


-- ============================================================
-- Query 15
-- Which asteroids have both a very small perihelion distance
-- (q < 0.5 AU, Sun-grazing or Sun-approaching) and a large
-- inclination (i > 45 deg), suggesting unusual orbital dynamics?
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha,
    oe.q,
    oe.i,
    oe.e,
    oe.moid,
    pp.diameter,
    ob.data_arc
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN ObservationRecord ob ON n.spkid = ob.spkid
WHERE oe.q < 0.5
    AND oe.i > 45.0
ORDER BY oe.q ASC, oe.i DESC;
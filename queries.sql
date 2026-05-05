-- ============================================================
-- Query 1: Potentially hazardous NEOs with reliable orbits
-- Motivation: For planetary defense, we need to prioritize threats. 
-- A PHA flag with a poorly determined orbit (high condition_code) might be a false alarm.
-- By filtering for condition_code <= 2 (highly reliable orbits) and sorting by MOID 
-- (Minimum Orbit Intersection Distance), we identify the closest confirmed threats 
-- that require immediate radar tracking or risk assessment.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    ROUND(pp.diameter, 2) AS diameter_km,
    oe.moid,
    ROUND(oe.moid_ld, 1) AS moid_ld,
    ob.condition_code,
    ob.data_arc AS observation_days
FROM NEO n
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
JOIN ObservationRecord ob ON n.spkid = ob.spkid
WHERE n.pha = 'Y'
    AND ob.condition_code <= 2
    AND pp.diameter IS NOT NULL
ORDER BY oe.moid ASC
LIMIT 20;

-- ============================================================
-- Query 2: NEOs per orbital class with PHA comparison
-- Motivation: Different orbital classes (Apollo, Aten, Amor) represent distinct 
-- dynamical populations. Understanding what fraction of each class is actually 
-- hazardous vs. predicted by ML helps validate our risk models. For example, 
-- if ML predicts high risk for Atens (which orbit inside Earth), but the official 
-- flag disagrees, we may need to recalibrate our prediction algorithms.
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS total_count,
    SUM(CASE WHEN n.pha = 'Y' THEN 1 ELSE 0 END) AS pha_flag_count,
    ROUND(100.0 * SUM(CASE WHEN n.pha = 'Y' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pha_flag_pct,
    SUM(CASE WHEN p.pred_pha = 'Y' THEN 1 ELSE 0 END) AS pred_pha_count,
    ROUND(100.0 * SUM(CASE WHEN p.pred_pha = 'Y' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pred_pha_pct
FROM NEO n
LEFT JOIN PredictedPHAs p ON n.spkid = p.spkid
GROUP BY n.class
ORDER BY total_count DESC;

-- ============================================================
-- Query 3: Average properties by orbital class
-- Motivation: This serves as a baseline for "typical" NEO behavior. 
-- By knowing the average diameter, eccentricity, and inclination for each class, 
-- we can detect outliers that deviate from the norm. Outliers often represent 
-- fragmented comets, interstellar objects, or perturbed asteroids that may have 
-- unpredictable trajectories.
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS neo_count,
    ROUND(AVG(pp.diameter), 2) AS avg_diameter_km,
    ROUND(AVG(pp.H), 2) AS avg_magnitude_H,
    ROUND(AVG(oe.e), 4) AS avg_eccentricity,
    ROUND(AVG(oe.i), 2) AS avg_inclination_deg,
    ROUND(AVG(oe.moid), 6) AS avg_moid_au,
    ROUND(AVG(oe.moid_ld), 1) AS avg_moid_ld
FROM NEO n
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
WHERE pp.diameter IS NOT NULL
    AND pp.H IS NOT NULL
GROUP BY n.class
ORDER BY avg_moid_au ASC;

-- ============================================================
-- Query 4: Brightest/largest NEOs with ML predictions
-- Motivation: Absolute magnitude (H) correlates strongly with size. 
-- The largest NEOs (lowest H) are capable of causing global extinction events 
-- (like the 10km dinosaur-killer). We must track these "planet-killers" regardless 
-- of their current MOID, because a small perturbation could redirect them toward Earth. 
-- This query adds ML risk percentages to see if our models agree.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha AS official_pha,
    pp.H,
    ROUND(pp.diameter, 2) AS diameter_km,
    oe.moid,
    ROUND(oe.moid_ld, 1) AS moid_ld,
    p.pred_pha,
    ROUND(p.pha_prob * 100, 2) AS risk_percent
FROM NEO n
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN PredictedPHAs p ON n.spkid = p.spkid
WHERE pp.H IS NOT NULL
ORDER BY pp.H ASC
LIMIT 10;

-- ============================================================
-- Query 5: City-killer NEOs (diameter > 140m, MOID < 0.05 AU)
-- Motivation: The Chelyabinsk event (2013, ~20m) injured 1,500 people. 
-- A 140m "city-killer" would devastate a metropolitan area. 
-- MOID < 0.05 AU (~7.5 million km) is considered a "close approach" in astronomical terms. 
-- This intersection defines the most urgent targets for deflection mission planning 
-- (e.g., NASA's DART mission). Any asteroid meeting both criteria demands immediate follow-up.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.pha AS official_pha,
    n.class,
    ROUND(pp.diameter, 3) AS diameter_km,
    oe.moid,
    ROUND(oe.moid_ld, 1) AS moid_ld,
    ob.data_arc AS observation_days,
    ob.condition_code,
    p.pred_pha,
    ROUND(p.pha_prob * 100, 2) AS risk_pct
FROM NEO n
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
JOIN ObservationRecord ob ON n.spkid = ob.spkid
LEFT JOIN PredictedPHAs p ON n.spkid = p.spkid
WHERE oe.moid < 0.05
    AND pp.diameter > 0.14
ORDER BY oe.moid ASC, pp.diameter DESC;

-- ============================================================
-- Query 6: ML prediction discrepancies (false positives/negatives)
-- Motivation: This is the "red team" analysis for our machine learning model. 
-- False negatives (missed PHAs) are catastrophic: an asteroid we thought safe 
-- actually impacts. False positives (false alarms) waste telescope time and 
-- cause public panic. Analyzing these discrepancies reveals which features 
-- (e.g., high eccentricity, unusual inclination) confuse the classifier, 
-- allowing us to retrain the model with better weights.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha AS official_pha,
    p.pred_pha,
    ROUND(p.pha_prob * 100, 2) AS risk_probability,
    CASE 
        WHEN n.pha = 'Y' AND p.pred_pha = 'N' THEN 'False Negative (Missed)'
        WHEN n.pha = 'N' AND p.pred_pha = 'Y' THEN 'False Positive (False Alarm)'
        ELSE 'Agreement'
    END AS prediction_status,
    oa.anomaly_flag,
    ROUND(pp.diameter, 2) AS diameter_km,
    oe.moid
FROM NEO n
JOIN PredictedPHAs p ON n.spkid = p.spkid
LEFT JOIN PhysicalProperties pp ON n.spkid = pp.spkid
LEFT JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN OrbitalAnomalies oa ON n.spkid = oa.spkid
WHERE (n.pha = 'Y' AND p.pred_pha = 'N')
    OR (n.pha = 'N' AND p.pred_pha = 'Y')
ORDER BY p.pha_prob DESC
LIMIT 30;

-- ============================================================
-- Query 7: High-risk PHAs (probability > 0.5) despite moderate MOID
-- Motivation: Traditional risk assessment relies heavily on MOID (distance of closest approach). 
-- However, an asteroid with moderate MOID might still be dangerous due to gravitational 
-- keyholes—specific points where Earth's gravity bends the orbit into a future impact. 
-- If ML assigns >50% risk despite MOID > 0.05 AU, these objects need precise 
-- radio-radar ranging to rule out resonance returns or Yarkovsky effect drift.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    oe.moid,
    ROUND(oe.moid_ld, 1) AS moid_ld,
    ROUND(pp.diameter, 2) AS diameter_km,
    pp.H,
    p.pha_prob,
    ROUND(p.pha_prob * 100, 2) AS risk_percent,
    ob.data_arc AS observation_days,
    ob.condition_code,
    oa.anomaly_flag
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN PredictedPHAs p ON n.spkid = p.spkid
JOIN ObservationRecord ob ON n.spkid = ob.spkid
LEFT JOIN OrbitalAnomalies oa ON n.spkid = oa.spkid
WHERE n.pha = 'Y'
    AND p.pha_prob > 0.5
ORDER BY p.pha_prob DESC
LIMIT 30;

-- ============================================================
-- Query 8: Summary statistics comparing official vs ML predictions
-- Motivation: High-level dashboard for risk managers and space agencies. 
-- It answers: How many asteroids are we tracking? What fraction are actually dangerous? 
-- How many anomalies (suspicious orbital behaviors) exist? And critically, 
-- what is the average ML risk percentage? If avg_ml_risk_pct is rising over time, 
-- it suggests we are discovering more threatening objects or the model is becoming 
-- more sensitive (possibly due to better data).
-- ============================================================
SELECT
    'Overall Database' AS category,
    COUNT(DISTINCT n.spkid) AS total_asteroids,
    SUM(CASE WHEN n.pha = 'Y' THEN 1 ELSE 0 END) AS official_pha_count,
    SUM(CASE WHEN p.pred_pha = 'Y' THEN 1 ELSE 0 END) AS ml_pred_pha_count,
    SUM(CASE WHEN oa.anomaly_flag = 'Y' THEN 1 ELSE 0 END) AS anomaly_count,
    ROUND(AVG(pp.diameter), 2) AS avg_diameter_km,
    ROUND(AVG(oe.moid), 6) AS avg_moid_au,
    ROUND(AVG(p.pha_prob) * 100, 2) AS avg_ml_risk_pct
FROM NEO n
LEFT JOIN PhysicalProperties pp ON n.spkid = pp.spkid
LEFT JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN PredictedPHAs p ON n.spkid = p.spkid
LEFT JOIN OrbitalAnomalies oa ON n.spkid = oa.spkid;

-- ============================================================
-- Query 9: Best-determined orbits (condition_code = 0)
-- Motivation: The "gold standard" asteroids. Condition_code = 0 means the orbit is 
-- determined with uncertainty < 1 arcsecond. These are ideal candidates for 
-- spacecraft missions (e.g., sample return, deflection tests) because we can 
-- predict their position accurately for years. The observation_years column shows 
-- how long we've tracked them—decades-long arcs reveal subtle perturbations 
-- from non-gravitational forces (like solar radiation pressure).
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha,
    ob.condition_code,
    ob.data_arc AS observation_days,
    ROUND(ob.data_arc / 365.25, 1) AS observation_years,
    oe.moid,
    ROUND(pp.diameter, 2) AS diameter_km,
    oa.anomaly_flag,
    CONCAT_WS(', ',
        CASE WHEN oa.moid_anomaly_yn = 'Y' THEN 'MOID' END,
        CASE WHEN oa.e_anomaly_yn = 'Y' THEN 'Eccentricity' END,
        CASE WHEN oa.i_anomaly_yn = 'Y' THEN 'Inclination' END
    ) AS anomaly_types
FROM NEO n
JOIN ObservationRecord ob ON n.spkid = ob.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN PhysicalProperties pp ON n.spkid = pp.spkid
LEFT JOIN OrbitalAnomalies oa ON n.spkid = oa.spkid
WHERE ob.condition_code = 0
ORDER BY ob.data_arc DESC
LIMIT 30;

-- ============================================================
-- Query 10: Perihelion distribution by class
-- Motivation: Perihelion (q) is the closest distance to the Sun. 
-- Sun-approaching objects (q < 0.3 AU) experience extreme heating, 
-- which can cause thermal fracturing, outgassing, or even disintegration 
-- (like sungrazing comets). Earth-crossers (q between 0.3 and 1.0 AU) are 
-- the ones that actually intersect our orbit. This query quantifies how many 
-- NEOs in each class are true "fireballs" versus harmless outer-orbit objects.
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS neo_count,
    ROUND(MIN(oe.q), 4) AS min_q_au,
    ROUND(MAX(oe.q), 4) AS max_q_au,
    ROUND(AVG(oe.q), 4) AS avg_q_au,
    SUM(CASE WHEN oe.q < 0.3 THEN 1 ELSE 0 END) AS sun_approaching_count,
    SUM(CASE WHEN oe.q BETWEEN 0.3 AND 1.0 THEN 1 ELSE 0 END) AS earth_crosser_count,
    ROUND(100.0 * SUM(CASE WHEN oe.q < 0.3 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_sun_approaching,
    SUM(CASE WHEN oa.anomaly_flag = 'Y' THEN 1 ELSE 0 END) AS anomaly_count
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN OrbitalAnomalies oa ON n.spkid = oa.spkid
WHERE oe.q IS NOT NULL
GROUP BY n.class
ORDER BY avg_q_au ASC;

-- ============================================================
-- Query 11: Class statistics for groups with >10 members
-- Motivation: Small sample sizes (classes with <10 members) produce unreliable statistics. 
-- By filtering for classes with >10 known asteroids, we ensure our averages 
-- and standard deviations are statistically meaningful. The standard deviation 
-- of diameter tells us if a class contains a mix of tiny pebbles and large boulders 
-- (high stddev) or is relatively uniform (low stddev). Anomaly percentage reveals 
-- which orbital families have the most "weird" members that warrant individual study.
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS member_count,
    ROUND(AVG(pp.diameter), 2) AS avg_diameter_km,
    ROUND(STDDEV(pp.diameter), 2) AS stddev_diameter_km,
    ROUND(AVG(pp.H), 2) AS avg_magnitude_H,
    ROUND(AVG(oe.e), 4) AS avg_eccentricity,
    ROUND(AVG(oe.i), 2) AS avg_inclination_deg,
    SUM(CASE WHEN oa.anomaly_flag = 'Y' THEN 1 ELSE 0 END) AS anomaly_count,
    ROUND(100.0 * SUM(CASE WHEN oa.anomaly_flag = 'Y' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_anomalies
FROM NEO n
JOIN PhysicalProperties pp ON n.spkid = pp.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN OrbitalAnomalies oa ON n.spkid = oa.spkid
WHERE pp.diameter IS NOT NULL
    AND pp.H IS NOT NULL
GROUP BY n.class
HAVING COUNT(*) > 10
ORDER BY member_count DESC;

-- ============================================================
-- Query 12: Eccentricity distribution by class
-- Motivation: Eccentricity (e) measures how elongated an orbit is. 
-- e = 0 is circular, e > 1 is hyperbolic (interstellar). High eccentricity NEOs 
-- (e > 0.8) often originate from the Oort cloud or main belt collisions. 
-- They are harder to track because they move fast at perihelion and slow 
-- at aphelion. This query reveals which classes have the most extreme 
-- eccentricity distributions—Atiras (e near 0) are boring circles, 
-- while Oort cloud comets (e near 1) are edge cases. e_anomaly_count identifies 
-- statistical outliers for targeted observation.
-- ============================================================
SELECT
    n.class,
    COUNT(*) AS neo_count,
    ROUND(MIN(oe.e), 4) AS min_e,
    ROUND(MAX(oe.e), 4) AS max_e,
    ROUND(AVG(oe.e), 4) AS mean_e,
    ROUND(STDDEV_POP(oe.e), 4) AS stddev_e,
    ROUND(AVG(oe.i), 2) AS mean_incl_deg,
    ROUND(STDDEV_POP(oe.i), 2) AS stddev_incl_deg,
    SUM(CASE WHEN oa.e_anomaly_yn = 'Y' THEN 1 ELSE 0 END) AS e_anomaly_count
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN OrbitalAnomalies oa ON n.spkid = oa.spkid
WHERE oe.e IS NOT NULL
    AND oe.i IS NOT NULL
GROUP BY n.class
ORDER BY mean_e DESC;

-- ============================================================
-- Query 13: High-eccentricity NEOs (e > 0.9)
-- Motivation: Extreme eccentricity objects are exotic: they could be 
-- dormant comets that still have volatile ices, fragments from giant impacts, 
-- or even captured interstellar objects (like 'Oumuamua). 
-- Their orbits are chaotic and hard to predict decades in advance. 
-- This query lists the "wild cards" of the solar system. If any of these 
-- also have a high ML risk percentage, they become top priority for 
-- spectroscopic analysis to determine composition (rocky vs icy).
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha,
    ROUND(oe.e, 4) AS eccentricity,
    ROUND(oe.i, 2) AS inclination_deg,
    ROUND(oe.q, 4) AS perihelion_au,
    ROUND(oe.moid, 6) AS moid_au,
    ROUND(pp.diameter, 2) AS diameter_km,
    pp.H,
    p.pred_pha,
    ROUND(p.pha_prob * 100, 2) AS ml_risk_pct,
    oa.anomaly_flag
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN PhysicalProperties pp ON n.spkid = pp.spkid
LEFT JOIN PredictedPHAs p ON n.spkid = p.spkid
LEFT JOIN OrbitalAnomalies oa ON n.spkid = oa.spkid
WHERE oe.e > 0.9
ORDER BY oe.e DESC, oe.moid ASC
LIMIT 30;

-- ============================================================
-- Query 14: Sun-grazing (q < 0.5 AU) and high-inclination (i > 45°)
-- Motivation: These are the "out-of-plane" weirdos. Most planets orbit 
-- within 3 degrees of the ecliptic plane. Objects with i > 45° are 
-- in polar or retrograde orbits—they came from the Oort cloud or were 
-- violently scattered by Jupiter. Combining this with q < 0.5 AU (Sun-grazing) 
-- means they dive through the inner solar system perpendicular to everything else. 
-- They're difficult to detect because they approach from above/below typical survey fields.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha,
    ROUND(oe.q, 4) AS perihelion_au,
    ROUND(oe.i, 2) AS inclination_deg,
    ROUND(oe.e, 4) AS eccentricity,
    ROUND(oe.moid, 6) AS moid_au,
    ROUND(oe.moid_ld, 1) AS moid_ld,
    ROUND(pp.diameter, 2) AS diameter_km,
    ob.data_arc AS observation_days,
    p.pred_pha,
    ROUND(p.pha_prob * 100, 2) AS ml_risk_pct,
    oa.anomaly_flag,
    CONCAT_WS(', ',
        CASE WHEN oa.moid_anomaly_yn = 'Y' THEN 'MOID' END,
        CASE WHEN oa.e_anomaly_yn = 'Y' THEN 'Eccentricity' END,
        CASE WHEN oa.i_anomaly_yn = 'Y' THEN 'Inclination' END
    ) AS anomaly_types
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN PhysicalProperties pp ON n.spkid = pp.spkid
LEFT JOIN ObservationRecord ob ON n.spkid = ob.spkid
LEFT JOIN PredictedPHAs p ON n.spkid = p.spkid
LEFT JOIN OrbitalAnomalies oa ON n.spkid = oa.spkid
WHERE oe.q < 0.5
    AND oe.i > 45.0
ORDER BY oe.q ASC, oe.i DESC;

-- ============================================================
-- Query 15: Full orbital ellipse reconstruction
-- Motivation: This query transforms Keplerian elements into geometric 
-- parameters needed for visualization (e.g., in Python's matplotlib or JS's Three.js). 
-- By computing semi-major axis, perihelion, aphelion, and center offset, 
-- we can plot the actual orbit ellipses around the Sun. The classification 
-- (Earth-Crossing, Earth-Approaching, etc.) helps mission planners design 
-- intercept trajectories. For example, an "Earth-Crossing" asteroid is reachable 
-- by a spacecraft launched from Earth, while "Inside Earth Orbit" requires 
-- a solar-powered probe.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    oe.e AS eccentricity,
    ROUND(oe.q / (1 - oe.e), 4) AS semi_major_axis_au,
    ROUND(oe.q, 4) AS perihelion_au,
    ROUND(oe.q * (1 + oe.e) / (1 - oe.e), 4) AS aphelion_au,
    ROUND((oe.q * (1 + oe.e) / (1 - oe.e) + oe.q) / 2, 4) AS center_offset_au,
    ROUND((oe.q * (1 + oe.e) / (1 - oe.e) - oe.q) / 2, 4) AS semi_latus_rectum,
    ROUND(oe.q * (1 + oe.e) / (1 - oe.e) - 1.0, 4) AS beyond_earth_au,
    CASE 
        WHEN oe.q < 1.0 AND oe.q * (1 + oe.e) / (1 - oe.e) > 1.0 THEN 'Earth-Crossing'
        WHEN oe.q < 1.0 THEN 'Earth-Approaching (Inside Only)'
        WHEN oe.q * (1 + oe.e) / (1 - oe.e) > 1.0 THEN 'Earth-Approaching (Outside Only)'
        WHEN oe.q > 1.0 AND oe.q * (1 + oe.e) / (1 - oe.e) < 1.0 THEN 'Inside Earth Orbit'
        ELSE 'Safe'
    END AS earth_intersection_type,
    ROUND(oe.moid, 6) AS moid_au,
    p.pred_pha,
    ROUND(p.pha_prob * 100, 2) AS ml_risk_pct
FROM NEO n
JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN PredictedPHAs p ON n.spkid = p.spkid
WHERE oe.e < 0.99
    AND oe.e != 1.0
    AND oe.q IS NOT NULL
ORDER BY semi_major_axis_au ASC
LIMIT 100;

-- ============================================================
-- Query 16: Longest observational arcs (>27 years)
-- Motivation: Observational arc length is the most important factor 
-- in orbit certainty. Objects tracked for decades (data_arc > 10,000 days) 
-- have had their positions measured over many orbital periods, allowing 
-- astronomers to detect subtle gravitational perturbations from other planets 
-- and non-gravitational forces (like Yarkovsky effect—infrared emission causing drift). 
-- These "well-studied" asteroids serve as anchors for calibrating dynamical models. 
-- If an anomaly_flag exists despite long observations, it means the object is 
-- weird for reasons other than measurement error.
-- ============================================================
SELECT
    n.spkid,
    n.full_name,
    n.class,
    n.pha,
    ob.data_arc AS observation_days,
    ROUND(ob.data_arc / 365.25, 1) AS observation_years,
    ob.condition_code,
    ROUND(oe.e, 4) AS eccentricity,
    ROUND(oe.i, 2) AS inclination_deg,
    ROUND(oe.moid, 6) AS moid_au,
    oa.anomaly_flag,
    ROUND(pp.diameter, 2) AS diameter_km
FROM NEO n
JOIN ObservationRecord ob ON n.spkid = ob.spkid
JOIN OrbitalElements oe ON n.spkid = oe.spkid
LEFT JOIN PhysicalProperties pp ON n.spkid = pp.spkid
LEFT JOIN OrbitalAnomalies oa ON n.spkid = oa.spkid
WHERE ob.data_arc > 10000
ORDER BY ob.data_arc DESC
LIMIT 50;
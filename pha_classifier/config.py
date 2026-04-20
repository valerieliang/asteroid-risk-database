# config.py

# Orbital and physical features
NUMERIC_FEATURES = [
    # Core orbital elements
    'e',            # eccentricity
    'q',            # perihelion distance (AU)
    'i',            # inclination (deg)
    'om',           # longitude of ascending node
    'w',            # argument of perihelion
    'ad',           # aphelion distance (AU)
    'per_y',        # orbital period (years)
    'a',            # semi-major axis (AU)
    # Earth proximity
    'moid',         # minimum orbit intersection distance (AU)
    'moid_ld',      # MOID in lunar distances
    'moid_jup',     # MOID from Jupiter (AU)
    # Physical / dynamical
    'H',            # absolute magnitude (proxy for size)
    't_jup',        # Tisserand parameter wrt Jupiter
    # Observation quality
    'data_arc',     # observational arc length (days)
    'n_obs_used',   # number of observations used
    'condition_code',
    'rms',          # orbit fit RMS residual
    # Orbital uncertainty (sigma columns)
    'sigma_e', 'sigma_q', 'sigma_i',
    'sigma_om', 'sigma_w', 'sigma_a',
]

CATEGORICAL_FEATURES = [
    'class',        # AMO / APO / ATE / IEO
]

DERIVED_FEATURES = [
    'earth_crossing',
    'moid_er',
    'est_diameter_km',
    'e_x_i',
    'v_rel_proxy',
    'ke_proxy',
    'arc_per_ratio',
]

def get_all_features():
    """Return combined list of all features."""
    return NUMERIC_FEATURES + DERIVED_FEATURES, CATEGORICAL_FEATURES
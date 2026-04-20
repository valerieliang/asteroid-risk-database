# feature_engineering.py

import numpy as np
import pandas as pd
from config import NUMERIC_FEATURES

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived features to the dataframe.
    
    Args:
        df: Input dataframe with base features
        
    Returns:
        DataFrame with additional derived features
    """
    df = df.copy()

    # Cast all numeric columns
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- Derived features ---
    
    # Earth-crossing proxy: q < 1 AU and ad > 1 AU
    df['earth_crossing'] = ((df['q'] < 1.0) & (df['ad'] > 1.0)).astype(float)

    # MOID safety margin: distance to Earth in Earth radii (1 AU = 23,455 ER)
    df['moid_er'] = df['moid'] * 23455.0

    # Size proxy from H (smaller H = larger object)
    # Approximate diameter (km) assuming albedo 0.15 (median for S-types)
    df['est_diameter_km'] = (1329.0 / np.sqrt(0.15)) * 10 ** (-df['H'] / 5.0)

    # Orbit energy proxy: combined eccentricity x inclination
    df['e_x_i'] = df['e'] * df['i']

    # Perihelion approach speed proxy: sqrt((1+e)/(1-e)) for ~v_inf
    df['v_rel_proxy'] = np.where(
        df['e'] < 1.0,
        np.sqrt(np.clip((1 + df['e']) / (1 - df['e']), 1e-6, 1e6)),
        np.nan
    )

    # Kinetic energy proxy (relative) = est_mass x v^2 proportional to diameter^3 x v^2
    df['ke_proxy'] = df['est_diameter_km'] ** 3 * df['v_rel_proxy'] ** 2

    # Observation completeness: arc / period
    df['arc_per_ratio'] = df['data_arc'] / (df['per_y'] * 365.25 + 1e-6)

    return df


def prepare_features(df: pd.DataFrame):
    """
    Prepare feature matrix from dataframe.
    
    Args:
        df: DataFrame with all features
        
    Returns:
        tuple: (X, y) where y is None if 'pha' column not present
    """
    from config import get_all_features
    
    num_feats, cat_feats = get_all_features()
    all_feats = num_feats + cat_feats
    
    X = df[all_feats]
    
    if 'pha' in df.columns:
        y = (df['pha'] == 'Y').astype(int)
    else:
        y = None
        
    return X, y
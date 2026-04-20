# data_loader.py

import numpy as np
import pandas as pd


def load_data(path: str):
    """
    Load CSV data and split into labelled (pha known) and unlabelled sets.
    
    Args:
        path: Path to CSV file
        
    Returns:
        tuple: (labelled_df, unlabelled_df)
    """
    df = pd.read_csv(path, low_memory=False)
    print(f"Loaded {len(df):,} rows, {df.shape[1]} columns")

    # Replace empty strings with NaN
    df.replace('', np.nan, inplace=True)

    # Split into labelled (train/eval) and unlabelled (inference)
    labelled = df[df['pha'].isin(['Y', 'N'])].copy()
    unlabelled = df[~df['pha'].isin(['Y', 'N'])].copy()

    print(f"  Labelled   (pha known): {len(labelled):,}  "
          f"[PHA-Y={(labelled['pha'] == 'Y').sum():,}  "
          f"PHA-N={(labelled['pha'] == 'N').sum():,}]")
    print(f"  Unlabelled (pha blank): {len(unlabelled):,}")

    return labelled, unlabelled
# anomaly_flagger/flagger.py

import pandas as pd
import os


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_data():
    neo = pd.read_csv(os.path.join(DATA_DIR, "neo_cleaned.csv"))
    orbital = pd.read_csv(os.path.join(DATA_DIR, "orbital_elements_cleaned.csv"))

    # Merge on spkid
    df = pd.merge(neo, orbital, on="spkid", how="inner")

    # Ensure numeric
    for col in ["moid", "e", "i"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def compute_anomalies(df, feature="moid", threshold=2.0):
    """
    Flags anomalies per class based on z-score threshold
    """

    # Compute class-wise mean and std
    stats = df.groupby("class")[feature].agg(["mean", "std"]).reset_index()
    stats.columns = ["class", f"{feature}_mean", f"{feature}_std"]

    # Merge stats back
    df = df.merge(stats, on="class", how="left")

    # Compute z-score
    df[f"{feature}_z"] = (
        (df[feature] - df[f"{feature}_mean"]) / df[f"{feature}_std"]
    )

    # Flag anomalies (1 = anomalous, 0 = normal)
    df[f"{feature}_anomaly"] = (df[f"{feature}_z"].abs() > threshold).astype(int)

    return df


def run_all():
    df = load_data()

    # Compute anomalies for each orbital parameter
    for feature in ["moid", "e", "i"]:
        df = compute_anomalies(df, feature=feature)

    # Combined anomaly flag (if ANY is anomalous)
    df["anomaly_flag"] = (
        (df["moid_anomaly"] == 1) |
        (df["e_anomaly"] == 1) |
        (df["i_anomaly"] == 1)
    ).astype(int)

    # Filter to only anomalies (where ANY parameter is anomalous)
    anomalies_df = df[df["anomaly_flag"] == 1].copy()
    
    # Binarize values to Y/N for the flagged anomalies
    # Convert the numeric anomaly flags to Y/N
    anomalies_df["moid_anomaly_yn"] = anomalies_df["moid_anomaly"].map({1: "Y", 0: "N"})
    anomalies_df["e_anomaly_yn"] = anomalies_df["e_anomaly"].map({1: "Y", 0: "N"})
    anomalies_df["i_anomaly_yn"] = anomalies_df["i_anomaly"].map({1: "Y", 0: "N"})
    
    # For the specific feature values, we can also binarize them to indicate if they're anomalies
    # But keeping original values as well for context
    anomalies_df["moid_is_anomaly"] = anomalies_df["moid_anomaly_yn"]
    anomalies_df["e_is_anomaly"] = anomalies_df["e_anomaly_yn"]
    anomalies_df["i_is_anomaly"] = anomalies_df["i_anomaly_yn"]
    
    # Save to current folder (where the script is running from)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, "anomalies_only.csv")
    
    # Select which columns to save
    columns_to_save = [
        "spkid", "class",
        "moid_anomaly_yn",
        "e_anomaly_yn", 
        "i_anomaly_yn",
        "anomaly_flag"
    ]
    
    # Only include columns that exist
    existing_columns = [col for col in columns_to_save if col in anomalies_df.columns]
    anomalies_df[existing_columns].to_csv(output_path, index=False)
    
    print(f"Saved anomalies (Y/N format) to: {output_path}")
    print(f"Total anomalies found: {len(anomalies_df)} out of {len(df)} total objects")
    print(f"Columns saved: {existing_columns}")
    
    return anomalies_df


if __name__ == "__main__":
    run_all()
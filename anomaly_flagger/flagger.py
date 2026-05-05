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

    # Flag anomalies
    df[f"{feature}_anomaly_flag"] = (df[f"{feature}_z"].abs() > threshold).astype(int)

    return df


def run_all():
    df = load_data()

    # Compute anomalies for each orbital parameter
    for feature in ["moid", "e", "i"]:
        df = compute_anomalies(df, feature=feature)

    # Combined anomaly flag (if ANY is anomalous)
    df["anomaly_flag"] = (
        (df["moid_anomaly_flag"] == 1) |
        (df["e_anomaly_flag"] == 1) |
        (df["i_anomaly_flag"] == 1)
    ).astype(int)

    # Save results
    output_path = os.path.join(DATA_DIR, "neo_with_anomalies.csv")
    df.to_csv(output_path, index=False)

    print(f"Saved anomaly results to: {output_path}")

    return df


if __name__ == "__main__":
    run_all()
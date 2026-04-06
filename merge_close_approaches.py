import pandas as pd

# Load CSVs
ca   = pd.read_csv("data/close_approaches.csv")
sbdb = pd.read_csv("data/sbdb_query_results.csv", dtype={"spkid": str})
neos = pd.read_csv("data/neos.csv", dtype={"id": str})

# Merge with sbdb and neos to get spkid
ca = (
    ca
    .merge(sbdb[["pdes", "spkid"]], left_on="neo_des", right_on="pdes", how="left")
    .merge(neos[["id"]], left_on="spkid", right_on="id", how="left")
)

# Keep only relevant columns
ca = ca[["approach_id", "spkid", "close_approach_date", "miss_distance", "relative_velocity", "v_infinity"]]

# Optional: rename spkid to match your database column
ca = ca.rename(columns={"spkid": "neo_id"})

# Save back to CSV 
ca.to_csv("data/close_approaches_clean.csv", index=False)
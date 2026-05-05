import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Paths
DATA_PATH = "./data/orbital_elements_cleaned.csv"
OUTPUT_PATH = "./visualization/moid_bubble_grid.png"

# Load data
df = pd.read_csv(DATA_PATH)

# Drop missing values
df = df.dropna(subset=["moid"])

# Convert moid to numeric, coercing errors to NaN
df["moid"] = pd.to_numeric(df["moid"], errors='coerce')

# Drop any rows where conversion failed
df = df.dropna(subset=["moid"])

# Normalize MOID for visualization
moid = df["moid"]

# Invert for danger (small MOID = dangerous)
moid_norm = (moid - moid.min()) / (moid.max() - moid.min())
danger = 1 - moid_norm

# Bubble size scaling
sizes = 50 + (danger * 1000)

# Color mapping (red = dangerous, green = safe)
colors = plt.cm.RdYlGn(moid_norm)

# Create grid positions
n = len(df)
grid_x = np.arange(n)
grid_y = np.zeros(n)

fig, ax = plt.subplots(figsize=(12, 3))

scatter = ax.scatter(grid_x, grid_y, s=sizes, c=moid, cmap='RdYlGn', alpha=0.7, edgecolors='k')

plt.title("MOID Bubble Grid (NEO Risk Visualization)")
plt.xlabel("Objects")
plt.yticks([])

# Colorbar (now using the scatter plot as the mappable)
plt.colorbar(scatter, label="MOID (AU)")

os.makedirs("./visualization", exist_ok=True)
plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches='tight')
plt.show()
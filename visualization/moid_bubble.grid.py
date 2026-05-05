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

plt.figure(figsize=(12, 3))

plt.scatter(grid_x, grid_y, s=sizes, c=colors, alpha=0.7, edgecolors='k')

# Optional labels (comment out if too crowded)
# for i, row in df.iterrows():
#     plt.text(i, 0, str(row["spkid"]), fontsize=6)

plt.title("MOID Bubble Grid (NEO Risk Visualization)")
plt.xlabel("Objects")
plt.yticks([])

# Colorbar
sm = plt.cm.ScalarMappable(cmap="RdYlGn", norm=plt.Normalize(vmin=moid.min(), vmax=moid.max()))
plt.colorbar(sm, label="MOID (AU)")

os.makedirs("./visualization", exist_ok=True)
plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches='tight')
plt.show()
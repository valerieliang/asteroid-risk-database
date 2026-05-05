import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Paths
DATA_PATH = "./data/orbital_elements_cleaned.csv"
OUTPUT_PATH = "./visualization/orbital_ellipses.png"

# Load data
df = pd.read_csv(DATA_PATH)

# Compute semi-major axis (a = q / (1 - e))
df["a"] = df["q"] / (1 - df["e"])

# Prepare plot
plt.figure(figsize=(8, 8))

theta = np.linspace(0, 2 * np.pi, 500)

# Plot each orbit
for _, row in df.iterrows():
    e = row["e"]
    a = row["a"]

    # Polar equation of ellipse
    r = (a * (1 - e**2)) / (1 + e * np.cos(theta))

    x = r * np.cos(theta)
    y = r * np.sin(theta)

    plt.plot(x, y, alpha=0.5)

# Plot Sun at origin
plt.scatter(0, 0, color='yellow', s=100, label='Sun')

# Plot Earth's orbit (approx circle, a=1 AU)
earth_theta = np.linspace(0, 2*np.pi, 500)
plt.plot(np.cos(earth_theta), np.sin(earth_theta), 
         linestyle='--', label='Earth Orbit (1 AU)')

plt.xlabel("AU")
plt.ylabel("AU")
plt.title("Reconstructed NEO Orbital Ellipses")
plt.legend()
plt.axis("equal")

os.makedirs("./visualization", exist_ok=True)
plt.savefig(OUTPUT_PATH, dpi=300)
plt.show()
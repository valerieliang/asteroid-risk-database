import csv
from utils import nullable_float, MPC_OBSCODE_API, requests

OBSERVATORY_FILE = "Observatory.csv"

def fetch_observatories() -> dict:
    r = requests.get(MPC_OBSCODE_API, json={}, timeout=60)
    r.raise_for_status()
    return r.json()

def load_observatory_data():
    raw_obs = fetch_observatories()
    with open(OBSERVATORY_FILE, "w", newline="", encoding="utf-8") as f_obs:
        obs_w = csv.writer(f_obs)
        obs_w.writerow(["observatory_code", "observatory_name", "longitude", "parallax_cos", "parallax_sin"])

        for code, info in raw_obs.items():
            name = (info.get("name") or "").strip()
            longitude = nullable_float(info.get("longitude"))
            cos_val = nullable_float(info.get("rhocosphi"))
            sin_val = nullable_float(info.get("rhosinphi"))

            if not name or longitude is None or cos_val is None or sin_val is None:
                continue
            if longitude > 180:
                longitude -= 360
            obs_w.writerow([code, name, round(longitude, 6), round(cos_val, 7), round(sin_val, 7)])

    print(f"Written {len(raw_obs)} Observatory rows")

if __name__ == "__main__":
    load_observatory_data()
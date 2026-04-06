import csv
import time
import uuid
import requests
from utils import nullable_float, CAD_API, BATCH_SIZE, DATE_MIN, DATE_MAX, JPL_REQUEST_DELAY

CLOSE_APP_FILE = "data/close_approaches.csv"

def fetch_cad_batch(limit_from: int) -> dict:
    params = {
        "date-min": DATE_MIN,
        "date-max": DATE_MAX,
        "neo": "true",
        "limit": BATCH_SIZE,
        "limit-from": limit_from,
    }
    r = requests.get(CAD_API, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def load_close_approaches():
    with open(CLOSE_APP_FILE, "w", newline="", encoding="utf-8") as f_ca:
        ca_w = csv.writer(f_ca)
        ca_w.writerow([
            "approach_id", "neo_des", "close_approach_date",
            "miss_distance", "relative_velocity", "v_infinity"
        ])

        limit_from = 1
        total_ca = 0

        while True:
            batch = fetch_cad_batch(limit_from)
            rows = batch.get("data", [])
            if not rows:
                break

            fields = batch.get("fields", [])
            idx_des   = fields.index("des")
            idx_cd    = fields.index("cd")
            idx_dist  = fields.index("dist")
            idx_v_rel = fields.index("v_rel")
            idx_v_inf = fields.index("v_inf") if "v_inf" in fields else None

            for row in rows:
                des  = (row[idx_des] or "").strip()
                cd   = (row[idx_cd]  or "").strip()
                dist = nullable_float(row[idx_dist])
                vrel = nullable_float(row[idx_v_rel])
                vinf = nullable_float(row[idx_v_inf]) if idx_v_inf is not None else None

                if not des or not cd or dist is None or vrel is None:
                    continue
                if dist < 0 or vrel < 0:
                    continue

                ca_w.writerow([str(uuid.uuid4()), des, cd, dist, vrel, vinf])
                total_ca += 1

            fetched = limit_from + len(rows) - 1
            api_total = int(batch.get("total", fetched))
            print(f"  CAD: {fetched}/{api_total}")
            if fetched >= api_total:
                break
            limit_from += len(rows)
            time.sleep(JPL_REQUEST_DELAY)

    print(f"Written {total_ca} CloseApproach rows")

if __name__ == "__main__":
    load_close_approaches()
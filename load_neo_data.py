import csv
import time
import requests
from typing import Optional
from utils import nullable_float, map_orbit_class, pick_spectral_class, JPL_REQUEST_DELAY, BATCH_SIZE, SBDB_QUERY_API

NEO_FILE = "NEOs.csv"
PHYSICAL_FILE = "PhysicalInfo.csv"
ORBITAL_FILE = "OrbitalData.csv"

def fetch_sbdb_page(limit: int, limit_from: int) -> dict:
    params = {
        "sb-group": "neo",
        "fields": (
            "pdes,full_name,first_obs,pha,"
            "H,diameter,albedo,spec_T,spec_B,"
            "e,i,per_y,class,moid"
        ),
        "limit": limit,
        "limit-from": limit_from,
        "full-prec": "true",
    }
    r = requests.get(SBDB_QUERY_API, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def fetch_all_sbdb() -> list[dict]:
    all_records = []
    limit_from = 0
    while True:
        data = fetch_sbdb_page(BATCH_SIZE, limit_from)
        fields = data.get("fields", [])
        rows = data.get("data", [])
        if not rows:
            break
        for row in rows:
            all_records.append(dict(zip(fields, row)))
        fetched = limit_from + len(rows)
        total = int(data.get("total", fetched))
        print(f"  SBDB: {fetched}/{total}")
        if fetched >= total:
            break
        limit_from = fetched
        time.sleep(JPL_REQUEST_DELAY)
    return all_records

def load_neo_data():
    records = fetch_all_sbdb()
    print(f"Total SBDB records: {len(records)}")

    with (
        open(NEO_FILE, "w", newline="", encoding="utf-8") as f_neo,
        open(PHYSICAL_FILE, "w", newline="", encoding="utf-8") as f_phys,
        open(ORBITAL_FILE, "w", newline="", encoding="utf-8") as f_orb,
    ):
        neo_w = csv.writer(f_neo)
        phys_w = csv.writer(f_phys)
        orb_w = csv.writer(f_orb)

        neo_w.writerow(["neo_id", "name", "discovery_date", "potentially_hazardous"])
        phys_w.writerow(["neo_id", "diameter", "absolute_magnitude", "albedo", "spectral_class"])
        orb_w.writerow(["neo_id", "eccentricity", "inclination", "orbital_period",
                        "orbit_class", "moid"])

        for rec in records:
            neo_id = (rec.get("pdes") or "").strip()
            if not neo_id:
                continue
            full_name = (rec.get("full_name") or neo_id).strip()
            discovery_date = (rec.get("first_obs") or "").strip() or None
            pha_raw = (rec.get("pha") or "").strip().upper()
            potentially_haz = 1 if pha_raw == "Y" else 0

            if not discovery_date:
                continue

            neo_w.writerow([neo_id, full_name, discovery_date, potentially_haz])

            diameter = nullable_float(rec.get("diameter"))
            abs_magnitude = nullable_float(rec.get("H"))
            albedo = nullable_float(rec.get("albedo"))
            spectral_class = pick_spectral_class(rec.get("spec_T"), rec.get("spec_B"))

            if diameter is not None and abs_magnitude is not None:
                phys_w.writerow([neo_id, diameter, abs_magnitude, albedo, spectral_class])

            eccentricity = nullable_float(rec.get("e"))
            inclination = nullable_float(rec.get("i"))
            orbital_period = nullable_float(rec.get("per_y"))
            orbit_class = map_orbit_class(rec.get("class"))
            moid = nullable_float(rec.get("moid"))

            if (eccentricity is not None and 0 <= eccentricity <= 1
                and inclination is not None
                and orbital_period is not None and orbital_period > 0
                and orbit_class is not None
                and moid is not None and moid >= 0):
                orb_w.writerow([neo_id, eccentricity, inclination,
                                 orbital_period, orbit_class, moid])

if __name__ == "__main__":
    load_neo_data()
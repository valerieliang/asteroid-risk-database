"""
NASA/MPC NEO Data Importer (Async Observations)
================================================
Populates all six tables from public APIs.
Step 4 (MPC Observations) now uses asyncio + aiohttp for parallel requests.
"""

import csv
import time
import uuid
from typing import Optional, List
import asyncio
import aiohttp

import requests

# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
CAD_API         = "https://ssd-api.jpl.nasa.gov/cad.api"
SBDB_QUERY_API  = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
MPC_OBSCODE_API = "https://data.minorplanetcenter.net/api/obscodes"
MPC_OBS_API     = "https://data.minorplanetcenter.net/api/get-obs"

# ---------------------------------------------------------------------------
# Output CSV paths
# ---------------------------------------------------------------------------
NEO_FILE         = "NEOs.csv"
PHYSICAL_FILE    = "PhysicalInfo.csv"
ORBITAL_FILE     = "OrbitalData.csv"
CLOSE_APP_FILE   = "CloseApproaches.csv"
OBSERVATORY_FILE = "Observatory.csv"
OBSERVATION_FILE = "Observation.csv"

# ---------------------------------------------------------------------------
# Tuning knobs
# ---------------------------------------------------------------------------
DATE_MIN  = "1900-01-01"
DATE_MAX  = "2100-12-31"
BATCH_SIZE = 10_000

JPL_REQUEST_DELAY = 0.5   # seconds between paginated JPL requests
OBS_REQUEST_DELAY = 0  # Not needed with async (we control concurrency)
MAX_NEOS_FOR_OBSERVATIONS = 500
MAX_CONCURRENT_REQUESTS = 20  # limit concurrency to avoid API overload

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def nullable_float(val) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

ORBIT_CLASS_MAP = {
    "IEO": "Atira",
    "ATE": "Aten",
    "APO": "Apollo",
    "AMO": "Amor",
}

def map_orbit_class(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    return ORBIT_CLASS_MAP.get(code.strip().upper())

def pick_spectral_class(spec_t: Optional[str], spec_b: Optional[str]) -> Optional[str]:
    raw = spec_t or spec_b
    if not raw:
        return None
    first = raw.strip()[0].upper()
    return first if first in ("C", "S", "X") else None

# ---------------------------------------------------------------------------
# JPL SBDB Query API
# ---------------------------------------------------------------------------
def fetch_sbdb_page(limit: int, limit_from: int) -> dict:
    params = {
        "sb-group": "neo",
        "fields": (
            "pdes,full_name,first_obs,pha,"
            "H,diameter,albedo,spec_T,spec_B,"
            "e,i,per_y,class,moid"
        ),
        "limit":      limit,
        "limit-from": limit_from,
        "full-prec":  "true",
    }
    r = requests.get(SBDB_QUERY_API, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def fetch_all_sbdb() -> List[dict]:
    all_records: List[dict] = []
    limit_from = 0
    while True:
        data   = fetch_sbdb_page(BATCH_SIZE, limit_from)
        fields = data.get("fields", [])
        rows   = data.get("data", [])
        if not rows:
            break
        for row in rows:
            all_records.append(dict(zip(fields, row)))
        fetched = limit_from + len(rows)
        total   = int(data.get("total", fetched))
        print(f"  SBDB: {fetched} / {total}")
        if fetched >= total:
            break
        limit_from = fetched
        time.sleep(JPL_REQUEST_DELAY)
    return all_records

# ---------------------------------------------------------------------------
# JPL CAD API
# ---------------------------------------------------------------------------
def fetch_cad_batch(limit_from: int) -> dict:
    params = {
        "date-min":   DATE_MIN,
        "date-max":   DATE_MAX,
        "neo":        "true",
        "limit":      BATCH_SIZE,
        "limit-from": limit_from,
    }
    r = requests.get(CAD_API, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

# ---------------------------------------------------------------------------
# MPC Observatory Codes API
# ---------------------------------------------------------------------------
def fetch_observatories() -> dict:
    r = requests.get(MPC_OBSCODE_API, json={}, timeout=60)
    r.raise_for_status()
    return r.json()

# ---------------------------------------------------------------------------
# Async MPC Observations API
# ---------------------------------------------------------------------------
async def fetch_observations_for_neo_async(session: aiohttp.ClientSession, designation: str) -> List[dict]:
    try:
        async with session.post(
            MPC_OBS_API,
            json={"desigs": [designation], "output_format": ["ADES_DF"]},
            timeout=30
        ) as r:
            if r.status != 200:
                return []
            payload = await r.json()
            if not payload or not payload[0].get("ADES_DF"):
                return []

            results = []
            for row in payload[0]["ADES_DF"]:
                stn = row.get("stn") or row.get("observatory")
                obs_time = row.get("obsTime") or row.get("obs_time")
                if stn and obs_time:
                    obs_date = obs_time.rstrip("Z").replace("T", " ")
                    results.append({
                        "observatory_code": str(stn).strip(),
                        "observation_date": obs_date,
                    })
            return results
    except Exception:
        return []

async def fetch_all_observations(neo_ids: List[str], observatory_codes: set) -> List[dict]:
    results = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession() as session:
        async def fetch_with_semaphore(neo_id):
            async with semaphore:
                obs_list = await fetch_observations_for_neo_async(session, neo_id)
                for obs in obs_list:
                    code = obs["observatory_code"]
                    date = obs["observation_date"]
                    if code in observatory_codes:
                        results.append({
                            "observation_id": str(uuid.uuid4()),
                            "neo_id": neo_id,
                            "observatory_code": code,
                            "observation_date": date
                        })

        tasks = [fetch_with_semaphore(nid) for nid in neo_ids]
        for idx, task in enumerate(asyncio.as_completed(tasks), 1):
            await task
            if idx % 50 == 0 or idx == len(tasks):
                print(f"  {idx}/{len(tasks)} NEOs queried, {len(results)} observations collected")
    return results

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def write_csvs() -> None:
    # Step 1 - SBDB: NEOs, PhysicalInfo, OrbitalData
    print("\n-- Step 1: SBDB Query API --")
    neo_records = fetch_all_sbdb()
    print(f"  Total SBDB records: {len(neo_records)}")

    valid_neo_ids: List[str] = []

    with (
        open(NEO_FILE,      "w", newline="", encoding="utf-8") as f_neo,
        open(PHYSICAL_FILE, "w", newline="", encoding="utf-8") as f_phys,
        open(ORBITAL_FILE,  "w", newline="", encoding="utf-8") as f_orb,
    ):
        neo_w  = csv.writer(f_neo)
        phys_w = csv.writer(f_phys)
        orb_w  = csv.writer(f_orb)

        neo_w.writerow(["neo_id", "name", "discovery_date", "potentially_hazardous"])
        phys_w.writerow(["neo_id", "diameter", "absolute_magnitude", "albedo", "spectral_class"])
        orb_w.writerow(["neo_id", "eccentricity", "inclination", "orbital_period",
                         "orbit_class", "moid"])

        skipped = 0
        for rec in neo_records:
            neo_id = (rec.get("pdes") or "").strip()
            if not neo_id:
                skipped += 1
                continue

            full_name       = (rec.get("full_name") or neo_id).strip()
            discovery_date  = (rec.get("first_obs") or "").strip() or None
            pha_raw         = (rec.get("pha") or "").strip().upper()
            potentially_haz = 1 if pha_raw == "Y" else 0

            if not discovery_date:
                skipped += 1
                continue

            neo_w.writerow([neo_id, full_name, discovery_date, potentially_haz])
            valid_neo_ids.append(neo_id)

            diameter       = nullable_float(rec.get("diameter"))
            abs_magnitude  = nullable_float(rec.get("H"))
            albedo         = nullable_float(rec.get("albedo"))
            spectral_class = pick_spectral_class(rec.get("spec_T"), rec.get("spec_B"))

            if diameter is not None and abs_magnitude is not None:
                phys_w.writerow([neo_id, diameter, abs_magnitude, albedo, spectral_class])

            eccentricity   = nullable_float(rec.get("e"))
            inclination    = nullable_float(rec.get("i"))
            orbital_period = nullable_float(rec.get("per_y"))
            orbit_class    = map_orbit_class(rec.get("class"))
            moid           = nullable_float(rec.get("moid"))

            if (
                eccentricity   is not None and 0 <= eccentricity <= 1
                and inclination    is not None
                and orbital_period is not None and orbital_period > 0
                and orbit_class    is not None
                and moid           is not None and moid >= 0
            ):
                orb_w.writerow([neo_id, eccentricity, inclination,
                                 orbital_period, orbit_class, moid])

    print(f"  Written {len(valid_neo_ids)} NEO rows  (skipped {skipped})")

    # Step 2 - CAD API: CloseApproaches
    print("\n-- Step 2: JPL CAD API (CloseApproaches) --")
    with open(CLOSE_APP_FILE, "w", newline="", encoding="utf-8") as f_ca:
        ca_w = csv.writer(f_ca)
        ca_w.writerow([
            "approach_id", "neo_id", "close_approach_date",
            "miss_distance", "relative_velocity",
        ])
        limit_from = 1
        total_ca = 0
        skipped_ca = 0
        while True:
            batch  = fetch_cad_batch(limit_from)
            rows   = batch.get("data", [])
            if not rows:
                break
            fields    = batch.get("fields", [])
            idx_des   = fields.index("des")
            idx_cd    = fields.index("cd")
            idx_dist  = fields.index("dist")
            idx_v_rel = fields.index("v_rel")
            for row in rows:
                neo_id = (row[idx_des] or "").strip()
                cd     = (row[idx_cd]  or "").strip()
                dist   = nullable_float(row[idx_dist])
                vrel   = nullable_float(row[idx_v_rel])
                if not neo_id or not cd or dist is None or vrel is None:
                    skipped_ca += 1
                    continue
                if dist < 0 or vrel < 0:
                    skipped_ca += 1
                    continue
                ca_w.writerow([str(uuid.uuid4()), neo_id, cd, dist, vrel])
                total_ca += 1
            fetched   = limit_from + len(rows) - 1
            api_total = int(batch.get("total", fetched))
            print(f"  CAD: {fetched} / {api_total}")
            if fetched >= api_total:
                break
            limit_from += len(rows)
            time.sleep(JPL_REQUEST_DELAY)

    print(f"  Written {total_ca} CloseApproach rows  (skipped {skipped_ca})")

    # Step 3 - MPC Observatory Codes API: Observatory
    print("\n-- Step 3: MPC Observatory Codes API (Observatory) --")
    raw_obs = fetch_observatories()
    observatory_codes_written: set = set()
    with open(OBSERVATORY_FILE, "w", newline="", encoding="utf-8") as f_obs:
        obs_w = csv.writer(f_obs)
        obs_w.writerow(["observatory_code", "observatory_name",
                        "longitude", "parallax_cos", "parallax_sin"])
        skipped_obs = 0
        for code, info in raw_obs.items():
            name      = (info.get("name") or "").strip()
            longitude = nullable_float(info.get("longitude"))
            cos_val   = nullable_float(info.get("rhocosphi"))
            sin_val   = nullable_float(info.get("rhosinphi"))
            if not name or longitude is None or cos_val is None or sin_val is None:
                skipped_obs += 1
                continue
            if longitude > 180:
                longitude -= 360
            if not (-180 <= longitude <= 180):
                skipped_obs += 1
                continue
            obs_w.writerow([code, name, round(longitude, 6), round(cos_val, 7), round(sin_val, 7)])
            observatory_codes_written.add(code)
    print(f"  Written {len(observatory_codes_written)} Observatory rows  (skipped {skipped_obs})")

    # Step 4 - MPC Observations API: Observation (async)
    print("\n-- Step 4: MPC Observations API (Observation, async) --")
    neo_ids_to_query = valid_neo_ids
    if MAX_NEOS_FOR_OBSERVATIONS is not None:
        neo_ids_to_query = valid_neo_ids[:MAX_NEOS_FOR_OBSERVATIONS]

    print(f"  Querying {len(neo_ids_to_query)} NEOs "
          f"({'all' if MAX_NEOS_FOR_OBSERVATIONS is None else f'capped at {MAX_NEOS_FOR_OBSERVATIONS}'})")

    obs_records = asyncio.run(fetch_all_observations(neo_ids_to_query, observatory_codes_written))

    with open(OBSERVATION_FILE, "w", newline="", encoding="utf-8") as f_ob:
        writer = csv.writer(f_ob)
        writer.writerow(["observation_id", "neo_id", "observatory_code", "observation_date"])
        for obs in obs_records:
            writer.writerow([obs["observation_id"], obs["neo_id"], obs["observatory_code"], obs["observation_date"]])

    print(f"  Written {len(obs_records)} Observation rows")
    if MAX_NEOS_FOR_OBSERVATIONS is not None and len(valid_neo_ids) > MAX_NEOS_FOR_OBSERVATIONS:
        print(f"  WARNING: {len(valid_neo_ids) - MAX_NEOS_FOR_OBSERVATIONS} NEOs not queried.")

    # Summary
    print("\n-- Output files --")
    for f in [NEO_FILE, PHYSICAL_FILE, ORBITAL_FILE,
              CLOSE_APP_FILE, OBSERVATORY_FILE, OBSERVATION_FILE]:
        print(f"  {f}")

if __name__ == "__main__":
    write_csvs()
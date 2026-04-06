import csv
import asyncio
import aiohttp
import hashlib
import pandas as pd
from utils import MPC_OBS_API, MAX_CONCURRENT_OBS

OBSERVATION_FILE = "Observation.csv"

def generate_obs_hash(rec, neo_id):
    rec_str = f"{neo_id}|{rec.get('stn')}|{rec.get('obsTime')}"
    return hashlib.sha256(rec_str.encode("utf-8")).hexdigest()

async def fetch_obs_for_neo(session, semaphore, neo_id):
    payload = {"trksubs": [neo_id], "output_format": ["ADES_DF"]}
    async with semaphore:
        async with session.get(MPC_OBS_API, json=payload) as resp:
            if resp.status != 200:
                print(f"Error fetching {neo_id}: {resp.status}")
                return []
            raw = await resp.json(content_type=None)

    if not raw or "ADES_DF" not in raw[0]:
        return []

    rows = []
    for rec in raw[0]["ADES_DF"]:
        obscode = rec.get("stn")
        obs_time = rec.get("obsTime")
        if not obscode or not obs_time:
            continue
        rows.append({
            "observation_id": generate_obs_hash(rec, neo_id),
            "neo_id": neo_id,
            "observatory_code": obscode.strip(),
            "observation_date": obs_time.replace("T", " ").rstrip("Z"),
        })
    return rows

async def fetch_all_observations_async(neo_ids):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_OBS)
    all_rows = []
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_obs_for_neo(session, semaphore, neo_id) for neo_id in neo_ids]
        for coro in asyncio.as_completed(tasks):
            rows = await coro
            all_rows.extend(rows)
    return all_rows

def load_observation_data_from_csv(neos_csv_path):
    # Read NEO IDs from CSV
    df_neos = pd.read_csv(neos_csv_path)
    neo_ids = df_neos["neo_id"].dropna().tolist()
    print(f"Found {len(neo_ids)} NEO IDs")

    # Fetch all observations
    obs_rows = asyncio.run(fetch_all_observations_async(neo_ids))

    # Save to CSV
    with open(OBSERVATION_FILE, "w", newline="", encoding="utf-8") as f_ob:
        ob_w = csv.writer(f_ob)
        ob_w.writerow(["observation_id", "neo_id", "observatory_code", "observation_date"])
        for row in obs_rows:
            ob_w.writerow([row["observation_id"], row["neo_id"], row["observatory_code"], row["observation_date"]])
    print(f"Written {len(obs_rows)} Observation rows to {OBSERVATION_FILE}")

if __name__ == "__main__":
    load_observation_data_from_csv("NEOs.csv")
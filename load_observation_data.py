import csv
import uuid
import asyncio
from utils import MPC_OBS_API, MAX_CONCURRENT_OBS, aiohttp

OBSERVATION_FILE = "Observation.csv"

async def fetch_obs_for_neo(session, semaphore, designation):
    payload = {"desigs": [designation], "output_format": ["MPC"]}
    async with semaphore:
        async with session.post(MPC_OBS_API, json=payload) as resp:
            if resp.status != 200:
                return []
            raw = await resp.json(content_type=None)

    if not raw or "data" not in raw[0]:
        return []

    rows = []
    for rec in raw[0]["data"]:
        obscode = rec.get("observatory")
        obs_time = rec.get("obs_date")
        if not obscode or not obs_time:
            continue
        rows.append({
            "observation_id": str(uuid.uuid4()),
            "neo_id": designation,
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

def load_observation_data(neo_ids):
    obs_rows = asyncio.run(fetch_all_observations_async(neo_ids))
    with open(OBSERVATION_FILE, "w", newline="", encoding="utf-8") as f_ob:
        ob_w = csv.writer(f_ob)
        ob_w.writerow(["observation_id", "neo_id", "observatory_code", "observation_date"])
        for row in obs_rows:
            ob_w.writerow([row["observation_id"], row["neo_id"], row["observatory_code"], row["observation_date"]])
    print(f"Written {len(obs_rows)} Observation rows")
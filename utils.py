from typing import Optional
import aiohttp
import requests

BATCH_SIZE = 10_000
JPL_REQUEST_DELAY = 0.5
DATE_MIN = "1900-01-01"
DATE_MAX = "2100-12-31"
SBDB_QUERY_API = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
CAD_API = "https://ssd-api.jpl.nasa.gov/cad.api"
MPC_OBSCODE_API = "https://data.minorplanetcenter.net/api/obscodes"
MPC_OBS_API = "https://data.minorplanetcenter.net/api/get-obs"
MAX_CONCURRENT_OBS = 20

def nullable_float(val) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

ORBIT_CLASS_MAP = {"IEO": "Atira", "ATE": "Aten", "APO": "Apollo", "AMO": "Amor"}

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
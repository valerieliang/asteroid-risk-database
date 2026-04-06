#!/usr/bin/env python3
"""
parse_neos.py -- JPL Small-Body Database NEO CSV Parser
=======================================================
Reads the raw JPL SBDB CSV export (sbdb_query_results.csv by default),
filters to confirmed NEOs only, validates NOT NULL constraints, and writes
five clean CSV files matching the relational schema:

    neos.csv
    physical_info.csv
    orbital_data.csv
    close_approaches.csv   (empty -- no CA data in this source file)
    observation_records.csv

Usage:
    python3 parse_neos.py [input.csv] [--outdir ./data]

Column mapping (raw CSV -> schema):
    spkid          -> NEOs.id
    name           -> NEOs.name
    pha            -> NEOs.potentially_hazardous  (Y->1, else->0)
    sats           -> NEOs.num_satellites
    diameter       -> PhysicalInfo.diameter
    H              -> PhysicalInfo.absolute_magnitude
    G              -> PhysicalInfo.slope_parameter
    albedo         -> PhysicalInfo.albedo
    rot_per        -> PhysicalInfo.rotational_period_hrs
    GM             -> PhysicalInfo.gravitational_param
    spec_B         -> PhysicalInfo.spectral_class_b
    spec_T         -> PhysicalInfo.spectral_class_t
    e              -> OrbitalData.eccentricity
    i              -> OrbitalData.inclination
    per_y          -> OrbitalData.orbital_period
    class          -> OrbitalData.orbit_class
    moid           -> OrbitalData.earth_moid
    producer       -> ObservationRecord.discovering_org
    first_obs      -> ObservationRecord.first_obs
    last_obs       -> ObservationRecord.latest_obs
    n_obs_used     -> ObservationRecord.num_obs
"""

import csv
import sys
import os
import argparse
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s"
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Column mapping: raw CSV column name -> output field name
# ---------------------------------------------------------------------------
NEOS_COLS = {
    "spkid": "id",
    "name":  "name",
    "pha":   "potentially_hazardous",
    "sats":  "num_satellites",
}

PHYSICAL_COLS = {
    "spkid":   "id",
    "diameter": "diameter",
    "H":        "absolute_magnitude",
    "G":        "slope_parameter",
    "albedo":   "albedo",
    "rot_per":  "rotational_period_hrs",
    "GM":       "gravitational_param",
    "spec_B":   "spectral_class_b",
    "spec_T":   "spectral_class_t",
}

ORBITAL_COLS = {
    "spkid": "id",
    "e":     "eccentricity",
    "i":     "inclination",
    "per_y": "orbital_period",
    "class": "orbit_class",
    "moid":  "earth_moid",
}

OBS_COLS = {
    "spkid":      "id",
    "producer":   "discovering_org",
    "first_obs":  "first_obs",
    "last_obs":   "latest_obs",
    "n_obs_used": "num_obs",
}

# NOT NULL columns per table (raw CSV names).
# Rows missing any of these will be dropped from that table only.
NEOS_REQUIRED      = {"spkid", "name"}
ORBITAL_REQUIRED   = {"spkid", "e", "i", "per_y", "class"}
OBS_REQUIRED       = {"spkid", "n_obs_used"}
# PhysicalInfo has no required non-PK fields (all physical measurements nullable)


def clean(value: str) -> str:
    """Strip surrounding whitespace and quotes; return empty string for blanks."""
    return value.strip().strip('"').strip()


def to_nullable(value: str) -> str:
    """Return empty string (will be written as blank CSV field -> MySQL NULL) if blank."""
    v = clean(value)
    return v if v else ""


def pha_to_bool(value: str) -> str:
    """Convert Y/N/blank PHA flag to 1/0 for MySQL BOOLEAN."""
    return "1" if clean(value).upper() == "Y" else "0"


def parse(input_path: Path, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    # Output file paths
    path_neos    = outdir / "neos.csv"
    path_phys    = outdir / "physical_info.csv"
    path_orb     = outdir / "orbital_data.csv"
    path_ca      = outdir / "close_approaches.csv"
    path_obs     = outdir / "observation_records.csv"

    counters = {
        "read": 0,
        "skipped_not_neo": 0,
        "dropped_neos": 0,
        "dropped_orb": 0,
        "dropped_obs": 0,
        "written_neos": 0,
        "written_phys": 0,
        "written_orb": 0,
        "written_obs": 0,
    }

    with (
        open(input_path, newline="", encoding="utf-8") as fin,
        open(path_neos,  "w", newline="", encoding="utf-8") as f_neos,
        open(path_phys,  "w", newline="", encoding="utf-8") as f_phys,
        open(path_orb,   "w", newline="", encoding="utf-8") as f_orb,
        open(path_ca,    "w", newline="", encoding="utf-8") as f_ca,
        open(path_obs,   "w", newline="", encoding="utf-8") as f_obs,
    ):
        reader = csv.DictReader(fin)

        # Normalise header names (strip whitespace/quotes)
        reader.fieldnames = [clean(h) for h in reader.fieldnames]

        # Validate expected columns exist
        required_raw = set(NEOS_COLS) | set(PHYSICAL_COLS) | set(ORBITAL_COLS) | set(OBS_COLS)
        missing = required_raw - set(reader.fieldnames)
        if missing:
            log.warning("Columns not found in source (will be NULL): %s", missing)

        # Writers
        w_neos = csv.DictWriter(f_neos, fieldnames=list(NEOS_COLS.values()),
                                extrasaction="ignore", lineterminator="\n")
        w_phys = csv.DictWriter(f_phys, fieldnames=list(PHYSICAL_COLS.values()),
                                extrasaction="ignore", lineterminator="\n")
        w_orb  = csv.DictWriter(f_orb,  fieldnames=list(ORBITAL_COLS.values()),
                                extrasaction="ignore", lineterminator="\n")
        w_ca   = csv.DictWriter(f_ca,   fieldnames=["approach_id","id","close_approach_date",
                                                     "miss_distance","relative_velocity","v_infinity"],
                                extrasaction="ignore", lineterminator="\n")
        w_obs  = csv.DictWriter(f_obs,  fieldnames=["observation_id"] + list(OBS_COLS.values()),
                                extrasaction="ignore", lineterminator="\n")

        w_neos.writeheader()
        w_phys.writeheader()
        w_orb.writeheader()
        w_ca.writeheader()
        w_obs.writeheader()

        # CloseApproaches: no data in this source -- write header only
        log.info("close_approaches.csv: no CA data in SBDB bulk export; header written only.")

        obs_id = 1  # surrogate key counter for ObservationRecord

        for raw_row in reader:
            counters["read"] += 1

            # Normalize all values
            row = {k: clean(v) for k, v in raw_row.items()}

            # ---------------------------------------------------------------
            # Filter: keep confirmed NEOs only (neo column = 'Y')
            # ---------------------------------------------------------------
            if row.get("neo", "").upper() != "Y":
                counters["skipped_not_neo"] += 1
                continue

            spkid = row.get("spkid", "")

            # ---------------------------------------------------------------
            # NEOs table -- drop row if NOT NULL fields are missing
            # ---------------------------------------------------------------
            neo_missing = [c for c in NEOS_REQUIRED if not row.get(c)]
            if neo_missing:
                log.debug("DROP NEO spkid=%s -- missing required: %s", spkid, neo_missing)
                counters["dropped_neos"] += 1
                continue  # can't write any table without a valid NEOs row

            neos_row = {
                "id":                   spkid,
                "name":                 row.get("name", ""),
                "potentially_hazardous": pha_to_bool(row.get("pha", "")),
                "num_satellites":        row.get("sats", "0") or "0",
            }
            w_neos.writerow(neos_row)
            counters["written_neos"] += 1

            # ---------------------------------------------------------------
            # PhysicalInfo -- all measurement columns nullable; always write
            # ---------------------------------------------------------------
            phys_row = {
                "id":                   spkid,
                "diameter":             to_nullable(row.get("diameter", "")),
                "absolute_magnitude":   to_nullable(row.get("H", "")),
                "slope_parameter":      to_nullable(row.get("G", "")),
                "albedo":               to_nullable(row.get("albedo", "")),
                "rotational_period_hrs": to_nullable(row.get("rot_per", "")),
                "gravitational_param":  to_nullable(row.get("GM", "")),
                "spectral_class_b":     to_nullable(row.get("spec_B", "")),
                "spectral_class_t":     to_nullable(row.get("spec_T", "")),
            }
            w_phys.writerow(phys_row)
            counters["written_phys"] += 1

            # ---------------------------------------------------------------
            # OrbitalData -- drop row (not NEO row) if required fields missing
            # ---------------------------------------------------------------
            orb_missing = [c for c in ORBITAL_REQUIRED if not row.get(c)]
            if orb_missing:
                log.debug("SKIP OrbitalData spkid=%s -- missing: %s", spkid, orb_missing)
                counters["dropped_orb"] += 1
            else:
                orb_row = {
                    "id":             spkid,
                    "eccentricity":   to_nullable(row.get("e", "")),
                    "inclination":    to_nullable(row.get("i", "")),
                    "orbital_period": to_nullable(row.get("per_y", "")),
                    "orbit_class":    to_nullable(row.get("class", "")),
                    "earth_moid":     to_nullable(row.get("moid", "")),
                }
                w_orb.writerow(orb_row)
                counters["written_orb"] += 1

            # ---------------------------------------------------------------
            # ObservationRecord -- drop row if required fields missing
            # ---------------------------------------------------------------
            obs_missing = [c for c in OBS_REQUIRED if not row.get(c)]
            if obs_missing:
                log.debug("SKIP ObsRecord spkid=%s -- missing: %s", spkid, obs_missing)
                counters["dropped_obs"] += 1
            else:
                obs_row = {
                    "observation_id": obs_id,
                    "id":             spkid,
                    "discovering_org": to_nullable(row.get("producer", "")),
                    "first_obs":      to_nullable(row.get("first_obs", "")),
                    "latest_obs":     to_nullable(row.get("last_obs", "")),
                    "num_obs":        to_nullable(row.get("n_obs_used", "")),
                }
                w_obs.writerow(obs_row)
                obs_id += 1
                counters["written_obs"] += 1

    # ---------------------------------------------------------------
    # Summary report
    # ---------------------------------------------------------------
    log.info("=" * 54)
    log.info("Parse complete")
    log.info("  Raw rows read          : %d", counters["read"])
    log.info("  Skipped (not NEO)      : %d", counters["skipped_not_neo"])
    log.info("  Dropped (missing PK/NN): %d", counters["dropped_neos"])
    log.info("  Written -> neos.csv     : %d", counters["written_neos"])
    log.info("  Written -> physical_info: %d", counters["written_phys"])
    log.info("  Written -> orbital_data : %d (skipped %d)",
             counters["written_orb"], counters["dropped_orb"])
    log.info("  Written -> obs_records  : %d (skipped %d)",
             counters["written_obs"], counters["dropped_obs"])
    log.info("  Output directory       : %s", outdir.resolve())
    log.info("=" * 54)


def main():
    parser = argparse.ArgumentParser(
        description="Parse JPL NEO bulk CSV into normalized table CSVs."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="sbdb_query_results.csv",
        help="Path to raw JPL SBDB CSV export (default: sbdb_query_results.csv)"
    )
    parser.add_argument(
        "--outdir",
        default="./data",
        help="Directory to write output CSVs (default: ./data)"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        log.error("Input file not found: %s", input_path)
        sys.exit(1)

    parse(input_path, Path(args.outdir))


if __name__ == "__main__":
    main()
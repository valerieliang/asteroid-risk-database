# NEO Sentry · Planetary Defense Intelligence Interface

A complete, production-ready Near-Earth Object hazard assessment system that transforms NASA JPL SBDB public data into an interactive threat monitoring dashboard. The system serves 16 analytical SQL queries across six interconnected MySQL tables, with a PHP JSON middleware layer and a single‑page HTML/JavaScript front end.

---

## What This System Does

The NEO Sentry interface answers planetary defense questions such as:

- **Which potentially hazardous asteroids have the most reliable orbits?** (Q1)
- **Where does the ML model disagree with official classifications?** (Q6)
- **Which city‑killers (diameter > 140m AND MOID < 0.05 AU) need immediate follow‑up?** (Q5)
- **What are the most eccentric, sun‑grazing, or high‑inclination objects?** (Q13, Q14)
- **How well‑determined is each orbit?** (condition_code, data_arc, Q9, Q16)
- **Which orbital classes have the highest anomaly rates?** (Q11)

The system includes a **Random Forest PHA classifier** and a **statistical anomaly flagger** that operate on the cleaned JPL data, producing `pred_pha` (ML hazard prediction) and `anomaly_flag` (orbital outlier detection) tables.

---

## Database Schema

```
NEO (spkid PK, full_name, pha, class)
  ├── PhysicalProperties (spkid → NEO, H, diameter)
  ├── OrbitalElements   (spkid → NEO, e, q, i, moid, moid_ld)
  ├── ObservationRecord (spkid → NEO, data_arc, condition_code)
  ├── PredictedPHAs     (spkid → NEO, pred_pha, pha_prob)   ← ML output
  └── OrbitalAnomalies  (spkid → NEO, moid/e/i anomaly flags) ← anomaly detector
```

All relationships use foreign keys with `ON DELETE CASCADE`.

---

## File Inventory

| File | Purpose |
|------|---------|
| `setup.sql` | Creates 6 tables with primary/foreign keys |
| `cleanup.sql` | Drops all tables in reverse dependency order |
| `load.sql` | Bulk‑loads cleaned CSVs into MySQL |
| `queries.sql` | The 16 analytical queries with detailed comments |
| `process.py` | Splits raw JPL CSV into 4 cleaned table CSVs |
| `requirements.txt` | Python dependencies (`pandas`, `scikit‑learn`, `matplotlib`) |
| `api.php` | JSON middleware: all 16 queries + search + stats + CSV export |
| `index.html` | Single‑page interface with 7 tabs, live stats, filters, and results tables |
| `process.txt` | Full documentation of cleaning steps, ML pipeline, and load order |

> **Note:** The actual `pha_classifier/` and `anomaly_flagger/` directories are referenced in `process.txt` but not included in the upload. The database schema and API are fully compatible with their output CSVs (`predictions_unlabelled.csv`, `anomalies_only.csv`).

---

## How to Run the Entire System

### 1. Prerequisites

- **MySQL** server (local or remote)
- **PHP** ≥ 7.4 (for `api.php`)
- **Python** ≥ 3.9 with pip
- A modern web browser

### 2. Obtain the Raw JPL Data

Download `sbdb_query_results.csv` from the [JPL Small‑Body Database Query Tool](https://ssd.jpl.nasa.gov/tools/sbdb_query.html).  
Select **all available fields** and filter for `neo = 'Y'` (Near‑Earth Objects only).

Place the file in a `data/` directory:

```bash
mkdir data
mv ~/Downloads/sbdb_query_results.csv data/
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Clean the Raw CSV → 4 Table CSVs

```bash
python process.py --input data/sbdb_query_results.csv
```

This creates:

- `data/neo_cleaned.csv`
- `data/physical_properties_cleaned.csv`
- `data/orbital_elements_cleaned.csv`
- `data/observation_record_cleaned.csv`

### 5. Run ML Prediction & Anomaly Detection

If you have the `pha_classifier` and `anomaly_flagger` pipelines:

```bash
python pha_classifier/run_pipeline.py          # → data/predictions_unlabelled.csv
python anomaly_flagger/flagger.py              # → data/anomalies_only.csv
```

Without these, the `PredictedPHAs` and `OrbitalAnomalies` tables will remain empty — the queries will still work but show `NULL` for ML and anomaly columns.

### 6. Create the MySQL Database and Tables

```bash
mysql -u root -p
CREATE DATABASE neo_hazard_db;
USE neo_hazard_db;
SOURCE setup.sql;
EXIT;
```

### 7. Load the Cleaned CSV Data

Edit `load.sql` to adjust file paths if needed, then:

```bash
mysql -u root -p neo_hazard_db < load.sql
```

Verify row counts:

```sql
SELECT COUNT(*) FROM NEO;                -- should match your NEO count
SELECT COUNT(*) FROM PredictedPHAs;      -- if ML pipeline was run
```

### 8. Configure the PHP Middleware

Edit `api.php` and update the database credentials:

```php
define('DB_HOST', 'localhost');
define('DB_USER', 'neo_user');
define('DB_PASS', 'your_password');
define('DB_NAME', 'neo_hazard_db');
```

Place `api.php` and `index.html` in the same web‑accessible directory.

### 9. Set File Permissions (for CS web servers)

Following the JHU CS personal webpage instructions:

```bash
chmod 0701 ~
mkdir ~/public_html
chmod 0701 ~/public_html
cp api.php index.html ~/public_html/
chmod 0604 ~/public_html/api.php ~/public_html/index.html
```

### 10. Access the Interface

- **CS Ugrad net:** `http://www.ugrad.cs.jhu.edu/~<account>/`

The interface will automatically load the **stats cards** and the **Search tab**. All 16 query tabs work on‑demand.

---

## API Endpoints (for developers)

`api.php` accepts an `action` parameter:

| `action` | Description |
|----------|-------------|
| `stats` | Dashboard summary (total NEOs, PHA counts, anomaly count, avg risk %) |
| `search` | Multi‑filter search (name, class, PHA, ML prediction, MOID, diameter, risk %, anomaly) |
| `q1` … `q16` | Each of the 16 analytical queries (supports `limit` and query‑specific filters) |
| `export` | Streams any query as CSV download |

Example: `api.php?action=q5&limit=50`

All responses are JSON with `{ok: true, data: [...]}` or `{error: ...}`.

---

## Query Summary (16 Analytical Queries)

| Query | Title | Purpose |
|-------|-------|---------|
| Q1 | PHA Threat Priority | Confirmed PHAs, cond_code ≤ 2, sorted by MOID |
| Q2 | PHA% vs ML% per Class | Compare official vs ML hazard rates by orbital class |
| Q3 | Average Properties by Class | Baseline stats: diameter, H, e, i, MOID |
| Q4 | Planet‑Killers | Largest NEOs (lowest H) with ML risk |
| Q5 | City‑Killers | Diameter > 140m AND MOID < 0.05 AU |
| Q6 | ML Discrepancies | False positives / false negatives of the Random Forest |
| Q7 | Keyhole PHAs | Official PHAs with ML risk > 50% |
| Q8 | Summary Dashboard | Single‑row aggregate stats |
| Q9 | Gold‑Standard Orbits | Condition code = 0, best‑determined orbits |
| Q10 | Perihelion Distribution | q statistics per class, sun‑approaching vs Earth‑crossers |
| Q11 | Anomaly Stats by Class | Classes with >10 members, anomaly rates |
| Q12 | Eccentricity Distribution | Min/max/mean/stddev of e per class |
| Q13 | High‑eccentricity Wildcards | e > 0.9 |
| Q14 | Sun‑Grazers & High‑Inclination | q < 0.5 AND i > 45° |
| Q15 | Orbital Ellipse Reconstruction | Semi‑major axis, aphelion, Earth‑crossing type |
| Q16 | Longest Observational Arcs | data_arc > 10,000 days (>27 years) |

---

## Tearing Down the Database

To completely remove all tables:

```bash
mysql -u root -p neo_hazard_db < cleanup.sql
```
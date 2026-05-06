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

The system includes a **Random Forest PHA classifier** (AUC > 0.99) and a **statistical anomaly flagger** (≥2 standard deviations from class mean for eccentricity, inclination, or MOID) that operate on the cleaned JPL data, producing `pred_pha` (ML hazard prediction) and `anomaly_flag` (orbital outlier detection) tables.

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

---

## How to Run the Entire System

### 1. Prerequisites

- **MySQL** server (local or remote)
- **PHP** ≥ 7.4 (for `api.php`) - Note: JHU ugrad servers use older PHP versions
- **Python** ≥ 3.9 with pip
- A modern web browser
- JHU CS ugrad machine access (for web hosting)

### 2. Obtain the Raw JPL Data

Download `sbdb_query_results.csv` from the [JPL Small‑Body Database Query Tool](https://ssd.jpl.nasa.gov/tools/sbdb_query.html).  
Select **all available fields** and filter for `neo = 'Y'` (Near‑Earth Objects only).

**Important:** Ensure the file is placed in the `data/` directory:

```bash
mkdir data
mv ~/Downloads/sbdb_query_results.csv data/
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install numpy pandas scikit-learn matplotlib
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

**Random Forest Classifier:**
```bash
python pha_classifier/run_pipeline.py
```
This generates `data/predictions_unlabelled.csv` with predicted PHA status and probability scores (0-100).

**Anomaly Detection:**
```bash
python anomaly_flagger/flagger.py
```
This generates `data/anomalies_only.csv` flagging objects with eccentricity, inclination, or MOID deviations ≥2 standard deviations from class mean.

### 6. Set Up MySQL Database

Connect to the JHU MySQL server:
```bash
mysql -h dbase.cs.jhu.edu -u 26sp_<JHED> -p 26sp_<JHED>_db
```

Create tables:
```sql
SOURCE setup.sql;
```

Load data:
```sql
SOURCE load.sql;
```

Verify the data loaded correctly:
```sql
SELECT COUNT(*) FROM NEO;
SELECT COUNT(*) FROM PhysicalProperties;
SELECT COUNT(*) FROM OrbitalElements;
SELECT COUNT(*) FROM ObservationRecord;
SELECT COUNT(*) FROM PredictedPHAs;
SELECT COUNT(*) FROM OrbitalAnomalies;
```

### 7. Configure Web Interface

**Create `secrets.php` in your home directory:**

```php
<?php
define('DB_HOST', 'dbase.cs.jhu.edu');
define('DB_USER', '26sp_<JHED>');
define('DB_PASS', 'your_password');
define('DB_NAME', '26sp_<JHED>_db');
?>
```

**Set up your personal webpage:**

Follow the JHU CS documentation:
- [Creating a Personal Webpage](https://support.cs.jhu.edu/wiki/Creating_a_Personal_Webpage)
- [Running PHP Scripts on the CS Webservers](https://support.cs.jhu.edu/wiki/Running_PHP_Scripts_on_the_CS_Webservers)

Essential commands:
```bash
# Set proper permissions
chmod 0711 ~
chmod 0711 ~/public_html

# Copy web files to public_html
cp index.html api.php ~/public_html/

# Set file permissions
chmod 0644 ~/public_html/index.html
chmod 0644 ~/public_html/api.php

# Ensure PHP can read secrets.php
chmod 0644 ~/secrets.php
```

### 8. Access the Interface

Your website will be available at:
```
https://www.ugrad.cs.jhu.edu/~<JHED>/
```

Replace `<JHED>` with your JHU username (e.g., `vliang5`).

---

## Using the Web Interface

### Navigation
The interface features 7 main tabs:
- **Search** - Multi-filter asteroid lookup
- **Threat Assessment** - Q1-Q5 hazard queries
- **ML & Anomalies** - Q6-Q8 model evaluation
- **Orbital Dynamics** - Q9-Q12 orbit analysis
- **Extreme Objects** - Q13-Q15 unusual orbits
- **Observation Quality** - Q16 data reliability
- **Documentation** - Query descriptions

### Features
- **Live Statistics Cards** - Real-time dashboard of NEO counts, PHA percentages, anomaly rates
- **Dynamic Results Tables** - Color-coded HTML tables with column highlighting
- **Search Functionality** - Look up any asteroid name for full detail page
- **CSV Export** - Download any query results
- **Result Limit Control** - Display 10, 25, 50, or 100 results per query

### Example Queries

**Find closest-approaching PHAs:**
```sql
SELECT n.full_name, oe.moid, pp.diameter 
FROM NEO n 
JOIN OrbitalElements oe ON n.spkid = oe.spkid 
JOIN PhysicalProperties pp ON n.spkid = pp.spkid 
WHERE n.pha = 'Y' 
ORDER BY oe.moid ASC 
LIMIT 20;
```

**Find ML model disagreements (false positives/negatives):**
```sql
SELECT n.full_name, n.pha, p.pred_pha, p.pha_prob
FROM NEO n
JOIN PredictedPHAs p ON n.spkid = p.spkid
WHERE (n.pha = 'Y' AND p.pred_pha = 'N')
   OR (n.pha = 'N' AND p.pred_pha = 'Y');
```

---

## API Endpoints (for developers)

`api.php` accepts an `action` parameter:

| `action` | Description |
|----------|-------------|
| `stats` | Dashboard summary (total NEOs, PHA counts, anomaly count, avg risk %) |
| `search` | Multi‑filter search (name, class, PHA, ML prediction, MOID, diameter, risk %, anomaly) |
| `q1` … `q16` | Each of the 16 analytical queries (supports `limit` and query‑specific filters) |
| `export` | Streams any query as CSV download |

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
mysql -h dbase.cs.jhu.edu -u 26sp_<JHED> -p 26sp_<JHED>_db < cleanup.sql
```

---
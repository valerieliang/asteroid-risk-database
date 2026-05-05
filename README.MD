# NEO Sentry · Planetary Defense Intelligence Interface

A comprehensive database and web interface for assessing, ranking, and querying collision risks posed by Near-Earth Objects (NEOs). The system integrates official NASA JPL orbital data, machine learning risk predictions, and statistical anomaly detection across 16 analytical queries.

## Overview

Near-Earth Objects—asteroids and comets whose orbits bring them into Earth's neighborhood—are catalogued by NASA's Jet Propulsion Laboratory with extensive observational, physical, and orbital parameters. This system transforms that raw data into actionable intelligence for planetary defense:

- **Threat prioritization** based on reliable orbits and Minimum Orbit Intersection Distance (MOID)
- **Size classification** from city-killers (≥140m) to planet-killers (≥1km)
- **Machine learning predictions** (Random Forest) that complement official PHA flags
- **Orbital anomaly detection** across eccentricity, inclination, and MOID
- **Observation quality assessment** using condition codes and observational arcs

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   process.py    │────▶│   MySQL Tables  │◀────│   api.php       │
│  (CSV cleaning) │     │   (6 tables)    │     │  (JSON API)     │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
         │                      │                        │
         ▼                      ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ sbdb_query.csv  │     │   load.sql      │     │   index.html    │
│ (JPL export)    │     │  (data loading) │     │  (frontend UI)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Database Schema

| Table | Purpose |
|-------|---------|
| `NEO` | Core identity: SPKID, name, PHA flag, orbital class |
| `PhysicalProperties` | Absolute magnitude (H), diameter (km) |
| `OrbitalElements` | Eccentricity (e), perihelion (q), inclination (i), MOID (AU/LD) |
| `ObservationRecord` | Data arc length (days), condition code (0=best, 9=worst) |
| `PredictedPHAs` | ML-derived PHA probability and prediction (Random Forest) |
| `OrbitalAnomalies` | Statistical outlier flags for MOID, eccentricity, inclination |

## Prerequisites

- **XAMPP** (Apache + MySQL + PHP) or equivalent LAMP/WAMP stack
- **Python 3.9+** (for data processing and ML pipeline)
- MySQL 5.7+ or MariaDB 10.2+
- PHP 7.4+ with MySQLi extension

## Installation

### 1. Download Source Data

Download the JPL SBDB query results CSV from:
```
https://ssd.jpl.nasa.gov/tools/sbdb_query.html
```

Select **all columns** and filter for:
- `neo = 'Y'` (Near-Earth Objects only)

Save as `data/sbdb_query_results.csv`

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Process and Clean Data

```bash
python process.py
```

This splits the raw JPL export into four cleaned CSV files:
- `data/neo_cleaned.csv`
- `data/physical_properties_cleaned.csv`
- `data/orbital_elements_cleaned.csv`
- `data/observation_record_cleaned.csv`

### 4. Run ML Pipeline

```bash
python pha_classifier/run_pipeline.py
python anomaly_flagger/flagger.py
```

This generates:
- `data/predictions_unlabelled.csv` (Random Forest PHA predictions)
- `data/anomalies_only.csv` (Statistical anomaly flags)

### 5. Set Up MySQL Database

Start MySQL via XAMPP Control Panel, then:

```bash
mysql -u root -p < setup.sql
mysql -u root -p < load.sql
```

### 6. Configure PHP API

Edit `api.php` and update database credentials:

```php
define('DB_HOST', 'localhost');
define('DB_USER', 'root');
define('DB_PASS', '');
define('DB_NAME', 'neo_hazard_db');
```

### 7. Deploy Web Interface

**XAMPP (Windows):**
```bash
cd C:/xampp/htdocs
mkdir public_html
cd public_html
# Copy all .php, .html, .js, .css files here
```

**Permissions (Linux/Mac):**
```bash
chmod 705 public_html
cd public_html
chmod 704 *.php
```

### 8. Access the Interface

Open browser to:
```
http://localhost/public_html/index.html
```

## The 16 Analytical Queries

| Query | Description | Use Case |
|-------|-------------|----------|
| **Q1** | PHA Threat Priority (cond_code ≤ 2, sorted by MOID) | Reliable orbit filtering for deflection planning |
| **Q2** | Official vs ML PHA % by orbital class | Model validation per dynamical population |
| **Q3** | Average properties by orbital class | Baseline for outlier detection |
| **Q4** | Planet-Killers (lowest H magnitude) | Global extinction event tracking |
| **Q5** | City-Killers (>140m, MOID<0.05 AU) | DART-class mission candidates |
| **Q6** | ML discrepancies (false positives/negatives) | Model retraining insights |
| **Q7** | Keyhole PHAs (ML risk >50% on official PHAs) | Gravitational keyhole investigation |
| **Q8** | Summary dashboard statistics | Executive risk overview |
| **Q9** | Gold-standard orbits (cond_code=0) | Spacecraft mission targets |
| **Q10** | Perihelion distribution by class | Sun-approaching object census |
| **Q11** | Anomaly stats for classes >10 members | Dynamically unusual families |
| **Q12** | Eccentricity distribution by class | Comet-like vs asteroid-like orbits |
| **Q13** | High-eccentricity wildcards (e>0.9) | Interstellar candidate identification |
| **Q14** | Sun-grazers + high inclination | Out-of-plane detection challenges |
| **Q15** | Orbital ellipse reconstruction | 3D visualization & trajectory planning |
| **Q16** | Longest observational arcs (>27 years) | Yarkovsky effect detection |

## Web Interface Features

- **Live dashboard** with summary statistics (total NEOs, PHA counts, anomaly flags)
- **Multi-parameter search** with real-time filtering by class, PHA status, MOID, diameter, condition code
- **Tab-organized queries** across 6 categories (Threat, Size, ML, Orbital, Anomaly, Observation)
- **Interactive results tables** with color-coded risk indicators
- **CSV export** for all query results
- **Responsive design** with dark theme optimized for astronomical data

## File Reference

| File | Purpose |
|------|---------|
| `process.py` | CSV cleaning and table splitting |
| `setup.sql` | Table creation DDL |
| `load.sql` | Data loading statements |
| `queries.sql` | All 16 analytical SQL queries |
| `api.php` | JSON API middleware |
| `index.html` | Frontend web interface |
| `cleanup.sql` | Table removal for fresh rebuild |
| `requirements.txt` | Python dependencies |
| `process.txt` | Detailed processing documentation |

## Data Source Attribution

All orbital and physical data provided by NASA Jet Propulsion Laboratory Solar System Dynamics Group. ML predictions and anomaly flags are generated by this system for analytical purposes and do not represent official NASA risk assessments.

---
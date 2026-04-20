# PHA Classification Pipeline - Random Forest

A machine learning pipeline for classifying Potentially Hazardous Asteroids (PHAs) based on orbital mechanics, physical properties, and observation quality using Random Forest classification.

## Overview

This pipeline trains and evaluates a Random Forest classifier to predict whether a Near-Earth Object (NEO) should be labeled as a Potentially Hazardous Asteroid (PHA = 'Y' or 'N'). The classification is based solely on orbital elements, derived physical properties, and observation quality metrics, without using the `pha` column itself during feature generation.

The system:
- Loads and filters NEO data from the SBDB (Small-Body Database)
- Engineers derived features from orbital mechanics
- Trains a Random Forest classifier with balanced class weights
- Evaluates performance with comprehensive metrics and visualizations
- Predicts PHA status for unlabelled objects

## File Structure

```
pha_classifier/
├── config.py                # Configuration and feature definitions
├── data_loader.py           # Data loading and initial filtering
├── feature_engineering.py   # Feature creation and transformation
├── model_pipeline.py        # Random Forest pipeline builder
├── evaluation.py            # Evaluation metrics and visualization
├── inference.py             # Inference on unlabelled data
├── run_pipeline.py          # Main orchestration script
├── utils.py                 # Shared utility functions (optional)
└── README.md                # This file
```

## File Descriptions

### `config.py`
**Purpose**: Central configuration for all features used in the pipeline.

**Contents**:
- `NUMERIC_FEATURES`: List of orbital, physical, and observation quality features (24 features)
- `CATEGORICAL_FEATURES`: List of categorical features (orbital class: AMO/APO/ATE/IEO)
- `DERIVED_FEATURES`: List of engineered features created from base features (7 features)
- `get_all_features()`: Function that returns combined numeric and categorical feature lists

---

### `data_loader.py`
**Purpose**: Load raw CSV data and split into labelled and unlabelled datasets.

**Contents**:
- `load_data(path)`: Reads CSV, replaces empty strings with NaN, splits data based on whether `pha` column has 'Y'/'N' values

**Output**:
- `labelled`: DataFrame with known PHA status (for training/evaluation)
- `unlabelled`: DataFrame with blank PHA status (for inference)

---

### `feature_engineering.py`
**Purpose**: Create derived features from base orbital and physical properties.

**Contents**:
- `engineer_features(df)`: Adds 7 derived features including:
  - `earth_crossing`: Binary flag for Earth-crossing orbits (q < 1 AU and ad > 1 AU)
  - `moid_er`: MOID in Earth radii (1 AU = 23,455 Earth radii)
  - `est_diameter_km`: Estimated diameter from absolute magnitude (assumes albedo 0.15)
  - `e_x_i`: Combined eccentricity-inclination metric (orbit energy proxy)
  - `v_rel_proxy`: Relative velocity proxy based on eccentricity
  - `ke_proxy`: Kinetic energy proxy (diameter^3 x velocity^2)
  - `arc_per_ratio`: Observation completeness ratio (arc length / orbital period)
- `prepare_features(df)`: Extracts feature matrix X and target vector y

---

### `model_pipeline.py`
**Purpose**: Build and configure scikit-learn pipeline for preprocessing and Random Forest classification.

**Contents**:
- `get_model_config()`: Returns Random Forest configuration:
  - 300 estimators (trees)
  - Max depth of 12 (prevents overfitting)
  - Balanced class weights (handles PHA/N imbalance)
  - Parallel processing (n_jobs=-1)
  - Fixed random state for reproducibility
- `build_pipeline(model)`: Creates a full pipeline with:
  - Median imputation for numeric features
  - Standard scaling for numeric features
  - Most-frequent imputation for categorical features
  - One-hot encoding for categorical features
  - Random Forest classifier
- `get_feature_names(pipe)`: Extracts feature names after preprocessing (including one-hot encoded categories)

---

### `evaluation.py`
**Purpose**: Evaluate Random Forest performance and generate diagnostic visualizations.

**Contents**:
- `evaluate_model(pipe, X_train, X_test, y_train, y_test)`: Trains model and computes:
  - ROC-AUC score
  - Average precision score
  - 5-fold cross-validated ROC-AUC (with standard deviation)
  - Confusion matrix
  - Classification report (precision, recall, f1-score per class)
- `plot_diagnostics(result, X_test, y_test, out_path)`: Creates a 4-panel diagnostic dashboard:
  1. ROC curve with AUC score
  2. Precision-Recall curve with Average Precision score
  3. Confusion matrix showing true/false positives/negatives
  4. Probability score distributions for PHA vs Non-PHA classes
- `plot_feature_importance(result, out_path, top_n)`: Horizontal bar chart of top N most important features
- `save_summary(result, out_path)`: Exports all performance metrics as JSON

---

### `inference.py`
**Purpose**: Apply trained Random Forest model to predict PHA status for unlabelled objects.

**Contents**:
- `run_inference(result, unlabelled, out_path)`: 
  - Applies feature engineering to unlabelled data
  - Generates probability scores and binary predictions
  - Sorts by probability (highest risk first)
  - Saves results to CSV with columns: `spkid`, `full_name`, `class`, `pha_prob`, `pha_pred`
  - Prints summary statistics and top 10 predicted PHAs

---

### `run_pipeline.py`
**Purpose**: Main orchestration script that executes the complete Random Forest workflow.

**Execution Flow**:
1. Parse command-line arguments (`--input`, `--outdir`)
2. Load and split data via `data_loader.load_data()`
3. Engineer features via `feature_engineering.engineer_features()`
4. Prepare feature matrix via `feature_engineering.prepare_features()`
5. Split data 80/20 (stratified) for training/testing
6. Build Random Forest pipeline via `model_pipeline.build_pipeline()`
7. Train and evaluate via `evaluation.evaluate_model()`
8. Generate diagnostic plots via `evaluation.plot_diagnostics()`
9. Plot feature importance via `evaluation.plot_feature_importance()`
10. Run inference on unlabelled data via `inference.run_inference()`
11. Save performance summary JSON via `evaluation.save_summary()`
12. Display summary metrics in console

---

### `utils.py` (optional)
**Purpose**: Shared utility functions for logging and file validation.

**Contents**:
- `setup_logging(log_file, level)`: Configures logging to console and optionally file
- `validate_input_file(filepath)`: Checks if input file exists and is readable

## Order of Usage

The pipeline executes in this specific order:

```
1. config.py (imported by all modules)
         |
         v
2. run_pipeline.py (main entry point)
         |
         +--> 3. data_loader.py (load and split data)
         |
         +--> 4. feature_engineering.py (create 7 derived features)
         |
         +--> 5. model_pipeline.py (build preprocessing + Random Forest pipeline)
         |
         +--> 6. evaluation.py (train, cross-validate, evaluate, plot diagnostics)
         |
         +--> 7. inference.py (predict on unlabelled data)
```

## Installation Requirements

```bash
pip install numpy pandas scikit-learn matplotlib
```


## Usage

### Basic Usage
```bash
python run_pipeline.py --input /path/to/sbdb_query_results.csv --outdir /path/to/outputs
```

### With Default Paths
```bash
python run_pipeline.py
```

### Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `--input` | Path to input CSV file | `/mnt/user-data/uploads/sbdb_query_results.csv` |
| `--outdir` | Output directory for results | `/home/claude/outputs` |

## Output Files

The pipeline generates the following files in the output directory:

| File | Description |
|------|-------------|
| `diagnostics.png` | 4-panel visualization dashboard: ROC curve, Precision-Recall curve, Confusion Matrix, Score Distribution |
| `feature_importance.png` | Horizontal bar chart of top 20 most important features with importance values |
| `predictions_unlabelled.csv` | PHA predictions for objects with unknown status, sorted by probability (highest first) |
| `model_summary.json` | Complete performance metrics in JSON format |

## Input Data Format

The input CSV should contain SBDB query results with at minimum:

### Required Columns
| Category | Columns |
|----------|---------|
| Orbital Elements | `e`, `q`, `i`, `om`, `w`, `ad`, `per_y`, `a` |
| Earth Proximity | `moid`, `moid_ld`, `moid_jup` |
| Physical Properties | `H`, `t_jup` |
| Observation Quality | `data_arc`, `n_obs_used`, `condition_code`, `rms` |
| Uncertainty Metrics | `sigma_e`, `sigma_q`, `sigma_i`, `sigma_om`, `sigma_w`, `sigma_a` |
| Classification | `class` (AMO/APO/ATE/IEO) |
| Target Variable | `pha` ('Y', 'N', or blank) |
| Identifiers | `spkid`, `full_name` |

## Random Forest Configuration

The model uses the following hyperparameters optimized for this classification task:

```python
RandomForestClassifier(
    n_estimators=300,        # Number of trees in the forest
    max_depth=12,           # Maximum depth of each tree
    class_weight='balanced',  # Automatically adjust weights inversely proportional to class frequencies
    n_jobs=-1,              # Use all available CPU cores
    random_state=0          # For reproducibility
)
```

### Why These Parameters?

- **n_estimators=300**: Sufficient trees for stable predictions without excessive computation time
- **max_depth=12**: Prevents overfitting while allowing complex decision boundaries
- **class_weight='balanced'**: Compensates for PHA/N class imbalance (typically ~15% PHA)
- **n_jobs=-1**: Parallelizes training across all CPU cores for speed
- **random_state=0**: Ensures reproducible results across runs

## Performance Metrics

The pipeline evaluates the Random Forest model using:

| Metric | Description | Target |
|--------|-------------|--------|
| **ROC-AUC** | Area under ROC curve, measures overall discriminative ability | >0.99 |
| **Average Precision** | Area under precision-recall curve, important for imbalanced data | >0.99 |
| **CV ROC-AUC** | 5-fold stratified cross-validated ROC-AUC on training set | >0.99 |
| **PHA Precision** | Proportion of predicted PHAs that are actually PHAs | >0.98 |
| **PHA Recall** | Proportion of actual PHAs that are correctly identified | >0.98 |
| **PHA F1-Score** | Harmonic mean of precision and recall for PHA class | >0.98 |
| **Accuracy** | Overall proportion of correct predictions | >0.99 |
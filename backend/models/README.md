# DemandLens - Models & Artifacts Directory

This directory stores the trained machine learning models, clustering artifacts, feature specifications, and group configurations for Store `CA_1` (3,049 items).

## Expected Artifacts & Destination Paths

Once Google Colab training (`DLens_07_LightGBM` and `DLens_08_Anomaly_Detection`) finishes, copy/download the following exported artifacts into this folder (`Models/`):

### 1. Demand Forecasting Models
| Filename | Description | Horizon | Objective / Config |
| :--- | :--- | :--- | :--- |
| `lightgbm_h7.joblib` | LightGBM Regressor | 7 Days | Tweedie loss ($p \in [1.1, 1.5]$), 24 features |
| `lightgbm_h28.joblib` | LightGBM Regressor | 28 Days | Tweedie loss ($p \in [1.1, 1.5]$), 24 features |

### 2. Feature Specification
- **`feature_lists.json`**:
  Contains JSON object with keys `features_7` and `features_28`.
  Exact 24 features used by the models:
  ```json
  {
    "features_7": [
      "lag_7", "lag_28", "rolling_mean_7", "rolling_mean_28",
      "wday", "month", "year", "is_weekend", "snap", "has_event",
      "sell_price", "price_change", "ev_Cultural", "ev_National",
      "ev_Religious", "ev_Sporting", "ev_None", "dept_FOODS_1",
      "dept_FOODS_2", "dept_FOODS_3", "dept_HOBBIES_1", "dept_HOBBIES_2",
      "dept_HOUSEHOLD_1", "dept_HOUSEHOLD_2"
    ],
    "features_28": [
      "lag_7", "lag_28", "rolling_mean_7", "rolling_mean_28",
      "wday", "month", "year", "is_weekend", "snap", "has_event",
      "sell_price", "price_change", "ev_Cultural", "ev_National",
      "ev_Religious", "ev_Sporting", "ev_None", "dept_FOODS_1",
      "dept_FOODS_2", "dept_FOODS_3", "dept_HOBBIES_1", "dept_HOBBIES_2",
      "dept_HOUSEHOLD_1", "dept_HOUSEHOLD_2"
    ]
  }
  ```

### 3. Clustering & Anomaly Detection Artifacts
| Filename | Description | Role in Pipeline |
| :--- | :--- | :--- |
| `kmeans_scaler.joblib` | `StandardScaler` | Normalizes demand features for clustering |
| `kmeans.joblib` | `KMeans` Model | Assigns items to demand velocity groups |
| `iso_forest.joblib` | `IsolationForest` Model | Unsupervised anomaly scoring on residual/sales |
| `item_groups.csv` | Item velocity groups | CSV columns: `item_id`, `group` |
| `group_thresholds.csv` | Rule-based thresholds | CSV columns: `group`, `spike_std`, `drop_std` |

---

## Processed Test Datasets (Save in `../data/`)
Processed test tables should be placed directly inside `data/`:
1. `data/CA_1_h7_test.parquet` (7-day evaluation features & ground truth for `2016-04-25` to `2016-05-22`)
2. `data/CA_1_h28_test.parquet` (28-day evaluation features & ground truth)
3. `data/anomalies_test.parquet` (Flagged historical anomalies with rule flags, isolation forest scores, and root causes)

---

## Automated Graceful Fallback
The FastAPI backend (`app/backend/`) is built with a dual-mode **Lifespan Model Loader**:
- If the above `.joblib` and `.parquet` files are present in `Models/` and `data/`, it loads them directly into memory.
- If they have not been copied yet, it logs a clean warning and falls back to a deterministic synthetic generator for Store `CA_1` so you and your team can test the backend and integrate frontend components immediately!

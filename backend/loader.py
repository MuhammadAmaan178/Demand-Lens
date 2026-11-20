"""
DemandLens Backend — Model and Data Loader
Loads all pre-trained LightGBM models, feature lists, and datasets once on startup.
"""

import json
import logging
import joblib
import pandas as pd
from config import (
    MODEL_H7_PATH,
    MODEL_H28_PATH,
    FEATURE_LISTS_PATH,
    HISTORY_SMALL_PATH,
    CALENDAR_SMALL_PATH,
    ANOMALIES_VAL_PATH,
    ITEM_GROUPS_PATH,
    GROUP_THRESHOLDS_PATH,
    ITEM_ERROR_SPREAD_PATH,
    validate_paths,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DemandLens.Loader")


class DataRegistry:
    """
    In-memory singleton container holding pre-loaded models and data tables.
    Loaded exactly once when the application boots up.
    """
    def __init__(self):
        self.is_loaded = False
        self.load_error = None

        # Models
        self.model_h7 = None
        self.model_h28 = None
        self.feature_lists = None

        # DataFrames
        self.df_history = None
        self.df_calendar = None
        self.df_anomalies = None
        self.df_item_groups = None
        self.df_group_thresholds = None
        self.df_item_error_spread = None

        # Metadata
        self.unique_items = []
        self.unique_items_set = set()
        self.unique_item_count = 0
        self.items_list = []

    def load_all(self):
        """Loads all required models and datasets with error handling and logging."""
        if self.is_loaded:
            logger.info("Artifacts already loaded in memory.")
            return

        logger.info("Initializing DemandLens Phase 2 artifact loading...")

        try:
            # 1. Validate that all required files exist
            validate_paths()
            logger.info("File path validation passed.")

            # 2. Load LightGBM Models
            logger.info(f"Loading 7-day model from: {MODEL_H7_PATH.name}")
            self.model_h7 = joblib.load(MODEL_H7_PATH)
            logger.info(f"Successfully loaded H7 model: {type(self.model_h7).__name__}")

            logger.info(f"Loading 28-day model from: {MODEL_H28_PATH.name}")
            self.model_h28 = joblib.load(MODEL_H28_PATH)
            logger.info(f"Successfully loaded H28 model: {type(self.model_h28).__name__}")

            # 3. Load Feature Lists JSON
            logger.info(f"Loading feature lists from: {FEATURE_LISTS_PATH.name}")
            with open(FEATURE_LISTS_PATH, "r", encoding="utf-8") as f:
                self.feature_lists = json.load(f)
            features_7 = self.feature_lists.get("features_7", [])
            features_28 = self.feature_lists.get("features_28", [])
            logger.info(
                f"Feature lists loaded (features_7: {len(features_7)} cols, features_28: {len(features_28)} cols)"
            )

            # 4. Load History Small (Parquet)
            logger.info(f"Loading history data from: {HISTORY_SMALL_PATH.name}")
            self.df_history = pd.read_parquet(HISTORY_SMALL_PATH)
            required_hist_cols = ["item_id", "dept_id", "date", "sales", "sell_price"]
            for col in required_hist_cols:
                if col not in self.df_history.columns:
                    raise ValueError(f"Missing required column '{col}' in {HISTORY_SMALL_PATH.name}")
            logger.info(f"History data loaded: {len(self.df_history):,} rows")

            # 5. Load Calendar Small (CSV)
            logger.info(f"Loading calendar data from: {CALENDAR_SMALL_PATH.name}")
            self.df_calendar = pd.read_csv(CALENDAR_SMALL_PATH)
            required_cal_cols = ["date", "wday", "month", "year", "event_name_1", "snap_CA"]
            for col in required_cal_cols:
                if col not in self.df_calendar.columns:
                    raise ValueError(f"Missing required column '{col}' in {CALENDAR_SMALL_PATH.name}")
            logger.info(f"Calendar data loaded: {len(self.df_calendar):,} rows")

            # 6. Load Anomalies Validation (Parquet)
            logger.info(f"Loading anomalies validation data from: {ANOMALIES_VAL_PATH.name}")
            self.df_anomalies = pd.read_parquet(ANOMALIES_VAL_PATH)
            required_anom_cols = ["item_id", "date", "sales", "forecast", "direction", "reason", "flagged_by"]
            for col in required_anom_cols:
                if col not in self.df_anomalies.columns:
                    raise ValueError(f"Missing required column '{col}' in {ANOMALIES_VAL_PATH.name}")
            logger.info(f"Anomalies validation data loaded: {len(self.df_anomalies):,} rows")

            # 7. Load Item Groups (CSV)
            logger.info(f"Loading item groups from: {ITEM_GROUPS_PATH.name}")
            self.df_item_groups = pd.read_csv(ITEM_GROUPS_PATH)
            if "item_id" not in self.df_item_groups.columns or "group" not in self.df_item_groups.columns:
                raise ValueError(f"Missing required columns in {ITEM_GROUPS_PATH.name}")
            logger.info(f"Item groups loaded: {len(self.df_item_groups):,} items")

            # 8. Load Group Thresholds (CSV)
            logger.info(f"Loading group thresholds from: {GROUP_THRESHOLDS_PATH.name}")
            self.df_group_thresholds = pd.read_csv(GROUP_THRESHOLDS_PATH)
            logger.info(f"Group thresholds loaded: {len(self.df_group_thresholds)} groups")

            # 9. Load Item Error Spread (CSV)
            logger.info(f"Loading item error spread from: {ITEM_ERROR_SPREAD_PATH.name}")
            self.df_item_error_spread = pd.read_csv(ITEM_ERROR_SPREAD_PATH)
            if "item_id" not in self.df_item_error_spread.columns or "typical_daily_error" not in self.df_item_error_spread.columns:
                raise ValueError(f"Missing required columns in {ITEM_ERROR_SPREAD_PATH.name}")
            logger.info(f"Item error spread loaded: {len(self.df_item_error_spread):,} items")

            # 10. Verify Store CA_1 Item Count (must be exactly 3,049)
            self.unique_items = sorted(self.df_item_groups["item_id"].dropna().unique().tolist())
            self.unique_items_set = set(self.unique_items)
            self.unique_item_count = len(self.unique_items)
            logger.info(f"Verified unique CA_1 items count: {self.unique_item_count}")

            if self.unique_item_count != 3049:
                logger.warning(
                    f"Expected 3,049 items for CA_1 but found {self.unique_item_count}. Check dataset filtering."
                )

            # Pre-build structured item list for fast picker dropdowns (GET /items)
            self.items_list = [
                {
                    "item_id": str(row["item_id"]),
                    "department": "_".join(str(row["item_id"]).split("_")[:2]),
                    "group": str(row["group"])
                }
                for _, row in self.df_item_groups.iterrows()
            ]
            logger.info(f"Pre-built {len(self.items_list)} item dictionary records for API dropdowns.")

            self.is_loaded = True
            logger.info(">>> ALL DEMANDLENS MODELS AND DATASETS LOADED SUCCESSFULLY <<<")

        except Exception as e:
            self.load_error = str(e)
            logger.error(f"FATAL: Error during model or data loading: {e}", exc_info=True)
            raise e

    def get_status_summary(self):
        """Returns clean diagnostic status summary without exposing sensitive filesystem paths."""
        if not self.is_loaded:
            return {
                "status": "error",
                "error": self.load_error or "Artifacts not loaded yet."
            }

        return {
            "status": "ready",
            "models": {
                "lightgbm_h7": "loaded" if self.model_h7 is not None else "failed",
                "lightgbm_h28": "loaded" if self.model_h28 is not None else "failed"
            },
            "feature_lists": {
                "status": "loaded" if self.feature_lists is not None else "failed",
                "features_7_count": len(self.feature_lists.get("features_7", [])),
                "features_28_count": len(self.feature_lists.get("features_28", []))
            },
            "datasets": {
                "history_small": {
                    "loaded": self.df_history is not None,
                    "rows": len(self.df_history) if self.df_history is not None else 0,
                    "unique_items": int(self.df_history["item_id"].nunique()) if self.df_history is not None else 0
                },
                "calendar_small": {
                    "loaded": self.df_calendar is not None,
                    "rows": len(self.df_calendar) if self.df_calendar is not None else 0
                },
                "anomalies_validation": {
                    "loaded": self.df_anomalies is not None,
                    "rows": len(self.df_anomalies) if self.df_anomalies is not None else 0,
                    "unique_items": int(self.df_anomalies["item_id"].nunique()) if self.df_anomalies is not None else 0
                },
                "item_groups": {
                    "loaded": self.df_item_groups is not None,
                    "rows": len(self.df_item_groups) if self.df_item_groups is not None else 0,
                    "unique_items": int(self.df_item_groups["item_id"].nunique()) if self.df_item_groups is not None else 0
                },
                "group_thresholds": {
                    "loaded": self.df_group_thresholds is not None,
                    "rows": len(self.df_group_thresholds) if self.df_group_thresholds is not None else 0
                },
                "item_error_spread": {
                    "loaded": self.df_item_error_spread is not None,
                    "rows": len(self.df_item_error_spread) if self.df_item_error_spread is not None else 0,
                    "unique_items": int(self.df_item_error_spread["item_id"].nunique()) if self.df_item_error_spread is not None else 0
                }
            },
            "unique_ca1_items": self.unique_item_count,
            "modules": {
                "features": "available",
                "reorder": "available"
            }
        }


# Global registry instance
registry = DataRegistry()

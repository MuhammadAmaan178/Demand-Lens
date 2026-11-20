"""
DemandLens Backend — Configuration Module
Manages file paths, directory settings, and validation for models and datasets.
"""

import os
from pathlib import Path

# Paths to core directories
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

# Check primary locations: backend/data or backend handover/
HANDOVER_DIR = PROJECT_DIR / "backend handover"
BACKEND_DATA_DIR = BACKEND_DIR / "data"
BACKEND_MODELS_DIR = BACKEND_DIR / "models"


def resolve_file_path(filename, subfolder=None):
    """
    Finds a required file across supported project directories:
    1. backend/data or backend/models (if subfolder provided)
    2. backend handover/
    3. project parent directory (DemandLens/..)
    """
    candidates = []
    if subfolder:
        candidates.append(BACKEND_DIR / subfolder / filename)
    candidates.append(HANDOVER_DIR / filename)
    candidates.append(BACKEND_DIR / filename)
    candidates.append(PROJECT_DIR.parent / "files" / filename)

    for path in candidates:
        if path.is_file():
            return path

    # If not found, return primary expected path for error reporting
    return HANDOVER_DIR / filename


# File paths for Phase 2 loading
MODEL_H7_PATH = resolve_file_path("lightgbm_h7.joblib", "models")
MODEL_H28_PATH = resolve_file_path("lightgbm_h28.joblib", "models")
FEATURE_LISTS_PATH = resolve_file_path("feature_lists.json", "data")
HISTORY_SMALL_PATH = resolve_file_path("history_small.parquet", "data")
CALENDAR_SMALL_PATH = resolve_file_path("calendar_small.csv", "data")
ANOMALIES_VAL_PATH = resolve_file_path("anomalies_validation.parquet", "data")
ITEM_GROUPS_PATH = resolve_file_path("item_groups.csv", "data")
GROUP_THRESHOLDS_PATH = resolve_file_path("group_thresholds.csv", "data")
ITEM_ERROR_SPREAD_PATH = resolve_file_path("item_error_spread.csv", "data")

REQUIRED_FILES = {
    "model_h7": MODEL_H7_PATH,
    "model_h28": MODEL_H28_PATH,
    "feature_lists": FEATURE_LISTS_PATH,
    "history_small": HISTORY_SMALL_PATH,
    "calendar_small": CALENDAR_SMALL_PATH,
    "anomalies_val": ANOMALIES_VAL_PATH,
    "item_groups": ITEM_GROUPS_PATH,
    "group_thresholds": GROUP_THRESHOLDS_PATH,
    "item_error_spread": ITEM_ERROR_SPREAD_PATH,
}


def validate_paths():
    """
    Verifies that all required models and datasets exist on disk.
    Raises FileNotFoundError if any file is missing.
    """
    missing = []
    for name, path in REQUIRED_FILES.items():
        if not path.is_file():
            missing.append(f"{name}: {path.name} (checked in {path.parent})")

    if missing:
        error_msg = "Missing required backend handover files:\n" + "\n".join(f" - {m}" for m in missing)
        raise FileNotFoundError(error_msg)
    return True

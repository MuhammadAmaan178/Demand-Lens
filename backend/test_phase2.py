"""
DemandLens — Backend Phase 2 Verification Test Suite
Tests model loading, data loading, column existence, item counts, error handling, and endpoints.
"""

import sys
import unittest
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import app
from loader import registry


class TestBackendPhase2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_01_models_loaded(self):
        """Verify H7 and H28 LightGBM models are loaded and intact."""
        self.assertIsNotNone(registry.model_h7, "H7 model is None")
        self.assertIsNotNone(registry.model_h28, "H28 model is None")
        self.assertEqual(type(registry.model_h7).__name__, "LGBMRegressor")
        self.assertEqual(type(registry.model_h28).__name__, "LGBMRegressor")

    def test_02_feature_lists(self):
        """Verify feature_lists.json structure and feature counts."""
        self.assertIsNotNone(registry.feature_lists, "feature_lists is None")
        self.assertIn("features_7", registry.feature_lists)
        self.assertIn("features_28", registry.feature_lists)
        self.assertEqual(len(registry.feature_lists["features_7"]), 27)
        self.assertEqual(len(registry.feature_lists["features_28"]), 27)

    def test_03_history_small_dataset(self):
        """Verify history_small dataset has rows, unique items, and required columns."""
        df = registry.df_history
        self.assertIsNotNone(df, "df_history is None")
        self.assertGreater(len(df), 0)
        for col in ["item_id", "dept_id", "date", "sales", "sell_price"]:
            self.assertIn(col, df.columns)
        self.assertEqual(df["item_id"].nunique(), 3049)

    def test_04_calendar_small_dataset(self):
        """Verify calendar_small dataset and required columns."""
        df = registry.df_calendar
        self.assertIsNotNone(df, "df_calendar is None")
        for col in ["date", "wday", "month", "year", "event_name_1", "snap_CA"]:
            self.assertIn(col, df.columns)

    def test_05_anomalies_validation_dataset(self):
        """Verify anomalies_validation dataset, columns, and item count."""
        df = registry.df_anomalies
        self.assertIsNotNone(df, "df_anomalies is None")
        for col in ["item_id", "date", "sales", "forecast", "direction", "reason", "flagged_by"]:
            self.assertIn(col, df.columns)
        self.assertEqual(df["item_id"].nunique(), 3049)

    def test_06_item_groups_and_thresholds(self):
        """Verify item_groups (3,049 items) and group_thresholds (3 groups)."""
        df_groups = registry.df_item_groups
        self.assertIsNotNone(df_groups, "df_item_groups is None")
        self.assertEqual(df_groups["item_id"].nunique(), 3049)
        self.assertIn("group", df_groups.columns)

        df_thresh = registry.df_group_thresholds
        self.assertIsNotNone(df_thresh, "df_group_thresholds is None")
        self.assertEqual(len(df_thresh), 3)

    def test_07_item_error_spread(self):
        """Verify item_error_spread has exactly 3,049 items and typical_daily_error."""
        df_spread = registry.df_item_error_spread
        self.assertIsNotNone(df_spread, "df_item_error_spread is None")
        self.assertEqual(df_spread["item_id"].nunique(), 3049)
        self.assertIn("typical_daily_error", df_spread.columns)

    def test_08_exact_ca1_item_count(self):
        """Verify Store CA_1 item count is exactly 3,049."""
        self.assertEqual(registry.unique_item_count, 3049)

    def test_09_health_endpoint_ready(self):
        """Verify /health and /api/health respond 200 OK with artifacts: loaded."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "ok")
        self.assertEqual(json_data["artifacts"], "loaded")

        res_api = self.client.get("/api/health")
        self.assertEqual(res_api.status_code, 200)
        self.assertEqual(res_api.get_json()["status"], "ok")

    def test_10_debug_status_endpoint(self):
        """Verify /debug/status returns 200 with complete diagnostic summary without leaking paths."""
        res = self.client.get("/debug/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["models"]["lightgbm_h7"], "loaded")
        self.assertEqual(data["models"]["lightgbm_h28"], "loaded")
        self.assertEqual(data["feature_lists"]["features_7_count"], 27)
        self.assertEqual(data["feature_lists"]["features_28_count"], 27)
        self.assertEqual(data["unique_ca1_items"], 3049)
        self.assertTrue(data["datasets"]["history_small"]["loaded"])
        self.assertTrue(data["datasets"]["anomalies_validation"]["loaded"])

    def test_11_health_degraded_when_artifacts_not_loaded(self):
        """Verify /health returns 503 and not_ready if artifacts failed to load."""
        original_state = registry.is_loaded
        try:
            registry.is_loaded = False
            res = self.client.get("/health")
            self.assertEqual(res.status_code, 503)
            self.assertEqual(res.get_json()["status"], "not_ready")
            self.assertIn("error", res.get_json())
        finally:
            registry.is_loaded = original_state

    def test_12_phase1_endpoints_labeled_as_mock(self):
        """Verify Phase 1 compatibility endpoints clearly return is_demo_data: True."""
        res_items = self.client.get("/api/items")
        self.assertTrue(res_items.get_json().get("is_demo_data"))

        res_forecast = self.client.get("/api/forecast")
        self.assertTrue(res_forecast.get_json().get("is_demo_data"))

        res_anomalies = self.client.get("/api/anomalies")
        self.assertTrue(res_anomalies.get_json().get("is_demo_data"))

        res_reorder = self.client.post("/api/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-05-01",
            "current_stock": 10,
            "lead_time_days": 3
        })
        self.assertTrue(res_reorder.get_json().get("is_demo_data"))


if __name__ == "__main__":
    unittest.main()

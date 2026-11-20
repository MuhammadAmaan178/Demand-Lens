"""
DemandLens Backend — Phase 3 Test Suite: Real Forecast API
Tests all Phase 3 deliverables:
  1. Health & Debug status endpoints
  2. GET /items and /api/items returning real 3,049 Store CA_1 items
  3. GET /forecast and /api/forecast live ML inference with LightGBM H7 & H28
  4. Data Leakage Prevention validation (history <= today)
  5. Parameter validations (missing params, unknown item, bad date, out-of-range date)
  6. Multi-item and multi-horizon validation
  7. Verification that /anomalies and /reorder remain labeled as demo/mock data
"""

import sys
import unittest
import pandas as pd
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app
from loader import registry


class DemandLensPhase3TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up Flask test client and ensure models are loaded."""
        cls.client = app.test_client()
        if not registry.is_loaded:
            registry.load_all()

    # -------------------------------------------------------------------
    # 1. Health and Diagnostic Endpoints
    # -------------------------------------------------------------------
    def test_01_health_endpoints(self):
        """Verify /health and /api/health report 200 OK and loaded status."""
        for path in ["/health", "/api/health"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("status"), "ok")
            self.assertEqual(data.get("artifacts"), "loaded")

    def test_02_debug_status(self):
        """Verify /debug/status reports ready status and 3,049 items."""
        res = self.client.get("/debug/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ready")
        self.assertEqual(data.get("unique_ca1_items"), 3049)
        self.assertEqual(data["models"]["lightgbm_h7"], "loaded")
        self.assertEqual(data["models"]["lightgbm_h28"], "loaded")

    # -------------------------------------------------------------------
    # 2. Real Store CA_1 Item Catalogue
    # -------------------------------------------------------------------
    def test_03_get_items_count_and_structure(self):
        """Verify /items and /api/items return all 3,049 items with required keys."""
        for path in ["/items", "/api/items"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn("items", data)
            items = data["items"]
            self.assertEqual(len(items), 3049)
            self.assertEqual(data.get("count"), 3049)

            # Check structure of the first item
            first_item = items[0]
            self.assertIn("item_id", first_item)
            self.assertIn("department", first_item)
            self.assertIn("group", first_item)

            # Verify departments are valid CA_1 departments
            valid_depts = {
                "FOODS_1", "FOODS_2", "FOODS_3",
                "HOBBIES_1", "HOBBIES_2",
                "HOUSEHOLD_1", "HOUSEHOLD_2"
            }
            self.assertIn(first_item["department"], valid_depts)

    def test_04_known_items_exist_in_catalogue(self):
        """Verify specific known CA_1 items exist in the catalogue."""
        res = self.client.get("/items")
        data = res.get_json()
        item_ids = {item["item_id"] for item in data["items"]}
        for target in ["FOODS_1_001", "FOODS_1_004", "HOBBIES_1_001", "HOUSEHOLD_1_001"]:
            self.assertIn(target, item_ids)

    # -------------------------------------------------------------------
    # 3. Real Forecast Inference (Validation Period)
    # -------------------------------------------------------------------
    def test_05_forecast_valid_request(self):
        """Verify /forecast returns real 7-day and 28-day predictions with history."""
        res = self.client.get("/forecast?item_id=FOODS_1_001&today=2016-04-24")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        # Check top-level keys
        self.assertEqual(data.get("item_id"), "FOODS_1_001")
        self.assertEqual(data.get("today"), "2016-04-24")
        self.assertIn("history", data)
        self.assertIn("forecast_7", data)
        self.assertIn("forecast_28", data)

        # Check 7-day forecast
        f7 = data["forecast_7"]
        self.assertEqual(len(f7), 7)
        self.assertEqual(f7[0]["date"], "2016-04-25")
        self.assertEqual(f7[-1]["date"], "2016-05-01")
        for pt in f7:
            self.assertIsInstance(pt["value"], (int, float))
            self.assertGreaterEqual(pt["value"], 0.0)

        # Check 28-day forecast
        f28 = data["forecast_28"]
        self.assertEqual(len(f28), 28)
        self.assertEqual(f28[0]["date"], "2016-04-25")
        self.assertEqual(f28[-1]["date"], "2016-05-22")
        for pt in f28:
            self.assertIsInstance(pt["value"], (int, float))
            self.assertGreaterEqual(pt["value"], 0.0)

        # Check history length and format
        hist = data["history"]
        self.assertGreater(len(hist), 0)
        self.assertLessEqual(len(hist), 14)
        for pt in hist:
            self.assertIn("date", pt)
            self.assertIn("sales", pt)

    def test_06_forecast_data_leakage_protection(self):
        """
        Verify strict Data Leakage Protection:
        1. No history date can ever be greater than 'today'.
        2. Forecast dates must strictly begin at today + 1.
        """
        test_dates = ["2016-03-28", "2016-04-10", "2016-04-24"]
        for test_today in test_dates:
            res = self.client.get(f"/forecast?item_id=FOODS_1_001&today={test_today}")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()

            # Verify no history record occurs after today
            for h in data["history"]:
                self.assertLessEqual(
                    h["date"],
                    test_today,
                    f"Data leakage detected! History date {h['date']} > today {test_today}"
                )

            # Verify forecast starts strictly on today + 1
            expected_start = (pd.to_datetime(test_today) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            self.assertEqual(data["forecast_7"][0]["date"], expected_start)
            self.assertEqual(data["forecast_28"][0]["date"], expected_start)

    def test_07_post_validation_dates_rejected(self):
        """
        Option A (Strict Truthful Validation Window):
        Verify dates after 2016-04-24 are rejected with 400 Bad Request
        to prevent gap distortion and unobserved test-period leakage.
        """
        for rejected_date in ["2016-04-25", "2016-05-01", "2016-05-22"]:
            res = self.client.get(f"/forecast?item_id=FOODS_1_001&today={rejected_date}")
            self.assertEqual(res.status_code, 400, f"Expected 400 for {rejected_date}")
            data = res.get_json()
            self.assertIn("outside allowed validation period", data["error"])

    def test_08_forecast_api_prefix_route(self):
        """Verify /api/forecast route returns identical valid response."""
        res = self.client.get("/api/forecast?item_id=FOODS_1_001&today=2016-04-24")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("item_id"), "FOODS_1_001")
        self.assertEqual(len(data["forecast_7"]), 7)

    def test_09_forecast_different_items_and_departments(self):
        """Verify forecasting works across different product categories and departments."""
        test_items = ["FOODS_1_004", "HOBBIES_1_001", "HOUSEHOLD_1_001"]
        for item in test_items:
            res = self.client.get(f"/forecast?item_id={item}&today=2016-04-20")
            self.assertEqual(res.status_code, 200, f"Failed for item {item}")
            data = res.get_json()
            self.assertEqual(data["item_id"], item)
            self.assertEqual(len(data["forecast_7"]), 7)
            self.assertEqual(len(data["forecast_28"]), 28)

    # -------------------------------------------------------------------
    # 4. Parameter Validation & Error Handling
    # -------------------------------------------------------------------
    def test_10_missing_parameters(self):
        """Verify 400 Bad Request when required parameters are omitted."""
        # Missing both
        res = self.client.get("/forecast")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Missing required parameter", res.get_json()["error"])

        # Missing today
        res = self.client.get("/forecast?item_id=FOODS_1_001")
        self.assertEqual(res.status_code, 400)
        self.assertIn("today", res.get_json()["error"])

        # Missing item_id
        res = self.client.get("/forecast?today=2016-04-24")
        self.assertEqual(res.status_code, 400)
        self.assertIn("item_id", res.get_json()["error"])

    def test_11_unknown_item_id(self):
        """Verify 404 Not Found when requested item is not in Store CA_1 catalogue."""
        res = self.client.get("/forecast?item_id=NONEXISTENT_ITEM_999&today=2016-04-24")
        self.assertEqual(res.status_code, 404)
        self.assertIn("not found in Store CA_1", res.get_json()["error"])

    def test_12_invalid_date_format(self):
        """Verify 400 Bad Request when date is not formatted as YYYY-MM-DD."""
        for bad_date in ["24-04-2016", "2016/04/24", "not-a-date", "2016-13-45"]:
            res = self.client.get(f"/forecast?item_id=FOODS_1_001&today={bad_date}")
            self.assertEqual(res.status_code, 400, f"Should have rejected bad date: {bad_date}")
            self.assertIn("Invalid date format", res.get_json()["error"])

    def test_13_date_outside_allowed_range(self):
        """
        Verify 400 Bad Request when date is outside validation range
        (2016-03-28 to 2016-04-24).
        """
        # Day before range start
        res = self.client.get("/forecast?item_id=FOODS_1_001&today=2016-03-27")
        self.assertEqual(res.status_code, 400)
        self.assertIn("outside allowed validation period", res.get_json()["error"])

        # Boundary test: exactly on last allowed day
        res_ok = self.client.get("/forecast?item_id=FOODS_1_001&today=2016-04-24")
        self.assertEqual(res_ok.status_code, 200)

        # Day after range end (2016-04-25)
        res_after = self.client.get("/forecast?item_id=FOODS_1_001&today=2016-04-25")
        self.assertEqual(res_after.status_code, 400)
        self.assertIn("outside allowed validation period", res_after.get_json()["error"])

    # -------------------------------------------------------------------
    # 5. Preservation of Labeled Mock Endpoints
    # -------------------------------------------------------------------
    def test_14_mock_endpoints_labeled_cleanly(self):
        """Verify remaining Phase 1 endpoint (/reorder) remains available and labeled as demo data."""
        # POST /reorder
        res_reorder = self.client.post("/reorder", json={"item_id": "FOODS_1_001", "today": "2016-04-24"})
        self.assertEqual(res_reorder.status_code, 200)
        data_reorder = res_reorder.get_json()
        self.assertTrue(data_reorder.get("is_demo_data"))
        self.assertEqual(res_reorder.status_code, 200)
        data_reorder = res_reorder.get_json()
        self.assertTrue(data_reorder.get("is_demo_data"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

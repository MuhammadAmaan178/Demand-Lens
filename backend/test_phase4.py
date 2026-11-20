"""
DemandLens Backend — Phase 4 Test Suite: Real Anomaly Detection API
Tests all Phase 4 deliverables:
  1. Valid anomalies request
  2. Optional item_id omitted (returns all store anomalies)
  3. Valid individual item_id
  4. Unknown item_id (400 Bad Request)
  5. Invalid date format (400 Bad Request)
  6. Date below minimum (400 Bad Request)
  7. Date above maximum (400 Bad Request)
  8. No anomaly with date greater than selected today
  9. Correct chronological ordering
  10. Spike/drop filtering compatibility
  11. Reason and flagged_by compatibility
  12. Summary counts match returned records
  13. Empty results handled correctly
  14. Response does not claim demo/mock data
  15. H7-only anomaly data is used
  16. No test-period data is loaded
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


class DemandLensPhase4TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up Flask test client and ensure data is loaded."""
        cls.client = app.test_client()
        if not registry.is_loaded:
            registry.load_all()

    # -------------------------------------------------------------------
    # 1. Valid Requests & Parameter Filtering
    # -------------------------------------------------------------------
    def test_01_valid_anomalies_request(self):
        """Verify GET /anomalies and /api/anomalies return 200 OK with required schema."""
        for path in ["/anomalies?today=2016-04-24", "/api/anomalies?today=2016-04-24"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("today"), "2016-04-24")
            self.assertIn("anomalies", data)
            self.assertIsInstance(data["anomalies"], list)
            self.assertGreater(len(data["anomalies"]), 0)

            # Inspect structure of first record
            first = data["anomalies"][0]
            for field in ["item_id", "date", "sales", "forecast", "direction", "reason", "flagged_by"]:
                self.assertIn(field, first)

    def test_02_optional_item_id_omitted(self):
        """When item_id is omitted, verify all store anomalies on or before today are returned."""
        res = self.client.get("/anomalies?today=2016-04-24")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsNone(data.get("item_id"))
        anomalies = data["anomalies"]

        # Multiple different items should be present
        unique_items = {a["item_id"] for a in anomalies}
        self.assertGreater(len(unique_items), 100)
        # Total flagged anomalies on or before 2016-04-24 is exactly 1,908
        self.assertEqual(len(anomalies), 1908)

    def test_03_valid_individual_item_id(self):
        """When a valid item_id is specified, verify only that item's anomalies are returned."""
        test_item = "FOODS_3_090"
        res = self.client.get(f"/anomalies?today=2016-04-24&item_id={test_item}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("item_id"), test_item)
        anomalies = data["anomalies"]
        self.assertGreater(len(anomalies), 0)
        for a in anomalies:
            self.assertEqual(a["item_id"], test_item)

    def test_04_unknown_item_id(self):
        """Verify 400 Bad Request when an unknown item_id is provided."""
        res = self.client.get("/anomalies?today=2016-04-24&item_id=NONEXISTENT_ITEM_XYZ")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("not found in Store CA_1 catalogue", data.get("error", ""))

    # -------------------------------------------------------------------
    # 2. Date Validation & Boundary Tests
    # -------------------------------------------------------------------
    def test_05_invalid_date_format(self):
        """Verify 400 Bad Request when date is not formatted as YYYY-MM-DD."""
        for bad_date in ["24-04-2016", "2016/04/24", "invalid-date", "2016-02-31"]:
            res = self.client.get(f"/anomalies?today={bad_date}")
            self.assertEqual(res.status_code, 400)
            self.assertIn("Invalid date format", res.get_json().get("error", ""))

    def test_06_date_below_minimum(self):
        """Verify 400 Bad Request when date is before 2016-03-28."""
        res = self.client.get("/anomalies?today=2016-03-27")
        self.assertEqual(res.status_code, 400)
        self.assertIn("outside allowed validation period", res.get_json().get("error", ""))

    def test_07_date_above_maximum(self):
        """Verify 400 Bad Request when date is after 2016-04-24."""
        for future_date in ["2016-04-25", "2016-05-01", "2016-05-22"]:
            res = self.client.get(f"/anomalies?today={future_date}")
            self.assertEqual(res.status_code, 400)
            self.assertIn("outside allowed validation period", res.get_json().get("error", ""))

    def test_08_no_anomaly_date_greater_than_today(self):
        """Verify strict temporal cutoff: no anomaly record can have a date > today."""
        cutoff_dates = ["2016-03-28", "2016-04-05", "2016-04-15", "2016-04-24"]
        for test_today in cutoff_dates:
            res = self.client.get(f"/anomalies?today={test_today}")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            for a in data["anomalies"]:
                self.assertLessEqual(
                    a["date"],
                    test_today,
                    f"Temporal leakage: anomaly date {a['date']} > selected today {test_today}"
                )

    def test_09_correct_chronological_ordering(self):
        """Verify anomaly records are sorted in chronological order (dates ascending)."""
        res = self.client.get("/anomalies?today=2016-04-24")
        self.assertEqual(res.status_code, 200)
        anomalies = res.get_json()["anomalies"]
        dates = [a["date"] for a in anomalies]
        self.assertEqual(dates, sorted(dates), "Anomalies must be sorted chronologically by date.")

    # -------------------------------------------------------------------
    # 3. Frontend Filter Compatibility & Schema Integrity
    # -------------------------------------------------------------------
    def test_10_spike_drop_filtering_compatibility(self):
        """Verify all returned anomalies have direction in {'spike', 'drop'} matching frontend options."""
        res = self.client.get("/anomalies?today=2016-04-24")
        self.assertEqual(res.status_code, 200)
        anomalies = res.get_json()["anomalies"]
        directions = {a["direction"] for a in anomalies}
        self.assertTrue(directions.issubset({"spike", "drop"}))
        self.assertIn("spike", directions)
        self.assertIn("drop", directions)

    def test_11_reason_and_flagged_by_compatibility(self):
        """Verify reason labels and mapped flagged_by values align with frontend filter expectations."""
        res = self.client.get("/anomalies?today=2016-04-24")
        self.assertEqual(res.status_code, 200)
        anomalies = res.get_json()["anomalies"]

        flags = {a["flagged_by"] for a in anomalies}
        self.assertTrue(flags.issubset({"rule", "isolation", "both"}))
        self.assertIn("rule", flags)
        self.assertIn("isolation", flags)
        self.assertIn("both", flags)

        reasons = {a["reason"] for a in anomalies}
        valid_reasons = {"SNAP day", "price change", "unexplained", "event"}
        self.assertTrue(reasons.issubset(valid_reasons))

    def test_12_summary_counts_match_returned_records(self):
        """Verify summary counts in the response exactly match the count and composition of returned anomalies."""
        res = self.client.get("/anomalies?today=2016-04-24")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        anomalies = data["anomalies"]
        summary = data["summary"]

        self.assertEqual(summary["total"], len(anomalies))
        self.assertEqual(data["count"], len(anomalies))

        # Check spikes and drops
        expected_spikes = sum(1 for a in anomalies if a["direction"] == "spike")
        expected_drops = sum(1 for a in anomalies if a["direction"] == "drop")
        self.assertEqual(summary["spikes"], expected_spikes)
        self.assertEqual(summary["drops"], expected_drops)
        self.assertEqual(summary["spikes"] + summary["drops"], summary["total"])

        # Check flags
        expected_rule = sum(1 for a in anomalies if a["flagged_by"] == "rule")
        expected_iso = sum(1 for a in anomalies if a["flagged_by"] == "isolation")
        expected_both = sum(1 for a in anomalies if a["flagged_by"] == "both")
        self.assertEqual(summary["by_flag"]["rule"], expected_rule)
        self.assertEqual(summary["by_flag"]["isolation"], expected_iso)
        self.assertEqual(summary["by_flag"]["both"], expected_both)

    def test_13_empty_results_handled_correctly(self):
        """Verify items with zero anomalies (e.g., FOODS_1_001) return empty list with 200 OK."""
        res = self.client.get("/anomalies?today=2016-04-24&item_id=FOODS_1_001")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("anomalies"), [])
        self.assertEqual(data.get("count"), 0)
        self.assertEqual(data.get("summary")["total"], 0)

    # -------------------------------------------------------------------
    # 4. Strict ML & Data Integrity Tests
    # -------------------------------------------------------------------
    def test_14_response_does_not_claim_demo_mock_data(self):
        """Verify the real Phase 4 response does NOT claim demo/mock data."""
        res = self.client.get("/anomalies?today=2016-04-24")
        data = res.get_json()
        self.assertFalse(data.get("is_demo_data", False))
        self.assertNotIn("source", data)

    def test_15_h7_only_anomaly_data_is_used(self):
        """Verify anomaly records stem from H7 validation forecasts (Notebook 08 pipeline)."""
        df_anom = registry.df_anomalies
        self.assertIsNotNone(df_anom)
        self.assertEqual(len(df_anom), 85372)
        # Dates span exactly the 28-day validation period
        self.assertEqual(pd.to_datetime(df_anom["date"]).min().strftime("%Y-%m-%d"), "2016-03-28")
        self.assertEqual(pd.to_datetime(df_anom["date"]).max().strftime("%Y-%m-%d"), "2016-04-24")

    def test_16_no_test_period_data_loaded(self):
        """Verify anomalies_test.parquet is NOT loaded into memory and max date is strictly 2016-04-24."""
        df_anom = registry.df_anomalies
        max_date = pd.to_datetime(df_anom["date"]).max()
        self.assertLessEqual(max_date, pd.to_datetime("2016-04-24"))
        # Ensure registry does not hold any test anomaly attribute
        self.assertFalse(hasattr(registry, "df_anomalies_test"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

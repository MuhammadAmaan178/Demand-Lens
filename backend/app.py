"""
DemandLens Flask Backend — Phase 3: Real Forecast API
Loads all pre-trained LightGBM models and prepared datasets once on startup.
Provides real item catalogue and live multi-horizon forecasting (H7 & H28).

Endpoints:
  - GET  /health (and /api/health) — Service health check
  - GET  /debug/status — Diagnostic report on model and dataset status
  - GET  /items  (and /api/items) — [Phase 3 Real] All 3,049 Store CA_1 items
  - GET  /forecast (and /api/forecast) — [Phase 3 Real] LightGBM H7 & H28 forecast
  - GET  /anomalies (and /api/anomalies) — [Mock Phase 1] Sample anomalies (Phase 4)
  - POST /reorder (and /api/reorder) — [Mock Phase 1] Sample reorder advice (Phase 5)
"""

import logging
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import feature engineering and reorder business modules (logic untouched)
import features
import reorder

# Import DataRegistry for Phase 2 pre-trained models and datasets
from loader import registry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DemandLens.App")

app = Flask(__name__)
CORS(app)

# Load all models and datasets once when the Flask application starts
startup_error = None
try:
    registry.load_all()
    logger.info("DemandLens Phase 2 models and datasets successfully loaded into memory.")
except Exception as err:
    startup_error = str(err)
    logger.error(f"Startup artifact loading failed: {err}")


# =======================================================================
# 1. Health & Diagnostic Endpoints (Phase 2)
# =======================================================================

@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    Reports 200 OK only when models and datasets are fully loaded.
    Reports 503 Service Unavailable if artifact loading has failed.
    """
    if not registry.is_loaded:
        return jsonify({
            "status": "not_ready",
            "service": "DemandLens Backend",
            "version": "1.0.0",
            "error": "Required models or datasets failed to load. See /debug/status for diagnosis."
        }), 503

    return jsonify({
        "status": "ok",
        "service": "DemandLens Backend",
        "version": "1.0.0",
        "artifacts": "loaded"
    }), 200


@app.route("/debug/status", methods=["GET"])
def debug_status():
    """
    Diagnostic status endpoint.
    Reports whether required models, datasets, and feature lists loaded successfully.
    Does NOT expose raw file contents or sensitive host filesystem paths.
    """
    summary = registry.get_status_summary()
    http_code = 200 if summary.get("status") == "ready" else 500
    return jsonify(summary), http_code


# =======================================================================
# Allowed pretend date range (Walmart M5 CA_1 Strict Validation period)
# =======================================================================
VALID_MIN_DATE = "2016-03-28"
VALID_MAX_DATE = "2016-04-24"


# =======================================================================
# 2. Real Store CA_1 Item Catalogue (Phase 3)
# =======================================================================

@app.route("/items", methods=["GET"])
@app.route("/api/items", methods=["GET"])
def get_items():
    """
    Returns the real list of all 3,049 Store CA_1 items with department and sales group.
    Populated directly from item_groups.csv loaded at startup.
    """
    if not registry.is_loaded:
        return jsonify({
            "error": "Backend models and datasets are not ready yet."
        }), 503

    return jsonify({
        "items": registry.items_list,
        "count": len(registry.items_list)
    }), 200


# =======================================================================
# 3. Real Forecast API (Phase 3)
# =======================================================================

@app.route("/forecast", methods=["GET"])
@app.route("/api/forecast", methods=["GET"])
def get_forecast():
    """
    Phase 3 Real Forecast API.
    Runs pre-trained LightGBM H7 and H28 models using features.build_features().
    Strictly protects against data leakage by filtering historical data to date <= today.
    """
    if not registry.is_loaded:
        return jsonify({
            "error": "Backend models and datasets are not ready yet."
        }), 503

    item_id = request.args.get("item_id")
    today = request.args.get("today")

    # 1. Parameter presence validation
    if not item_id:
        return jsonify({"error": "Missing required parameter: item_id"}), 400
    if not today:
        return jsonify({"error": "Missing required parameter: today"}), 400

    # 2. Item ID existence validation
    if item_id not in registry.unique_items_set:
        return jsonify({
            "error": f"Item '{item_id}' not found in Store CA_1 catalogue."
        }), 404

    # 3. Date format validation (YYYY-MM-DD)
    try:
        today_dt = pd.to_datetime(today, format="%Y-%m-%d", errors="raise")
    except Exception:
        return jsonify({
            "error": "Invalid date format for 'today'. Expected YYYY-MM-DD."
        }), 400

    # 4. Pretend date range validation (2016-03-28 to 2016-04-24)
    if today < VALID_MIN_DATE or today > VALID_MAX_DATE:
        return jsonify({
            "error": f"Date 'today' ({today}) is outside allowed validation period ({VALID_MIN_DATE} to {VALID_MAX_DATE})."
        }), 400

    try:
        # 5. Extract item history with strict Data Leakage Protection
        # Only historical records on or before 'today' are accessed
        item_hist = registry.df_history[
            (registry.df_history["item_id"] == item_id) &
            (pd.to_datetime(registry.df_history["date"]) <= today_dt)
        ].copy()

        if item_hist.empty:
            return jsonify({
                "error": f"No historical records found for item '{item_id}' on or before {today}."
            }), 404

        # 6. Construct future forecast dates (strictly day + 1 to day + horizon)
        future_dates_7 = [today_dt + pd.Timedelta(days=i) for i in range(1, 8)]
        future_dates_28 = [today_dt + pd.Timedelta(days=i) for i in range(1, 29)]

        # 7. Generate features and predict with 7-day model
        feat_7 = features.build_features(
            item_hist,
            registry.df_calendar,
            registry.feature_lists,
            horizon=7,
            future_dates=future_dates_7
        )
        cols_7 = registry.feature_lists["features_7"]
        raw_preds_7 = registry.model_h7.predict(feat_7[cols_7])
        preds_7 = np.clip(raw_preds_7, 0, None)

        # 8. Generate features and predict with 28-day model
        feat_28 = features.build_features(
            item_hist,
            registry.df_calendar,
            registry.feature_lists,
            horizon=28,
            future_dates=future_dates_28
        )
        cols_28 = registry.feature_lists["features_28"]
        raw_preds_28 = registry.model_h28.predict(feat_28[cols_28])
        preds_28 = np.clip(raw_preds_28, 0, None)

        # 9. Format historical actual sales (last 14 available days <= today)
        recent_hist = item_hist.sort_values("date").tail(14)
        history_list = [
            {
                "date": pd.to_datetime(row["date"]).strftime("%Y-%m-%d"),
                "sales": int(row["sales"]) if pd.notna(row["sales"]) and float(row["sales"]).is_integer() else round(float(row["sales"]), 1)
            }
            for _, row in recent_hist.iterrows()
        ]

        # 10. Format 7-day forecast
        forecast_7_list = [
            {
                "date": pd.to_datetime(row["date"]).strftime("%Y-%m-%d"),
                "value": round(float(val), 2)
            }
            for (_, row), val in zip(feat_7.iterrows(), preds_7)
        ]

        # 11. Format 28-day forecast
        forecast_28_list = [
            {
                "date": pd.to_datetime(row["date"]).strftime("%Y-%m-%d"),
                "value": round(float(val), 2)
            }
            for (_, row), val in zip(feat_28.iterrows(), preds_28)
        ]

        return jsonify({
            "item_id": item_id,
            "today": today,
            "history": history_list,
            "forecast_7": forecast_7_list,
            "forecast_28": forecast_28_list
        }), 200

    except Exception as e:
        logger.error(f"Error computing forecast for {item_id} at {today}: {e}", exc_info=True)
        return jsonify({
            "error": f"Failed to compute forecast: {str(e)}"
        }), 500


# =======================================================================
# 4. Phase 1 Mock Endpoints (Preserved as labeled DEMO data until Phase 4/5)
# =======================================================================


@app.route("/anomalies", methods=["GET"])
@app.route("/api/anomalies", methods=["GET"])
def get_anomalies():
    """
    [TEMPORARY PHASE 1 MOCK ENDPOINT]
    Returns simulated anomaly events for frontend compatibility.
    Real validation anomaly queries will be connected in Phase 3/4.
    """
    today = request.args.get("today", "2016-05-01")
    item_id = request.args.get("item_id", "")

    anomalies = [
        {
            "item_id": "FOODS_1_001",
            "date": "2016-04-20",
            "sales": 15,
            "forecast": 4.1,
            "direction": "spike",
            "reason": "event",
            "flagged_by": "both"
        },
        {
            "item_id": "FOODS_1_001",
            "date": "2016-04-12",
            "sales": 0,
            "forecast": 3.8,
            "direction": "drop",
            "reason": "unexplained",
            "flagged_by": "rule"
        },
        {
            "item_id": "FOODS_3_795",
            "date": "2016-04-25",
            "sales": 18,
            "forecast": 5.1,
            "direction": "spike",
            "reason": "price change",
            "flagged_by": "both"
        }
    ]

    filtered = [
        a for a in anomalies
        if (not item_id or a["item_id"] == item_id) and a["date"] <= today
    ]

    return jsonify({
        "anomalies": filtered,
        "is_demo_data": True,
        "source": "mock_phase1"
    }), 200


@app.route("/reorder", methods=["POST"])
@app.route("/api/reorder", methods=["POST"])
def get_reorder():
    """
    [TEMPORARY PHASE 1 MOCK ENDPOINT]
    Returns simulated replenishment advice for frontend compatibility.
    The live reorder engine will be integrated in Phase 3/4.
    """
    data = request.get_json() or {}
    item_id = data.get("item_id", "FOODS_1_001")
    today = data.get("today", "2016-05-01")
    current_stock = float(data.get("current_stock", 15))
    lead_time_days = int(data.get("lead_time_days", 5))

    typical_daily = 3.9
    expected_demand = round(typical_daily * lead_time_days, 1)
    safety_stock = 4
    reorder_point = int(expected_demand + safety_stock)
    days_of_stock_left = round(current_stock / typical_daily, 1)
    order_quantity = max(0, int(typical_daily * (lead_time_days + 7) + safety_stock - current_stock))

    risk = "High" if days_of_stock_left < lead_time_days else ("Medium" if days_of_stock_left < lead_time_days + 3 else "Low")
    message = "Order now: stock will run out before delivery." if risk == "High" else "Stock level is adequate."

    return jsonify({
        "item_id": item_id,
        "today": today,
        "days_of_stock_left": days_of_stock_left,
        "expected_demand_in_lead_time": expected_demand,
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "order_quantity": order_quantity,
        "risk": risk,
        "message": message,
        "is_demo_data": True,
        "source": "mock_phase1"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

"""
DemandLens Flask Backend — Phase 2: Model & Data Loading
Loads all pre-trained LightGBM models and prepared datasets once on startup.
Phase 1 mock endpoints are preserved and clearly labeled as demo endpoints
until full live inference and database logic are connected in Phase 3/4.

Endpoints:
  - GET  /health (and /api/health) — Service health, reports 503 if artifacts fail to load
  - GET  /debug/status — Diagnostic report on model and dataset memory status
  - GET  /items  (and /api/items) — [Mock Phase 1] List of items
  - GET  /forecast (and /api/forecast) — [Mock Phase 1] Sample forecast
  - GET  /anomalies (and /api/anomalies) — [Mock Phase 1] Sample anomalies
  - POST /reorder (and /api/reorder) — [Mock Phase 1] Sample reorder advice
"""

import logging
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
# 2. Phase 1 Endpoints (Temporarily preserved as labeled MOCK data)
# NOTE: Real inference and data queries will be implemented in Phase 3/4.
# =======================================================================

@app.route("/items", methods=["GET"])
@app.route("/api/items", methods=["GET"])
def get_items():
    """
    [TEMPORARY PHASE 1 MOCK ENDPOINT]
    Returns static sample items for frontend compatibility until Phase 3/4.
    """
    items = [
        {"item_id": "FOODS_1_001", "department": "FOODS_1", "group": "fast sellers"},
        {"item_id": "FOODS_3_795", "department": "FOODS_3", "group": "steady sellers"},
        {"item_id": "FOODS_2_180", "department": "FOODS_2", "group": "slow sellers"},
        {"item_id": "HOBBIES_1_001", "department": "HOBBIES_1", "group": "erratic sellers"},
        {"item_id": "HOBBIES_1_234", "department": "HOBBIES_1", "group": "fast sellers"},
        {"item_id": "HOUSEHOLD_1_001", "department": "HOUSEHOLD_1", "group": "steady sellers"},
        {"item_id": "HOUSEHOLD_2_045", "department": "HOUSEHOLD_2", "group": "slow sellers"},
    ]
    return jsonify({
        "items": items,
        "is_demo_data": True,
        "source": "mock_phase1"
    }), 200


@app.route("/forecast", methods=["GET"])
@app.route("/api/forecast", methods=["GET"])
def get_forecast():
    """
    [TEMPORARY PHASE 1 MOCK ENDPOINT]
    Returns simulated forecast data for frontend compatibility.
    Real LightGBM model inference will be connected in Phase 3/4.
    """
    item_id = request.args.get("item_id", "FOODS_1_001")
    today = request.args.get("today", "2016-05-01")

    history = [
        {"date": "2016-04-28", "sales": 3},
        {"date": "2016-04-29", "sales": 5},
        {"date": "2016-04-30", "sales": 4},
        {"date": "2016-05-01", "sales": 6},
    ]

    forecast_7 = [
        {"date": "2016-05-02", "value": 3.8},
        {"date": "2016-05-03", "value": 4.1},
        {"date": "2016-05-04", "value": 3.9},
        {"date": "2016-05-05", "value": 4.5},
        {"date": "2016-05-06", "value": 5.0},
        {"date": "2016-05-07", "value": 5.2},
        {"date": "2016-05-08", "value": 4.7},
    ]

    forecast_28 = [
        {"date": "2016-05-02", "value": 3.5},
        {"date": "2016-05-03", "value": 3.7},
        {"date": "2016-05-04", "value": 3.6},
        {"date": "2016-05-05", "value": 4.0},
        {"date": "2016-05-06", "value": 4.6},
        {"date": "2016-05-07", "value": 4.8},
        {"date": "2016-05-08", "value": 4.4},
    ]

    return jsonify({
        "item_id": item_id,
        "today": today,
        "history": history,
        "forecast_7": forecast_7,
        "forecast_28": forecast_28,
        "is_demo_data": True,
        "source": "mock_phase1"
    }), 200


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

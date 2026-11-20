"""
DemandLens Flask Backend — Phase 1 Skeleton
Provides the agreed REST API routes for DemandLens Store CA_1.
Endpoints:
  - GET  /health (and /api/health)
  - GET  /items  (and /api/items)
  - GET  /forecast (and /api/forecast)
  - GET  /anomalies (and /api/anomalies)
  - POST /reorder (and /api/reorder)
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS so the React frontend on any port can communicate with the backend
CORS(app)


# --- 1. Health Check Endpoint ---
@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "DemandLens Backend", "version": "1.0.0"}), 200


# --- 2. Items List Endpoint ---
@app.route("/items", methods=["GET"])
@app.route("/api/items", methods=["GET"])
def get_items():
    items = [
        {"item_id": "FOODS_1_001", "department": "FOODS_1", "group": "fast sellers"},
        {"item_id": "FOODS_3_795", "department": "FOODS_3", "group": "steady sellers"},
        {"item_id": "FOODS_2_180", "department": "FOODS_2", "group": "slow sellers"},
        {"item_id": "HOBBIES_1_001", "department": "HOBBIES_1", "group": "erratic sellers"},
        {"item_id": "HOBBIES_1_234", "department": "HOBBIES_1", "group": "fast sellers"},
        {"item_id": "HOUSEHOLD_1_001", "department": "HOUSEHOLD_1", "group": "steady sellers"},
        {"item_id": "HOUSEHOLD_2_045", "department": "HOUSEHOLD_2", "group": "slow sellers"},
    ]
    return jsonify({"items": items}), 200


# --- 3. Forecast Endpoint ---
@app.route("/forecast", methods=["GET"])
@app.route("/api/forecast", methods=["GET"])
def get_forecast():
    item_id = request.args.get("item_id", "FOODS_1_001")
    today = request.args.get("today", "2016-05-01")

    # Sample response matching Part 8 of DemandLens_Remaining_Work_Guide.pdf
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
        "forecast_28": forecast_28
    }), 200


# --- 4. Anomalies Endpoint ---
@app.route("/anomalies", methods=["GET"])
@app.route("/api/anomalies", methods=["GET"])
def get_anomalies():
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

    # Filter by item_id if specified, and date <= today
    filtered = [
        a for a in anomalies
        if (not item_id or a["item_id"] == item_id) and a["date"] <= today
    ]

    return jsonify({"anomalies": filtered}), 200


# --- 5. Reorder Advice Endpoint ---
@app.route("/reorder", methods=["POST"])
@app.route("/api/reorder", methods=["POST"])
def get_reorder():
    data = request.get_json() or {}
    item_id = data.get("item_id", "FOODS_1_001")
    today = data.get("today", "2016-05-01")
    current_stock = float(data.get("current_stock", 15))
    lead_time_days = int(data.get("lead_time_days", 5))

    # Reorder formulas from Task B (Notebook 09)
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
        "message": message
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

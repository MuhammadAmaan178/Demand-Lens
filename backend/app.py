"""
DemandLens Flask Backend — Phase 5: Real Inventory & Reorder Intelligence API
Loads all pre-trained LightGBM models and prepared datasets once on startup.
Provides real item catalogue, live multi-horizon forecasting (H7 & H28),
real historical anomaly detection queries (H7 validation),
and live inventory replenishment & reorder advice engine.

Endpoints:
  - GET  /health (and /api/health) — Service health check
  - GET  /debug/status — Diagnostic report on model and dataset status
  - GET  /items  (and /api/items) — [Phase 3 Real] All 3,049 Store CA_1 items
  - GET  /forecast (and /api/forecast) — [Phase 3 Real] LightGBM H7 & H28 forecast
  - GET  /anomalies (and /api/anomalies) — [Phase 4 Real] H7 validation anomaly events
  - POST /reorder (and /api/reorder) — [Phase 5 Real] Live inventory reorder engine
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
# 1. Root, Health & Diagnostic Endpoints (Phase 2)
# =======================================================================

@app.route("/", methods=["GET"])
def root():
    """
    Root entry point.
    Returns basic service status and links to the health endpoint.
    """
    return jsonify({
        "service": "DemandLens Backend",
        "status": "running",
        "message": "DemandLens API is running. Visit /api/health to check backend readiness.",
        "health_endpoint": "/api/health"
    }), 200


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
# 4. Real Anomaly Detection API (Phase 4)
# =======================================================================

@app.route("/anomalies", methods=["GET"])
@app.route("/api/anomalies", methods=["GET"])
def get_anomalies():
    """
    Phase 4 Real Anomaly Detection API.
    Queries pre-computed H7 validation anomalies from anomalies_validation.parquet.
    Filters records up to and including 'today' (strictly no future leakage).
    Supports optional 'item_id' filter.
    Returns clear 400 Bad Request for invalid/out-of-range dates or unknown item IDs.
    """
    if not registry.is_loaded:
        return jsonify({
            "error": "Backend models and datasets are not ready yet."
        }), 503

    today = request.args.get("today")
    item_id = request.args.get("item_id", "").strip()

    # 1. Parameter presence validation for 'today'
    if not today:
        return jsonify({"error": "Missing required parameter: today"}), 400

    # 2. Date format validation (YYYY-MM-DD)
    try:
        today_dt = pd.to_datetime(today, format="%Y-%m-%d", errors="raise")
    except Exception:
        return jsonify({
            "error": "Invalid date format for 'today'. Expected YYYY-MM-DD."
        }), 400

    # 3. Allowed validation date range (2016-03-28 to 2016-04-24)
    if today < VALID_MIN_DATE or today > VALID_MAX_DATE:
        return jsonify({
            "error": f"Date 'today' ({today}) is outside allowed validation period ({VALID_MIN_DATE} to {VALID_MAX_DATE})."
        }), 400

    # 4. Item ID validation if provided
    if item_id and item_id not in registry.unique_items_set:
        return jsonify({
            "error": f"Item '{item_id}' not found in Store CA_1 catalogue."
        }), 400

    try:
        # Filter pre-loaded flagged anomalies on or before today
        df = registry.df_flagged_anomalies
        mask = df["date_dt"] <= today_dt
        if item_id:
            mask = mask & (df["item_id"] == item_id)

        filtered = df[mask].sort_values(by=["date", "item_id"]).copy()

        # Flag mapping dictionary to align with frontend filter options
        flag_map = {
            "rule_1": "rule",
            "isolation_forest": "isolation",
            "both": "both"
        }

        anomalies_list = []
        for _, row in filtered.iterrows():
            direction = str(row["direction"])
            # If direction was normal in isolation forest outlier, assign spike/drop by residual
            if direction == "normal":
                direction = "spike" if float(row["sales"]) >= float(row["forecast"]) else "drop"

            anomalies_list.append({
                "item_id": str(row["item_id"]),
                "date": pd.to_datetime(row["date"]).strftime("%Y-%m-%d"),
                "sales": int(row["sales"]),
                "forecast": round(float(row["forecast"]), 2),
                "residual": round(float(row["residual"]), 2),
                "direction": direction,
                "group": str(row["group"]),
                "is_anomaly": bool(row["is_anomaly"]),
                "flagged_by": flag_map.get(str(row["flagged_by"]), str(row["flagged_by"])),
                "reason": str(row["reason"])
            })

        # Summary statistics matching returned records
        summary = {
            "total": len(anomalies_list),
            "spikes": sum(1 for a in anomalies_list if a["direction"] == "spike"),
            "drops": sum(1 for a in anomalies_list if a["direction"] == "drop"),
            "by_reason": {
                "price_change": sum(1 for a in anomalies_list if a["reason"] == "price change"),
                "event": sum(1 for a in anomalies_list if "event" in a["reason"].lower()),
                "snap_day": sum(1 for a in anomalies_list if "snap" in a["reason"].lower()),
                "unexplained": sum(1 for a in anomalies_list if "unexplained" in a["reason"].lower()),
            },
            "by_flag": {
                "rule": sum(1 for a in anomalies_list if a["flagged_by"] == "rule"),
                "isolation": sum(1 for a in anomalies_list if a["flagged_by"] == "isolation"),
                "both": sum(1 for a in anomalies_list if a["flagged_by"] == "both"),
            }
        }

        return jsonify({
            "today": today,
            "item_id": item_id if item_id else None,
            "anomalies": anomalies_list,
            "count": len(anomalies_list),
            "summary": summary
        }), 200

    except Exception as e:
        logger.error(f"Error querying anomalies for today={today}, item={item_id}: {e}", exc_info=True)
        return jsonify({
            "error": f"Failed to query anomalies: {str(e)}"
        }), 500


# =======================================================================
# 5. Real Inventory & Reorder Intelligence API (Phase 5)
# =======================================================================


def compute_item_forecast(item_id, today_dt, horizon=7):
    """
    Computes real LightGBM forecasts for a single item for a given horizon (7 or 28 days).
    Strictly protects against data leakage by slicing history <= today_dt.
    Returns DataFrame with columns ['item_id', 'date', 'forecast'].
    """
    item_hist = registry.df_history[
        (registry.df_history["item_id"] == item_id) &
        (pd.to_datetime(registry.df_history["date"]) <= today_dt)
    ].copy()

    if item_hist.empty:
        raise ValueError(f"No historical records found for item '{item_id}' on or before {today_dt.strftime('%Y-%m-%d')}.")

    future_dates = [today_dt + pd.Timedelta(days=i) for i in range(1, horizon + 1)]
    feat_df = features.build_features(
        item_hist,
        registry.df_calendar,
        registry.feature_lists,
        horizon=horizon,
        future_dates=future_dates
    )
    cols = registry.feature_lists[f"features_{horizon}"]
    model = registry.model_h7 if horizon == 7 else registry.model_h28
    raw_preds = model.predict(feat_df[cols])
    preds = np.clip(raw_preds, 0, None)

    return pd.DataFrame({
        "item_id": item_id,
        "date": feat_df["date"],
        "forecast": preds
    })


@app.route("/reorder", methods=["POST"])
@app.route("/api/reorder", methods=["POST"])
def get_reorder():
    """
    [Phase 5 Real Endpoint]
    Calculates live inventory replenishment & reorder advice for a single item.
    Enforces strict input validation, horizon-appropriate model selection (H7 for lead_time <= 7,
    H28 for lead_time > 7), error-spread variance safety buffers, and risk classification.
    """
    # 1. Readiness check
    if not registry.is_loaded:
        return jsonify({
            "status": "not_ready",
            "error": "Backend models and datasets are not yet loaded. Please check /health."
        }), 503

    # 2. JSON payload validation
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a valid JSON object."
        }), 400

    # 3. Item ID validation
    item_id = data.get("item_id")
    if not item_id or not isinstance(item_id, str) or not item_id.strip():
        return jsonify({
            "error": "Field 'item_id' is required and must be a non-empty string."
        }), 400

    item_id = item_id.strip()
    if item_id not in registry.unique_items_set:
        return jsonify({
            "error": f"Item '{item_id}' not found in Store CA_1 catalogue. Check /items for valid IDs."
        }), 400

    # 4. Date validation (YYYY-MM-DD within allowed validation range)
    today = data.get("today")
    if not today or not isinstance(today, str):
        return jsonify({
            "error": "Field 'today' is required and must be a valid date string (YYYY-MM-DD)."
        }), 400

    try:
        today_dt = pd.to_datetime(today, format="%Y-%m-%d", errors="raise")
    except Exception:
        return jsonify({
            "error": "Invalid date format for 'today'. Expected YYYY-MM-DD."
        }), 400

    if today < VALID_MIN_DATE or today > VALID_MAX_DATE:
        return jsonify({
            "error": f"Date 'today' ({today}) is outside allowed validation period ({VALID_MIN_DATE} to {VALID_MAX_DATE})."
        }), 400

    # 5. Current stock validation (integer >= 0)
    if "current_stock" not in data or data["current_stock"] is None:
        return jsonify({
            "error": "Field 'current_stock' is required."
        }), 400

    stock_val = data["current_stock"]
    if isinstance(stock_val, bool):
        return jsonify({
            "error": "Field 'current_stock' must be a non-negative integer (>= 0)."
        }), 400

    try:
        stock_float = float(stock_val)
        if not stock_float.is_integer() or stock_float < 0:
            return jsonify({
                "error": "Field 'current_stock' must be a non-negative integer (>= 0)."
            }), 400
        current_stock = int(stock_float)
    except (ValueError, TypeError):
        return jsonify({
            "error": "Field 'current_stock' must be a valid non-negative integer."
        }), 400

    # 6. Lead time validation (integer between 1 and 28)
    if "lead_time_days" not in data or data["lead_time_days"] is None:
        return jsonify({
            "error": "Field 'lead_time_days' is required."
        }), 400

    lt_val = data["lead_time_days"]
    if isinstance(lt_val, bool):
        return jsonify({
            "error": "Field 'lead_time_days' must be an integer between 1 and 28."
        }), 400

    try:
        lt_float = float(lt_val)
        if not lt_float.is_integer() or int(lt_float) < 1 or int(lt_float) > 28:
            return jsonify({
                "error": "Field 'lead_time_days' must be an integer between 1 and 28."
            }), 400
        lead_time_days = int(lt_float)
    except (ValueError, TypeError):
        return jsonify({
            "error": "Field 'lead_time_days' must be a valid integer between 1 and 28."
        }), 400

    # 7. Model selection and live inference
    try:
        if lead_time_days <= 7:
            h7_preds_df = compute_item_forecast(item_id, today_dt, horizon=7)
            h28_preds_df = pd.DataFrame(columns=["item_id", "date", "forecast"])
        else:
            h7_preds_df = pd.DataFrame(columns=["item_id", "date", "forecast"])
            h28_preds_df = compute_item_forecast(item_id, today_dt, horizon=28)

        # 8. Compute reorder advice using validated engine
        advice = reorder.reorder_advice(
            item_id=item_id,
            current_stock=current_stock,
            lead_time_days=lead_time_days,
            h7_preds_df=h7_preds_df,
            h28_preds_df=h28_preds_df,
            error_spread_df=registry.df_item_error_spread,
            review_days=7
        )

        # 9. Format response for frontend compatibility
        advice["today"] = today
        if advice["risk"] == "High":
            advice["message"] = "Order now: stock will run out before delivery."
        elif advice["risk"] == "Medium":
            advice["message"] = "Stock is running low: plan replenishment soon."
        else:
            advice["message"] = "Stock level is adequate."

        return jsonify(advice), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error computing reorder advice for {item_id} at {today}: {e}", exc_info=True)
        return jsonify({
            "error": f"Failed to compute reorder advice: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

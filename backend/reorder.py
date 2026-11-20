"""
DemandLens — Inventory & Reorder Intelligence Module (Store CA_1)
Generated and verified in Notebook 09.
"""

import math
import numpy as np


def reorder_advice(
    item_id,
    current_stock,
    lead_time_days,
    h7_preds_df,
    h28_preds_df,
    error_spread_df,
    review_days=7
):
    """
    Calculates inventory and reorder intelligence for a single item.
    """

    # --- Input Validation ---
    if not isinstance(item_id, str) or not item_id.strip():
        raise ValueError("Invalid item_id: must be a non-empty string.")

    if current_stock is None or current_stock < 0:
        raise ValueError(
            f"Invalid current_stock ({current_stock}): must be >= 0."
        )

    if lead_time_days is None or lead_time_days <= 0:
        raise ValueError(
            f"Invalid lead_time_days ({lead_time_days}): must be > 0."
        )

    # 1. Select H7 or H28 forecast
    if lead_time_days <= 7:
        forecast_source = "H7"
        item_forecasts = h7_preds_df[
            h7_preds_df["item_id"] == item_id
        ].sort_values("date")
    else:
        forecast_source = "H28"
        item_forecasts = h28_preds_df[
            h28_preds_df["item_id"] == item_id
        ].sort_values("date")

    if len(item_forecasts) == 0:
        raise ValueError(
            f"Invalid item_id: '{item_id}' not found in {forecast_source} forecast data."
        )

    daily_forecasts = item_forecasts["forecast"].values

    # 2. Expected demand in lead time
    lead_time_slice = daily_forecasts[:lead_time_days]

    expected_demand_lead_time = float(np.sum(lead_time_slice))
    avg_daily_forecast = float(np.mean(lead_time_slice))

    # 3. Get item error information
    item_error_row = error_spread_df[
        error_spread_df["item_id"] == item_id
    ]

    if len(item_error_row) == 0:
        raise ValueError(
            f"Invalid item_id: '{item_id}' not found in item_error_spread."
        )

    typical_daily_error = float(
        item_error_row["typical_daily_error"].values[0]
    )

    item_group = str(item_error_row["group"].values[0])

    # 4. Calculate safety stock
    safety_stock = (
        1.65 * typical_daily_error * math.sqrt(lead_time_days)
    )

    # 5. Calculate reorder point
    reorder_point = expected_demand_lead_time + safety_stock

    # 6. Calculate days of stock left
    if avg_daily_forecast > 0:
        days_of_stock_left = current_stock / avg_daily_forecast
    else:
        days_of_stock_left = 999.0 if current_stock > 0 else 0.0

    # 7. Calculate order quantity
    total_window_days = lead_time_days + review_days

    if len(daily_forecasts) >= total_window_days:
        expected_demand_window = float(
            np.sum(daily_forecasts[:total_window_days])
        )
    else:
        missing_days = total_window_days - len(daily_forecasts)

        expected_demand_window = (
            float(np.sum(daily_forecasts))
            + missing_days * avg_daily_forecast
        )

    raw_order_qty = (
        expected_demand_window + safety_stock - current_stock
    )

    order_quantity = max(0, math.ceil(raw_order_qty))

    # 8. Risk classification
    if days_of_stock_left < lead_time_days:
        risk = "High"
    elif days_of_stock_left < (lead_time_days + 3):
        risk = "Medium"
    else:
        risk = "Low"

    return {
        "item_id": item_id,
        "group": item_group,
        "forecast_model_used": forecast_source,
        "current_stock": current_stock,
        "lead_time_days": lead_time_days,
        "average_daily_forecast": round(avg_daily_forecast, 2),
        "expected_demand_in_lead_time": round(expected_demand_lead_time, 2),
        "typical_daily_error": round(typical_daily_error, 2),
        "safety_stock": round(safety_stock, 2),
        "reorder_point": round(reorder_point, 2),
        "days_of_stock_left": round(days_of_stock_left, 1),
        "order_quantity": int(order_quantity),
        "risk": risk
    }


# Backward-compatible alias
calculate_reorder_plan = reorder_advice

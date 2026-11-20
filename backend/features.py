"""
DemandLens — Feature Engineering Module (Store CA_1)
Reproduces exact Notebook 03 feature engineering for H7 and H28 LightGBM models.
"""

import numpy as np
import pandas as pd


EVENT_TYPES = ["Cultural", "National", "Religious", "Sporting", "None"]
DEPARTMENTS = [
    "FOODS_1", "FOODS_2", "FOODS_3",
    "HOBBIES_1", "HOBBIES_2",
    "HOUSEHOLD_1", "HOUSEHOLD_2"
]


def build_features(history_df, calendar_df, feature_lists, horizon=7, future_dates=None):
    """
    Builds the exact 27-column feature matrix required by LightGBM (H7 or H28).
    """
    if horizon not in (7, 28):
        raise ValueError("horizon must be 7 or 28.")

    df = history_df[["item_id", "dept_id", "date", "sales", "sell_price"]].copy()

    # Convert item_id to plain string during grouping so unused categories are never created
    df["item_id"] = df["item_id"].astype(str)
    df["date"] = pd.to_datetime(df["date"])

    # If future_dates are requested, append skeleton rows with sales=NaN and last known price
    if future_dates is not None and len(future_dates) > 0:
        future_dates = pd.to_datetime(future_dates)
        last_rows = (
            df.sort_values(["item_id", "date"])
            .groupby("item_id", as_index=False)
            .last()[["item_id", "dept_id", "sell_price"]]
        )
        future_frames = []
        for fdate in future_dates:
            temp = last_rows.copy()
            temp["date"] = fdate
            temp["sales"] = np.nan  # Never use future actual sales
            future_frames.append(temp)
        df = pd.concat([df] + future_frames, ignore_index=True)

    # Sort chronologically per item before computing lags and rolling means
    df = df.sort_values(["item_id", "date"]).reset_index(drop=True)

    # 1. Lag and rolling mean features (strictly shifted by 'horizon' days)
    grouped_sales = df.groupby("item_id", sort=False)["sales"]
    if horizon == 7:
        df["lag_7"] = grouped_sales.shift(7)
        df["rolling_mean_7"] = grouped_sales.transform(lambda s: s.shift(7).rolling(7).mean())
        expected_cols = feature_lists["features_7"]
    else:
        df["lag_28"] = grouped_sales.shift(28)
        df["rolling_mean_28"] = grouped_sales.transform(lambda s: s.shift(28).rolling(28).mean())
        expected_cols = feature_lists["features_28"]

    # 2. Weekly price change (sell_price minus sell_price 7 days ago)
    df["price_change"] = df.groupby("item_id", sort=False)["sell_price"].transform(
        lambda s: s - s.shift(7)
    ).fillna(0.0)

    # 3. Merge calendar features (wday, month, year, event_type_1, snap_CA)
    cal = calendar_df[["date", "wday", "month", "year", "event_type_1", "snap_CA"]].copy()
    cal["date"] = pd.to_datetime(cal["date"])
    df = df.merge(cal, on="date", how="left")

    # Rename snap_CA -> snap to match model feature name
    df["snap"] = df["snap_CA"].fillna(0).astype(int)

    # Weekend flag (in M5, wday 1 = Saturday, 2 = Sunday)
    df["is_weekend"] = df["wday"].isin([1, 2]).astype(int)

    # Event flags and one-hot columns
    df["has_event"] = df["event_type_1"].notna().astype(int)
    event_clean = df["event_type_1"].fillna("None")
    for ev in EVENT_TYPES:
        df[f"ev_{ev}"] = (event_clean == ev).astype(int)

    # 4. Department one-hot columns
    for dept in DEPARTMENTS:
        df[f"dept_{dept}"] = (df["dept_id"] == dept).astype(int)

    # 5. Cyclical time features
    df["wday_sin"] = np.sin(2 * np.pi * df["wday"] / 7)
    df["wday_cos"] = np.cos(2 * np.pi * df["wday"] / 7)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # 6. Set item_id to exact categorical list from feature_lists.json
    df["item_id"] = pd.Categorical(
        df["item_id"],
        categories=feature_lists["item_categories"]
    )

    # If future_dates were requested, return only those future rows
    if future_dates is not None and len(future_dates) > 0:
        df = df[df["date"].isin(future_dates)].copy()

    # Keep date alongside the exact ordered feature columns for easy tracking
    return df[["date"] + expected_cols].reset_index(drop=True)

// =======================================================================
// DEMO MOCK DATA FOR DEMANDLENS (Store CA_1)
// Used when the Flask backend is not yet running or during initial testing.
// NOTE: These values are strictly DEMO DATA and not real model predictions.
// =======================================================================

// List of demo items matching the GET /items contract in the guide
export const mockItems = [
  { item_id: "FOODS_1_001", department: "FOODS_1", group: "fast sellers" },
  { item_id: "FOODS_3_795", department: "FOODS_3", group: "steady sellers" },
  { item_id: "FOODS_2_180", department: "FOODS_2", group: "slow sellers" },
  { item_id: "HOBBIES_1_001", department: "HOBBIES_1", group: "erratic sellers" },
  { item_id: "HOBBIES_1_234", department: "HOBBIES_1", group: "fast sellers" },
  { item_id: "HOUSEHOLD_1_001", department: "HOUSEHOLD_1", group: "steady sellers" },
  { item_id: "HOUSEHOLD_2_045", department: "HOUSEHOLD_2", group: "slow sellers" }
];

// Generates a mock forecast matching GET /forecast?item_id=...&today=...
export function getMockForecast(itemId = "FOODS_1_001", today = "2016-05-01") {
  const baseDate = new Date(today);
  const baseSales = itemId.startsWith("FOODS_1") ? 4.2 : itemId.startsWith("FOODS_3") ? 5.5 : 3.0;

  // 1. History: 14 days before today (real past sales)
  const history = [];
  for (let i = 14; i >= 1; i--) {
    const d = new Date(baseDate);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split("T")[0];
    const noise = Math.sin(i * 1.7) * 2;
    const sales = Math.max(0, Math.round(baseSales + noise));
    history.push({ date: dateStr, sales });
  }

  // 2. Forecast 7-day model (future predictions starting today)
  const forecast_7 = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(baseDate);
    d.setDate(d.getDate() + i);
    const dateStr = d.toISOString().split("T")[0];
    const trend = Math.cos(i * 0.9) * 1.1;
    const value = Math.max(0.5, Number((baseSales + trend).toFixed(1)));
    forecast_7.push({ date: dateStr, value });
  }

  // 3. Forecast 28-day model (future predictions for 28 days)
  const forecast_28 = [];
  for (let i = 0; i < 28; i++) {
    const d = new Date(baseDate);
    d.setDate(d.getDate() + i);
    const dateStr = d.toISOString().split("T")[0];
    const trend = Math.cos(i * 0.4) * 1.4;
    const value = Math.max(0.4, Number((baseSales - 0.2 + trend).toFixed(1)));
    forecast_28.push({ date: dateStr, value });
  }

  return {
    item_id: itemId,
    today: today,
    history,
    forecast_7,
    forecast_28,
    is_demo_data: true
  };
}

// Generates mock anomalies matching GET /anomalies?today=...&item_id=...
export function getMockAnomalies(today = "2016-05-01", itemId = "") {
  const allAnomalies = [
    {
      item_id: "FOODS_1_001",
      date: "2016-04-20",
      sales: 15,
      forecast: 4.1,
      direction: "spike",
      reason: "event",
      flagged_by: "both"
    },
    {
      item_id: "FOODS_1_001",
      date: "2016-04-12",
      sales: 0,
      forecast: 3.8,
      direction: "drop",
      reason: "unexplained",
      flagged_by: "rule"
    },
    {
      item_id: "FOODS_1_001",
      date: "2016-04-05",
      sales: 12,
      forecast: 4.0,
      direction: "spike",
      reason: "SNAP day",
      flagged_by: "isolation"
    },
    {
      item_id: "FOODS_3_795",
      date: "2016-04-25",
      sales: 18,
      forecast: 5.1,
      direction: "spike",
      reason: "price change",
      flagged_by: "both"
    },
    {
      item_id: "FOODS_3_795",
      date: "2016-04-18",
      sales: 1,
      forecast: 5.4,
      direction: "drop",
      reason: "unexplained",
      flagged_by: "rule"
    },
    {
      item_id: "HOBBIES_1_234",
      date: "2016-04-22",
      sales: 14,
      forecast: 3.2,
      direction: "spike",
      reason: "event",
      flagged_by: "both"
    }
  ];

  // Only return anomalies on or before the selected 'today' date
  const filtered = allAnomalies.filter((row) => {
    const isPast = row.date <= today;
    const matchesItem = !itemId || row.item_id === itemId;
    return isPast && matchesItem;
  });

  return {
    anomalies: filtered,
    is_demo_data: true
  };
}

// Generates mock reorder advice matching POST /reorder
export function getMockReorderAdvice(payload) {
  const currentStock = Number(payload.current_stock) || 0;
  const leadTimeDays = Number(payload.lead_time_days) || 1;

  // Mock math formulas from Section 4 of guide
  const typicalDailyDemand = 3.9;
  const expectedDemandInLeadTime = Number((typicalDailyDemand * leadTimeDays).toFixed(1));
  const typicalDailyError = 1.2;
  const safetyStock = Math.round(1.65 * typicalDailyError * Math.sqrt(leadTimeDays));
  const reorderPoint = Math.round(expectedDemandInLeadTime + safetyStock);
  const daysOfStockLeft = Number((currentStock / typicalDailyDemand).toFixed(1));

  // Review days = 7
  const reviewDays = 7;
  const expectedDuringProtection = typicalDailyDemand * (leadTimeDays + reviewDays);
  const rawOrderQty = expectedDuringProtection + safetyStock - currentStock;
  const orderQuantity = Math.max(0, Math.ceil(rawOrderQty));

  // Determine risk label
  let risk = "Low";
  let message = "Stock levels are healthy. No immediate order required.";

  if (daysOfStockLeft < leadTimeDays) {
    risk = "High";
    message = `Order now: stock will run out in ${daysOfStockLeft} days, before delivery in ${leadTimeDays} days.`;
  } else if (daysOfStockLeft < leadTimeDays + 3) {
    risk = "Medium";
    message = `Order soon: stock will run low shortly after the ${leadTimeDays}-day lead time.`;
  }

  return {
    days_of_stock_left: daysOfStockLeft,
    expected_demand_in_lead_time: expectedDemandInLeadTime,
    safety_stock: safetyStock,
    reorder_point: reorderPoint,
    order_quantity: orderQuantity,
    risk: risk,
    message: message,
    is_demo_data: true
  };
}

import React, { useState, useEffect } from 'react';
import { TrendingUp, Calendar, AlertCircle, Info, Sparkles, RefreshCw } from 'lucide-react';
import { getForecast } from '../services/api.js';
import { ForecastChart } from '../components/ForecastChart.jsx';

export function Forecast({ selectedItemId, today }) {
  // Local horizon selection: 7 days vs 28 days
  const [horizon, setHorizon] = useState(7);
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load forecast whenever selected item or pretend today changes
  async function loadData() {
    if (!selectedItemId || !today) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getForecast(selectedItemId, today);
      setForecastData(data);
    } catch (err) {
      console.error('Forecast load error:', err);
      setError(err.message || 'Unable to load forecast from backend.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [selectedItemId, today]);

  // Determine active forecast series based on the chosen horizon
  const activeForecast = horizon === 7
    ? (forecastData?.forecast_7 || [])
    : (forecastData?.forecast_28 || []);

  // Compute summary metrics: total sales and busiest forecast day
  const totalExpectedSales = activeForecast.reduce((sum, item) => sum + (item.value || 0), 0);
  
  let busiestDay = { date: '—', value: 0 };
  if (activeForecast.length > 0) {
    busiestDay = activeForecast.reduce((max, curr) => (curr.value > max.value ? curr : max), activeForecast[0]);
  }

  return (
    <div className="space-y-6">
      {/* Top Banner if using Mock/Demo Data */}
      {forecastData?.is_demo_data && (
        <div className="bg-amber-50 border border-amber-300 rounded p-3 text-xs text-amber-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>
              <strong>DEMO DATA:</strong> The Flask backend is offline. Displaying simulated forecast responses for evaluation.
            </span>
          </div>
          <button
            onClick={loadData}
            className="text-xs font-semibold text-amber-900 underline hover:no-underline"
          >
            Retry API
          </button>
        </div>
      )}

      {/* Page Title & Horizon Switch */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Demand Forecasting
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Compare past actual sales with future predicted demand for Item <strong className="text-slate-800">{selectedItemId}</strong> starting from pretend date <strong className="text-slate-800">{today}</strong>.
          </p>
        </div>

        {/* 7 Days / 28 Days Switch inside the Forecast Page */}
        <div className="flex items-center self-start sm:self-auto bg-slate-100 p-1 rounded border border-slate-200 text-xs">
          <span className="text-[11px] font-semibold text-slate-400 px-2 uppercase">Horizon:</span>
          <button
            type="button"
            onClick={() => setHorizon(7)}
            className={`px-3 py-1.5 rounded font-medium transition-colors ${
              horizon === 7
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            7 Days
          </button>
          <button
            type="button"
            onClick={() => setHorizon(28)}
            className={`px-3 py-1.5 rounded font-medium transition-colors ${
              horizon === 28
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            28 Days
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-white border border-slate-200 rounded p-12 text-center text-slate-600">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" />
          <p className="text-sm font-medium">Loading demand forecast...</p>
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div className="bg-white border border-rose-200 rounded p-8 text-center">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-slate-900">Failed to load forecast</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">{error}</p>
          <button
            onClick={loadData}
            className="mt-4 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Successful Content */}
      {!loading && !error && forecastData && (
        <>
          {/* Small Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-white border border-slate-200 rounded p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Expected Total Sales ({horizon}d)
              </span>
              <div className="text-2xl font-bold text-slate-900 mt-1">
                {totalExpectedSales.toFixed(1)} <span className="text-xs font-normal text-slate-500">units</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Avg {(totalExpectedSales / horizon).toFixed(1)} units/day
              </p>
            </div>

            <div className="bg-white border border-slate-200 rounded p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Busiest Forecast Day
              </span>
              <div className="text-2xl font-bold text-blue-600 mt-1">
                {busiestDay.date}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Peak expected demand: <strong className="text-slate-800">{busiestDay.value}</strong> units
              </p>
            </div>

            <div className="bg-white border border-slate-200 rounded p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Historical Context
              </span>
              <div className="text-2xl font-bold text-slate-900 mt-1">
                {forecastData.history?.length || 0} <span className="text-xs font-normal text-slate-500">days</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Actual sales up to pretend today
              </p>
            </div>
          </div>

          {/* Line Chart Card */}
          <div className="bg-white border border-slate-200 rounded p-5 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Sales History & {horizon}-Day Forecast
                </h2>
                <p className="text-xs text-slate-500">
                  Solid navy line represents real past sales; dashed blue line shows model predictions.
                </p>
              </div>
            </div>

            <ForecastChart
              history={forecastData.history || []}
              forecast={activeForecast}
            />

            {/* Note required by the guide */}
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-start gap-2 text-xs text-slate-500">
              <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
              <span>
                <strong>Note:</strong> The 28-day forecast uses older lag information, so it is generally less accurate than the 7-day forecast.
              </span>
            </div>
          </div>

          {/* Table with forecast values by date */}
          <div className="bg-white border border-slate-200 rounded shadow-xs overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-200 bg-slate-50">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Detailed Forecast Table ({horizon} Days)
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50/50 text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-2 font-semibold">Forecast Date</th>
                    <th className="px-4 py-2 font-semibold">Predicted Units</th>
                    <th className="px-4 py-2 font-semibold">Day Offset</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activeForecast.map((row, idx) => (
                    <tr key={row.date} className="hover:bg-slate-50">
                      <td className="px-4 py-2 font-medium text-slate-800">{row.date}</td>
                      <td className="px-4 py-2 font-bold text-blue-600">{row.value}</td>
                      <td className="px-4 py-2 text-slate-500">Day +{idx + 1}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

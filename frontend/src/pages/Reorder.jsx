import React, { useState } from 'react';
import { PackageCheck, ArrowRight, AlertTriangle, ShieldCheck, Clock, Sparkles } from 'lucide-react';
import { getReorderAdvice } from '../services/api.js';

export function Reorder({ selectedItemId, today }) {
  // Form input state
  const [currentStock, setCurrentStock] = useState('15');
  const [leadTimeDays, setLeadTimeDays] = useState('5');
  const [inputError, setInputError] = useState('');

  // Result state
  const [adviceResult, setAdviceResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);

  // Form submission handler
  async function handleSubmit(e) {
    e.preventDefault();
    setInputError('');
    setApiError(null);

    // 1. Browser validation (positive whole numbers)
    const stockNum = Number(currentStock);
    const leadTimeNum = Number(leadTimeDays);

    if (currentStock === '' || isNaN(stockNum) || stockNum < 0 || !Number.isInteger(stockNum)) {
      setInputError('Current stock must be a non-negative whole number (0 or more).');
      return;
    }

    if (leadTimeDays === '' || isNaN(leadTimeNum) || leadTimeNum < 1 || leadTimeNum > 28 || !Number.isInteger(leadTimeNum)) {
      setInputError('Lead time must be an integer between 1 and 28 days.');
      return;
    }

    // 2. Call API service
    setLoading(true);
    try {
      const result = await getReorderAdvice({
        item_id: selectedItemId,
        today: today,
        current_stock: stockNum,
        lead_time_days: leadTimeNum
      });
      setAdviceResult(result);
    } catch (err) {
      console.error('Reorder advice error:', err);
      setApiError(err.message || 'Failed to calculate reorder advice.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <PackageCheck className="w-5 h-5 text-blue-600" />
          Inventory & Reorder Advice
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Enter current stock and supplier lead time to get safety stock, reorder point, and order quantity recommendation.
        </p>
      </div>

      {/* Demo Banner */}
      {adviceResult?.is_demo_data && (
        <div className="bg-amber-50 border border-amber-300 rounded p-3 text-xs text-amber-800 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>
            <strong>DEMO DATA:</strong> Flask backend is offline. Advice shown was computed by the frontend fallback math model.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Form Card */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded p-6 shadow-xs">
          <h2 className="text-sm font-bold text-slate-900 mb-1">
            Reorder Calculator
          </h2>
          <p className="text-xs text-slate-500 mb-4">
            Simulate inventory parameters for <strong className="text-slate-800">{selectedItemId}</strong> on <strong className="text-slate-800">{today}</strong>.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Input: Current Stock */}
            <div>
              <label htmlFor="current-stock-input" className="block text-xs font-semibold text-slate-700 mb-1">
                Current Stock on Hand (units)
              </label>
              <input
                id="current-stock-input"
                type="number"
                min="0"
                step="1"
                value={currentStock}
                onChange={(e) => setCurrentStock(e.target.value)}
                placeholder="e.g. 15"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
              />
              <span className="text-[11px] text-slate-400 mt-0.5 block">
                Number of physical units currently on store shelves.
              </span>
            </div>

            {/* Input: Lead Time in Days */}
            <div>
              <label htmlFor="lead-time-input" className="block text-xs font-semibold text-slate-700 mb-1">
                Supplier Lead Time (days)
              </label>
              <input
                id="lead-time-input"
                type="number"
                min="1"
                max="28"
                step="1"
                value={leadTimeDays}
                onChange={(e) => setLeadTimeDays(e.target.value)}
                placeholder="e.g. 5"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
              />
              <span className="text-[11px] text-slate-400 mt-0.5 block">
                Days required for the distributor to deliver replacement stock (1 to 28 days).
              </span>
            </div>

            {/* Browser Validation Error */}
            {inputError && (
              <div className="p-2.5 rounded bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{inputError}</span>
              </div>
            )}

            {/* API Error */}
            {apiError && (
              <div className="p-2.5 rounded bg-rose-50 border border-rose-200 text-xs text-rose-700">
                {apiError}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded shadow-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? 'Calculating...' : 'Get Advice'}
              {!loading && <ArrowRight className="w-4 h-4" />}
            </button>
          </form>
        </div>

        {/* Right Column: Advice Result Card */}
        <div className="lg:col-span-7">
          {adviceResult ? (
            <div className="bg-white border border-slate-200 rounded p-6 shadow-xs space-y-5">
              {/* Risk Status Header */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                    Inventory Risk Assessment
                  </span>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">
                    {adviceResult.message}
                  </div>
                </div>

                {/* Risk Badge */}
                <span
                  className={`px-3 py-1 rounded text-xs font-bold uppercase tracking-wider ${
                    adviceResult.risk === 'High'
                      ? 'bg-rose-100 text-rose-800 border border-rose-300'
                      : adviceResult.risk === 'Medium'
                      ? 'bg-amber-100 text-amber-800 border border-amber-300'
                      : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  }`}
                >
                  {adviceResult.risk} Risk
                </span>
              </div>

              {/* 6 Recommended Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <div className="bg-slate-50 border border-slate-200 rounded p-3">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Days of Stock Left
                  </span>
                  <div className="text-xl font-bold text-slate-900 mt-1">
                    {adviceResult.days_of_stock_left} <span className="text-xs font-normal text-slate-500">days</span>
                  </div>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded p-3">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Lead-Time Demand
                  </span>
                  <div className="text-xl font-bold text-slate-900 mt-1">
                    {adviceResult.expected_demand_in_lead_time} <span className="text-xs font-normal text-slate-500">units</span>
                  </div>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded p-3">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Safety Stock
                  </span>
                  <div className="text-xl font-bold text-slate-900 mt-1">
                    {adviceResult.safety_stock} <span className="text-xs font-normal text-slate-500">units</span>
                  </div>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded p-3">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Reorder Point (ROP)
                  </span>
                  <div className="text-xl font-bold text-blue-600 mt-1">
                    {adviceResult.reorder_point} <span className="text-xs font-normal text-slate-500">units</span>
                  </div>
                </div>

                <div className="bg-blue-50/60 border border-blue-200 rounded p-3 col-span-2 sm:col-span-2">
                  <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wider block">
                    Recommended Order Quantity
                  </span>
                  <div className="text-2xl font-black text-blue-700 mt-1">
                    {adviceResult.order_quantity} <span className="text-xs font-normal text-blue-600">units</span>
                  </div>
                  <span className="text-[10px] text-blue-600 mt-0.5 block">
                    Calculated for (Lead Time + 7 review days) + Safety Stock - Current Stock.
                  </span>
                </div>
              </div>

              {/* Explanatory Help */}
              <div className="text-xs text-slate-500 pt-3 border-t border-slate-100 flex items-start gap-2">
                <Clock className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                <span>
                  High risk occurs when stock lasts fewer days than the supplier lead time. Reorder immediately to avoid stockouts.
                </span>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[300px] bg-slate-50 border border-dashed border-slate-300 rounded p-8 flex flex-col items-center justify-center text-center text-slate-500">
              <ShieldCheck className="w-10 h-10 text-slate-300 mb-2" />
              <h3 className="text-sm font-semibold text-slate-700">No Advice Generated Yet</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-xs">
                Fill in the stock and lead time fields on the left and click "Get Advice" to calculate replenishment quantities.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

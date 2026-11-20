import React from 'react';
import { TrendingUp } from 'lucide-react';

export function Forecasting({ selectedItemId, selectedItem, horizon }) {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Demand Forecasting
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Machine learning forecasts with historical sales comparison for Store CA_1.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200">
            Active Horizon: {horizon} Days
          </span>
        </div>
      </div>

      {/* Placeholder content for Step 3 */}
      <div className="bg-white border border-slate-200 rounded p-6 shadow-xs text-center text-slate-600">
        <p className="text-sm font-medium">
          Forecasting screen navigation ready. Recharts line forecast chart and metrics will be connected in Step 6.
        </p>
      </div>
    </div>
  );
}

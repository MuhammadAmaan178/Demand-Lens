import React from 'react';
import { ClipboardPenLine } from 'lucide-react';

export function SalesEntry({ selectedItemId, selectedItem, onSaveSale }) {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <ClipboardPenLine className="w-5 h-5 text-blue-600" />
            Daily Sales Entry
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Log actual daily sales, update inventory balances, and immediately trigger anomaly detection checks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
            Active Item: {selectedItemId}
          </span>
        </div>
      </div>

      {/* Placeholder content for Step 3 */}
      <div className="bg-white border border-slate-200 rounded p-6 shadow-xs text-center text-slate-600">
        <p className="text-sm font-medium">
          Daily sales entry navigation ready. Sales entry form and stock deduction will be connected in Step 7.
        </p>
      </div>
    </div>
  );
}

import React from 'react';
import { Boxes } from 'lucide-react';

export function Inventory({ selectedItemId, selectedItem, items }) {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Boxes className="w-5 h-5 text-blue-600" />
            Inventory Management
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Monitor on-hand inventory levels, safety stock, and reorder thresholds across Store CA_1.
          </p>
        </div>
      </div>

      {/* Placeholder content for Step 3 */}
      <div className="bg-white border border-slate-200 rounded p-6 shadow-xs text-center text-slate-600">
        <p className="text-sm font-medium">
          Inventory screen navigation ready. Inventory catalog table and reorder calculator will be connected in Step 5.
        </p>
      </div>
    </div>
  );
}

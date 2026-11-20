import React, { useState, useEffect } from 'react';
import { AlertTriangle, Filter, Sparkles, RefreshCw, AlertCircle } from 'lucide-react';
import { getAnomalies } from '../services/api.js';
import { AnomalyChart } from '../components/AnomalyChart.jsx';

export function Anomalies({ selectedItemId, today }) {
  const [anomaliesData, setAnomaliesData] = useState([]);
  const [isDemoData, setIsDemoData] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters state
  const [directionFilter, setDirectionFilter] = useState('ALL');
  const [reasonFilter, setReasonFilter] = useState('ALL');
  const [flaggedFilter, setFlaggedFilter] = useState('ALL');

  // Load anomalies
  async function loadData() {
    if (!today) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getAnomalies(today, selectedItemId);
      setAnomaliesData(res.anomalies || []);
      setIsDemoData(Boolean(res.is_demo_data));
    } catch (err) {
      console.error('Anomalies load error:', err);
      setError(err.message || 'Unable to load anomalies from backend.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [selectedItemId, today]);

  // Apply filters
  const filteredList = anomaliesData.filter((item) => {
    if (directionFilter !== 'ALL' && item.direction.toLowerCase() !== directionFilter.toLowerCase()) {
      return false;
    }
    if (reasonFilter !== 'ALL' && item.reason.toLowerCase() !== reasonFilter.toLowerCase()) {
      return false;
    }
    if (flaggedFilter !== 'ALL' && item.flagged_by.toLowerCase() !== flaggedFilter.toLowerCase()) {
      return false;
    }
    return true;
  });

  // Calculate reason counts for summary cards
  const reasonCounts = {
    'price change': 0,
    'event': 0,
    'SNAP day': 0,
    'unexplained': 0
  };

  anomaliesData.forEach((item) => {
    const r = (item.reason || '').toLowerCase();
    if (r.includes('price')) reasonCounts['price change']++;
    else if (r.includes('snap')) reasonCounts['SNAP day']++;
    else if (r.includes('event')) reasonCounts['event']++;
    else reasonCounts['unexplained']++;
  });

  return (
    <div className="space-y-6">
      {/* Demo Data Banner */}
      {isDemoData && (
        <div className="bg-amber-50 border border-amber-300 rounded p-3 text-xs text-amber-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>
              <strong>DEMO DATA:</strong> The Flask backend is offline. Displaying simulated anomaly records for evaluation.
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

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            Anomaly Detection
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Identify unusual past sales spikes and unexpected drops before pretend date <strong className="text-slate-800">{today}</strong> for <strong className="text-slate-800">{selectedItemId}</strong>.
          </p>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="bg-white border border-slate-200 rounded p-12 text-center text-slate-600">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" />
          <p className="text-sm font-medium">Checking historical sales for anomalies...</p>
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="bg-white border border-rose-200 rounded p-8 text-center">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-slate-900">Failed to load anomalies</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">{error}</p>
          <button
            onClick={loadData}
            className="mt-4 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div className="bg-white border border-slate-200 rounded p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Total Flagged
              </span>
              <div className="text-xl font-bold text-slate-900 mt-1">
                {anomaliesData.length}
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Price Changes
              </span>
              <div className="text-xl font-bold text-blue-600 mt-1">
                {reasonCounts['price change']}
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                SNAP Days
              </span>
              <div className="text-xl font-bold text-emerald-600 mt-1">
                {reasonCounts['SNAP day']}
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Store Events
              </span>
              <div className="text-xl font-bold text-purple-600 mt-1">
                {reasonCounts['event']}
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Unexplained
              </span>
              <div className="text-xl font-bold text-slate-600 mt-1">
                {reasonCounts['unexplained']}
              </div>
            </div>
          </div>

          {/* Chart Card */}
          <div className="bg-white border border-slate-200 rounded p-5 shadow-xs">
            <h2 className="text-sm font-bold text-slate-900 mb-1">
              Anomaly Timeline for {selectedItemId}
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Red markers pinpoint dates where actual sales deviated significantly from expected baseline.
            </p>
            <AnomalyChart anomalies={anomaliesData} />
          </div>

          {/* Filter Bar */}
          <div className="bg-white border border-slate-200 rounded p-4 flex flex-wrap items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 font-bold text-slate-700">
              <Filter className="w-3.5 h-3.5 text-blue-600" />
              <span>Filters:</span>
            </div>

            {/* Direction Filter */}
            <div className="flex items-center gap-1">
              <span className="text-slate-500">Direction:</span>
              <select
                value={directionFilter}
                onChange={(e) => setDirectionFilter(e.target.value)}
                className="bg-slate-50 border border-slate-300 rounded px-2 py-1 font-medium text-slate-800"
              >
                <option value="ALL">All</option>
                <option value="spike">Spike</option>
                <option value="drop">Drop</option>
              </select>
            </div>

            {/* Reason Filter */}
            <div className="flex items-center gap-1">
              <span className="text-slate-500">Reason:</span>
              <select
                value={reasonFilter}
                onChange={(e) => setReasonFilter(e.target.value)}
                className="bg-slate-50 border border-slate-300 rounded px-2 py-1 font-medium text-slate-800"
              >
                <option value="ALL">All</option>
                <option value="price change">Price Change</option>
                <option value="event">Event</option>
                <option value="SNAP day">SNAP Day</option>
                <option value="unexplained">Unexplained</option>
              </select>
            </div>

            {/* Flagged By Filter */}
            <div className="flex items-center gap-1">
              <span className="text-slate-500">Flagged By:</span>
              <select
                value={flaggedFilter}
                onChange={(e) => setFlaggedFilter(e.target.value)}
                className="bg-slate-50 border border-slate-300 rounded px-2 py-1 font-medium text-slate-800"
              >
                <option value="ALL">All</option>
                <option value="both">Both (Strongest)</option>
                <option value="rule">Simple Rule</option>
                <option value="isolation">Isolation Forest</option>
              </select>
            </div>

            <span className="text-slate-400 ml-auto">
              Showing {filteredList.length} of {anomaliesData.length} records
            </span>
          </div>

          {/* Anomalies Table */}
          <div className="bg-white border border-slate-200 rounded shadow-xs overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-200 bg-slate-50">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Flagged Anomaly Records
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-2 font-semibold">Item ID</th>
                    <th className="px-4 py-2 font-semibold">Date</th>
                    <th className="px-4 py-2 font-semibold">Real Sales</th>
                    <th className="px-4 py-2 font-semibold">Expected</th>
                    <th className="px-4 py-2 font-semibold">Direction</th>
                    <th className="px-4 py-2 font-semibold">Reason Label</th>
                    <th className="px-4 py-2 font-semibold">Flagged By</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredList.length > 0 ? (
                    filteredList.map((row, idx) => (
                      <tr key={`${row.item_id}-${row.date}-${idx}`} className="hover:bg-slate-50">
                        <td className="px-4 py-2 font-medium text-slate-800">{row.item_id}</td>
                        <td className="px-4 py-2 text-slate-600">{row.date}</td>
                        <td className="px-4 py-2 font-bold text-slate-900">{row.sales}</td>
                        <td className="px-4 py-2 text-slate-500">{row.forecast}</td>
                        <td className="px-4 py-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              row.direction === 'spike'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}
                          >
                            {row.direction}
                          </span>
                        </td>
                        <td className="px-4 py-2 font-medium text-slate-700">{row.reason}</td>
                        <td className="px-4 py-2 text-slate-500">{row.flagged_by}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7" className="px-4 py-8 text-center text-slate-400">
                        No anomalies match the current filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  TrendingUp,
  AlertTriangle,
  PackageCheck,
  Layers,
  Store,
  X
} from 'lucide-react';

// The three main dashboard sections specified by the guide
const NAV_LINKS = [
  { name: 'Forecast', path: '/forecast', icon: TrendingUp },
  { name: 'Anomalies', path: '/anomalies', icon: AlertTriangle },
  { name: 'Reorder', path: '/reorder', icon: PackageCheck },
];

export function Sidebar({ isOpen, onClose }) {
  return (
    <>
      {/* Mobile background overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/50 lg:hidden"
        />
      )}

      {/* Main Sidebar */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-900 text-slate-200 border-r border-slate-800 flex flex-col transition-transform duration-200 lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand header */}
        <div className="h-16 px-6 flex items-center justify-between border-b border-slate-800 bg-slate-950/40">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center text-white font-bold">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="text-base font-bold text-white leading-tight">
                Demand<span className="text-blue-400">Lens</span>
              </div>
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">
                Store CA_1 Intelligence
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white lg:hidden"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Store badge info */}
        <div className="mx-4 my-3 px-3 py-2 rounded bg-slate-800/80 border border-slate-700/60 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <Store className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-medium">Store CA_1</span>
          </div>
          <span className="px-1.5 py-0.5 rounded bg-blue-900/60 text-blue-300 text-[10px] font-semibold">
            California
          </span>
        </div>

        {/* Navigation items: Forecast, Anomalies, Reorder */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          {NAV_LINKS.map((link) => {
            const IconComponent = link.icon;
            return (
              <NavLink
                key={link.path}
                to={link.path}
                onClick={onClose}
                className={({ isActive }) => {
                  if (isActive) {
                    return 'flex items-center gap-3 px-3 py-2.5 rounded text-xs font-semibold bg-blue-600 text-white shadow-sm';
                  }
                  return 'flex items-center gap-3 px-3 py-2.5 rounded text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors';
                }}
              >
                <IconComponent className="w-4 h-4 flex-shrink-0" />
                <span>{link.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/30 text-xs text-slate-400 space-y-1">
          <div className="flex items-center justify-between">
            <span>Allowed Window:</span>
            <span className="font-mono text-[11px] text-slate-200">2016-03-28 — 05-22</span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-500">
            <span>Model:</span>
            <span className="text-blue-400">LightGBM (h7 / h28)</span>
          </div>
        </div>
      </aside>
    </>
  );
}

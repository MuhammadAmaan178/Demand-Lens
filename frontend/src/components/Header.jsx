import React, { useState } from 'react';
import { Menu, Calendar, Search, ChevronDown } from 'lucide-react';

export function Header({
  selectedItemId,
  onSelectItem,
  items = [],
  today,
  onChangeToday,
  onOpenSidebar
}) {
  // Local state for searching/filtering within the item dropdown
  const [searchTerm, setSearchTerm] = useState('');

  // Filter items matching search term
  const filteredItems = items.filter((item) =>
    item.item_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (item.department && item.department.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200">
      <div className="h-16 px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-4">
        {/* Left: Mobile hamburger menu and store label */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenSidebar}
            className="p-2 rounded text-slate-500 hover:text-slate-800 hover:bg-slate-100 lg:hidden"
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Walmart Store
            </span>
            <span className="text-sm font-bold text-slate-900">
              CA_1 (California)
            </span>
          </div>
        </div>

        {/* Right: Item Picker & Today (Pretend) Date Picker */}
        <div className="flex items-center flex-wrap gap-3">
          {/* 1. Item Picker Dropdown with Search Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium text-slate-500 hidden sm:inline">
              Item:
            </span>
            <div className="relative min-w-[170px] sm:min-w-[210px]">
              <select
                value={selectedItemId}
                onChange={(e) => onSelectItem(e.target.value)}
                className="w-full appearance-none bg-slate-50 hover:bg-white text-slate-900 text-xs font-semibold py-2 pl-3 pr-8 rounded border border-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                {filteredItems.length > 0 ? (
                  filteredItems.map((item) => (
                    <option key={item.item_id} value={item.item_id}>
                      {item.item_id} {item.group ? `(${item.group})` : ''}
                    </option>
                  ))
                ) : (
                  <option value={selectedItemId}>{selectedItemId}</option>
                )}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* 2. Today (Pretend) Date Picker */}
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-300 rounded px-2.5 py-1">
            <Calendar className="w-4 h-4 text-blue-600 flex-shrink-0" />
            <div className="flex flex-col">
              <label htmlFor="today-picker" className="text-[10px] font-bold text-slate-500 uppercase tracking-tight">
                Today (pretend)
              </label>
              <input
                id="today-picker"
                type="date"
                value={today}
                min="2016-03-28"
                max="2016-04-24"
                onChange={(e) => {
                  if (e.target.value) {
                    onChangeToday(e.target.value);
                  }
                }}
                className="bg-transparent text-xs font-semibold text-slate-900 focus:outline-none cursor-pointer"
              />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Layout components
import { Sidebar } from './components/Sidebar.jsx';
import { Header } from './components/Header.jsx';

// Pages
import { Forecast } from './pages/Forecast.jsx';
import { Anomalies } from './pages/Anomalies.jsx';
import { Reorder } from './pages/Reorder.jsx';

// API Service
import { getItems } from './services/api.js';

export default function App() {
  // 1. Shared State: Selected Item ID (default to first CA_1 item)
  const [selectedItemId, setSelectedItemId] = useState('FOODS_1_001');

  // 2. Shared State: Today (pretend) date, restricted between 2016-03-28 and 2016-05-22
  const [today, setToday] = useState('2016-05-01');

  // 3. Shared State: Items list loaded from API
  const [items, setItems] = useState([]);
  const [itemsLoading, setItemsLoading] = useState(true);

  // 4. Mobile sidebar visibility
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Load items from API or fallback mock on component mount
  useEffect(() => {
    async function loadItems() {
      setItemsLoading(true);
      try {
        const res = await getItems();
        if (res && res.items) {
          setItems(res.items);
          // If current selected item is not in list, select the first one
          if (res.items.length > 0 && !res.items.some(i => i.item_id === selectedItemId)) {
            setSelectedItemId(res.items[0].item_id);
          }
        }
      } catch (err) {
        console.error('Failed to load items list:', err);
      } finally {
        setItemsLoading(false);
      }
    }
    loadItems();
  }, []);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 flex flex-col antialiased">
        {/* Left Sidebar Navigation (Forecast, Anomalies, Reorder) */}
        <Sidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />

        {/* Main Content Area */}
        <div className="lg:pl-64 flex flex-col flex-1 min-w-0">
          {/* Shared Header with Item Picker and Today Date Picker */}
          <Header
            selectedItemId={selectedItemId}
            onSelectItem={setSelectedItemId}
            items={items}
            today={today}
            onChangeToday={setToday}
            onOpenSidebar={() => setIsSidebarOpen(true)}
          />

          {/* Three Dashboard Routes */}
          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
            <Routes>
              {/* Redirect root to /forecast */}
              <Route path="/" element={<Navigate to="/forecast" replace />} />

              {/* 1. Demand Forecast Page */}
              <Route
                path="/forecast"
                element={<Forecast selectedItemId={selectedItemId} today={today} />}
              />

              {/* 2. Anomaly Detection Page */}
              <Route
                path="/anomalies"
                element={<Anomalies selectedItemId={selectedItemId} today={today} />}
              />

              {/* 3. Inventory & Reorder Advice Page */}
              <Route
                path="/reorder"
                element={<Reorder selectedItemId={selectedItemId} today={today} />}
              />

              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/forecast" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

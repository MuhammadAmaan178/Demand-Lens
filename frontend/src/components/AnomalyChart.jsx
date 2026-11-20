import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';

export function AnomalyChart({ anomalies = [] }) {
  // If no anomalies, show empty state
  if (!anomalies || anomalies.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-400 text-xs border border-dashed border-slate-200 rounded">
        No anomaly events recorded for this selection.
      </div>
    );
  }

  // Sort anomalies chronologically by date
  const sorted = [...anomalies].sort((a, b) => a.date.localeCompare(b.date));

  // Prepare chart points
  const chartData = sorted.map((item) => ({
    date: item.date,
    actual: item.sales,
    forecast: item.forecast,
    anomalyPoint: item.sales, // for red dot highlight
    direction: item.direction,
    reason: item.reason
  }));

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: '#64748B' }}
            stroke="#CBD5E1"
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#64748B' }}
            stroke="#CBD5E1"
            label={{ value: 'Units', angle: -90, position: 'insideLeft', fill: '#64748B', fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#FFFFFF',
              borderColor: '#E2E8F0',
              borderRadius: '4px',
              fontSize: '12px'
            }}
          />
          <Legend
            verticalAlign="top"
            height={36}
            wrapperStyle={{ fontSize: '12px', paddingBottom: '10px' }}
          />

          {/* Actual sales line */}
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual Sales"
            stroke="#0F172A"
            strokeWidth={2}
            dot={{ r: 3, fill: '#0F172A' }}
          />

          {/* Model expected forecast line */}
          <Line
            type="monotone"
            dataKey="forecast"
            name="Model Expected"
            stroke="#2563EB"
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={{ r: 2, fill: '#2563EB' }}
          />

          {/* Highlighted red dots on anomaly days */}
          <Scatter
            dataKey="anomalyPoint"
            name="Anomaly Flag"
            fill="#DC2626"
            shape="circle"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

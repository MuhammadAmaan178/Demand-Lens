import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';

export function ForecastChart({ history = [], forecast = [] }) {
  // Combine past sales and future forecast into a single timeline array
  // Past sales have 'actual', future forecast has 'forecast'
  const chartData = [];

  // Add historical points
  history.forEach((item) => {
    chartData.push({
      date: item.date,
      actual: item.sales,
      forecast: null
    });
  });

  // Add forecast points
  forecast.forEach((item, index) => {
    // If it's the first forecast point and history exists, connect them visually
    if (index === 0 && history.length > 0) {
      const lastHist = history[history.length - 1];
      // Bridge point
      chartData[chartData.length - 1].forecast = lastHist.sales;
    }

    chartData.push({
      date: item.date,
      actual: null,
      forecast: item.value ?? item.predicted
    });
  });

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: '#64748B' }}
            tickLine={false}
            stroke="#CBD5E1"
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#64748B' }}
            tickLine={false}
            stroke="#CBD5E1"
            label={{ value: 'Units Sold', angle: -90, position: 'insideLeft', fill: '#64748B', fontSize: 12 }}
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
          {/* Historical actual sales: solid navy line */}
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual Sales"
            stroke="#0F172A"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#0F172A' }}
            connectNulls={false}
          />
          {/* Forecasted sales: dashed blue line */}
          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecasted Sales"
            stroke="#2563EB"
            strokeWidth={2.5}
            strokeDasharray="5 5"
            dot={{ r: 3, fill: '#2563EB' }}
            connectNulls={true}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

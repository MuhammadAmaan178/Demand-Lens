// =======================================================================
// DemandLens Centralized API Service Layer
// Connects the React Frontend to the Python Flask Backend.
// All endpoints follow: DemandLens_Remaining_Work_Guide.pdf (Part 8)
// =======================================================================

import {
  mockItems,
  getMockForecast,
  getMockAnomalies,
  getMockReorderAdvice
} from '../data/mockData.js';

// Base API URL from environment variable, with localhost fallback
const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL)
  ? import.meta.env.VITE_API_BASE_URL
  : 'http://localhost:5000/api';

/**
 * Generic helper to make HTTP requests with proper error handling.
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers
      }
    });

    // Check for HTTP errors (e.g., 404, 500)
    if (!response.ok) {
      let errorMessage = `Server error (${response.status}): ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData && errorData.error) {
          errorMessage = errorData.error;
        }
      } catch (_) {
        // Response was not JSON
      }
      const error = new Error(errorMessage);
      error.status = response.status;
      throw error;
    }

    return await response.json();
  } catch (error) {
    // Handle network offline / connection refused errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      const netError = new Error(
        `Backend server is offline or unreachable at ${API_BASE_URL}. Please start the Flask server.`
      );
      netError.isNetworkError = true;
      throw netError;
    }
    throw error;
  }
}

// =======================================================================
// API Endpoints Specified by the Guide
// =======================================================================

/**
 * 1. Health check to test if backend is running.
 * Endpoint: GET /health
 */
export async function getHealth() {
  try {
    return await apiRequest('/health', { method: 'GET' });
  } catch (error) {
    throw error;
  }
}

/**
 * 2. Get list of items for the header picker.
 * Endpoint: GET /items
 * Expected Response: { items: [ { item_id, department, group } ] }
 */
export async function getItems() {
  try {
    return await apiRequest('/items', { method: 'GET' });
  } catch (error) {
    // If backend is offline, return mock data with explicit demo label
    if (error.isNetworkError) {
      console.warn('Backend is offline. Using DEMO items data.');
      return { items: mockItems, is_demo_data: true };
    }
    throw error;
  }
}

/**
 * 3. Get 7-day and 28-day forecasts for a selected item and pretend today date.
 * Endpoint: GET /forecast?item_id=...&today=...
 * Expected Response: { item_id, today, history: [...], forecast_7: [...], forecast_28: [...] }
 */
export async function getForecast(itemId, today) {
  if (!itemId || !today) {
    throw new Error('Both item_id and today parameters are required for forecast.');
  }

  const query = new URLSearchParams({ item_id: itemId, today }).toString();

  try {
    return await apiRequest(`/forecast?${query}`, { method: 'GET' });
  } catch (error) {
    if (error.isNetworkError) {
      console.warn(`Backend is offline. Using DEMO forecast data for ${itemId}.`);
      return getMockForecast(itemId, today);
    }
    throw error;
  }
}

/**
 * 4. Get anomalies recorded before or on today.
 * Endpoint: GET /anomalies?today=...&item_id=... (item_id is optional)
 * Expected Response: { anomalies: [ { item_id, date, sales, forecast, direction, reason, flagged_by } ] }
 */
export async function getAnomalies(today, itemId = '') {
  if (!today) {
    throw new Error('The today parameter is required for anomalies.');
  }

  const params = { today };
  if (itemId) {
    params.item_id = itemId;
  }

  const query = new URLSearchParams(params).toString();

  try {
    return await apiRequest(`/anomalies?${query}`, { method: 'GET' });
  } catch (error) {
    if (error.isNetworkError) {
      console.warn(`Backend is offline. Using DEMO anomalies data for ${today}.`);
      return getMockAnomalies(today, itemId);
    }
    throw error;
  }
}

/**
 * 5. Calculate inventory and reorder advice.
 * Endpoint: POST /reorder
 * Payload: { item_id, today, current_stock, lead_time_days }
 * Expected Response: { days_of_stock_left, expected_demand_in_lead_time, safety_stock, reorder_point, order_quantity, risk, message }
 */
export async function getReorderAdvice(payload) {
  if (!payload || !payload.item_id || !payload.today) {
    throw new Error('item_id and today are required for reorder advice.');
  }

  try {
    return await apiRequest('/reorder', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  } catch (error) {
    if (error.isNetworkError) {
      console.warn('Backend is offline. Using DEMO reorder calculation.');
      return getMockReorderAdvice(payload);
    }
    throw error;
  }
}

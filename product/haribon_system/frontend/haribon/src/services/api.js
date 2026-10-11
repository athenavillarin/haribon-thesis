import axios from 'axios';
import { MOCK_LATEST_FORECAST, MOCK_LOCATIONS, MOCK_HISTORICAL_DATA } from './mockData';

// Set to false for live backend connection. Can be toggled with VITE_USE_MOCK_DATA=true.
export const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';  // Fallback for local dev

const LATEST_TTL_MS = 10 * 60 * 1000;
const RETRY_DELAYS_MS = [3000, 8000];
const FORECAST_STORAGE_KEY = 'haribon:lastForecast';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const isRetryable = (error) => {
  if (!error.response) return true;
  return error.response.status >= 500;
};

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 45000,
    });
    this.latest = { promise: null, fetchedAt: 0 };
  }

  // Render's free tier sleeps when idle; ping early so it starts waking up.
  warmUp() {
    if (USE_MOCK_DATA) return;
    this.client.get('/health').catch(() => {});
  }

  async getWithRetry(url, config) {
    for (let attempt = 0; ; attempt += 1) {
      try {
        const response = await this.client.get(url, config);
        return response.data;
      } catch (error) {
        if (attempt >= RETRY_DELAYS_MS.length || !isRetryable(error)) throw error;
        await sleep(RETRY_DELAYS_MS[attempt]);
      }
    }
  }

  getCachedForecast() {
    if (USE_MOCK_DATA) {
      return { data: MOCK_LATEST_FORECAST, savedAt: Date.now() };
    }
    try {
      const raw = localStorage.getItem(FORECAST_STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  saveCachedForecast(data) {
    if (USE_MOCK_DATA) return;
    try {
      localStorage.setItem(FORECAST_STORAGE_KEY, JSON.stringify({ data, savedAt: Date.now() }));
    } catch {
      // Storage may be unavailable (private mode, quota); the live data still renders.
    }
  }

  getLatestForecast({ force = false } = {}) {
    if (USE_MOCK_DATA) {
      return Promise.resolve(MOCK_LATEST_FORECAST);
    }

    const fresh = Date.now() - this.latest.fetchedAt < LATEST_TTL_MS;
    if (this.latest.promise && !force && fresh) {
      return this.latest.promise;
    }

    const promise = this.getWithRetry('/api/forecast/latest')
      .then((data) => {
        this.saveCachedForecast(data);
        return data;
      })
      .catch((error) => {
        if (this.latest.promise === promise) this.latest = { promise: null, fetchedAt: 0 };
        console.error('Error fetching latest forecast:', error);
        throw error;
      });

    this.latest = { promise, fetchedAt: Date.now() };
    return promise;
  }

  async getLocations() {
    if (USE_MOCK_DATA) {
      return MOCK_LOCATIONS;
    }
    try {
      return await this.getWithRetry('/api/forecast/locations');
    } catch (error) {
      console.error('Error fetching locations:', error);
      throw error;
    }
  }

  async getLocationDetails(locationId) {
    if (USE_MOCK_DATA) {
      const loc = MOCK_LATEST_FORECAST.locations.find(
        (l) => l.id === locationId || l.name.toLowerCase() === (locationId || '').toLowerCase()
      );
      return loc || MOCK_LATEST_FORECAST.locations[0];
    }
    try {
      return await this.getWithRetry(`/api/forecast/location/${locationId}`);
    } catch (error) {
      console.error('Error fetching location details:', error);
      throw error;
    }
  }

  async getHistoricalData(locationId, options = {}) {
    if (USE_MOCK_DATA) {
      const normId = (locationId || 'all').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
      const isAll = normId === 'all' || !normId;
      const rawRows = isAll
        ? MOCK_HISTORICAL_DATA.all
        : (MOCK_HISTORICAL_DATA.byLocation[normId] || []);

      let filtered = rawRows;
      if (options.fromDate) {
        const fromYm = options.fromDate.slice(0, 7);
        filtered = filtered.filter((r) => r.label >= fromYm);
      }
      if (options.toDate) {
        const toYm = options.toDate.slice(0, 7);
        filtered = filtered.filter((r) => r.label <= toYm);
      }

      return {
        location: isAll ? 'all' : locationId,
        monthly_alerts: filtered,
        timeline: [],
        available_range: MOCK_HISTORICAL_DATA.available_range,
      };
    }
    try {
      const params = {};
      if (options.fromDate) params.from_date = options.fromDate;
      if (options.toDate) params.to_date = options.toDate;

      return await this.getWithRetry(`/api/forecast/historical/${locationId}`, { params });
    } catch (error) {
      console.error('Error fetching historical data:', error);
      throw error;
    }
  }
}

const apiService = new ApiService();
export default apiService;

import axios from 'axios';

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
    try {
      const raw = localStorage.getItem(FORECAST_STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  saveCachedForecast(data) {
    try {
      localStorage.setItem(FORECAST_STORAGE_KEY, JSON.stringify({ data, savedAt: Date.now() }));
    } catch {
      // Storage may be unavailable (private mode, quota); the live data still renders.
    }
  }

  getLatestForecast({ force = false } = {}) {
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
    try {
      return await this.getWithRetry('/api/forecast/locations');
    } catch (error) {
      console.error('Error fetching locations:', error);
      throw error;
    }
  }

  async getLocationDetails(locationId) {
    try {
      return await this.getWithRetry(`/api/forecast/location/${locationId}`);
    } catch (error) {
      console.error('Error fetching location details:', error);
      throw error;
    }
  }

  async getHistoricalData(locationId, options = {}) {
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

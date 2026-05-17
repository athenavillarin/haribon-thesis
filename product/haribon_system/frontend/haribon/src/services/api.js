import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';  // Fallback for local dev

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
    });
  }

  async getLatestForecast() {
    try {
      const response = await this.client.get('/api/forecast/latest');
      return response.data;
    } catch (error) {
      console.error('Error fetching latest forecast:', error);
      throw error;
    }
  }

  async getLocations() {
    try {
      const response = await this.client.get('/api/forecast/locations');
      return response.data;
    } catch (error) {
      console.error('Error fetching locations:', error);
      throw error;
    }
  }

  async getRiskSummary() {
    try {
      const response = await this.client.get('/api/forecast/risk-summary');
      return response.data;
    } catch (error) {
      console.error('Error fetching risk summary:', error);
      throw error;
    }
  }

  async getEnvironmentalOverview() {
    try {
      const response = await this.client.get('/api/forecast/environmental-overview');
      return response.data;
    } catch (error) {
      console.error('Error fetching environmental overview:', error);
      throw error;
    }
  }

  async triggerDailyUpdate() {
    try {
      const response = await this.client.post('/api/forecast/trigger-update');
      return response.data;
    } catch (error) {
      console.error('Error triggering daily update:', error);
      throw error;
    }
  }

  async getLocationDetails(locationId) {
    try {
      const response = await this.client.get(`/api/forecast/location/${locationId}`);
      return response.data;
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

      const response = await this.client.get(`/api/forecast/historical/${locationId}`, {
        params,
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching historical data:', error);
      throw error;
    }
  }
}

const apiService = new ApiService();
export default apiService;
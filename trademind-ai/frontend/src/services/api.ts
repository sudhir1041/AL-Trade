import axios from 'axios';
import type { User, Tenant, ExchangeAccount, MarketData, Indicator, ScanResult, AISignal, Strategy, Order, Portfolio, RiskMetrics, Notification } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token expiration
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/accounts/login/', { username, password });
    if (response.data.access) {
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
    }
    return response.data;
  },

  register: async (data: { username: string; email: string; password: string }) => {
    const response = await apiClient.post('/accounts/register/', data);
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/accounts/me/');
    return response.data;
  },
};

export const tenantService = {
  getCurrent: async (): Promise<Tenant> => {
    const response = await apiClient.get('/tenants/current/');
    return response.data;
  },

  getMembers: async () => {
    const response = await apiClient.get('/tenants/members/');
    return response.data;
  },
};

export const exchangeService = {
  getAccounts: async (): Promise<ExchangeAccount[]> => {
    const response = await apiClient.get('/exchanges/accounts/');
    return response.data;
  },

  createAccount: async (data: Partial<ExchangeAccount>) => {
    const response = await apiClient.post('/exchanges/accounts/', data);
    return response.data;
  },

  deleteAccount: async (id: number) => {
    await apiClient.delete(`/exchanges/accounts/${id}/`);
  },
};

export const marketService = {
  getOHLCV: async (symbol: string, timeframe: string = '1h', limit: number = 100): Promise<MarketData[]> => {
    const response = await apiClient.get('/market/ohlcv/', { params: { symbol, timeframe, limit } });
    return response.data;
  },

  getLatestPrice: async (symbol: string): Promise<MarketData> => {
    const response = await apiClient.get(`/market/latest/${symbol}/`);
    return response.data;
  },
};

export const indicatorService = {
  getAll: async (): Promise<Indicator[]> => {
    const response = await apiClient.get('/indicators/');
    return response.data;
  },

  calculate: async (indicatorId: number, symbol: string, timeframe: string) => {
    const response = await apiClient.post(`/indicators/${indicatorId}/calculate/`, { symbol, timeframe });
    return response.data;
  },
};

export const scannerService = {
  getResults: async (): Promise<ScanResult[]> => {
    const response = await apiClient.get('/scanner/results/');
    return response.data;
  },

  runScan: async () => {
    const response = await apiClient.post('/scanner/run/');
    return response.data;
  },
};

export const aiService = {
  getSignals: async (): Promise<AISignal[]> => {
    const response = await apiClient.get('/ai/signals/');
    return response.data;
  },

  generatePrediction: async (symbol: string): Promise<AISignal> => {
    const response = await apiClient.post('/ai/predict/', { symbol });
    return response.data;
  },
};

export const mlService = {
  predict: async (symbol: string, features: Record<string, any>) => {
    const response = await apiClient.post('/ml/predict/', { symbol, features });
    return response.data;
  },

  trainModel: async (modelType: string, trainingData: any) => {
    const response = await apiClient.post('/ml/train/', { model_type: modelType, data: trainingData });
    return response.data;
  },
};

export const strategyService = {
  getAll: async (): Promise<Strategy[]> => {
    const response = await apiClient.get('/strategies/');
    return response.data;
  },

  create: async (data: Partial<Strategy>) => {
    const response = await apiClient.post('/strategies/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Strategy>) => {
    const response = await apiClient.patch(`/strategies/${id}/`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await apiClient.delete(`/strategies/${id}/`);
  },

  activate: async (id: number) => {
    const response = await apiClient.post(`/strategies/${id}/activate/`);
    return response.data;
  },

  deactivate: async (id: number) => {
    const response = await apiClient.post(`/strategies/${id}/deactivate/`);
    return response.data;
  },
};

export const orderService = {
  getAll: async (): Promise<Order[]> => {
    const response = await apiClient.get('/orders/');
    return response.data;
  },

  create: async (data: Partial<Order>) => {
    const response = await apiClient.post('/orders/', data);
    return response.data;
  },

  cancel: async (id: number) => {
    const response = await apiClient.post(`/orders/${id}/cancel/`);
    return response.data;
  },
};

export const portfolioService = {
  getSummary: async (): Promise<Portfolio> => {
    const response = await apiClient.get('/portfolio/summary/');
    return response.data;
  },

  getPositions: async () => {
    const response = await apiClient.get('/portfolio/positions/');
    return response.data;
  },

  getPnL: async () => {
    const response = await apiClient.get('/portfolio/pnl/');
    return response.data;
  },
};

export const riskService = {
  getMetrics: async (): Promise<RiskMetrics> => {
    const response = await apiClient.get('/risk/metrics/');
    return response.data;
  },

  calculate: async () => {
    const response = await apiClient.post('/risk/calculate/');
    return response.data;
  },
};

export const notificationService = {
  getAll: async (): Promise<Notification[]> => {
    const response = await apiClient.get('/notifications/');
    return response.data;
  },

  markAsRead: async (id: number) => {
    const response = await apiClient.patch(`/notifications/${id}/read/`);
    return response.data;
  },

  markAllAsRead: async () => {
    const response = await apiClient.post('/notifications/read-all/');
    return response.data;
  },
};

export default apiClient;

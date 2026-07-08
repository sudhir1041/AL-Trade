/**
 * services/index.ts
 * T16 ✅  All API service functions.
 */
import { api } from '@/lib/api'
import type {
  ApiResponse, PaginatedResponse,
  Exchange, ExchangeAccount,
  Ticker, Candle, TradingPair,
  AIScore, Order, Position,
  Portfolio, PnLHistory,
  RiskProfile, UserStrategy, Strategy,
  Notification, ScannerResult, Report,
} from '@/types'

// ── Exchanges ──────────────────────────────────────────────────────────────
export const exchangeService = {
  list:        () => api.get<ApiResponse<Exchange[]>>('/exchanges/'),
  getAccounts: () => api.get<ApiResponse<ExchangeAccount[]>>('/exchanges/accounts/'),
  addAccount:  (d: { exchange: string; label: string; api_key: string; api_secret: string; api_passphrase?: string; is_testnet?: boolean }) =>
                api.post<ApiResponse<ExchangeAccount>>('/exchanges/accounts/', d),
  updateAccount: (id: string, d: Partial<ExchangeAccount>) =>
                  api.patch<ApiResponse<ExchangeAccount>>(`/exchanges/accounts/${id}/`, d),
  deleteAccount: (id: string) => api.delete(`/exchanges/accounts/${id}/`),
  testAccount:   (id: string) => api.post(`/exchanges/accounts/${id}/test/`),
  syncAccount:   (id: string) => api.post(`/exchanges/accounts/${id}/sync/`),
  getBalances:   (id: string) => api.get(`/exchanges/accounts/${id}/balances/`),
}

// ── Market ─────────────────────────────────────────────────────────────────
export const marketService = {
  list:          (exchange?: string)  => api.get<ApiResponse<TradingPair[]>>(`/markets/${exchange ? `?exchange=${exchange}` : ''}`),
  getTicker:     (symbol: string)     => api.get<ApiResponse<Ticker>>(`/markets/${symbol}/ticker/`),
  getOHLCV:      (symbol: string, timeframe = '1h', limit = 200) =>
                   api.get<ApiResponse<Candle[]>>(`/markets/${symbol}/ohlcv/?timeframe=${timeframe}&limit=${limit}`),
  getFundingRate:(symbol: string)     => api.get(`/markets/${symbol}/funding-rate/`),
  getOI:         (symbol: string)     => api.get(`/markets/${symbol}/open-interest/`),
  search:        (q: string)          => api.get<ApiResponse<TradingPair[]>>(`/markets/search/?q=${q}`),
}

// ── AI ─────────────────────────────────────────────────────────────────────
export const aiService = {
  analyze:        (symbol: string)   => api.post(`/ai/analyze/`, { symbol }),
  getScore:       (symbol: string)   => api.get<ApiResponse<AIScore>>(`/ai/score/${symbol}/`),
  getRecommendation: (symbol: string) => api.get(`/ai/recommendation/${symbol}/`),
  getExplanation: (symbol: string)   => api.get(`/ai/explanation/${symbol}/`),
  getHistory:     (symbol?: string, limit = 50) =>
                   api.get<ApiResponse<AIScore[]>>(`/ai/history/?${symbol ? `symbol=${symbol}&` : ''}limit=${limit}`),
}

// ── Scanner ────────────────────────────────────────────────────────────────
export const scannerService = {
  run:          () => api.post('/scanner/run/'),
  getStatus:    () => api.get('/scanner/status/'),
  getResults:   (limit = 50) => api.get<ApiResponse<ScannerResult[]>>(`/scanner/results/?limit=${limit}`),
  getCandidates:() => api.get<ApiResponse<ScannerResult[]>>('/scanner/candidates/'),
  getSettings:  () => api.get('/scanner/settings/'),
  updateSettings: (d: Record<string, unknown>) => api.patch('/scanner/settings/', d),
}

// ── Orders ─────────────────────────────────────────────────────────────────
export const orderService = {
  list:           (params?: Record<string, string>) =>
                   api.get<PaginatedResponse<Order>>(`/orders/?${new URLSearchParams(params).toString()}`),
  create:         (d: Record<string, unknown>) => api.post<ApiResponse<Order>>('/orders/', d),
  get:            (id: string)     => api.get<ApiResponse<Order>>(`/orders/${id}/`),
  update:         (id: string, d: Record<string, unknown>) => api.patch(`/orders/${id}/`, d),
  cancel:         (id: string)     => api.delete(`/orders/${id}/`),
  getPositions:   () => api.get<ApiResponse<Position[]>>('/orders/positions/'),
  getPosition:    (id: string) => api.get<ApiResponse<Position>>(`/orders/positions/${id}/`),
  closePosition:  (id: string) => api.post(`/orders/positions/${id}/close/`),
  partialClose:   (id: string, pct: number) =>
                   api.post(`/orders/positions/${id}/partial-close/`, { close_pct: pct }),
  getTradeHistory:() => api.get<PaginatedResponse<Order>>('/orders/trades/'),
}

// ── Portfolio ──────────────────────────────────────────────────────────────
export const portfolioService = {
  get:         () => api.get<ApiResponse<Portfolio[]>>('/portfolio/'),
  performance: (limit = 90) => api.get<ApiResponse<PnLHistory[]>>(`/portfolio/performance/?limit=${limit}`),
  history:     (limit = 168) => api.get(`/portfolio/history/?limit=${limit}`),
  pnl:         () => api.get('/portfolio/pnl/'),
}

// ── Risk ───────────────────────────────────────────────────────────────────
export const riskService = {
  getProfile:     () => api.get<ApiResponse<RiskProfile>>('/risk/profile/'),
  updateProfile:  (d: Partial<RiskProfile>) => api.patch('/risk/profile/', d),
  getExposure:    () => api.get('/risk/exposure/'),
  getLimits:      () => api.get('/risk/limits/'),
  emergencyStop:  (reason: string) => api.post('/risk/emergency-stop/', { reason }),
  resume:         () => api.post('/risk/resume/'),
}

// ── Strategies ─────────────────────────────────────────────────────────────
export const strategyService = {
  library:      () => api.get<ApiResponse<Strategy[]>>('/strategies/library/'),
  list:         () => api.get<ApiResponse<UserStrategy[]>>('/strategies/'),
  create:       (d: Record<string, unknown>) => api.post('/strategies/', d),
  get:          (id: string) => api.get(`/strategies/${id}/`),
  update:       (id: string, d: Record<string, unknown>) => api.patch(`/strategies/${id}/`, d),
  delete:       (id: string) => api.delete(`/strategies/${id}/`),
  activate:     (id: string) => api.post(`/strategies/${id}/activate/`),
  deactivate:   (id: string) => api.post(`/strategies/${id}/deactivate/`),
  performance:  (id: string) => api.get(`/strategies/${id}/performance/`),
  backtest:     (id: string, d: Record<string, unknown>) => api.post(`/strategies/${id}/backtest/`, d),
}

// ── Notifications ──────────────────────────────────────────────────────────
export const notificationService = {
  list:       (page = 1) => api.get<ApiResponse<Notification[]>>(`/notifications/?page=${page}`),
  markRead:   (ids?: string[]) => api.patch('/notifications/read/', ids ? { ids } : {}),
  delete:     (id: string) => api.delete(`/notifications/${id}/`),
}

// ── Reports ────────────────────────────────────────────────────────────────
export const reportService = {
  list:     (type?: string) => api.get<ApiResponse<Report[]>>(`/reports/${type ? `?type=${type}` : ''}`),
  generate: (d: { report_type: string; title?: string; parameters?: Record<string, unknown> }) =>
             api.post<ApiResponse<Report>>('/reports/generate/', d),
  get:      (id: string) => api.get<ApiResponse<Report>>(`/reports/${id}/`),
  delete:   (id: string) => api.delete(`/reports/${id}/`),
}

// ── Billing ────────────────────────────────────────────────────────────────
export const billingService = {
  getPlans:          () => api.get('/billing/plans/'),
  getSubscription:   () => api.get('/billing/subscription/'),
  subscribe:         (plan_id: string, is_yearly = false) => api.post('/billing/subscription/', { plan_id, is_yearly }),
  cancel:            () => api.post('/billing/subscription/cancel/'),
  getInvoices:       () => api.get('/billing/invoices/'),
  validateCoupon:    (code: string) => api.post('/billing/coupons/validate/', { code }),
}

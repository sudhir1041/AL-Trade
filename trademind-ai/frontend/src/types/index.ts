export interface User {
  id: number;
  username: string;
  email: string;
  tenant_id?: number;
}

export interface Tenant {
  id: number;
  name: string;
  slug: string;
}

export interface ExchangeAccount {
  id: number;
  user: number;
  exchange: string;
  account_name: string;
  api_key: string;
  is_active: boolean;
}

export interface MarketData {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Indicator {
  id: number;
  name: string;
  type: string;
  parameters: Record<string, any>;
}

export interface ScanResult {
  id: number;
  symbol: string;
  pattern: string;
  timeframe: string;
  detected_at: string;
  strength: number;
}

export interface AISignal {
  id: number;
  symbol: string;
  signal_type: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  predicted_price: number;
  generated_at: string;
}

export interface Strategy {
  id: number;
  name: string;
  description: string;
  user: number;
  is_active: boolean;
  created_at: string;
}

export interface Order {
  id: number;
  strategy: number;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  status: 'PENDING' | 'EXECUTED' | 'CANCELLED' | 'FAILED';
  executed_at?: string;
}

export interface Portfolio {
  id: number;
  user: number;
  total_value: number;
  cash_balance: number;
  invested_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
}

export interface RiskMetrics {
  id: number;
  portfolio: number;
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  var_95: number;
  calculated_at: string;
}

export interface Notification {
  id: number;
  user: number;
  title: string;
  message: string;
  type: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';
  is_read: boolean;
  created_at: string;
}

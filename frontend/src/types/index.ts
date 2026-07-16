// T16.1 ✅ — Shared TypeScript types

export interface ApiResponse<T = unknown> {
  success: boolean
  message: string
  data:    T
  meta:    Record<string, unknown>
  error?:  { code: string; message: string; details?: Record<string, unknown> }
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  meta: { page: number; page_size: number; total_count: number; total_pages: number; has_next: boolean; has_previous: boolean }
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id:               string
  email:            string
  username:         string
  first_name:       string
  last_name:        string
  full_name:        string
  role:             UserRole
  is_active:        boolean
  is_2fa_enabled:   boolean
  timezone:         string
  language:         string
  preferred_currency: string
  date_joined:      string
}

export type UserRole = 'GUEST' | 'USER' | 'PREMIUM' | 'ENTERPRISE' | 'SUPPORT' | 'ADMIN' | 'SUPER_ADMIN'

export interface LoginResponse {
  access_token:  string
  refresh_token: string
  token_type:    string
  user:          Pick<User, 'id' | 'email' | 'username' | 'role'>
}

// ── Exchange ──────────────────────────────────────────────────────────────────
export interface Exchange {
  id:                 string
  name:               string
  slug:               string
  logo_url:           string
  is_active:          boolean
  supports_futures:   boolean
  supports_spot:      boolean
  phase:              number
}

export interface ExchangeAccount {
  id:               string
  exchange:         string
  exchange_name:    string
  exchange_slug:    string
  exchange_logo:    string
  label:            string
  api_key_masked:   string
  is_active:        boolean
  is_testnet:       boolean
  connection_status: 'CONNECTED' | 'DISCONNECTED' | 'ERROR' | 'TESTING'
  last_sync_at:     string | null
  created_at:       string
}

// ── Market ────────────────────────────────────────────────────────────────────
export interface Ticker {
  symbol:        string
  price:         string
  bid:           string
  ask:           string
  high_24h:      string
  low_24h:       string
  volume_24h:    string
  change_24h_pct: string
  timestamp:     string
}

export interface Candle {
  timeframe: string
  open:      string
  high:      string
  low:       string
  close:     string
  volume:    string
  timestamp: string
}

export interface TradingPair {
  id:           string
  symbol:       string
  base_asset:   string
  quote_asset:  string
  exchange_name: string
  is_active:    boolean
  is_futures:   boolean
}

// ── AI ────────────────────────────────────────────────────────────────────────
export interface AIScore {
  id:                   string
  symbol:               string
  direction:            'BUY' | 'SELL' | 'HOLD' | 'IGNORE'
  confidence_score:     string
  risk_level:           'LOW' | 'MEDIUM' | 'HIGH' | 'EXTREME'
  market_regime:        string
  entry_zone_low:       string | null
  entry_zone_high:      string | null
  stop_loss_suggest:    string | null
  tp1_suggest:          string | null
  tp2_suggest:          string | null
  risk_reward_ratio:    string | null
  supporting_factors:   string[]
  conflicting_factors:  string[]
  reasoning:            string
  mtf_alignment:        Record<string, string>
  compatible_strategies: string[]
  created_at:           string
}

// ── Orders ────────────────────────────────────────────────────────────────────
export interface Order {
  id:                  string
  symbol:              string
  exchange_name:       string
  strategy_name:       string | null
  side:                'BUY' | 'SELL'
  order_type:          string
  status:              OrderStatus
  quantity:            string
  price:               string | null
  filled_quantity:     string
  remaining_quantity:  string
  average_fill_price:  string | null
  stop_loss_price:     string | null
  take_profit_price:   string | null
  ai_confidence:       string | null
  is_paper_trade:      boolean
  created_at:          string
  filled_at:           string | null
}

export type OrderStatus = 'CREATED' | 'SUBMITTED' | 'ACCEPTED' | 'FILLED' | 'PARTIALLY_FILLED' | 'CANCELLED' | 'REJECTED' | 'EXPIRED'

export interface Position {
  id:               string
  symbol:           string
  exchange_name:    string
  side:             'LONG' | 'SHORT'
  status:           'OPEN' | 'CLOSED' | 'PARTIALLY_CLOSED'
  entry_price:      string
  current_price:    string
  quantity:         string
  unrealized_pnl:   string
  realized_pnl:     string
  pnl_pct:          number
  stop_loss_price:  string | null
  take_profit_price: string | null
  leverage:         number
  is_paper_trade:   boolean
  opened_at:        string
  closed_at:        string | null
}

// ── Portfolio ─────────────────────────────────────────────────────────────────
export interface Portfolio {
  id:               string
  exchange_name:    string
  total_balance:    string
  available_balance: string
  unrealized_pnl:   string
  realized_pnl:     string
  return_pct:       number
  max_drawdown_pct: string
  assets:           PortfolioAsset[]
  last_synced_at:   string | null
}

export interface PortfolioAsset {
  asset:          string
  quantity:       string
  current_price:  string
  value_usdt:     string
  allocation_pct: string
  unrealized_pnl: string
}

export interface PnLHistory {
  date:            string
  daily_pnl:       string
  cumulative_pnl:  string
  portfolio_value: string
  trade_count:     number
  win_rate_pct:    string
}

// ── Risk ──────────────────────────────────────────────────────────────────────
export interface RiskProfile {
  id:                       string
  name:                     string
  profile_type:             'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE' | 'CUSTOM'
  max_risk_per_trade_pct:   string
  max_daily_loss_pct:       string
  max_open_positions:       number
  max_drawdown_pct:         string
  trailing_stop_enabled:    boolean
  break_even_enabled:       boolean
  is_active:                boolean
}

// ── Strategy ──────────────────────────────────────────────────────────────────
export interface Strategy {
  id:              string
  name:            string
  slug:            string
  strategy_type:   string
  description:     string
  suitable_regimes: string[]
  default_params:  Record<string, unknown>
}

export interface UserStrategy {
  id:                    string
  strategy:              string
  strategy_name:         string
  strategy_type:         string
  name:                  string
  automation_level:      'MANUAL' | 'SEMI_AUTO' | 'FULL_AUTO'
  min_confidence_score:  string
  is_active:             boolean
  is_paper_mode:         boolean
}

// ── Notifications ─────────────────────────────────────────────────────────────
export interface Notification {
  id:         string
  event_type: string
  title:      string
  message:    string
  is_read:    boolean
  created_at: string
}

// ── Scanner ───────────────────────────────────────────────────────────────────
export interface ScannerResult {
  id:               string
  symbol:           string
  exchange_name:    string
  confidence_score: string
  risk_score:       string
  trend_direction:  string
  volume_24h_usdt:  string
  volume_spike:     boolean
  factors:          Record<string, unknown>
  is_candidate:     boolean
  created_at:       string
}

// ── Reports ───────────────────────────────────────────────────────────────────
export interface Report {
  id:          string
  report_type: string
  title:       string
  status:      'PENDING' | 'GENERATING' | 'READY' | 'FAILED'
  data:        Record<string, unknown>
  created_at:  string
  generated_at: string | null
}

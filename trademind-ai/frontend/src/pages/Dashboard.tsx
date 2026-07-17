import React, { useEffect } from 'react';
import { useAppStore } from '../../store/appStore';
import { Card, CardContent, CardHeader } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Table } from '../ui/Table';
import { Button } from '../ui/Button';
import { formatCurrency, formatPercentage, formatNumber, getSignalColor } from '../../lib/utils';
import { TrendingUp, TrendingDown, Activity, Wallet, Brain, Zap } from 'lucide-react';

// Mock data for demonstration
const mockSignals = [
  { id: 1, symbol: 'BTC/USDT', signal_type: 'BUY' as const, confidence: 0.87, predicted_price: 52340.50, generated_at: new Date().toISOString() },
  { id: 2, symbol: 'ETH/USDT', signal_type: 'SELL' as const, confidence: 0.79, predicted_price: 3120.25, generated_at: new Date().toISOString() },
  { id: 3, symbol: 'BNB/USDT', signal_type: 'HOLD' as const, confidence: 0.65, predicted_price: 412.80, generated_at: new Date().toISOString() },
];

const mockStrategies = [
  { id: 1, name: 'Momentum Scalper', description: 'High-frequency momentum strategy', is_active: true, created_at: new Date().toISOString() },
  { id: 2, name: 'Mean Reversion', description: 'Statistical arbitrage strategy', is_active: true, created_at: new Date().toISOString() },
  { id: 3, name: 'Trend Following', description: 'Long-term trend detection', is_active: false, created_at: new Date().toISOString() },
];

const mockPortfolio = {
  total_value: 125430.50,
  cash_balance: 32150.25,
  invested_value: 93280.25,
  unrealized_pnl: 8432.15,
  realized_pnl: 15230.80,
};

export const Dashboard: React.FC = () => {
  const { setSignals, setStrategies, setPortfolio } = useAppStore();

  useEffect(() => {
    // In real app, fetch from API
    setSignals(mockSignals);
    setStrategies(mockStrategies);
    setPortfolio(mockPortfolio);
  }, [setSignals, setStrategies, setPortfolio]);

  const stats = [
    { name: 'Total Value', value: formatCurrency(mockPortfolio.total_value), change: '+12.5%', icon: Wallet, color: 'text-green-400' },
    { name: 'Unrealized P&L', value: formatCurrency(mockPortfolio.unrealized_pnl), change: formatPercentage(mockPortfolio.unrealized_pnl / mockPortfolio.invested_value), icon: TrendingUp, color: 'text-blue-400' },
    { name: 'Active Strategies', value: mockStrategies.filter(s => s.is_active).length.toString(), change: `${mockStrategies.length} total`, icon: Brain, color: 'text-purple-400' },
    { name: 'AI Signals Today', value: mockSignals.length.toString(), change: 'Last 24h', icon: Zap, color: 'text-yellow-400' },
  ];

  const signalColumns = [
    { key: 'symbol', label: 'Symbol' },
    { 
      key: 'signal_type', 
      label: 'Signal',
      render: (value: string) => <Badge variant={value === 'BUY' ? 'success' : value === 'SELL' ? 'danger' : 'warning'}>{value}</Badge>
    },
    { 
      key: 'confidence', 
      label: 'Confidence',
      render: (value: number) => (
        <div className="flex items-center gap-2">
          <div className="w-16 bg-dark-700 rounded-full h-2">
            <div className="bg-primary-500 h-2 rounded-full" style={{ width: `${value * 100}%` }} />
          </div>
          <span>{formatNumber(value * 100, 0)}%</span>
        </div>
      )
    },
    { 
      key: 'predicted_price', 
      label: 'Target Price',
      render: (value: number) => formatCurrency(value)
    },
  ];

  const strategyColumns = [
    { key: 'name', label: 'Strategy Name' },
    { key: 'description', label: 'Description' },
    { 
      key: 'is_active', 
      label: 'Status',
      render: (value: boolean) => <Badge variant={value ? 'success' : 'default'}>{value ? 'Active' : 'Inactive'}</Badge>
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Overview of your trading performance</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Card key={stat.name}>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">{stat.name}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                  <p className={`text-sm mt-1 ${stat.color}`}>{stat.change}</p>
                </div>
                <stat.icon className={`h-10 w-10 ${stat.color}`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row - Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Portfolio Performance" description="Last 30 days">
          <CardContent>
            <div className="h-64 flex items-center justify-center bg-dark-900/50 rounded-lg">
              <p className="text-gray-500">Chart placeholder - Integrate Recharts here</p>
            </div>
          </CardContent>
        </Card>

        <Card title="Asset Allocation" description="Current distribution">
          <CardContent>
            <div className="h-64 flex items-center justify-center bg-dark-900/50 rounded-lg">
              <p className="text-gray-500">Pie chart placeholder - Integrate Recharts here</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Signals Table */}
      <Card 
        title="Latest AI Signals" 
        action={<Button variant="outline" size="sm">View All</Button>}
      >
        <Table columns={signalColumns} data={mockSignals} />
      </Card>

      {/* Active Strategies */}
      <Card 
        title="Active Strategies" 
        action={<Button size="sm">Create Strategy</Button>}
      >
        <Table columns={strategyColumns} data={mockStrategies} />
      </Card>
    </div>
  );
};

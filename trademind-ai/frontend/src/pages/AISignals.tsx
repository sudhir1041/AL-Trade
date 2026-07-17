import React from 'react';
import { useAppStore } from '../store/appStore';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Table } from '../ui/Table';
import { formatCurrency, formatNumber, getSignalColor } from '../lib/utils';
import { Brain, Zap, TrendingUp, Activity } from 'lucide-react';

const mockSignals = [
  { id: 1, symbol: 'BTC/USDT', signal_type: 'BUY' as const, confidence: 0.87, predicted_price: 52340.50, generated_at: new Date().toISOString() },
  { id: 2, symbol: 'ETH/USDT', signal_type: 'SELL' as const, confidence: 0.79, predicted_price: 3120.25, generated_at: new Date().toISOString() },
  { id: 3, symbol: 'BNB/USDT', signal_type: 'HOLD' as const, confidence: 0.65, predicted_price: 412.80, generated_at: new Date().toISOString() },
  { id: 4, symbol: 'SOL/USDT', signal_type: 'BUY' as const, confidence: 0.82, predicted_price: 115.50, generated_at: new Date().toISOString() },
  { id: 5, symbol: 'XRP/USDT', signal_type: 'SELL' as const, confidence: 0.71, predicted_price: 0.52, generated_at: new Date().toISOString() },
];

export const AISignals: React.FC = () => {
  const { signals, setSignals } = useAppStore();

  React.useEffect(() => {
    setSignals(mockSignals);
  }, [setSignals]);

  const columns = [
    { key: 'symbol', label: 'Symbol' },
    { 
      key: 'signal_type', 
      label: 'Signal',
      render: (value: string) => (
        <Badge variant={value === 'BUY' ? 'success' : value === 'SELL' ? 'danger' : 'warning'}>
          {value}
        </Badge>
      )
    },
    { 
      key: 'confidence', 
      label: 'Confidence',
      render: (value: number) => (
        <div className="flex items-center gap-2">
          <div className="w-24 bg-dark-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${
                value >= 0.8 ? 'bg-green-500' : value >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
              }`} 
              style={{ width: `${value * 100}%` }} 
            />
          </div>
          <span className="text-sm">{formatNumber(value * 100, 0)}%</span>
        </div>
      )
    },
    { 
      key: 'predicted_price', 
      label: 'Target Price',
      render: (value: number) => formatCurrency(value)
    },
    {
      key: 'generated_at',
      label: 'Generated',
      render: (value: string) => new Date(value).toLocaleString()
    },
    {
      key: 'actions',
      label: 'Action',
      render: (_: any, row: any) => (
        <Button size="sm" variant={row.signal_type === 'BUY' ? 'primary' : row.signal_type === 'SELL' ? 'danger' : 'secondary'}>
          Trade
        </Button>
      )
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Signals</h1>
          <p className="text-gray-400 mt-1">Machine learning powered trading signals</p>
        </div>
        
        <Button>
          <Zap className="h-5 w-5 mr-2" />
          Generate New Signal
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-600/20 rounded-lg">
                <Brain className="h-6 w-6 text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Total Signals</p>
                <p className="text-2xl font-bold text-white">{signals.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-600/20 rounded-lg">
                <TrendingUp className="h-6 w-6 text-green-400" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Buy Signals</p>
                <p className="text-2xl font-bold text-green-400">
                  {signals.filter(s => s.signal_type === 'BUY').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-600/20 rounded-lg">
                <TrendingUp className="h-6 w-6 text-red-400 rotate-180" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Sell Signals</p>
                <p className="text-2xl font-bold text-red-400">
                  {signals.filter(s => s.signal_type === 'SELL').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-600/20 rounded-lg">
                <Activity className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Avg Confidence</p>
                <p className="text-2xl font-bold text-white">
                  {formatNumber(signals.reduce((acc, s) => acc + s.confidence, 0) / signals.length * 100, 1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Signals Table */}
      <Card>
        <Table columns={columns} data={signals} />
      </Card>

      {/* Model Info */}
      <Card title="AI Model Information">
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Model Type</h4>
              <p className="text-white">Ensemble (LSTM + XGBoost)</p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Training Data</h4>
              <p className="text-white">Last 2 years OHLCV + Indicators</p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Last Updated</h4>
              <p className="text-white">{new Date().toLocaleDateString()}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

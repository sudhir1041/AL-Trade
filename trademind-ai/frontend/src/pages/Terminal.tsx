import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Table } from '../ui/Table';
import { formatCurrency, formatNumber } from '../../lib/utils';
import { TrendingUp, TrendingDown, Clock, BarChart3 } from 'lucide-react';

// Mock market data
const mockOHLCV = Array.from({ length: 50 }, (_, i) => ({
  timestamp: new Date(Date.now() - (50 - i) * 3600000).toISOString(),
  open: 52000 + Math.random() * 1000,
  high: 52500 + Math.random() * 1000,
  low: 51500 + Math.random() * 1000,
  close: 52000 + Math.random() * 1000,
  volume: Math.random() * 10000,
}));

const mockOrderBook = {
  bids: Array.from({ length: 10 }, (_, i) => ({
    price: 52000 - i * 10,
    quantity: Math.random() * 5,
  })),
  asks: Array.from({ length: 10 }, (_, i) => ({
    price: 52000 + (i + 1) * 10,
    quantity: Math.random() * 5,
  })),
};

const mockSymbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT'];

export const Terminal: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
  const [timeframe, setTimeframe] = useState('1h');
  const [orderType, setOrderType] = useState('limit');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [price, setPrice] = useState('52000');
  const [quantity, setQuantity] = useState('0.1');

  // Simulate live price updates
  const [currentPrice, setCurrentPrice] = useState(52000);
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentPrice(prev => prev + (Math.random() - 0.5) * 100);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'];

  const orderColumns = [
    { 
      key: 'price', 
      label: 'Price',
      render: (value: number) => formatCurrency(value)
    },
    { 
      key: 'quantity', 
      label: 'Quantity',
      render: (value: number) => formatNumber(value, 4)
    },
    { 
      key: 'total', 
      label: 'Total',
      render: (_: any, row: any) => formatCurrency(row.price * row.quantity)
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Market Terminal</h1>
          <p className="text-gray-400 mt-1">Real-time trading interface</p>
        </div>
        
        {/* Symbol Selector */}
        <div className="flex items-center gap-4">
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-dark-800 border border-dark-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {mockSymbols.map(symbol => (
              <option key={symbol} value={symbol}>{symbol}</option>
            ))}
          </select>
          
          <div className="text-right">
            <p className="text-sm text-gray-400">Last Price</p>
            <p className={`text-2xl font-bold ${currentPrice > 52000 ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(currentPrice)}
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Chart Area */}
        <div className="lg:col-span-3 space-y-4">
          {/* Timeframe Selector */}
          <div className="flex items-center gap-2">
            {timeframes.map(tf => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  timeframe === tf
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-800 text-gray-400 hover:text-white'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* Chart Placeholder */}
          <Card>
            <CardContent>
              <div className="h-96 flex items-center justify-center bg-dark-900/50 rounded-lg border-2 border-dashed border-dark-700">
                <div className="text-center">
                  <BarChart3 className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-500">TradingView Chart Integration</p>
                  <p className="text-sm text-gray-600 mt-2">{selectedSymbol} - {timeframe}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Order Book */}
          <div className="grid grid-cols-2 gap-4">
            <Card title="Bids (Buy)">
              <CardContent>
                <Table 
                  columns={orderColumns} 
                  data={mockOrderBook.bids.slice(0, 5)} 
                />
              </CardContent>
            </Card>
            
            <Card title="Asks (Sell)">
              <CardContent>
                <Table 
                  columns={orderColumns} 
                  data={mockOrderBook.asks.slice(0, 5)} 
                />
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Order Form */}
        <div className="space-y-4">
          <Card title="Place Order">
            <CardContent className="space-y-4">
              {/* Order Type */}
              <div className="flex gap-2">
                <button
                  onClick={() => setOrderType('limit')}
                  className={`flex-1 py-2 rounded text-sm font-medium ${
                    orderType === 'limit'
                      ? 'bg-primary-600 text-white'
                      : 'bg-dark-800 text-gray-400'
                  }`}
                >
                  Limit
                </button>
                <button
                  onClick={() => setOrderType('market')}
                  className={`flex-1 py-2 rounded text-sm font-medium ${
                    orderType === 'market'
                      ? 'bg-primary-600 text-white'
                      : 'bg-dark-800 text-gray-400'
                  }`}
                >
                  Market
                </button>
              </div>

              {/* Side Selector */}
              <div className="flex gap-2">
                <button
                  onClick={() => setSide('buy')}
                  className={`flex-1 py-3 rounded-lg font-medium ${
                    side === 'buy'
                      ? 'bg-green-600 text-white'
                      : 'bg-dark-800 text-gray-400'
                  }`}
                >
                  Buy
                </button>
                <button
                  onClick={() => setSide('sell')}
                  className={`flex-1 py-3 rounded-lg font-medium ${
                    side === 'sell'
                      ? 'bg-red-600 text-white'
                      : 'bg-dark-800 text-gray-400'
                  }`}
                >
                  Sell
                </button>
              </div>

              {/* Price Input */}
              {orderType === 'limit' && (
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Price (USDT)</label>
                  <input
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    className="w-full bg-dark-900 border border-dark-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              )}

              {/* Quantity Input */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">Quantity</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  className="w-full bg-dark-900 border border-dark-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Total */}
              <div className="pt-4 border-t border-dark-700">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Total</span>
                  <span className="text-white font-medium">
                    {formatCurrency(parseFloat(price) * parseFloat(quantity))}
                  </span>
                </div>
              </div>

              {/* Submit Button */}
              <button
                className={`w-full py-3 rounded-lg font-medium text-white ${
                  side === 'buy' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                } transition-colors`}
              >
                {side === 'buy' ? 'Buy' : 'Sell'} {selectedSymbol.split('/')[0]}
              </button>
            </CardContent>
          </Card>

          {/* Recent Trades */}
          <Card title="Recent Trades">
            <CardContent>
              <div className="space-y-2">
                {Array.from({ length: 5 }, (_, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className={i % 2 === 0 ? 'text-green-400' : 'text-red-400'}>
                      {formatCurrency(52000 + (Math.random() - 0.5) * 200)}
                    </span>
                    <span className="text-gray-400">{formatNumber(Math.random() * 2, 4)}</span>
                    <span className="text-gray-500 text-xs">
                      {new Date().toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

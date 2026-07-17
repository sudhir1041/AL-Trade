import React from 'react';
import { useAppStore } from '../store/appStore';
import { Card, CardContent } from '../ui/Card';
import { formatCurrency, formatPercentage } from '../lib/utils';
import { Wallet, TrendingUp, TrendingDown, DollarSign, PieChart } from 'lucide-react';

const mockPositions = [
  { symbol: 'BTC', quantity: 0.5, avgPrice: 48000, currentPrice: 52000, value: 26000, pnl: 2000, pnlPercent: 0.0833 },
  { symbol: 'ETH', quantity: 5.2, avgPrice: 2900, currentPrice: 3120, value: 16224, pnl: 1144, pnlPercent: 0.0759 },
  { symbol: 'BNB', quantity: 25, avgPrice: 380, currentPrice: 412, value: 10300, pnl: 800, pnlPercent: 0.0842 },
  { symbol: 'SOL', quantity: 150, avgPrice: 95, currentPrice: 108, value: 16200, pnl: 1950, pnlPercent: 0.1368 },
];

export const Portfolio: React.FC = () => {
  const { portfolio } = useAppStore();

  const totalValue = portfolio?.total_value || 125430.50;
  const totalPnL = portfolio?.unrealized_pnl || 8432.15;
  const totalPnLPercent = totalPnL / (portfolio?.invested_value || 93280.25);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Portfolio</h1>
        <p className="text-gray-400 mt-1">Track your holdings and performance</p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary-600/20 rounded-lg">
                <Wallet className="h-6 w-6 text-primary-400" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Total Value</p>
                <p className="text-2xl font-bold text-white">{formatCurrency(totalValue)}</p>
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
                <p className="text-sm text-gray-400">Unrealized P&L</p>
                <p className="text-2xl font-bold text-green-400">+{formatCurrency(totalPnL)}</p>
                <p className="text-xs text-green-400">{formatPercentage(totalPnLPercent)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-600/20 rounded-lg">
                <DollarSign className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Cash Balance</p>
                <p className="text-2xl font-bold text-white">{formatCurrency(portfolio?.cash_balance || 32150.25)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-600/20 rounded-lg">
                <PieChart className="h-6 w-6 text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Invested</p>
                <p className="text-2xl font-bold text-white">{formatCurrency(portfolio?.invested_value || 93280.25)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Positions Table */}
      <Card title="Current Positions">
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-dark-700">
              <thead className="bg-dark-900/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Asset</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Quantity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Avg Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Current Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Value</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">P&L</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700">
                {mockPositions.map((position) => (
                  <tr key={position.symbol} className="hover:bg-dark-800/50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-8 w-8 rounded-full bg-primary-600/20 flex items-center justify-center mr-3">
                          <span className="text-xs font-bold text-primary-400">{position.symbol[0]}</span>
                        </div>
                        <span className="font-medium text-white">{position.symbol}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-300">{position.quantity}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-300">{formatCurrency(position.avgPrice)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-300">{formatCurrency(position.currentPrice)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-white font-medium">{formatCurrency(position.value)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={position.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                        {position.pnl >= 0 ? '+' : ''}{formatCurrency(position.pnl)}
                      </div>
                      <div className={`text-xs ${position.pnlPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {position.pnlPercent >= 0 ? '+' : ''}{formatPercentage(position.pnlPercent)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Allocation Chart Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Asset Allocation">
          <CardContent>
            <div className="h-64 flex items-center justify-center bg-dark-900/50 rounded-lg">
              <div className="text-center">
                <PieChart className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500">Pie chart showing asset distribution</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card title="Performance History">
          <CardContent>
            <div className="h-64 flex items-center justify-center bg-dark-900/50 rounded-lg">
              <div className="text-center">
                <TrendingUp className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500">Portfolio value over time</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

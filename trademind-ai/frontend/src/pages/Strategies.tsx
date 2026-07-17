import React, { useState } from 'react';
import { useAppStore } from '../store/appStore';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Table } from '../ui/Table';
import { Plus, Play, Square, Trash2, Edit } from 'lucide-react';

const mockStrategies = [
  { id: 1, name: 'Momentum Scalper', description: 'High-frequency momentum strategy using RSI and MACD', is_active: true, created_at: new Date().toISOString() },
  { id: 2, name: 'Mean Reversion', description: 'Statistical arbitrage on Bollinger Bands', is_active: true, created_at: new Date().toISOString() },
  { id: 3, name: 'Trend Following', description: 'Long-term trend detection with moving averages', is_active: false, created_at: new Date().toISOString() },
  { id: 4, name: 'Breakout Strategy', description: 'Volume-based breakout detection', is_active: true, created_at: new Date().toISOString() },
];

export const Strategies: React.FC = () => {
  const { strategies, setStrategies } = useAppStore();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<number | null>(null);

  React.useEffect(() => {
    setStrategies(mockStrategies);
  }, [setStrategies]);

  const handleActivate = (id: number) => {
    console.log('Activating strategy:', id);
  };

  const handleDeactivate = (id: number) => {
    console.log('Deactivating strategy:', id);
  };

  const handleDelete = (id: number) => {
    console.log('Deleting strategy:', id);
  };

  const columns = [
    { key: 'name', label: 'Strategy Name' },
    { key: 'description', label: 'Description' },
    { 
      key: 'is_active', 
      label: 'Status',
      render: (value: boolean) => (
        <Badge variant={value ? 'success' : 'default'}>
          {value ? 'Active' : 'Inactive'}
        </Badge>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_: any, row: any) => (
        <div className="flex items-center gap-2">
          {row.is_active ? (
            <button
              onClick={() => handleDeactivate(row.id)}
              className="p-1 text-yellow-400 hover:text-yellow-300"
              title="Deactivate"
            >
              <Square className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={() => handleActivate(row.id)}
              className="p-1 text-green-400 hover:text-green-300"
              title="Activate"
            >
              <Play className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={() => setSelectedStrategy(row.id)}
            className="p-1 text-blue-400 hover:text-blue-300"
            title="Edit"
          >
            <Edit className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleDelete(row.id)}
            className="p-1 text-red-400 hover:text-red-300"
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      )
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Strategies</h1>
          <p className="text-gray-400 mt-1">Manage your trading strategies</p>
        </div>
        
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-5 w-5 mr-2" />
          Create Strategy
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Strategies</p>
                <p className="text-2xl font-bold text-white mt-1">{strategies.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Active</p>
                <p className="text-2xl font-bold text-green-400 mt-1">
                  {strategies.filter(s => s.is_active).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Inactive</p>
                <p className="text-2xl font-bold text-gray-400 mt-1">
                  {strategies.filter(s => !s.is_active).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Strategies Table */}
      <Card>
        <Table columns={columns} data={strategies} />
      </Card>

      {/* Create Modal Placeholder */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg">
            <CardContent className="space-y-4">
              <h2 className="text-xl font-bold text-white">Create New Strategy</h2>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">Strategy Name</label>
                <input
                  type="text"
                  placeholder="e.g., Momentum Scalper"
                  className="w-full bg-dark-900 border border-dark-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">Description</label>
                <textarea
                  placeholder="Describe your strategy..."
                  rows={3}
                  className="w-full bg-dark-900 border border-dark-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <Button
                  variant="secondary"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button onClick={() => setShowCreateModal(false)} className="flex-1">
                  Create Strategy
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

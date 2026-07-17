import React, { useState } from 'react';
import { useAppStore } from '../store/appStore';
import { Sidebar, Header } from '../components/layout/Sidebar';
import { Dashboard } from './Dashboard';
import { Terminal } from './Terminal';
import { Strategies } from './Strategies';
import { Portfolio } from './Portfolio';
import { AISignals } from './AISignals';
import { Settings } from './Settings';

export const App: React.FC = () => {
  const { sidebarOpen, toggleSidebar, currentView } = useAppStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'terminal':
        return <Terminal />;
      case 'strategies':
        return <Strategies />;
      case 'portfolio':
        return <Portfolio />;
      case 'ai':
        return <AISignals />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-dark-900 overflow-hidden">
      {/* Sidebar */}
      <Sidebar 
        isOpen={mobileMenuOpen} 
        onClose={() => setMobileMenuOpen(false)} 
      />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <Header onMenuClick={() => setMobileMenuOpen(true)} />
        
        {/* Scrollable Content */}
        <main className="flex-1 overflow-y-auto scrollbar-hide">
          {renderView()}
        </main>
      </div>
    </div>
  );
};

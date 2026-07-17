import { create } from 'zustand';
import type { User, Tenant, AISignal, Strategy, Portfolio, Notification } from '../types';

interface AppState {
  // Auth
  user: User | null;
  isAuthenticated: boolean;
  tenant: Tenant | null;
  
  // Data
  signals: AISignal[];
  strategies: Strategy[];
  portfolio: Portfolio | null;
  notifications: Notification[];
  
  // UI
  sidebarOpen: boolean;
  currentView: string;
  
  // Actions
  setUser: (user: User | null) => void;
  setTenant: (tenant: Tenant | null) => void;
  logout: () => void;
  setSignals: (signals: AISignal[]) => void;
  setStrategies: (strategies: Strategy[]) => void;
  setPortfolio: (portfolio: Portfolio | null) => void;
  setNotifications: (notifications: Notification[]) => void;
  toggleSidebar: () => void;
  setCurrentView: (view: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  user: null,
  isAuthenticated: false,
  tenant: null,
  signals: [],
  strategies: [],
  portfolio: null,
  notifications: [],
  sidebarOpen: true,
  currentView: 'dashboard',
  
  // Actions
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setTenant: (tenant) => set({ tenant }),
  logout: () => set({ 
    user: null, 
    isAuthenticated: false, 
    tenant: null,
    signals: [],
    strategies: [],
    portfolio: null,
    notifications: []
  }),
  setSignals: (signals) => set({ signals }),
  setStrategies: (strategies) => set({ strategies }),
  setPortfolio: (portfolio) => set({ portfolio }),
  setNotifications: (notifications) => set({ notifications }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setCurrentView: (view) => set({ currentView: view }),
}));

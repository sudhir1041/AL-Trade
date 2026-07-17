import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

export function formatNumber(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatPercentage(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${(value * 100).toFixed(2)}%`;
}

export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getSignalColor(signalType: 'BUY' | 'SELL' | 'HOLD'): string {
  switch (signalType) {
    case 'BUY':
      return 'text-green-500';
    case 'SELL':
      return 'text-red-500';
    case 'HOLD':
      return 'text-yellow-500';
    default:
      return 'text-gray-500';
  }
}

export function getOrderStatusColor(status: string): string {
  switch (status) {
    case 'EXECUTED':
      return 'text-green-500';
    case 'PENDING':
      return 'text-yellow-500';
    case 'CANCELLED':
      return 'text-gray-500';
    case 'FAILED':
      return 'text-red-500';
    default:
      return 'text-gray-500';
  }
}

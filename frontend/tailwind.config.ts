import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // T16.1 ✅ Design tokens — brand colours
        brand: {
          50:  '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe',
          300: '#93c5fd', 400: '#60a5fa', 500: '#3b82f6',
          600: '#2563eb', 700: '#1d4ed8', 800: '#1e40af', 900: '#1e3a8a',
        },
        success:  { DEFAULT: '#22c55e', light: '#dcfce7', dark: '#15803d' },
        warning:  { DEFAULT: '#f59e0b', light: '#fef3c7', dark: '#b45309' },
        danger:   { DEFAULT: '#ef4444', light: '#fee2e2', dark: '#b91c1c' },
        neutral:  {
          50: '#f8fafc', 100: '#f1f5f9', 200: '#e2e8f0',
          300: '#cbd5e1', 400: '#94a3b8', 500: '#64748b',
          600: '#475569', 700: '#334155', 800: '#1e293b', 900: '#0f172a',
        },
        // Trading colours
        buy:  { DEFAULT: '#22c55e', muted: '#dcfce7' },
        sell: { DEFAULT: '#ef4444', muted: '#fee2e2' },
      },
      fontFamily: {
        sans:  ['Inter', 'system-ui', 'sans-serif'],
        mono:  ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'trading': ['13px', { lineHeight: '1.4', letterSpacing: '0.01em' }],
      },
      spacing: {
        // 4px grid — T16.1 ✅
        '0.5': '2px', '1': '4px', '1.5': '6px',  '2': '8px',
        '2.5': '10px','3': '12px','3.5': '14px',  '4': '16px',
        '5':   '20px','6': '24px','7':   '28px',  '8': '32px',
        '9':   '36px','10':'40px','12':  '48px',  '16': '64px',
      },
      borderRadius: {
        'card': '12px', 'widget': '8px', 'badge': '4px',
      },
      boxShadow: {
        'card':    '0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06)',
        'card-md': '0 4px 6px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.06)',
        'widget':  '0 1px 2px rgba(0,0,0,.05)',
      },
      animation: {
        'fade-in':   'fadeIn .15s ease-out',
        'slide-up':  'slideUp .2s ease-out',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: '0' },                   to: { opacity: '1' } },
        slideUp: { from: { transform: 'translateY(8px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}

export default config

# TradeMind AI Frontend

React + TypeScript frontend for the TradeMind AI quantitative trading platform.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will start at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/       # Sidebar, Header
│   │   └── ui/           # Reusable UI components (Button, Card, Table, Badge)
│   ├── pages/            # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Terminal.tsx
│   │   ├── Strategies.tsx
│   │   ├── Portfolio.tsx
│   │   ├── AISignals.tsx
│   │   └── Settings.tsx
│   ├── services/         # API client and services
│   ├── store/            # Zustand state management
│   ├── types/            # TypeScript type definitions
│   ├── lib/              # Utilities and helpers
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## 🎨 Features

### Pages Implemented
- **Dashboard**: Overview of portfolio, strategies, and AI signals
- **Terminal**: Real-time trading interface with order book and chart
- **Strategies**: Manage and create trading strategies
- **Portfolio**: Track holdings and performance
- **AI Signals**: View ML-powered trading signals
- **Settings**: Account and preference management

### UI Components
- Button (multiple variants)
- Card (with header, content, footer)
- Badge (status indicators)
- Table (sortable, clickable rows)
- Sidebar (responsive navigation)
- Header (search, notifications)

### State Management
- Zustand for global state
- React hooks for local state
- TypeScript for type safety

### API Integration
- Axios client with interceptors
- JWT authentication
- Services for all backend endpoints

## 🛠️ Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Zustand** - State management
- **React Router** - Navigation
- **Axios** - HTTP client
- **Recharts** - Charts (ready to integrate)
- **Lucide React** - Icons

## 🔌 API Connection

Update `.env` file to connect to your backend:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

## 📝 Mock Data

The frontend includes mock data for demonstration. Replace with real API calls when ready.

## 📄 License

MIT

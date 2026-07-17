# TradeMind AI Frontend

## Quick Start

### Prerequisites
- Node.js 18+ installed
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── public/              # Static assets
│   └── index.html       # Landing page (no dependencies)
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/           # Page components
│   ├── services/        # API service layer
│   ├── lib/             # Utilities and helpers
│   ├── styles/          # CSS stylesheets
│   ├── types/           # TypeScript type definitions
│   ├── App.jsx          # Main app component
│   ├── main.jsx         # Entry point
│   └── vite-env.d.ts    # Vite environment types
├── index.html           # HTML template for React app
├── package.json         # Dependencies and scripts
└── vite.config.js       # Vite configuration
```

## Features

✅ **Landing Page** (`public/index.html`)
- No dependencies required
- Opens directly in browser
- Shows platform features
- Backend health status indicator

✅ **React App** (requires `npm install`)
- Modern React 18 with Vite
- API integration ready
- Responsive design
- Beautiful gradient UI
- Feature showcase cards
- Real-time backend status

## Pages to Implement

1. **Authentication** - Login/Register
2. **Dashboard** - Overview and metrics
3. **Terminal** - Live trading interface
4. **Scanner** - Market opportunities
5. **Portfolio** - Holdings and performance
6. **Strategies** - Strategy management
7. **AI Signals** - ML predictions
8. **Reports** - Analytics and charts
9. **Settings** - User preferences
10. **Admin** - Admin panel

## API Integration

The frontend connects to the Django backend at `/api/v1/`. Configure proxy in `vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

## Scripts

- `npm run dev` - Start development server (port 3000)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint (when configured)

## Next Steps

1. Install dependencies: `npm install`
2. Start dev server: `npm run dev`
3. Open http://localhost:3000
4. Build remaining pages
5. Add authentication flow
6. Connect to backend APIs
7. Add real-time WebSocket updates

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **CSS3** - Styling with gradients and glassmorphism
- **Fetch API** - HTTP requests
- **Future**: TypeScript, Radix UI, TailwindCSS, Zustand

---

**Backend Status**: ✅ Complete (17 Django apps, 27 tests passing)
**Frontend Status**: 🚧 In Progress (Structure ready, needs dependencies)

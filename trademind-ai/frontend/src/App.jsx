import { useState, useEffect } from 'react'
import './styles/App.css'

function App() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [stats, setStats] = useState(null)

  useEffect(() => {
    checkAPI()
  }, [])

  const checkAPI = async () => {
    try {
      const response = await fetch('/api/v1/health/')
      const data = await response.json()
      setApiStatus('online')
      console.log('API Health:', data)
    } catch (error) {
      setApiStatus('offline')
      console.error('API Error:', error)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🚀 TradeMind AI</h1>
        <p>AI-Powered Quantitative Trading Platform</p>
      </header>

      <main className="main">
        <div className="status-bar">
          <span className={`status-indicator ${apiStatus}`}>
            ● {apiStatus === 'online' ? 'Backend Online' : apiStatus === 'offline' ? 'Backend Offline' : 'Checking...'}
          </span>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>Market Data</h3>
            <p>Real-time OHLCV data from multiple exchanges</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>AI Engine</h3>
            <p>ML-powered trading signals and predictions</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📈</div>
            <h3>Strategies</h3>
            <p>Backtest and deploy automated strategies</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">💼</div>
            <h3>Portfolio</h3>
            <p>Track performance and manage risk</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Live Trading</h3>
            <p>Execute trades across multiple exchanges</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>Scanner</h3>
            <p>Find trading opportunities with technical indicators</p>
          </div>
        </div>

        <div className="cta-section">
          <h2>Ready to Start Trading?</h2>
          <p>Connect your exchange accounts and let AI optimize your trading strategy</p>
          <button className="btn-primary" onClick={() => alert('Authentication coming soon!')}>
            Get Started
          </button>
        </div>
      </main>

      <footer className="footer">
        <p>&copy; 2024 TradeMind AI. All rights reserved.</p>
        <p>Backend: Django REST API | Frontend: React + Vite</p>
      </footer>
    </div>
  )
}

export default App

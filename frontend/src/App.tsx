import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import WatchlistManager from './pages/WatchlistManager'
import StockDetail from './pages/StockDetail'
import SettingsPage from './pages/SettingsPage'
import PortfolioPage from './pages/PortfolioPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/watchlist" element={<WatchlistManager />} />
          <Route path="/stocks/:ticker" element={<StockDetail />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

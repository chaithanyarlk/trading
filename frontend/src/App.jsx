import React, { useState, useEffect } from 'react';
import {
  TradeFeed, PortfolioOverview, PerformanceDashboard,
  TradingModeToggle, ReasoningPanel, SuggestionsPanel
} from './components/Dashboard';
import {
  EquityCurve, TradeDistribution, PortfolioAllocation
} from './components/Charts';
import {
  OptionsSuggestionsModal, MutualFundsModal, StocksToWatchModal
} from './components/Modals';
import { tradingAPI, createTradeStreamConnection } from './services/api';
import { FaCog, FaScroll, FaChartPie } from 'react-icons/fa';
import './App.css';

function App() {
  const [portfolio, setPortfolio] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [trades, setTrades] = useState([]);
  const [liveMode, setLiveMode] = useState(false);
  const [currentSignal, setCurrentSignal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [suggestions, setSuggestions] = useState([]);
  
  // Modals
  const [showOptionsModal, setShowOptionsModal] = useState(false);
  const [showFundsModal, setShowFundsModal] = useState(false);
  const [showStocksModal, setShowStocksModal] = useState(false);
  
  // WebSocket
  const [ws, setWs] = useState(null);
  
  useEffect(() => {
    initializeApp();
    setupWebSocket();
    
    return () => {
      if (ws) ws.close();
    };
  }, []);
  
  const initializeApp = async () => {
    try {
      setLoading(true);
      
      // Health check
      await tradingAPI.healthCheck();
      
      // Fetch initial data
      const [portfolioRes, metricsRes, tradesRes] = await Promise.all([
        tradingAPI.getPortfolio(),
        tradingAPI.getPerformance(),
        tradingAPI.getTrades()
      ]);
      
      setPortfolio(portfolioRes.data);
      setMetrics(metricsRes.data);
      setTrades(tradesRes.data);
      
      // Generate initial suggestions
      generateSuggestions();
    } catch (error) {
      console.error('Error initializing app:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const setupWebSocket = () => {
    const connection = createTradeStreamConnection(
      (data) => {
        if (data.type === 'signal') {
          setCurrentSignal(data.data);
          // Add to trades list
          setTrades(prev => [data.data, ...prev]);
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
      }
    );
    
    setWs(connection);
  };
  
  const generateSuggestions = () => {
    const generatedSuggestions = [
      {
        title: 'Bullish Setup Detected',
        description: 'TCS showing golden cross on daily chart with high volume confirmation',
        tags: ['Technical', 'Buy Signal', 'High Confidence']
      },
      {
        title: 'Trending Stock Alert',
        description: 'RELIANCE in strong uptrend - consider adding to positions',
        tags: ['Momentum', 'Risk-On']
      },
      {
        title: 'Diversification Opportunity',
        description: 'Start SIP in mid-cap mutual fund for long-term wealth',
        tags: ['Mutual Funds', 'SIP', 'Recommended']
      }
    ];
    setSuggestions(generatedSuggestions);
  };
  
  const handleToggleLiveMode = async (newMode) => {
    try {
      await tradingAPI.setTradingMode(newMode);
      setLiveMode(newMode);
    } catch (error) {
      alert('Error toggling trading mode: ' + error.message);
    }
  };
  
  const refreshData = async () => {
    try {
      const [portfolioRes, metricsRes] = await Promise.all([
        tradingAPI.getPortfolio(),
        tradingAPI.getPerformance()
      ]);
      
      setPortfolio(portfolioRes.data);
      setMetrics(metricsRes.data);
    } catch (error) {
      console.error('Error refreshing data:', error);
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Trading Dashboard...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-900 to-blue-700 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">AI Trading Assistant</h1>
            <p className="text-blue-200 text-sm">Intelligent Market Analysis & Execution</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={refreshData}
              className="bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded flex items-center gap-2"
            >
              <FaCog /> Refresh
            </button>
            <button
              onClick={() => setShowStocksModal(true)}
              className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded flex items-center gap-2"
            >
              <FaScroll /> Stocks to Watch
            </button>
            <button
              onClick={() => setShowFundsModal(true)}
              className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded flex items-center gap-2"
            >
              <FaChartPie /> Mutual Funds
            </button>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Trading Mode */}
        <div className="mb-8">
          <TradingModeToggle
            liveMode={liveMode}
            onToggle={handleToggleLiveMode}
          />
        </div>
        
        {/* Top Row: Trade Feed and Portfolio */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <TradeFeed trades={trades} />
          <PortfolioOverview portfolio={portfolio} />
        </div>
        
        {/* Middle Row: Performance and Reasoning */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <PerformanceDashboard metrics={metrics} />
          {currentSignal && <ReasoningPanel signal={currentSignal} />}
        </div>
        
        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div className="mb-8">
            <SuggestionsPanel suggestions={suggestions} />
          </div>
        )}
        
        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <EquityCurve
            trades={trades}
            initialCapital={1000000}
          />
          <TradeDistribution metrics={metrics} />
        </div>
        
        {/* Portfolio Allocation */}
        {portfolio && portfolio.holdings.length > 0 && (
          <div className="mb-8">
            <PortfolioAllocation holdings={portfolio.holdings} />
          </div>
        )}
      </main>
      
      {/* Modals */}
      <OptionsSuggestionsModal
        isOpen={showOptionsModal}
        onClose={() => setShowOptionsModal(false)}
        underlying="RELIANCE"
        price={2500}
      />
      
      <MutualFundsModal
        isOpen={showFundsModal}
        onClose={() => setShowFundsModal(false)}
      />
      
      <StocksToWatchModal
        isOpen={showStocksModal}
        onClose={() => setShowStocksModal(false)}
      />
      
      {/* Footer */}
      <footer className="bg-gray-800 text-gray-400 text-center py-4 mt-12">
        <p>© 2024 AI Trading Assistant | Paper Trading Mode | All prices are simulated</p>
      </footer>
    </div>
  );
}

export default App;

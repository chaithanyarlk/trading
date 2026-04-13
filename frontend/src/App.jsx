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
import {
  PaperTradingConfigPanel, AgentAnalysisPanel, AgentDecisionsList
} from './components/AgentPanel';
import {
  GrowwPortfolioPanel, PotentialBuysPanel, InstrumentsPanel
} from './components/PortfolioAndBuys';
import {
  SchedulerStatusBar, LiveActivityFeed, EodReportPanel
} from './components/SchedulerAndReport';
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
  
  // Agent system state
  const [paperConfig, setPaperConfig] = useState(null);
  const [agentDecisions, setAgentDecisions] = useState([]);
  const [agentLoading, setAgentLoading] = useState(false);
  const [agentPortfolio, setAgentPortfolio] = useState(null);
  const [agentMetrics, setAgentMetrics] = useState(null);

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

  // Auto-refresh agent data every 30s when configured
  useEffect(() => {
    if (!paperConfig) return;
    const interval = setInterval(async () => {
      try {
        const [portRes, perfRes] = await Promise.all([
          tradingAPI.getAgentPortfolio(),
          tradingAPI.getAgentPerformance(),
        ]);
        setAgentPortfolio(portRes.data);
        setAgentMetrics(perfRes.data);
      } catch (err) {
        // silent
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [paperConfig]);

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

      // Also refresh agent data if configured
      if (paperConfig) {
        try {
          const [agentPortRes, agentPerfRes] = await Promise.all([
            tradingAPI.getAgentPortfolio(),
            tradingAPI.getAgentPerformance(),
          ]);
          setAgentPortfolio(agentPortRes.data);
          setAgentMetrics(agentPerfRes.data);
        } catch (err) {
          console.error('Error refreshing agent data:', err);
        }
      }
    } catch (error) {
      console.error('Error refreshing data:', error);
    }
  };

  const handleConfigurePaperTrading = async (config) => {
    const res = await tradingAPI.configurePaperTrading(config);
    setPaperConfig(config);
    return res;
  };

  const handleRunAgentAnalysis = async (symbols, config, autoExecute) => {
    setAgentLoading(true);
    try {
      const res = await tradingAPI.runAgentPipeline(symbols, config, autoExecute);
      setAgentDecisions(res.data.decisions || []);

      // Refresh agent portfolio after execution
      if (autoExecute) {
        const [portRes, perfRes] = await Promise.all([
          tradingAPI.getAgentPortfolio(),
          tradingAPI.getAgentPerformance()
        ]);
        setAgentPortfolio(portRes.data);
        setAgentMetrics(perfRes.data);
      }
    } catch (error) {
      console.error('Error running agent analysis:', error);
      alert('Error running analysis: ' + (error.response?.data?.detail || error.message));
    }
    setAgentLoading(false);
  };

  const handleExecuteDecision = async (decision) => {
    try {
      await tradingAPI.executeDecision(decision);
      // Refresh
      const [portRes, perfRes] = await Promise.all([
        tradingAPI.getAgentPortfolio(),
        tradingAPI.getAgentPerformance()
      ]);
      setAgentPortfolio(portRes.data);
      setAgentMetrics(perfRes.data);
    } catch (error) {
      alert('Error executing trade: ' + (error.response?.data?.detail || error.message));
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
        {/* ═══ MULTI-AGENT TRADING SYSTEM ═══ */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">🤖 Multi-Agent Trading System</h2>

          {/* Paper Trading Config from UI */}
          <div className="mb-6">
            <PaperTradingConfigPanel
              onConfigure={handleConfigurePaperTrading}
              currentConfig={paperConfig}
            />
          </div>

          {/* Scheduler Status — shows if auto-scanning is running */}
          <div className="mb-6">
            <SchedulerStatusBar config={paperConfig} />
          </div>

          {/* Agent Analysis Runner */}
          <div className="mb-6">
            <AgentAnalysisPanel
              onRunAnalysis={handleRunAgentAnalysis}
              config={paperConfig}
              loading={agentLoading}
            />
          </div>

          {/* Agent Decisions + Live Feed */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <AgentDecisionsList
              decisions={agentDecisions}
              onExecute={handleExecuteDecision}
            />
            <LiveActivityFeed />
          </div>

          {/* Agent Portfolio */}
          {agentPortfolio && agentPortfolio.configured !== false && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <PortfolioOverview portfolio={agentPortfolio} />
              {agentMetrics && <PerformanceDashboard metrics={agentMetrics} />}
            </div>
          )}

          {/* Potential Buy Stocks — support, SL, exit prices */}
          <div className="mb-6">
            <PotentialBuysPanel config={paperConfig} onExecute={null} />
          </div>

          {/* EOD Report — auto-generated at 3:35 PM IST */}
          <div className="mb-6">
            <EodReportPanel />
          </div>

          {/* Real Groww Portfolio */}
          <div className="mb-6">
            <GrowwPortfolioPanel />
          </div>

          {/* Instruments Summary */}
          <div className="mb-6">
            <InstrumentsPanel />
          </div>
        </div>

        <hr className="border-gray-700 mb-8" />

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

import React, { useState } from 'react';
import { FaCog, FaRocket, FaExclamationTriangle } from 'react-icons/fa';

const DEFAULT_CONFIG = {
  initial_capital: 1000000,
  max_position_size_percent: 10,
  stop_loss_percent: 2,
  take_profit_percent: 5,
  max_open_positions: 10,
  risk_per_trade_percent: 1,
  trading_symbols: ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK'],
  enable_options: false,
  enable_short_selling: false,
  slippage_percent: 0.05,
  commission_per_trade: 20,
};

export const PaperTradingConfigPanel = ({ onConfigure, currentConfig }) => {
  const [config, setConfig] = useState(currentConfig || DEFAULT_CONFIG);
  const [symbolInput, setSymbolInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleChange = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
    setSaved(false);
  };

  const addSymbol = () => {
    const sym = symbolInput.trim().toUpperCase();
    if (sym && !config.trading_symbols.includes(sym)) {
      setConfig(prev => ({
        ...prev,
        trading_symbols: [...prev.trading_symbols, sym]
      }));
      setSymbolInput('');
      setSaved(false);
    }
  };

  const removeSymbol = (sym) => {
    setConfig(prev => ({
      ...prev,
      trading_symbols: prev.trading_symbols.filter(s => s !== sym)
    }));
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onConfigure(config);
      setSaved(true);
    } catch (err) {
      alert('Error saving config: ' + (err.response?.data?.detail || err.message));
    }
    setSaving(false);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center">
        <FaCog className="mr-2 text-gray-600" />
        Paper Trading Configuration
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
        {/* Capital */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Initial Capital (₹)</label>
          <input
            type="number"
            value={config.initial_capital}
            onChange={e => handleChange('initial_capital', parseFloat(e.target.value) || 0)}
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        {/* Max Position Size */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Max Position Size (%)</label>
          <input
            type="number"
            step="0.5"
            value={config.max_position_size_percent}
            onChange={e => handleChange('max_position_size_percent', parseFloat(e.target.value) || 0)}
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        {/* Stop Loss */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Stop Loss (%)</label>
          <input
            type="number"
            step="0.5"
            value={config.stop_loss_percent}
            onChange={e => handleChange('stop_loss_percent', parseFloat(e.target.value) || 0)}
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        {/* Take Profit */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Take Profit (%)</label>
          <input
            type="number"
            step="0.5"
            value={config.take_profit_percent}
            onChange={e => handleChange('take_profit_percent', parseFloat(e.target.value) || 0)}
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        {/* Max Open Positions */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Max Open Positions</label>
          <input
            type="number"
            value={config.max_open_positions}
            onChange={e => handleChange('max_open_positions', parseInt(e.target.value) || 1)}
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        {/* Risk Per Trade */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Risk Per Trade (%)</label>
          <input
            type="number"
            step="0.25"
            value={config.risk_per_trade_percent}
            onChange={e => handleChange('risk_per_trade_percent', parseFloat(e.target.value) || 0)}
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        {/* Slippage */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Slippage (%)</label>
          <input
            type="number"
            step="0.01"
            value={config.slippage_percent}
            onChange={e => handleChange('slippage_percent', parseFloat(e.target.value) || 0)}
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        {/* Commission */}
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Commission (₹/trade)</label>
          <input
            type="number"
            value={config.commission_per_trade}
            onChange={e => handleChange('commission_per_trade', parseFloat(e.target.value) || 0)}
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>
      </div>

      {/* Toggles */}
      <div className="flex gap-6 mb-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={config.enable_options}
            onChange={e => handleChange('enable_options', e.target.checked)}
          />
          Enable Options
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={config.enable_short_selling}
            onChange={e => handleChange('enable_short_selling', e.target.checked)}
          />
          Enable Short Selling
        </label>
      </div>

      {/* Trading Symbols */}
      <div className="mb-4">
        <label className="block text-xs font-semibold text-gray-600 mb-1">Trading Symbols</label>
        <div className="flex gap-2 mb-2 flex-wrap">
          {config.trading_symbols.map(sym => (
            <span
              key={sym}
              className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded flex items-center gap-1"
            >
              {sym}
              <button onClick={() => removeSymbol(sym)} className="text-red-500 hover:text-red-700 font-bold ml-1">×</button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Add symbol (e.g. SBIN)"
            value={symbolInput}
            onChange={e => setSymbolInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addSymbol()}
            className="border rounded px-3 py-1 text-sm flex-1"
          />
          <button
            onClick={addSymbol}
            className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
          >
            Add
          </button>
        </div>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        disabled={saving}
        className={`w-full py-2 rounded font-semibold text-white transition ${
          saved ? 'bg-green-600' : 'bg-blue-600 hover:bg-blue-700'
        } ${saving ? 'opacity-50' : ''}`}
      >
        {saving ? 'Saving...' : saved ? '✓ Config Saved' : 'Save & Initialize Paper Trading'}
      </button>
    </div>
  );
};


export const AgentAnalysisPanel = ({ onRunAnalysis, config, loading }) => {
  const [autoExecute, setAutoExecute] = useState(false);

  const handleRun = () => {
    if (!config || !config.trading_symbols?.length) {
      alert('Configure paper trading first (set symbols above)');
      return;
    }
    onRunAnalysis(config.trading_symbols, config, autoExecute);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center">
        <FaRocket className="mr-2 text-purple-600" />
        Multi-Agent Analysis
      </h2>

      <p className="text-sm text-gray-600 mb-4">
        Runs 4 AI agents: <strong>DataFetcher</strong> → <strong>AlgoAgent</strong> → <strong>SentimentAgent</strong> → <strong>ChiefAgent</strong> (the boss)
      </p>

      <div className="flex items-center gap-4 mb-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={autoExecute}
            onChange={e => setAutoExecute(e.target.checked)}
          />
          Auto-execute trades (paper)
        </label>
        {autoExecute && (
          <span className="text-xs text-orange-600 flex items-center gap-1">
            <FaExclamationTriangle /> Trades will execute automatically
          </span>
        )}
      </div>

      <button
        onClick={handleRun}
        disabled={loading}
        className={`w-full py-3 rounded font-semibold text-white transition ${
          loading ? 'bg-gray-400' : 'bg-purple-600 hover:bg-purple-700'
        }`}
      >
        {loading ? '🤖 Agents Working...' : '🚀 Run Agent Analysis'}
      </button>
    </div>
  );
};


export const AgentDecisionCard = ({ decision }) => {
  if (!decision) return null;

  const actionColors = {
    BUY: 'bg-green-100 text-green-800 border-green-500',
    SELL: 'bg-red-100 text-red-800 border-red-500',
    HOLD: 'bg-yellow-100 text-yellow-800 border-yellow-500',
  };

  const riskColors = {
    LOW: 'bg-green-200 text-green-900',
    MEDIUM: 'bg-yellow-200 text-yellow-900',
    HIGH: 'bg-orange-200 text-orange-900',
    VERY_HIGH: 'bg-red-200 text-red-900',
  };

  return (
    <div className={`border-l-4 rounded-lg shadow p-4 mb-4 ${actionColors[decision.action] || 'bg-gray-100 border-gray-400'}`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-bold">{decision.symbol}</h3>
          <span className={`text-sm font-bold px-2 py-0.5 rounded ${actionColors[decision.action]}`}>
            {decision.action} x{decision.quantity}
          </span>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold">₹{decision.price?.toFixed(2)}</p>
          <p className="text-xs">
            Confidence: <strong>{(decision.confidence * 100).toFixed(0)}%</strong>
          </p>
          <span className={`text-xs px-2 py-0.5 rounded ${riskColors[decision.risk_level] || ''}`}>
            {decision.risk_level} Risk
          </span>
        </div>
      </div>

      {/* Levels */}
      {(decision.stop_loss || decision.take_profit) && (
        <div className="flex gap-4 mb-3 text-xs">
          {decision.stop_loss && (
            <span className="bg-red-50 text-red-700 px-2 py-1 rounded">
              SL: ₹{decision.stop_loss?.toFixed(2)}
            </span>
          )}
          {decision.take_profit && (
            <span className="bg-green-50 text-green-700 px-2 py-1 rounded">
              TP: ₹{decision.take_profit?.toFixed(2)}
            </span>
          )}
          <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded">
            Position: {decision.position_size_percent?.toFixed(1)}%
          </span>
        </div>
      )}

      {/* Chief Reasoning */}
      <div className="mb-3">
        <h4 className="text-xs font-bold text-gray-700 mb-1">🏛️ Chief Decision</h4>
        <p className="text-sm text-gray-800">{decision.chief_reasoning}</p>
      </div>

      {/* Agent Verdicts */}
      <div className="grid grid-cols-2 gap-2 mb-2">
        {decision.algo_verdict && (
          <div className="bg-white bg-opacity-60 rounded p-2">
            <h5 className="text-xs font-bold text-blue-700">📊 AlgoAgent</h5>
            <p className="text-xs">
              {decision.algo_verdict.action} ({(decision.algo_verdict.confidence * 100).toFixed(0)}%)
              — {decision.algo_verdict.trend}
            </p>
          </div>
        )}
        {decision.sentiment_verdict && (
          <div className="bg-white bg-opacity-60 rounded p-2">
            <h5 className="text-xs font-bold text-purple-700">📰 SentimentAgent</h5>
            <p className="text-xs">
              {decision.sentiment_verdict.action} ({(decision.sentiment_verdict.confidence * 100).toFixed(0)}%)
              — Score: {decision.sentiment_verdict.sentiment_score?.toFixed(2)}
            </p>
          </div>
        )}
      </div>

      {/* Dissenting Opinions */}
      {decision.dissenting_opinions?.length > 0 && (
        <div className="mt-2">
          <h5 className="text-xs font-bold text-orange-700">⚠️ Dissenting Opinions</h5>
          {decision.dissenting_opinions.map((d, i) => (
            <p key={i} className="text-xs text-orange-600 italic">• {d}</p>
          ))}
        </div>
      )}
    </div>
  );
};


export const AgentDecisionsList = ({ decisions, onExecute }) => {
  if (!decisions || decisions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
        <p>No agent decisions yet. Run analysis above.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">🤖 Agent Decisions</h2>
      <div className="space-y-3">
        {decisions.map((decision, idx) => (
          <div key={idx}>
            <AgentDecisionCard decision={decision} />
            {decision.action !== 'HOLD' && !decision.executed && onExecute && (
              <button
                onClick={() => onExecute(decision)}
                className="text-sm bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700 mb-2"
              >
                Execute {decision.action} Paper Trade
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};


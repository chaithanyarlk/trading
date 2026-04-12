import React, { useState, useEffect } from 'react';
import { FaChartLine, FaChartBar, FaCoins, FaUserGraduate } from 'react-icons/fa';

export const TradeFeed = ({ trades }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center">
        <FaChartBar className="mr-2 text-blue-600" />
        Live Trade Feed
      </h2>
      
      <div className="overflow-y-auto max-h-96">
        {trades && trades.length > 0 ? (
          trades.map((trade, idx) => (
            <div
              key={idx}
              className="border-l-4 border-blue-600 pl-4 py-3 mb-3 hover:bg-gray-50"
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold text-gray-900">{trade.asset_name}</p>
                  <p className={`text-sm font-bold ${
                    trade.action === 'BUY' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {trade.action} {trade.quantity} @ ₹{trade.entry_price.toFixed(2)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">
                    {new Date(trade.timestamp).toLocaleTimeString()}
                  </p>
                  <p className="text-xs text-gray-600">
                    Status: {trade.status}
                  </p>
                </div>
              </div>
              <p className="text-xs text-gray-600 mt-2 italic">
                {trade.reasoning}
              </p>
            </div>
          ))
        ) : (
          <p className="text-gray-500 text-center py-8">No trades yet</p>
        )}
      </div>
    </div>
  );
};

export const PortfolioOverview = ({ portfolio }) => {
  if (!portfolio) return null;
  
  const totalReturn = portfolio.total_value - portfolio.total_invested;
  const returnPercent = ((totalReturn / portfolio.total_invested) * 100).toFixed(2);
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center">
        <FaCoins className="mr-2 text-green-600" />
        Portfolio Overview
      </h2>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded">
          <p className="text-gray-600 text-sm">Total Value</p>
          <p className="text-2xl font-bold text-blue-900">
            ₹{portfolio.total_value.toFixed(0)}
          </p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded">
          <p className="text-gray-600 text-sm">P&L</p>
          <p className={`text-2xl font-bold ${totalReturn >= 0 ? 'text-green-900' : 'text-red-900'}`}>
            ₹{totalReturn.toFixed(0)}
          </p>
          <p className={`text-xs ${totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {totalReturn >= 0 ? '+' : ''}{returnPercent}%
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded">
          <p className="text-gray-600 text-sm">Invested</p>
          <p className="text-2xl font-bold text-purple-900">
            ₹{portfolio.total_invested.toFixed(0)}
          </p>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded">
          <p className="text-gray-600 text-sm">Cash</p>
          <p className="text-2xl font-bold text-orange-900">
            ₹{portfolio.cash_balance.toFixed(0)}
          </p>
        </div>
      </div>
      
      <div>
        <h3 className="text-sm font-semibold mb-3">Holdings</h3>
        <div className="space-y-2">
          {portfolio.holdings && portfolio.holdings.length > 0 ? (
            portfolio.holdings.map((holding) => (
              <div key={holding.asset_id} className="flex justify-between text-sm">
                <div>
                  <p className="font-medium">{holding.asset_name}</p>
                  <p className="text-gray-600">{holding.quantity} shares</p>
                </div>
                <div className="text-right">
                  <p className="font-medium">₹{holding.current_value.toFixed(0)}</p>
                  <p className={`text-xs ${
                    holding.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {holding.unrealized_pnl >= 0 ? '+' : ''}{holding.unrealized_pnl_percent.toFixed(2)}%
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-center py-4">No holdings yet</p>
          )}
        </div>
      </div>
    </div>
  );
};

export const PerformanceDashboard = ({ metrics }) => {
  if (!metrics) return null;
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center">
        <FaChartLine className="mr-2 text-purple-600" />
        Performance Metrics
      </h2>
      
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-50 p-4 rounded">
          <p className="text-gray-600 text-xs font-semibold">Total Trades</p>
          <p className="text-2xl font-bold text-gray-900">{metrics.total_trades}</p>
        </div>
        <div className="bg-green-50 p-4 rounded">
          <p className="text-gray-600 text-xs font-semibold">Win Rate</p>
          <p className="text-2xl font-bold text-green-600">
            {metrics.win_rate.toFixed(1)}%
          </p>
          <p className="text-xs text-green-600">
            {metrics.winning_trades}W / {metrics.losing_trades}L
          </p>
        </div>
        <div className="bg-blue-50 p-4 rounded">
          <p className="text-gray-600 text-xs font-semibold">Net Profit</p>
          <p className={`text-2xl font-bold ${
            metrics.net_profit >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            ₹{metrics.net_profit.toFixed(0)}
          </p>
          <p className="text-xs text-gray-600">
            ROI: {metrics.roi.toFixed(2)}%
          </p>
        </div>
        <div className="bg-orange-50 p-4 rounded">
          <p className="text-gray-600 text-xs font-semibold">Avg Return/Trade</p>
          <p className="text-2xl font-bold text-orange-600">
            ₹{metrics.average_trade_return.toFixed(0)}
          </p>
        </div>
        <div className="bg-red-50 p-4 rounded">
          <p className="text-gray-600 text-xs font-semibold">Max Drawdown</p>
          <p className="text-2xl font-bold text-red-600">
            {metrics.max_drawdown.toFixed(2)}%
          </p>
        </div>
        <div className="bg-indigo-50 p-4 rounded">
          <p className="text-gray-600 text-xs font-semibold">Total Profit</p>
          <p className="text-2xl font-bold text-indigo-600">
            ₹{metrics.total_profit.toFixed(0)}
          </p>
        </div>
      </div>
    </div>
  );
};

export const TradingModeToggle = ({ liveMode, onToggle }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
      <div>
        <h3 className="font-semibold text-gray-900">Trading Mode</h3>
        <p className="text-sm text-gray-600">
          Currently in {liveMode ? 'LIVE' : 'PAPER'} trading mode
        </p>
      </div>
      <button
        onClick={() => onToggle(!liveMode)}
        className={`px-6 py-2 rounded font-semibold text-white transition ${
          liveMode
            ? 'bg-red-600 hover:bg-red-700'
            : 'bg-blue-600 hover:bg-blue-700'
        }`}
      >
        {liveMode ? 'Switch to Paper Trading' : 'Enable Live Trading'}
      </button>
    </div>
  );
};

export const ReasoningPanel = ({ signal }) => {
  if (!signal) return null;
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Trade Reasoning</h2>
      
      <div className="space-y-4">
        <div>
          <h3 className="font-semibold text-gray-900">Overview</h3>
          <p className="text-gray-700 mt-2">{signal.reasoning}</p>
        </div>
        
        <div>
          <h3 className="font-semibold text-gray-900">Indicators Used</h3>
          <div className="mt-2 space-y-2">
            {signal.indicators && signal.indicators.map((ind, idx) => (
              <div key={idx} className="bg-gray-50 p-3 rounded">
                <div className="flex justify-between">
                  <span className="font-medium">{ind.name}</span>
                  <span className={`text-sm font-bold ${
                    ind.signal === 'BUY' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {ind.signal}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Value: {ind.value.toFixed(2)} | 
                  Confidence: {(ind.confidence * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <h3 className="font-semibold text-gray-900">Risk Assessment</h3>
          <div className="mt-2">
            <span className={`px-3 py-1 rounded text-sm font-semibold text-white ${
              signal.risk_level === 'LOW' ? 'bg-green-600' :
              signal.risk_level === 'MEDIUM' ? 'bg-yellow-600' :
              'bg-red-600'
            }`}>
              {signal.risk_level} Risk
            </span>
            <p className="text-xs text-gray-600 mt-2">
              Confidence Score: {(signal.confidence * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export const SuggestionsPanel = ({ suggestions }) => {
  if (!suggestions) return null;
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center">
        <FaUserGraduate className="mr-2 text-yellow-600" />
        Smart Suggestions
      </h2>
      
      <div className="space-y-4">
        {suggestions.map((suggestion, idx) => (
          <div key={idx} className="border-l-4 border-yellow-500 pl-4 py-3 bg-yellow-50">
            <h3 className="font-semibold text-gray-900">{suggestion.title}</h3>
            <p className="text-sm text-gray-700 mt-1">{suggestion.description}</p>
            <div className="flex gap-2 mt-2">
              {suggestion.tags && suggestion.tags.map((tag, i) => (
                <span key={i} className="text-xs bg-yellow-200 text-yellow-800 px-2 py-1 rounded">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

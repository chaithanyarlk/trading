import React, { useState, useEffect } from 'react';
import { FaPlus, FaTimes } from 'react-icons/fa';
import { tradingAPI } from '../services/api';

export const OptionsSuggestionsModal = ({ isOpen, onClose, underlying, price }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (isOpen && underlying) {
      fetchSuggestions();
    }
  }, [isOpen, underlying, price]);
  
  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      const response = await tradingAPI.getOptionsSuggestions(underlying, price);
      setSuggestions(response.data);
    } catch (error) {
      console.error('Error fetching options suggestions:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">Options Strategies for {underlying}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <FaTimes />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          {loading ? (
            <p className="text-center text-gray-500">Loading suggestions...</p>
          ) : suggestions.length > 0 ? (
            suggestions.map((strategy, idx) => (
              <div key={idx} className="border rounded-lg p-4 hover:shadow-md">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-lg">{strategy.strategy_name}</h3>
                  <span className={`px-3 py-1 rounded text-xs font-bold text-white ${
                    strategy.max_loss < 500 ? 'bg-green-600' : 'bg-orange-600'
                  }`}>
                    Max Loss: ₹{strategy.max_loss}
                  </span>
                </div>
                
                <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                  <div>
                    <p className="text-gray-600">Strike Prices</p>
                    <p className="font-semibold">₹{strategy.strike_prices.map(s => s.toFixed(2)).join(', ')}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Expiry</p>
                    <p className="font-semibold">{strategy.expiry}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Max Profit</p>
                    <p className="font-semibold text-green-600">₹{strategy.max_profit}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Risk/Reward</p>
                    <p className="font-semibold">{strategy.risk_reward_ratio.toFixed(2)}</p>
                  </div>
                </div>
                
                <p className="text-sm text-gray-700 mt-3">{strategy.reasoning}</p>
                
                <button className="mt-3 w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
                  Place Order
                </button>
              </div>
            ))
          ) : (
            <p className="text-center text-gray-500">No suggestions available</p>
          )}
        </div>
      </div>
    </div>
  );
};

export const MutualFundsModal = ({ isOpen, onClose }) => {
  const [funds, setFunds] = useState([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (isOpen) {
      fetchFunds();
    }
  }, [isOpen]);
  
  const fetchFunds = async () => {
    try {
      setLoading(true);
      const response = await tradingAPI.getMutualFundRecommendations();
      setFunds(response.data);
    } catch (error) {
      console.error('Error fetching funds:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">Recommended Mutual Funds</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <FaTimes />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          {loading ? (
            <p className="text-center text-gray-500">Loading funds...</p>
          ) : funds.length > 0 ? (
            funds.map((fund, idx) => (
              <div key={idx} className="border rounded-lg p-4 hover:shadow-md">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-lg">{fund.fund_name}</h3>
                  <span className={`px-3 py-1 rounded text-xs font-bold text-white ${
                    fund.risk_level === 'LOW' ? 'bg-green-600' :
                    fund.risk_level === 'MEDIUM' ? 'bg-yellow-600' :
                    'bg-red-600'
                  }`}>
                    {fund.risk_level} Risk
                  </span>
                </div>
                
                <p className="text-sm text-gray-600">{fund.fund_category}</p>
                
                <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                  <div>
                    <p className="text-gray-600">Monthly SIP</p>
                    <p className="font-semibold">₹{fund.sip_amount}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Expected Return</p>
                    <p className="font-semibold text-green-600">{fund.expected_return}%</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Lump Sum</p>
                    <p className="font-semibold">₹{fund.lump_sum_amount || 'N/A'}</p>
                  </div>
                </div>
                
                <p className="text-sm text-gray-700 mt-3">{fund.reasoning}</p>
                
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <button className="bg-blue-600 text-white py-2 rounded hover:bg-blue-700 text-sm">
                    Start SIP
                  </button>
                  <button className="bg-green-600 text-white py-2 rounded hover:bg-green-700 text-sm">
                    Invest Lump Sum
                  </button>
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-gray-500">No funds available</p>
          )}
        </div>
      </div>
    </div>
  );
};

export const StocksToWatchModal = ({ isOpen, onClose }) => {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (isOpen) {
      fetchStocks();
    }
  }, [isOpen]);
  
  const fetchStocks = async () => {
    try {
      setLoading(true);
      const response = await tradingAPI.getStocksToWatch();
      setStocks(response.data);
    } catch (error) {
      console.error('Error fetching stocks:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">Stocks to Watch</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <FaTimes />
          </button>
        </div>
        
        <div className="p-6 space-y-3">
          {loading ? (
            <p className="text-center text-gray-500">Loading stocks...</p>
          ) : stocks.length > 0 ? (
            stocks.map((stock, idx) => (
              <div key={idx} className="border rounded-lg p-4 hover:shadow-md">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-lg">{stock.symbol}</h3>
                  <span className="text-xs font-bold text-white bg-blue-600 px-2 py-1 rounded">
                    Score: {(stock.technical_score).toFixed(1)}
                  </span>
                </div>
                
                <p className="text-sm text-gray-700">{stock.reason}</p>
                
                <div className="mt-3 flex gap-4 text-xs">
                  <div>
                    <span className="text-gray-600">Technical</span>
                    <p className="font-semibold">{stock.technical_score.toFixed(1)}/10</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Fundamental</span>
                    <p className="font-semibold">{stock.fundamental_score.toFixed(1)}/10</p>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-gray-500">No stocks available</p>
          )}
        </div>
      </div>
    </div>
  );
};

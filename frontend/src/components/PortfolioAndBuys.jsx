import React, { useState, useEffect } from 'react';
import { FaWallet, FaArrowUp, FaArrowDown, FaSpinner } from 'react-icons/fa';
import { tradingAPI } from '../services/api';


export const GrowwPortfolioPanel = () => {
  const [holdings, setHoldings] = useState(null);
  const [positions, setPositions] = useState(null);
  const [margin, setMargin] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPortfolio = async () => {
    setLoading(true);
    setError(null);
    try {
      const [holdingsRes, positionsRes, marginRes] = await Promise.all([
        tradingAPI.getGrowwHoldings(),
        tradingAPI.getGrowwPositions(),
        tradingAPI.getGrowwMargin(),
      ]);
      setHoldings(holdingsRes.data);
      setPositions(positionsRes.data);
      setMargin(marginRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const isOffline = holdings && !holdings.online;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold flex items-center">
          <FaWallet className="mr-2 text-green-600" />
          My Groww Portfolio
        </h2>
        <button
          onClick={fetchPortfolio}
          disabled={loading}
          className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
        >
          {loading ? <FaSpinner className="animate-spin" /> : 'Refresh'}
        </button>
      </div>

      {error && (
        <p className="text-red-500 text-sm mb-3">Error: {error}</p>
      )}

      {isOffline && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-3">
          <p className="text-yellow-700 text-sm">
            ⚠️ Groww API offline — set GROWW_API_KEY and GROWW_API_SECRET in .env to see real portfolio
          </p>
        </div>
      )}

      {/* Margin */}
      {margin && margin.online && (
        <div className="bg-blue-50 rounded p-3 mb-4">
          <h3 className="text-xs font-semibold text-blue-700 mb-1">Available Margin</h3>
          <pre className="text-xs text-gray-700 overflow-auto max-h-24">
            {JSON.stringify(margin.margin, null, 2)}
          </pre>
        </div>
      )}

      {/* Holdings */}
      <div className="mb-4">
        <h3 className="text-sm font-bold text-gray-700 mb-2">📦 Delivery Holdings</h3>
        {holdings && holdings.online ? (
          <div className="overflow-auto max-h-64">
            {(() => {
              const holdingList = holdings.holdings?.holdings || holdings.holdings;
              if (Array.isArray(holdingList) && holdingList.length > 0) {
                return holdingList.map((h, i) => (
                  <div key={i} className="flex justify-between items-center py-2 border-b text-sm">
                    <div>
                      <p className="font-semibold">{h.trading_symbol || 'Unknown'}</p>
                      <p className="text-xs text-gray-500">ISIN: {h.isin || '-'}</p>
                      <p className="text-xs text-gray-500">Qty: {h.quantity || 0} | Avg: ₹{(h.average_price || 0).toFixed(2)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">Free: {h.demat_free_quantity || 0} | T1: {h.t1_quantity || 0}</p>
                      <p className="text-xs text-gray-500">Pledged: {h.pledge_quantity || 0}</p>
                    </div>
                  </div>
                ));
              }
              return <p className="text-gray-500 text-sm">No delivery holdings found</p>;
            })()}
          </div>
        ) : (
          <p className="text-gray-400 text-sm">Not available</p>
        )}
      </div>

      {/* Positions */}
      <div>
        <h3 className="text-sm font-bold text-gray-700 mb-2">📊 Open Positions</h3>
        {positions && positions.online ? (
          <div className="overflow-auto max-h-48">
            {(() => {
              const posList = positions.positions?.data || positions.positions?.positions || positions.positions;
              if (Array.isArray(posList) && posList.length > 0) {
                return posList.map((p, i) => (
                  <div key={i} className="flex justify-between items-center py-2 border-b text-sm">
                    <div>
                      <p className="font-semibold">{p.trading_symbol || p.symbol}</p>
                      <p className="text-xs text-gray-500">
                        {p.product} | {p.transaction_type} | Qty: {p.quantity || p.qty}
                      </p>
                    </div>
                    <div className="text-right">
                      <p>₹{(p.ltp || p.last_price || 0).toFixed(2)}</p>
                      <p className={`text-xs ${(p.pnl || p.unrealised_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        P&L: ₹{(p.pnl || p.unrealised_pnl || 0).toFixed(2)}
                      </p>
                    </div>
                  </div>
                ));
              }
              return <p className="text-gray-500 text-sm">No open positions</p>;
            })()}
          </div>
        ) : (
          <p className="text-gray-400 text-sm">Not available</p>
        )}
      </div>
    </div>
  );
};


export const PotentialBuysPanel = ({ config, onExecute }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBuys = async () => {
    if (!config) {
      setError('Configure paper trading first');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await tradingAPI.getPotentialBuys(config);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
    setLoading(false);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">🎯 Potential Buy Stocks</h2>
        <button
          onClick={fetchBuys}
          disabled={loading || !config}
          className={`px-4 py-2 rounded text-sm font-semibold text-white ${
            loading ? 'bg-gray-400' : 'bg-emerald-600 hover:bg-emerald-700'
          }`}
        >
          {loading ? '🔍 Scanning...' : 'Scan for Buys'}
        </button>
      </div>

      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}

      {!data && !loading && (
        <p className="text-gray-500 text-sm text-center py-8">
          Click "Scan for Buys" to run multi-agent analysis on your configured symbols
        </p>
      )}

      {data && (
        <>
          {/* Summary */}
          <div className="flex gap-3 mb-4 text-xs">
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
              Analyzed: {data.total_analyzed}
            </span>
            <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
              Buys: {data.potential_buys?.length || 0}
            </span>
            <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
              Holds: {data.holds?.length || 0}
            </span>
            <span className="bg-red-100 text-red-800 px-2 py-1 rounded">
              Sells: {data.sells?.length || 0}
            </span>
          </div>

          {/* Buy Cards */}
          {data.potential_buys && data.potential_buys.length > 0 ? (
            <div className="space-y-4">
              {data.potential_buys.map((stock, idx) => (
                <div key={idx} className="border-l-4 border-green-500 bg-green-50 rounded-lg p-4">
                  {/* Header */}
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-lg font-bold text-green-900">{stock.symbol}</h3>
                      <span className="text-sm bg-green-200 text-green-900 px-2 py-0.5 rounded font-bold">
                        BUY — {stock.confidence}% confidence
                      </span>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-bold">₹{stock.current_price?.toFixed(2)}</p>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        stock.risk_level === 'LOW' ? 'bg-green-200 text-green-800' :
                        stock.risk_level === 'MEDIUM' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-red-200 text-red-800'
                      }`}>
                        {stock.risk_level} Risk
                      </span>
                    </div>
                  </div>

                  {/* Key Levels Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
                    {stock.support_price && (
                      <div className="bg-white rounded p-2">
                        <p className="text-xs font-semibold text-gray-500">Support</p>
                        <p className="text-sm font-bold text-blue-700">₹{stock.support_price}</p>
                      </div>
                    )}
                    {stock.resistance_price && (
                      <div className="bg-white rounded p-2">
                        <p className="text-xs font-semibold text-gray-500">Resistance</p>
                        <p className="text-sm font-bold text-purple-700">₹{stock.resistance_price}</p>
                      </div>
                    )}
                    {stock.stop_loss && (
                      <div className="bg-white rounded p-2">
                        <p className="text-xs font-semibold text-gray-500">Stop Loss</p>
                        <p className="text-sm font-bold text-red-700">₹{stock.stop_loss}</p>
                      </div>
                    )}
                    {stock.exit_price && (
                      <div className="bg-white rounded p-2">
                        <p className="text-xs font-semibold text-gray-500">Exit / Target</p>
                        <p className="text-sm font-bold text-green-700">₹{stock.exit_price}</p>
                      </div>
                    )}
                  </div>

                  {/* Extra info */}
                  <div className="flex gap-3 mb-2 text-xs">
                    <span className="bg-gray-100 px-2 py-1 rounded">
                      Trend: <strong>{stock.trend}</strong>
                    </span>
                    <span className="bg-gray-100 px-2 py-1 rounded">
                      Qty: <strong>{stock.quantity}</strong>
                    </span>
                    <span className="bg-gray-100 px-2 py-1 rounded">
                      Position: <strong>{stock.position_size_percent}%</strong>
                    </span>
                    {stock.sentiment_score !== null && (
                      <span className="bg-gray-100 px-2 py-1 rounded">
                        Sentiment: <strong>{stock.sentiment_score?.toFixed(2)}</strong>
                      </span>
                    )}
                  </div>

                  {/* Indicators */}
                  {stock.indicators && stock.indicators.length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs font-semibold text-gray-600 mb-1">Indicators:</p>
                      <div className="flex flex-wrap gap-1">
                        {stock.indicators.map((ind, i) => (
                          <span key={i} className={`text-xs px-2 py-0.5 rounded ${
                            ind.signal === 'BUY' ? 'bg-green-100 text-green-800' :
                            ind.signal === 'SELL' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {ind.name}: {ind.signal} ({ind.value})
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Reasoning */}
                  <p className="text-sm text-gray-700 italic mb-2">{stock.chief_reasoning}</p>

                  {/* Dissenting opinions */}
                  {stock.dissenting_opinions && stock.dissenting_opinions.length > 0 && (
                    <div className="text-xs text-orange-600">
                      {stock.dissenting_opinions.map((d, i) => (
                        <p key={i}>⚠️ {d}</p>
                      ))}
                    </div>
                  )}

                  {/* Execute button */}
                  {onExecute && (
                    <button
                      onClick={() => onExecute(stock)}
                      className="mt-2 bg-green-600 text-white px-4 py-1.5 rounded text-sm hover:bg-green-700 font-semibold"
                    >
                      Execute Paper Trade
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm text-center py-4">
              No buy signals found. All stocks are HOLD or SELL.
            </p>
          )}

          {/* Holds */}
          {data.holds && data.holds.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-bold text-gray-600 mb-2">⏸️ Hold</h3>
              {data.holds.map((h, i) => (
                <div key={i} className="bg-yellow-50 rounded p-2 mb-1 text-xs">
                  <strong>{h.symbol}</strong>: {h.reason}
                </div>
              ))}
            </div>
          )}

          {/* Sells */}
          {data.sells && data.sells.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-bold text-gray-600 mb-2">🔴 Sell Signals</h3>
              {data.sells.map((s, i) => (
                <div key={i} className="bg-red-50 rounded p-2 mb-1 text-xs">
                  <strong>{s.symbol}</strong> @ ₹{s.price?.toFixed(2)}: {s.reason}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};


export const InstrumentsPanel = () => {
  const [counts, setCounts] = useState(null);

  const fetchCounts = async () => {
    try {
      const res = await tradingAPI.getInstrumentCounts();
      setCounts(res.data.counts);
    } catch (err) {
      console.error('Error fetching instruments:', err);
    }
  };

  useEffect(() => {
    fetchCounts();
  }, []);

  if (!counts) return null;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-bold mb-2">📋 Groww Instruments</h3>
      <div className="flex gap-3 text-xs">
        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
          Total: {counts.total}
        </span>
        <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
          Stocks: {counts.stocks}
        </span>
        <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded">
          Options: {counts.options}
        </span>
        <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded">
          Futures: {counts.futures}
        </span>
      </div>
    </div>
  );
};




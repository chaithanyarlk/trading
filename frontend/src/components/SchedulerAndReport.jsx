import React, { useState, useEffect, useRef } from 'react';
import { FaRobot, FaStop, FaBolt, FaFileAlt, FaClock } from 'react-icons/fa';
import { tradingAPI, createAgentWebSocket } from '../services/api';


export const SchedulerStatusBar = ({ config }) => {
  const [status, setStatus] = useState(null);

  const fetchStatus = async () => {
    try {
      const res = await tradingAPI.getSchedulerStatus();
      setStatus(res.data);
    } catch (err) {
      // silent
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // poll every 10s
    return () => clearInterval(interval);
  }, []);

  const handleStop = async () => {
    await tradingAPI.stopScheduler();
    fetchStatus();
  };

  const handleScanNow = async () => {
    try {
      await tradingAPI.triggerScanNow();
      fetchStatus();
    } catch (err) {
      alert('Scan error: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (!status) return null;

  return (
    <div className={`rounded-lg shadow p-4 flex items-center justify-between flex-wrap gap-3 ${
      status.running ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'
    }`}>
      <div className="flex items-center gap-3">
        <FaRobot className={`text-xl ${status.running ? 'text-green-600 animate-pulse' : 'text-gray-400'}`} />
        <div>
          <p className="font-semibold text-sm">
            Auto-Scheduler: {status.running ? (
              <span className="text-green-700">RUNNING</span>
            ) : (
              <span className="text-gray-500">STOPPED</span>
            )}
          </p>
          <p className="text-xs text-gray-500">
            {status.running && (
              <>
                Every {status.scan_interval_minutes}min •
                {status.market_open ? ' 🟢 Market Open' : ' 🔴 Market Closed'} •
                IST {status.current_time_ist}
              </>
            )}
            {!status.running && config && 'Save config to start auto-scanning'}
            {!status.running && !config && 'Configure paper trading first'}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 text-xs">
        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
          Scans: {status.scans_completed}
        </span>
        <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
          Decisions: {status.decisions_today}
        </span>
        <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded">
          Trades: {status.executions_today}
        </span>

        {status.running && (
          <>
            <button
              onClick={handleScanNow}
              className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 flex items-center gap-1"
            >
              <FaBolt /> Scan Now
            </button>
            <button
              onClick={handleStop}
              className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 flex items-center gap-1"
            >
              <FaStop /> Stop
            </button>
          </>
        )}
      </div>
    </div>
  );
};


export const LiveActivityFeed = () => {
  const [events, setEvents] = useState([]);
  const wsRef = useRef(null);
  const feedRef = useRef(null);

  useEffect(() => {
    // Connect to agent WebSocket
    wsRef.current = createAgentWebSocket(
      // onScanComplete
      (data) => {
        setEvents(prev => [{
          type: 'scan',
          time: data.time || new Date().toLocaleTimeString(),
          data,
        }, ...prev].slice(0, 100)); // keep last 100
      },
      // onEodReport
      (data) => {
        setEvents(prev => [{
          type: 'eod_report',
          time: new Date().toLocaleTimeString(),
          data,
        }, ...prev].slice(0, 100));
      },
      // onError
      (err) => {
        console.error('Agent WS error:', err);
      }
    );

    // Also fetch today's existing data
    const fetchExisting = async () => {
      try {
        const [decisionsRes, executionsRes] = await Promise.all([
          tradingAPI.getTodaysDecisions(),
          tradingAPI.getTodaysExecutions(),
        ]);
        const decisions = decisionsRes.data || [];
        const executions = executionsRes.data || [];
        if (decisions.length > 0 || executions.length > 0) {
          setEvents(prev => [{
            type: 'history',
            time: 'Earlier today',
            data: { decisions_count: decisions.length, executions_count: executions.length, decisions, executions },
          }, ...prev]);
        }
      } catch (err) {
        // silent
      }
    };
    fetchExisting();

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center">
        <FaClock className="mr-2 text-blue-600" />
        Live Activity Feed
      </h2>

      <div ref={feedRef} className="overflow-auto max-h-96 space-y-2">
        {events.length === 0 && (
          <p className="text-gray-400 text-sm text-center py-8">
            Waiting for auto-scanner events... (scans run every 15 min during market hours)
          </p>
        )}

        {events.map((event, idx) => (
          <div key={idx} className={`rounded p-3 text-sm ${
            event.type === 'scan' ? 'bg-blue-50 border-l-4 border-blue-400' :
            event.type === 'eod_report' ? 'bg-yellow-50 border-l-4 border-yellow-400' :
            'bg-gray-50 border-l-4 border-gray-300'
          }`}>
            <div className="flex justify-between items-start">
              <span className="font-semibold text-xs">
                {event.type === 'scan' && `🔍 Scan ${event.data.scan_number || ''}`}
                {event.type === 'eod_report' && '📊 EOD Report'}
                {event.type === 'history' && '📋 Earlier Today'}
              </span>
              <span className="text-xs text-gray-400">{event.time}</span>
            </div>

            {event.type === 'scan' && event.data.summary && (
              <div className="flex gap-2 mt-1 text-xs">
                <span className="text-green-700">Buy: {event.data.summary.buys || 0}</span>
                <span className="text-red-700">Sell: {event.data.summary.sells || 0}</span>
                <span className="text-gray-600">Hold: {event.data.summary.holds || 0}</span>
                {event.data.executions && event.data.executions.length > 0 && (
                  <span className="text-purple-700 font-bold">
                    {event.data.executions.length} trade(s) executed
                  </span>
                )}
              </div>
            )}

            {event.type === 'scan' && event.data.executions && event.data.executions.map((ex, i) => (
              <div key={i} className="mt-1 text-xs bg-white rounded p-1">
                <strong>{ex.action}</strong> {ex.symbol} x{ex.quantity} @ ₹{ex.execution_price?.toFixed(2)}
                {ex.pnl !== undefined && ex.pnl !== null && (
                  <span className={ex.pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {' '}PnL: ₹{ex.pnl}
                  </span>
                )}
              </div>
            ))}

            {event.type === 'history' && (
              <p className="text-xs text-gray-600 mt-1">
                {event.data.decisions_count} decisions, {event.data.executions_count} trades
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};


export const EodReportPanel = () => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchReport = async () => {
    try {
      const res = await tradingAPI.getEodReport();
      if (res.data.available) {
        setReport(res.data.report);
      }
    } catch (err) {
      // silent
    }
  };

  const generateNow = async () => {
    setLoading(true);
    try {
      const res = await tradingAPI.generateEodReportNow();
      if (res.data.available) {
        setReport(res.data.report);
      }
    } catch (err) {
      alert('Error generating report: ' + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchReport();
    // Poll every 60s in case the auto-report just generated
    const interval = setInterval(fetchReport, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold flex items-center">
          <FaFileAlt className="mr-2 text-orange-600" />
          End-of-Day Report
        </h2>
        <div className="flex gap-2">
          <button
            onClick={fetchReport}
            className="bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-300"
          >
            Refresh
          </button>
          <button
            onClick={generateNow}
            disabled={loading}
            className={`px-3 py-1 rounded text-sm text-white font-semibold ${
              loading ? 'bg-gray-400' : 'bg-orange-600 hover:bg-orange-700'
            }`}
          >
            {loading ? 'Generating...' : 'Generate Now'}
          </button>
        </div>
      </div>

      <p className="text-xs text-gray-500 mb-3">
        Auto-generated at 3:35 PM IST after market close. Or click "Generate Now" anytime.
      </p>

      {!report ? (
        <div className="text-center py-8 text-gray-400">
          <FaFileAlt className="text-4xl mx-auto mb-2" />
          <p className="text-sm">No report yet. Will auto-generate at 3:35 PM IST.</p>
        </div>
      ) : report.error ? (
        <p className="text-red-500 text-sm">Error: {report.error}</p>
      ) : (
        <div>
          {/* Report header */}
          <div className="bg-gray-50 rounded p-3 mb-3">
            <div className="flex justify-between text-sm">
              <span>📅 {report.date}</span>
              <span>⏰ Generated at {report.generated_at}</span>
            </div>
            <div className="flex gap-3 mt-2 text-xs">
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                Scans: {report.total_scans}
              </span>
              <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                Decisions: {report.total_decisions}
              </span>
              <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded">
                Trades: {report.total_executions}
              </span>
            </div>
          </div>

          {/* AI Summary */}
          {report.ai_summary && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-3">
              <h3 className="text-sm font-bold text-yellow-800 mb-1">🤖 AI Market Summary</h3>
              <p className="text-sm text-gray-800 whitespace-pre-line">{report.ai_summary}</p>
            </div>
          )}

          {/* Portfolio snapshot */}
          {report.portfolio && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
              <div className="bg-blue-50 rounded p-2 text-center">
                <p className="text-xs text-gray-500">Portfolio Value</p>
                <p className="font-bold text-blue-900">₹{report.portfolio.total_value?.toFixed(0)}</p>
              </div>
              <div className="bg-green-50 rounded p-2 text-center">
                <p className="text-xs text-gray-500">Cash</p>
                <p className="font-bold text-green-900">₹{report.portfolio.cash_balance?.toFixed(0)}</p>
              </div>
              <div className="bg-purple-50 rounded p-2 text-center">
                <p className="text-xs text-gray-500">Unrealized P&L</p>
                <p className={`font-bold ${report.portfolio.unrealized_pnl >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                  ₹{report.portfolio.unrealized_pnl?.toFixed(0)}
                </p>
              </div>
              <div className="bg-orange-50 rounded p-2 text-center">
                <p className="text-xs text-gray-500">Holdings</p>
                <p className="font-bold text-orange-900">{report.portfolio.holdings?.length || 0}</p>
              </div>
            </div>
          )}

          {/* Performance */}
          {report.performance && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
              <div className="bg-gray-50 rounded p-2 text-center">
                <p className="text-xs text-gray-500">Total Trades</p>
                <p className="font-bold">{report.performance.total_trades}</p>
              </div>
              <div className="bg-gray-50 rounded p-2 text-center">
                <p className="text-xs text-gray-500">Win Rate</p>
                <p className="font-bold text-green-700">{report.performance.win_rate}%</p>
              </div>
              <div className="bg-gray-50 rounded p-2 text-center">
                <p className="text-xs text-gray-500">Net Profit</p>
                <p className={`font-bold ${report.performance.net_profit >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  ₹{report.performance.net_profit}
                </p>
              </div>
              <div className="bg-gray-50 rounded p-2 text-center">
                <p className="text-xs text-gray-500">ROI</p>
                <p className={`font-bold ${report.performance.roi >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {report.performance.roi}%
                </p>
              </div>
            </div>
          )}

          {/* Today's decisions */}
          {report.decisions_summary && report.decisions_summary.length > 0 && (
            <div className="mb-3">
              <h3 className="text-sm font-bold mb-1">📋 Today's Decisions</h3>
              <div className="space-y-1 max-h-48 overflow-auto">
                {report.decisions_summary.map((d, i) => (
                  <div key={i} className={`text-xs rounded p-2 ${
                    d.action === 'BUY' ? 'bg-green-50' : d.action === 'SELL' ? 'bg-red-50' : 'bg-gray-50'
                  }`}>
                    <strong>{d.action}</strong> {d.symbol} x{d.quantity} @ ₹{d.price?.toFixed(2)} —
                    {' '}{d.confidence?.toFixed(0)}% conf, {d.risk_level} risk
                    <p className="text-gray-600 italic mt-0.5">{d.reasoning}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};





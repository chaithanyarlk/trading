import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

export const EquityCurve = ({ trades, initialCapital }) => {
  const [data, setData] = useState([]);
  
  useEffect(() => {
    if (!trades || trades.length === 0) return;
    
    let cumProfit = 0;
    let portfolioValue = initialCapital;
    const chartData = [];
    
    trades.forEach((trade, idx) => {
      if (trade.status === 'EXECUTED') {
        // Simplified P&L calculation
        cumProfit += trade.entry_price * trade.quantity * (trade.action === 'BUY' ? -1 : 1);
        portfolioValue = initialCapital + cumProfit;
        
        chartData.push({
          date: new Date(trade.timestamp).toLocaleDateString(),
          value: portfolioValue,
          cumProfit
        });
      }
    });
    
    setData(chartData);
  }, [trades, initialCapital]);
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Equity Curve</h2>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#8884d8"
            fillOpacity={1}
            fill="url(#colorValue)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export const TradeDistribution = ({ metrics }) => {
  if (!metrics || metrics.total_trades === 0) return null;
  
  const data = [
    { name: 'Winning', value: metrics.winning_trades, fill: '#10b981' },
    { name: 'Losing', value: metrics.losing_trades, fill: '#ef4444' }
  ];
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Trade Distribution</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export const PortfolioAllocation = ({ holdings }) => {
  if (!holdings || holdings.length === 0) return null;
  
  const data = holdings.map(h => ({
    name: h.asset_name,
    value: h.current_value
  }));
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Portfolio Allocation</h2>
      <div className="space-y-2">
        {data.map((item, idx) => {
          const totalValue = data.reduce((sum, d) => sum + d.value, 0);
          const percentage = ((item.value / totalValue) * 100).toFixed(1);
          
          return (
            <div key={idx}>
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium">{item.name}</span>
                <span>{percentage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

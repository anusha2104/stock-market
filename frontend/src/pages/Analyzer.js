import React, { useState } from 'react';
import axios from 'axios';
import { Search, TrendingUp, TrendingDown, Loader2, BarChart3 } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { toast } from 'sonner';
import { useTheme } from '../contexts/ThemeContext';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "https://stock-market-dlbk.onrender.com";
const API = `${BACKEND_URL}/api`;

const Analyzer = () => {
  const { theme } = useTheme();
  const [symbol, setSymbol] = useState('');
  const [loading, setLoading] = useState(false);
  const [stockData, setStockData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [indicators, setIndicators] = useState(null);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const stockRes = await axios.get(`${API}/stocks/demo`);
      setStockData(stockRes.data);

      const chartRes = await axios.get(`${API}/stocks/demo/chart`);
      setChartData(chartRes.data);

      const predictionRes = await axios.get(`${API}/stocks/demo/predict`);
      setPrediction(predictionRes.data);

      const indicatorsRes = await axios.get(`${API}/stocks/demo/indicators`);
      setIndicators(indicatorsRes.data);

      toast.success("Loaded demo data successfully");
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Failed to load demo data");
    } finally {
      setLoading(false);
    }
  };


  const handleSearch = (e) => {
    e.preventDefault();
    if (symbol.trim()) {
      fetchAllData(symbol.toUpperCase());
    }
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: theme === 'dark' ? '#1e293b' : '#ffffff',
        titleColor: theme === 'dark' ? '#f8fafc' : '#0f172a',
        bodyColor: theme === 'dark' ? '#f8fafc' : '#0f172a',
        borderColor: theme === 'dark' ? '#334155' : '#e2e8f0',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        grid: {
          color: theme === 'dark' ? '#1e293b' : '#e2e8f0'
        },
        ticks: {
          color: theme === 'dark' ? '#94a3b8' : '#64748b'
        }
      },
      y: {
        grid: {
          color: theme === 'dark' ? '#1e293b' : '#e2e8f0'
        },
        ticks: {
          color: theme === 'dark' ? '#94a3b8' : '#64748b'
        }
      }
    }
  };

  const getChartData = () => {
    if (!chartData) return null;

    return {
      labels: chartData.data.map(item => item.date),
      datasets: [
        {
          label: 'Price',
          data: chartData.data.map(item => item.close),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4
        }
      ]
    };
  };

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Search Section */}
        <div className="text-center mb-8">
          <h1 
            className="text-4xl sm:text-5xl font-bold mb-4"
            style={{ fontFamily: "'Chivo', sans-serif" }}
            data-testid="analyzer-title"
          >
            Stock Analyzer
          </h1>
          <p className="text-muted-foreground mb-6">
            Enter a stock symbol to analyze price trends and predictions
          </p>

          <form onSubmit={handleSearch} className="max-w-md mx-auto">
            <div className="relative">
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="Enter stock symbol (e.g., AAPL, TSLA)"
                className="flex h-12 w-full rounded-full border border-input bg-background px-6 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                data-testid="stock-input"
              />
              <button
                type="submit"
                disabled={loading}
                className="absolute right-1 top-1 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-6 rounded-full font-medium transition-all disabled:opacity-50"
                data-testid="search-button"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Results */}
        {stockData && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Main Chart Area */}
            <div className="col-span-12 lg:col-span-8">
              {/* Price Card */}
              <div className="rounded-xl border bg-card shadow-sm p-6 mb-6" data-testid="price-card">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 
                      className="text-3xl font-bold mb-1" 
                      style={{ fontFamily: "'JetBrains Mono', monospace" }}
                      data-testid="stock-symbol"
                    >
                      {stockData.symbol}
                    </h2>
                    <p className="text-sm text-muted-foreground">{stockData.timestamp}</p>
                  </div>
                  <div className="text-right">
                    <p 
                      className="text-3xl font-bold mb-1" 
                      style={{ fontFamily: "'JetBrains Mono', monospace" }}
                      data-testid="stock-price"
                    >
                      ${stockData.price.toFixed(2)}
                    </p>
                    <div className={`flex items-center gap-1 ${stockData.change >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                      {stockData.change >= 0 ? (
                        <TrendingUp className="h-4 w-4" />
                      ) : (
                        <TrendingDown className="h-4 w-4" />
                      )}
                      <span className="font-medium" data-testid="stock-change">
                        {stockData.change >= 0 ? '+' : ''}{stockData.change.toFixed(2)} ({stockData.change_percent.toFixed(2)}%)
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  Volume: {stockData.volume.toLocaleString()}
                </div>
              </div>

              {/* Chart */}
              {chartData && (
                <div className="rounded-xl border bg-card shadow-sm p-6" data-testid="chart-container">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Price History (60 Days)
                  </h3>
                  <div style={{ height: '400px' }}>
                    <Line data={getChartData()} options={chartOptions} />
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="col-span-12 lg:col-span-4 space-y-6">
              {/* Prediction Card */}
              {prediction && (
                <div className="rounded-xl border bg-card shadow-sm p-6" data-testid="prediction-card">
                  <h3 className="text-lg font-semibold mb-4">AI Prediction</h3>
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Next Day Prediction</p>
                      <p 
                        className="text-2xl font-bold" 
                        style={{ fontFamily: "'JetBrains Mono', monospace" }}
                        data-testid="predicted-price"
                      >
                        ${prediction.predicted_price.toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Trend</p>
                      <span 
                        className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                          prediction.trend === 'bullish' 
                            ? 'bg-emerald-500/10 text-emerald-500' 
                            : prediction.trend === 'bearish'
                            ? 'bg-rose-500/10 text-rose-500'
                            : 'bg-slate-500/10 text-slate-500'
                        }`}
                        data-testid="prediction-trend"
                      >
                        {prediction.trend.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Confidence</p>
                      <span className="text-sm font-medium capitalize" data-testid="prediction-confidence">
                        {prediction.confidence}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Technical Indicators */}
              {indicators && (
                <div className="rounded-xl border bg-card shadow-sm p-6" data-testid="indicators-card">
                  <h3 className="text-lg font-semibold mb-4">Technical Indicators</h3>
                  <div className="space-y-3">
                    {indicators.sma_20 && (
                      <div className="flex justify-between" data-testid="indicator-sma20">
                        <span className="text-sm text-muted-foreground">SMA (20)</span>
                        <span className="font-medium" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                          ${indicators.sma_20.toFixed(2)}
                        </span>
                      </div>
                    )}
                    {indicators.sma_50 && (
                      <div className="flex justify-between" data-testid="indicator-sma50">
                        <span className="text-sm text-muted-foreground">SMA (50)</span>
                        <span className="font-medium" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                          ${indicators.sma_50.toFixed(2)}
                        </span>
                      </div>
                    )}
                    {indicators.ema_12 && (
                      <div className="flex justify-between" data-testid="indicator-ema12">
                        <span className="text-sm text-muted-foreground">EMA (12)</span>
                        <span className="font-medium" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                          ${indicators.ema_12.toFixed(2)}
                        </span>
                      </div>
                    )}
                    {indicators.ema_26 && (
                      <div className="flex justify-between" data-testid="indicator-ema26">
                        <span className="text-sm text-muted-foreground">EMA (26)</span>
                        <span className="font-medium" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                          ${indicators.ema_26.toFixed(2)}
                        </span>
                      </div>
                    )}
                    {indicators.rsi && (
                      <div className="flex justify-between" data-testid="indicator-rsi">
                        <span className="text-sm text-muted-foreground">RSI (14)</span>
                        <span 
                          className={`font-medium ${
                            indicators.rsi > 70 
                              ? 'text-rose-500' 
                              : indicators.rsi < 30 
                              ? 'text-emerald-500' 
                              : ''
                          }`}
                          style={{ fontFamily: "'JetBrains Mono', monospace" }}
                        >
                          {indicators.rsi.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!stockData && !loading && (
          <div className="text-center py-16" data-testid="empty-state">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
              <Search className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Search for a Stock</h3>
            <p className="text-muted-foreground">
              Enter a stock symbol above to view detailed analysis and predictions
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Analyzer;

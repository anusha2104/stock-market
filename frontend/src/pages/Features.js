import React from 'react';
import { Brain, Clock, BarChart3, Shield, TrendingUp, Zap } from 'lucide-react';

const Features = () => {
  const features = [
    {
      icon: <Brain className="h-12 w-12" />,
      title: 'AI-Based Price Prediction',
      description: 'Our advanced machine learning models use linear regression and historical data analysis to predict future stock prices. The system continuously learns from market patterns to improve accuracy over time.',
      details: [
        'Linear regression model for price forecasting',
        'Historical data analysis (60-day trends)',
        'Confidence scoring for predictions',
        'Trend identification (bullish/bearish/neutral)'
      ]
    },
    {
      icon: <Clock className="h-12 w-12" />,
      title: 'Real-Time Market Data',
      description: 'Access live stock prices and market data powered by Alpha Vantage API. Get instant updates on price changes, trading volume, and market movements.',
      details: [
        'Live price updates',
        'Real-time trading volume',
        'Intraday price changes',
        'Market open/close information'
      ]
    },
    {
      icon: <BarChart3 className="h-12 w-12" />,
      title: 'Technical Indicators',
      description: 'Comprehensive suite of technical analysis indicators to help you make informed trading decisions. All indicators are calculated using industry-standard formulas.',
      details: [
        'SMA (Simple Moving Average) - 20 & 50 day',
        'EMA (Exponential Moving Average) - 12 & 26 day',
        'RSI (Relative Strength Index) - 14 day',
        'MACD and other advanced indicators'
      ]
    },
    {
      icon: <TrendingUp className="h-12 w-12" />,
      title: 'Interactive Charts',
      description: 'Visualize stock price movements with beautiful, responsive charts. Track historical performance and identify patterns with ease.',
      details: [
        '60-day price history visualization',
        'Interactive chart tooltips',
        'Responsive design for all devices',
        'Dark/Light theme support'
      ]
    },
    {
      icon: <Zap className="h-12 w-12" />,
      title: 'Easy-to-Use Dashboard',
      description: 'Clean, intuitive interface designed for both beginners and experienced traders. Get all the information you need at a glance.',
      details: [
        'Simple stock symbol search',
        'Clear price trend indicators',
        'Organized data presentation',
        'Mobile-responsive design'
      ]
    },
    {
      icon: <Shield className="h-12 w-12" />,
      title: 'Reliable & Secure',
      description: 'Built with modern web technologies and best practices. Your data is secure and the platform is highly reliable.',
      details: [
        'FastAPI backend for performance',
        'MongoDB for data persistence',
        'Secure API integration',
        'Regular data updates'
      ]
    }
  ];

  return (
    <div className="min-h-screen py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 
            className="text-4xl sm:text-5xl font-bold mb-4"
            style={{ fontFamily: "'Chivo', sans-serif" }}
            data-testid="features-title"
          >
            Powerful Features
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Everything you need for comprehensive stock market analysis in one platform
          </p>
        </div>

        {/* Features List */}
        <div className="space-y-12">
          {features.map((feature, index) => (
            <div
              key={index}
              className={`grid grid-cols-1 lg:grid-cols-2 gap-8 items-center ${
                index % 2 === 1 ? 'lg:flex-row-reverse' : ''
              }`}
              data-testid={`feature-${index}`}
            >
              <div className={`${index % 2 === 1 ? 'lg:order-2' : ''}`}>
                <div className="rounded-xl border bg-card shadow-sm p-8">
                  <div className="text-primary mb-6">{feature.icon}</div>
                  <h2 
                    className="text-2xl sm:text-3xl font-bold mb-4"
                    style={{ fontFamily: "'Chivo', sans-serif" }}
                  >
                    {feature.title}
                  </h2>
                  <p className="text-muted-foreground mb-6">
                    {feature.description}
                  </p>
                  <ul className="space-y-2">
                    {feature.details.map((detail, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <div className="h-2 w-2 rounded-full bg-primary"></div>
                        </div>
                        <span className="text-sm">{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className={`${index % 2 === 1 ? 'lg:order-1' : ''}`}>
                <div className="relative h-80 rounded-xl overflow-hidden border bg-card/50">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 flex items-center justify-center">
                    <div className="text-primary/20">
                      {feature.icon}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <div className="rounded-2xl border bg-card shadow-lg p-12">
            <h2 
              className="text-3xl sm:text-4xl font-bold mb-4"
              style={{ fontFamily: "'Chivo', sans-serif" }}
            >
              Ready to Get Started?
            </h2>
            <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
              Start analyzing stocks with our powerful AI-driven platform today
            </p>
            <a
              href="/analyzer"
              className="inline-block bg-primary text-primary-foreground hover:bg-primary/90 h-12 px-8 py-2 rounded-full font-medium transition-all shadow-lg hover:shadow-xl hover:-translate-y-1"
              data-testid="features-cta-btn"
            >
              Try Analyzer Now
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Features;

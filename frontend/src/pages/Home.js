import React from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Brain, BarChart3, Clock, Shield, Zap } from 'lucide-react';

const Home = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Brain className="h-8 w-8" />,
      title: 'AI-Powered Predictions',
      description: 'Advanced machine learning algorithms analyze market trends to predict future stock prices with high accuracy.'
    },
    {
      icon: <Clock className="h-8 w-8" />,
      title: 'Real-Time Data',
      description: 'Get live stock prices and market data updated in real-time from Alpha Vantage API.'
    },
    {
      icon: <BarChart3 className="h-8 w-8" />,
      title: 'Technical Indicators',
      description: 'Access key technical indicators like SMA, EMA, and RSI to make informed trading decisions.'
    },
    {
      icon: <Zap className="h-8 w-8" />,
      title: 'Lightning Fast',
      description: 'Optimized performance ensures you get the data you need without any delays.'
    },
    {
      icon: <Shield className="h-8 w-8" />,
      title: 'Secure & Reliable',
      description: 'Your data is safe with enterprise-grade security and 99.9% uptime guarantee.'
    },
    {
      icon: <TrendingUp className="h-8 w-8" />,
      title: 'Trend Analysis',
      description: 'Identify bullish and bearish trends with our sophisticated analysis algorithms.'
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-20 lg:py-32 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-slate-900 dark:to-slate-800 opacity-50"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-4xl mx-auto">
            <h1 
              className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 tracking-tight"
              style={{ fontFamily: "'Chivo', sans-serif" }}
              data-testid="hero-title"
            >
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-cyan-500 dark:from-blue-400 dark:to-cyan-300">
                Smart Stock Analysis
              </span>
              <br />
              <span className="text-foreground">Powered by AI</span>
            </h1>
            
            <p className="text-lg sm:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Make informed investment decisions with real-time market data, AI-powered predictions, and comprehensive technical analysis tools.
            </p>
            
            <button
              onClick={() => navigate('/analyzer')}
              className="bg-primary text-primary-foreground hover:bg-primary/90 h-12 px-8 py-2 rounded-full font-medium transition-all shadow-lg hover:shadow-xl hover:-translate-y-1"
              data-testid="get-started-btn"
            >
              Get Started
            </button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 lg:py-24 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 
              className="text-3xl sm:text-4xl font-bold mb-4"
              style={{ fontFamily: "'Chivo', sans-serif" }}
            >
              Powerful Features
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Everything you need to analyze stocks and make better investment decisions
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 hover:-translate-y-1 transition-transform duration-300"
                data-testid={`feature-card-${index}`}
              >
                <div className="text-primary mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-2" style={{ fontFamily: "'Chivo', sans-serif" }}>
                  {feature.title}
                </h3>
                <p className="text-muted-foreground text-sm">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 lg:py-24 bg-card">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 
            className="text-3xl sm:text-4xl font-bold mb-4"
            style={{ fontFamily: "'Chivo', sans-serif" }}
          >
            Ready to Start Analyzing?
          </h2>
          <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join thousands of investors using our platform to make smarter trading decisions
          </p>
          <button
            onClick={() => navigate('/analyzer')}
            className="bg-primary text-primary-foreground hover:bg-primary/90 h-12 px-8 py-2 rounded-full font-medium transition-all shadow-lg"
            data-testid="cta-btn"
          >
            Start Analyzing Now
          </button>
        </div>
      </section>
    </div>
  );
};

export default Home;

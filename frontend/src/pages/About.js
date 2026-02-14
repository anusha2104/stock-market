import React from 'react';
import { Code, Database, Brain, Zap } from 'lucide-react';

const About = () => {
  const techStack = [
    {
      icon: <Code className="h-8 w-8" />,
      name: 'React',
      description: 'Modern frontend framework for building interactive UIs'
    },
    {
      icon: <Zap className="h-8 w-8" />,
      name: 'FastAPI',
      description: 'High-performance Python backend framework'
    },
    {
      icon: <Database className="h-8 w-8" />,
      name: 'MongoDB',
      description: 'NoSQL database for flexible data storage'
    },
    {
      icon: <Brain className="h-8 w-8" />,
      name: 'scikit-learn',
      description: 'Machine learning library for price predictions'
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
            data-testid="about-title"
          >
            About Stock Market Analyzer
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Empowering investors with AI-driven insights and real-time market data
          </p>
        </div>

        {/* Mission Section */}
        <div className="mb-16">
          <div className="rounded-xl border bg-card shadow-sm p-8 lg:p-12">
            <h2 
              className="text-3xl font-bold mb-6"
              style={{ fontFamily: "'Chivo', sans-serif" }}
            >
              Our Mission
            </h2>
            <div className="space-y-4 text-muted-foreground">
              <p>
                Stock Market Analyzer was created as a college major project to demonstrate the power of combining modern web technologies with machine learning for financial analysis. Our goal is to make stock market analysis accessible to everyone, from beginners to experienced traders.
              </p>
              <p>
                By leveraging real-time data from Alpha Vantage API and advanced machine learning algorithms, we provide accurate price predictions and comprehensive technical analysis. The platform is designed to be intuitive, fast, and reliable.
              </p>
              <p>
                This project showcases the integration of multiple cutting-edge technologies including React for the frontend, FastAPI for the backend, MongoDB for data persistence, and scikit-learn for machine learning predictions. It demonstrates best practices in full-stack development and data science.
              </p>
            </div>
          </div>
        </div>

        {/* Tech Stack */}
        <div className="mb-16">
          <h2 
            className="text-3xl font-bold mb-8 text-center"
            style={{ fontFamily: "'Chivo', sans-serif" }}
          >
            Technology Stack
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {techStack.map((tech, index) => (
              <div
                key={index}
                className="rounded-xl border bg-card shadow-sm p-6 text-center hover:-translate-y-1 transition-transform duration-300"
                data-testid={`tech-${index}`}
              >
                <div className="text-primary mb-4 flex justify-center">{tech.icon}</div>
                <h3 className="text-xl font-semibold mb-2" style={{ fontFamily: "'Chivo', sans-serif" }}>
                  {tech.name}
                </h3>
                <p className="text-sm text-muted-foreground">{tech.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Key Features Overview */}
        <div className="mb-16">
          <div className="rounded-xl border bg-card shadow-sm p-8 lg:p-12">
            <h2 
              className="text-3xl font-bold mb-6"
              style={{ fontFamily: "'Chivo', sans-serif" }}
            >
              What We Offer
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-xl font-semibold mb-3">For Investors</h3>
                <ul className="space-y-2 text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>Real-time stock price data</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>AI-powered price predictions</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>Comprehensive technical indicators</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>Interactive price charts</span>
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-3">For Learners</h3>
                <ul className="space-y-2 text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>Educational tool for finance students</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>Demonstrates ML in finance</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>Full-stack development showcase</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>Open architecture for extensions</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Future Enhancements */}
        <div>
          <div className="rounded-xl border bg-card shadow-sm p-8 lg:p-12">
            <h2 
              className="text-3xl font-bold mb-6"
              style={{ fontFamily: "'Chivo', sans-serif" }}
            >
              Future Enhancements
            </h2>
            <p className="text-muted-foreground mb-4">
              This project is designed to be extensible. Potential future improvements include:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ul className="space-y-2 text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-1">✓</span>
                  <span>Advanced ML models (LSTM, Prophet)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-1">✓</span>
                  <span>Portfolio tracking and management</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-1">✓</span>
                  <span>News sentiment analysis</span>
                </li>
              </ul>
              <ul className="space-y-2 text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-1">✓</span>
                  <span>User authentication and watchlists</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-1">✓</span>
                  <span>Price alerts and notifications</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-1">✓</span>
                  <span>Multi-stock comparison tools</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;

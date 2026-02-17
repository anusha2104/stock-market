import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Mail, Github, Linkedin } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="border-t border-border bg-card">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <Link to="/" className="flex items-center gap-2 mb-4">
              <TrendingUp className="h-6 w-6 text-primary" />
              <span className="font-bold text-lg" style={{ fontFamily: "'Chivo', sans-serif" }}>
                Stock Market Analyzer
              </span>
            </Link>
            <p className="text-sm text-muted-foreground max-w-md">
              Advanced stock market analysis powered by AI. Get real-time data, predictions, and technical indicators to make informed investment decisions.
            </p>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/analyzer" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                  Analyzer
                </Link>
              </li>
              <li>
                <Link to="/features" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                  Features
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                  About
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Connect</h3>
            <div className="flex gap-4">
              <a 
                href="mailto:contact@stockanalyzer.com" 
                className="p-2 rounded-full hover:bg-accent transition-colors"
                aria-label="Email"
              >
                <Mail className="h-5 w-5" />
              </a>
              <a 
                href="https://github.com/anusha2104" 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-2 rounded-full hover:bg-accent transition-colors"
                aria-label="GitHub"
              >
                <Github className="h-5 w-5" />
              </a>
              <a 
                href="https://www.linkedin.com/in/anusha-mittal-462543312/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-2 rounded-full hover:bg-accent transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-border text-center">
          <p className="text-sm text-muted-foreground">
            
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

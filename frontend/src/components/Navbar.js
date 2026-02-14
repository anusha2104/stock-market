import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Moon, Sun, TrendingUp } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const Navbar = () => {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-md bg-background/80 border-b border-border/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link 
            to="/" 
            className="flex items-center gap-2 font-bold text-xl"
            style={{ fontFamily: "'Chivo', sans-serif" }}
            data-testid="navbar-logo"
          >
            <TrendingUp className="h-6 w-6 text-primary" />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-cyan-500 dark:from-blue-400 dark:to-cyan-300">
              Stock Analyzer
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link
              to="/"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                isActive('/') ? 'text-primary' : 'text-foreground/80'
              }`}
              data-testid="nav-home"
            >
              Home
            </Link>
            <Link
              to="/analyzer"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                isActive('/analyzer') ? 'text-primary' : 'text-foreground/80'
              }`}
              data-testid="nav-analyzer"
            >
              Analyzer
            </Link>
            <Link
              to="/features"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                isActive('/features') ? 'text-primary' : 'text-foreground/80'
              }`}
              data-testid="nav-features"
            >
              Features
            </Link>
            <Link
              to="/about"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                isActive('/about') ? 'text-primary' : 'text-foreground/80'
              }`}
              data-testid="nav-about"
            >
              About
            </Link>
            <Link
              to="/contact"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                isActive('/contact') ? 'text-primary' : 'text-foreground/80'
              }`}
              data-testid="nav-contact"
            >
              Contact
            </Link>
          </div>

          <button
            onClick={toggleTheme}
            className="p-2 rounded-full hover:bg-accent transition-colors"
            aria-label="Toggle theme"
            data-testid="theme-toggle"
          >
            {theme === 'light' ? (
              <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

/**
 * js/api.js — Centralised API client
 *
 * All backend communication goes through this module.
 * Provides typed request wrappers with timeout and error normalisation.
 */

const API = (() => {

  const BASE_URL = 'http://127.0.0.1:5000/api';
  const TIMEOUT  = 30_000; // 30s — yfinance can be slow

  /**
   * Core fetch wrapper with timeout and unified error handling.
   * @param {string} endpoint — relative path, e.g. '/predict?ticker=TCS.NS'
   * @returns {Promise<any>} — resolved data payload or thrown Error
   */
  async function request(endpoint) {
    const controller = new AbortController();
    const timer      = setTimeout(() => controller.abort(), TIMEOUT);

    try {
      const res = await fetch(`${BASE_URL}${endpoint}`, {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' },
      });

      const json = await res.json();

      if (!res.ok || json.status === 'error') {
        throw new Error(json.message || `HTTP ${res.status}`);
      }

      return json.data;

    } catch (err) {
      if (err.name === 'AbortError') {
        throw new Error('Request timed out. Yahoo Finance may be slow — please retry.');
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }

  return {
    /**
     * Run full prediction pipeline for a ticker.
     * @param {string} ticker — e.g. 'RELIANCE.NS'
     * @param {string} period — '1mo' | '3mo' | '6mo' | '1y'
     */
    predict(ticker, period = '3mo') {
      return request(`/predict?ticker=${encodeURIComponent(ticker)}&period=${period}`);
    },

    /** Trending stocks snapshot list. */
    trending() {
      return request('/stocks/trending');
    },

    /** Top performing stocks snapshot list. */
    topStocks() {
      return request('/stocks/top');
    },

    /**
     * Quick quote lookup.
     * @param {string} ticker
     */
    quickQuote(ticker) {
      return request(`/stocks/search?q=${encodeURIComponent(ticker)}`);
    },
  };
})();
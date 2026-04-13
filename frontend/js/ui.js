/**
 * js/ui.js — DOM rendering helpers
 *
 * All DOM manipulation lives here. Components receive data objects
 * and return/mutate DOM nodes. No API calls in this file.
 */

const UI = (() => {

  // ── Loading state management ─────────────────────────────────────────────

  const LOADING_MESSAGES = [
    'Connecting to Yahoo Finance…',
    'Downloading OHLCV data…',
    'Computing technical indicators…',
    'Running signal analysis…',
    'Generating price forecast…',
    'Calculating confidence score…',
    'Rendering results…',
  ];

  let loadingTimer = null;
  let msgIndex     = 0;

  function showLoading() {
    const panel    = document.getElementById('analysisPanel');
    const loading  = document.getElementById('analysisLoading');
    const result   = document.getElementById('analysisResult');
    const error    = document.getElementById('analysisError');

    panel.style.display  = 'block';
    loading.style.display = 'flex';
    result.style.display  = 'none';
    error.style.display   = 'none';

    // Cycle loading messages
    msgIndex    = 0;
    clearInterval(loadingTimer);
    _setLoadingMsg(LOADING_MESSAGES[0]);
    loadingTimer = setInterval(() => {
      msgIndex = (msgIndex + 1) % LOADING_MESSAGES.length;
      _setLoadingMsg(LOADING_MESSAGES[msgIndex]);
    }, 1800);

    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function hideLoading() {
    clearInterval(loadingTimer);
    document.getElementById('analysisLoading').style.display = 'none';
  }

  function _setLoadingMsg(msg) {
    const el = document.getElementById('loadingMsg');
    if (el) el.textContent = msg;
  }

  // ── Error state ──────────────────────────────────────────────────────────

  function showError(title, message) {
    hideLoading();
    const panel  = document.getElementById('analysisPanel');
    const error  = document.getElementById('analysisError');
    const result = document.getElementById('analysisResult');

    panel.style.display  = 'block';
    error.style.display  = 'flex';
    result.style.display = 'none';

    document.getElementById('errorTitle').textContent = title || 'Analysis Failed';
    document.getElementById('errorMsg').textContent   = message || 'An unexpected error occurred.';
  }

  // ── Main result render ───────────────────────────────────────────────────

  function renderAnalysis(data) {
    hideLoading();

    const result = document.getElementById('analysisResult');
    const error  = document.getElementById('analysisError');
    result.style.display = 'block';
    error.style.display  = 'none';
    result.classList.add('panel-reveal');

    const { ticker, meta, current, predicted, trend, confidence,
            change_pct, indicators, chart, signals } = data;

    // ── Stock header ───────────────────────────────────────────────────
    document.getElementById('resultTicker').textContent       = ticker;
    document.getElementById('resultName').textContent         = meta.name;
    document.getElementById('resultSector').textContent       = meta.sector;
    document.getElementById('resultExchange').textContent     = meta.exchange;
    document.getElementById('resultMcap').textContent         = meta.market_cap;
    document.getElementById('resultCurrentPrice').textContent = `₹${current.toLocaleString('en-IN', {minimumFractionDigits:2})}`;
    document.getElementById('resultPredictedPrice').textContent = `₹${predicted.toLocaleString('en-IN', {minimumFractionDigits:2})}`;

    const trendArrow = document.getElementById('trendArrow');
    trendArrow.textContent = trend === 'BULLISH' ? '↗' :
                             trend === 'BEARISH' ? '↘' : '→';
    trendArrow.className   = `price-arrow ${trend === 'BEARISH' ? 'bearish' : ''}`;

    // ── KPI Row ────────────────────────────────────────────────────────
    const trendEl = document.getElementById('kpiTrendVal');
    trendEl.textContent = trend;
    trendEl.className   = `kpi-val trend-${trend.toLowerCase()}`;

    const changeEl = document.getElementById('kpiChange');
    changeEl.textContent = `${change_pct > 0 ? '+' : ''}${change_pct}%`;
    changeEl.style.color = change_pct >= 0 ? 'var(--green)' : 'var(--red)';

    document.getElementById('kpiVol').textContent = `${indicators.volatility_ann?.toFixed(1) ?? '—'}%`;
    document.getElementById('kpiRsi').textContent = indicators.rsi14?.toFixed(1) ?? '—';
    document.getElementById('kpiPE').textContent  = meta.pe_ratio > 0 ? meta.pe_ratio.toFixed(1) : 'N/A';

    // ── Confidence gauge ───────────────────────────────────────────────
    Charts.renderGauge(confidence);

    // ── Price chart ────────────────────────────────────────────────────
    Charts.renderPriceChart(chart, indicators, predicted, trend);

    // ── RSI + MACD ─────────────────────────────────────────────────────
    if (indicators.series) {
      const rsiSeries = indicators.series.rsi14 || [];
      Charts.renderRSI(chart.labels, rsiSeries);
      Charts.renderMACD(
        chart.labels,
        indicators.series.macd,
        indicators.series.macd_signal
      );
    }

    // ── Indicators grid ────────────────────────────────────────────────
    renderIndicatorGrid(indicators, meta);

    // ── Signal breakdown ───────────────────────────────────────────────
    renderSignals(signals);

    // ── Key stats ──────────────────────────────────────────────────────
    renderStats(meta, indicators);
  }

  // ── Indicator Grid ───────────────────────────────────────────────────────

  function renderIndicatorGrid(ind, meta) {
    const grid = document.getElementById('indicatorGrid');
    grid.innerHTML = '';

    const items = [
      { label: 'SMA 20',    value: fmtPrice(ind.sma20),   sub: 'Simple MA (20d)' },
      { label: 'SMA 50',    value: fmtPrice(ind.sma50),   sub: 'Simple MA (50d)' },
      { label: 'EMA 12',    value: fmtPrice(ind.ema12),   sub: 'Exponential MA (12d)' },
      { label: 'EMA 26',    value: fmtPrice(ind.ema26),   sub: 'Exponential MA (26d)' },
      { label: 'RSI 14',    value: ind.rsi14?.toFixed(1) ?? '—',
        sub: rsiLabel(ind.rsi14) },
      { label: 'MACD',      value: ind.macd?.toFixed(3)  ?? '—', sub: 'MACD Line' },
      { label: 'BB Upper',  value: fmtPrice(ind.bb_upper), sub: 'Bollinger Upper (2σ)' },
      { label: 'BB Lower',  value: fmtPrice(ind.bb_lower), sub: 'Bollinger Lower (2σ)' },
      { label: 'ATR 14',    value: fmtPrice(ind.atr14),   sub: 'Avg True Range (14d)' },
      { label: 'Vol (Ann)', value: ind.volatility_ann ? `${ind.volatility_ann.toFixed(2)}%` : '—',
        sub: 'Annualised Volatility' },
      { label: 'Return 7d', value: ind.return_7d  != null ? `${ind.return_7d.toFixed(2)}%`  : '—', sub: '7-Day Return' },
      { label: 'Return 30d',value: ind.return_30d != null ? `${ind.return_30d.toFixed(2)}%` : '—', sub: '30-Day Return' },
    ];

    items.forEach((item, i) => {
      const div = document.createElement('div');
      div.className = 'indicator-item animate-in';
      div.style.animationDelay = `${i * 0.04}s`;
      div.innerHTML = `
        <div class="indicator-item__label">${item.label}</div>
        <div class="indicator-item__value">${item.value}</div>
        <div class="indicator-item__sub">${item.sub}</div>
      `;
      grid.appendChild(div);
    });
  }

  // ── Signal Breakdown ─────────────────────────────────────────────────────

  function renderSignals(signals) {
    const list = document.getElementById('signalsList');
    list.innerHTML = '';

    if (!signals || !signals.length) {
      list.innerHTML = '<p style="color:var(--text-muted);padding:16px">No signal data available.</p>';
      return;
    }

    signals.forEach((sig, i) => {
      const item = document.createElement('div');
      item.className = 'signal-item animate-in';
      item.style.animationDelay = `${i * 0.05}s`;

      const score    = sig.score;
      const pct      = Math.abs(score) * 100;
      const fillClass = score > 0.1 ? 'positive' : score < -0.1 ? 'negative' : 'neutral';
      const badgeCls  = badgeClass(sig.label);

      item.innerHTML = `
        <div class="signal-item__name">${sig.name}</div>
        <div class="signal-item__bar-wrap">
          <div class="signal-bar-track">
            <div class="signal-bar-fill ${fillClass}"
                 style="width:${pct.toFixed(1)}%"></div>
          </div>
          <div class="signal-item__desc">${sig.desc}</div>
        </div>
        <div class="signal-badge ${badgeCls}">${sig.label}</div>
      `;

      list.appendChild(item);
    });
  }

  // ── Key Statistics ───────────────────────────────────────────────────────

  function renderStats(meta, ind) {
    const grid = document.getElementById('statsGrid');
    grid.innerHTML = '';

    const stats = [
      { label: '52-Week High',   value: meta.week_high !== 'N/A' ? `₹${meta.week_high}` : 'N/A' },
      { label: '52-Week Low',    value: meta.week_low  !== 'N/A' ? `₹${meta.week_low}`  : 'N/A' },
      { label: 'Market Cap',     value: meta.market_cap },
      { label: 'P/E Ratio',      value: meta.pe_ratio > 0 ? meta.pe_ratio.toFixed(2) : 'N/A' },
      { label: 'Currency',       value: meta.currency },
      { label: 'Exchange',       value: meta.exchange },
      { label: 'Sector',         value: meta.sector },
      { label: 'Industry',       value: meta.industry },
      { label: 'RSI (14)',       value: ind.rsi14?.toFixed(2) ?? 'N/A' },
      { label: 'MACD Histogram', value: ind.macd_hist?.toFixed(4) ?? 'N/A' },
      { label: '14-Day Return',  value: ind.return_14d != null ? `${ind.return_14d.toFixed(2)}%` : 'N/A' },
      { label: 'ATR (14)',       value: fmtPrice(ind.atr14) },
    ];

    stats.forEach(s => {
      const div = document.createElement('div');
      div.className = 'stat-item';
      div.innerHTML = `
        <div class="stat-item__label">${s.label}</div>
        <div class="stat-item__value">${s.value ?? '—'}</div>
      `;
      grid.appendChild(div);
    });
  }

  // ── Stock Cards ──────────────────────────────────────────────────────────

  function renderStockCards(stocks, gridId) {
    const grid = document.getElementById(gridId);
    grid.innerHTML = '';

    if (!stocks || !stocks.length) {
      grid.innerHTML = '<p style="color:var(--text-muted);padding:16px">Could not load stock data.</p>';
      return;
    }

    stocks.forEach((stock, i) => {
      const card = document.createElement('div');
      card.className = 'stock-card animate-in';
      card.style.animationDelay = `${i * 0.05}s`;

      const isUp     = stock.direction === 'up';
      const sparkId  = `spark-${gridId}-${i}`;
      const changeSign = isUp ? '+' : '';
      const chgColor = isUp ? 'var(--green)' : 'var(--red)';

      card.innerHTML = `
        <div class="stock-card__ticker">${stock.ticker}</div>
        <div class="stock-card__name">${_truncate(stock.name, 24)}</div>
        <div class="stock-card__price-row">
          <div class="stock-card__price">${stock.currency === 'INR' ? '₹' : '$'}${stock.price.toLocaleString('en-IN', {minimumFractionDigits:2})}</div>
          <div class="stock-card__change ${isUp ? 'up' : 'down'}">${changeSign}${stock.change_pct}%</div>
        </div>
        <canvas id="${sparkId}" class="stock-card__sparkline"></canvas>
      `;

      card.onclick = () => window.analyzeStock(stock.ticker);
      grid.appendChild(card);

      // Render sparkline after element is in DOM
      requestAnimationFrame(() => {
        Charts.renderSparkline(sparkId, stock.sparkline || [], isUp);
      });
    });
  }

  // ── Helpers ──────────────────────────────────────────────────────────────

  function fmtPrice(v) {
    if (v == null || isNaN(v)) return '—';
    return `₹${parseFloat(v).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  }

  function rsiLabel(rsi) {
    if (!rsi) return '—';
    if (rsi < 30) return '🟢 Oversold';
    if (rsi > 70) return '🔴 Overbought';
    return '⚪ Neutral';
  }

  function badgeClass(label) {
    const map = {
      'STRONG BUY' : 'badge-strong-buy',
      'BUY'        : 'badge-buy',
      'NEUTRAL'    : 'badge-neutral',
      'SELL'       : 'badge-sell',
      'STRONG SELL': 'badge-strong-sell',
    };
    return map[label] || 'badge-neutral';
  }

  function _truncate(str, n) {
    return str && str.length > n ? str.slice(0, n - 1) + '…' : str;
  }

  // ── Public ───────────────────────────────────────────────────────────────
  return {
    showLoading,
    hideLoading,
    showError,
    renderAnalysis,
    renderStockCards,
  };

})();
/**
 * js/charts.js — Chart rendering module
 *
 * Manages all Chart.js instances.
 * Each chart is stored and destroyed before re-creating to prevent memory leaks.
 */

const Charts = (() => {

  // ── Stored instances ─────────────────────────────────────────────────────
  let priceChartInst  = null;
  let gaugeChartInst  = null;
  let rsiChartInst    = null;
  let macdChartInst   = null;
  const sparklines    = {};

  // ── Shared Chart.js defaults ─────────────────────────────────────────────
  Chart.defaults.font.family    = "'DM Mono', monospace";
  Chart.defaults.font.size      = 11;
  Chart.defaults.color          = '#4a6377';
  Chart.defaults.borderColor    = '#1e2d4280';

  const GRID = {
    color      : '#1e2d4240',
    drawBorder : false,
  };

  const TICK = { color: '#4a6377', maxTicksLimit: 6 };

  // ── Colour helpers ───────────────────────────────────────────────────────
  function hex(cssVar) {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(cssVar).trim();
  }

  function gradient(ctx, colorStart, colorEnd) {
    const g = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    g.addColorStop(0, colorStart);
    g.addColorStop(1, colorEnd);
    return g;
  }

  // ── Destroy helper ───────────────────────────────────────────────────────
  function destroy(instance) {
    if (instance) { try { instance.destroy(); } catch (_) {} }
    return null;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  PRICE CHART
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Render main price chart with:
   *   - Candlestick-style close line
   *   - SMA20 / EMA12 overlays
   *   - Bollinger Band fill
   *   - Predicted price horizontal annotation
   *
   * @param {object} chart        — chart data from API (labels, close, ...)
   * @param {object} indicators   — indicator scalars + series
   * @param {number} predictedPrice
   * @param {string} trend        — 'BULLISH' | 'BEARISH' | 'NEUTRAL'
   */
  function renderPriceChart(chart, indicators, predictedPrice, trend) {
    priceChartInst = destroy(priceChartInst);
    const ctx = document.getElementById('priceChart').getContext('2d');

    const closeColor = trend === 'BULLISH' ? '#00e5a0' :
                       trend === 'BEARISH' ? '#ff4d6a' : '#00d4ff';

    const fillColor  = trend === 'BULLISH' ? 'rgba(0,229,160,0.08)' :
                       trend === 'BEARISH' ? 'rgba(255,77,106,0.08)' :
                                             'rgba(0,212,255,0.08)';

    // We may have more series data than labels (series is last 60)
    const labels = chart.labels;
    const n      = labels.length;
    const series = indicators.series || {};

    // Pad shorter series with nulls at the beginning
    function alignSeries(arr) {
      if (!arr || !arr.length) return Array(n).fill(null);
      if (arr.length >= n) return arr.slice(-n);
      return [...Array(n - arr.length).fill(null), ...arr];
    }

    const datasets = [
      {
        label      : 'Close',
        data       : chart.close,
        borderColor: closeColor,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        fill       : true,
        backgroundColor: gradient(ctx, fillColor, 'rgba(0,0,0,0)'),
        tension    : 0.3,
        order      : 1,
      },
      {
        label      : 'SMA 20',
        data       : alignSeries(series.sma20),
        borderColor: 'rgba(167,139,250,0.7)',
        borderWidth: 1.5,
        borderDash : [4, 3],
        pointRadius: 0,
        fill       : false,
        tension    : 0.3,
        order      : 2,
      },
      {
        label      : 'EMA 12',
        data       : alignSeries(series.ema12),
        borderColor: 'rgba(245,200,66,0.7)',
        borderWidth: 1.5,
        pointRadius: 0,
        fill       : false,
        tension    : 0.3,
        order      : 3,
      },
      {
        label      : 'BB Upper',
        data       : alignSeries(series.bb_upper),
        borderColor: 'rgba(0,212,255,0.25)',
        borderWidth: 1,
        borderDash : [2, 2],
        pointRadius: 0,
        fill       : '+1',
        backgroundColor: 'rgba(0,212,255,0.04)',
        tension    : 0.3,
        order      : 4,
      },
      {
        label      : 'BB Lower',
        data       : alignSeries(series.bb_lower),
        borderColor: 'rgba(0,212,255,0.25)',
        borderWidth: 1,
        borderDash : [2, 2],
        pointRadius: 0,
        fill       : false,
        tension    : 0.3,
        order      : 4,
      },
    ];

    priceChartInst = new Chart(ctx, {
      type   : 'line',
      data   : { labels, datasets },
      options: {
        responsive       : true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            display : true,
            position: 'top',
            align   : 'end',
            labels  : {
              boxWidth   : 12,
              boxHeight  : 2,
              padding    : 14,
              color      : '#8fa8c0',
              font       : { size: 10 },
            },
          },
          annotation: {
            annotations: {
              predictLine: {
                type       : 'line',
                yMin       : predictedPrice,
                yMax       : predictedPrice,
                borderColor: 'rgba(0,229,160,0.6)',
                borderWidth: 1.5,
                borderDash : [6, 3],
                label: {
                  display   : true,
                  content   : `Forecast ₹${predictedPrice}`,
                  position  : 'end',
                  color     : '#00e5a0',
                  font      : { size: 10, family: "'DM Mono', monospace" },
                  backgroundColor: 'rgba(0,229,160,0.12)',
                  padding   : 4,
                  borderRadius: 4,
                },
              },
            },
          },
          tooltip: {
            backgroundColor: 'rgba(13,20,32,0.95)',
            borderColor    : '#1e2d4280',
            borderWidth    : 1,
            titleColor     : '#f0f4f8',
            bodyColor      : '#8fa8c0',
            padding        : 12,
            callbacks: {
              label(ctx) {
                const v = ctx.parsed.y;
                return v === null ? '' : ` ${ctx.dataset.label}: ₹${v.toFixed(2)}`;
              },
            },
          },
        },
        scales: {
          x: {
            grid : GRID,
            ticks: { ...TICK, maxTicksLimit: 8,
              callback(val, idx) {
                const lbl = this.getLabelForValue(val);
                return lbl ? lbl.slice(5) : ''; // show MM-DD only
              },
            },
          },
          y: {
            grid    : GRID,
            ticks   : TICK,
            position: 'right',
          },
        },
      },
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  GAUGE CHART
  // ═══════════════════════════════════════════════════════════════════════════

  function renderGauge(confidence) {
    gaugeChartInst = destroy(gaugeChartInst);
    const ctx = document.getElementById('gaugeChart').getContext('2d');

    const angle    = (confidence / 100) * Math.PI;
    const filled   = confidence;
    const empty    = 100 - confidence;

    // Colour by confidence band
    const fillColor = confidence >= 65 ? '#00e5a0' :
                      confidence >= 45 ? '#f5c842' : '#ff4d6a';

    gaugeChartInst = new Chart(ctx, {
      type: 'doughnut',
      data: {
        datasets: [{
          data           : [filled, empty, 100],
          backgroundColor: [fillColor, '#1e2d42', 'transparent'],
          borderWidth    : 0,
          circumference  : 180,
          rotation       : 270,
        }],
      },
      options: {
        responsive         : false,
        cutout             : '72%',
        plugins: {
          legend : { display: false },
          tooltip: { enabled: false },
        },
      },
    });

    // Update numeric label
    document.getElementById('gaugeValue').textContent = confidence;
    document.getElementById('kpiConfidence').textContent = `${confidence}%`;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  RSI CHART
  // ═══════════════════════════════════════════════════════════════════════════

  function renderRSI(labels, rsiSeries) {
    rsiChartInst = destroy(rsiChartInst);
    const ctx    = document.getElementById('rsiChart').getContext('2d');
    const n      = Math.min(labels.length, rsiSeries.length);

    rsiChartInst = new Chart(ctx, {
      type: 'line',
      data: {
        labels  : labels.slice(-n),
        datasets: [{
          label      : 'RSI 14',
          data       : rsiSeries,
          borderColor: '#a78bfa',
          borderWidth: 2,
          pointRadius: 0,
          fill       : false,
          tension    : 0.4,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend : { display: false },
          tooltip: {
            backgroundColor: 'rgba(13,20,32,0.95)',
            borderColor    : '#1e2d4280',
            borderWidth    : 1,
            bodyColor      : '#8fa8c0',
          },
          annotation: {
            annotations: {
              ob : { type: 'line', yMin: 70, yMax: 70,
                     borderColor: 'rgba(255,77,106,0.4)', borderWidth: 1, borderDash: [3,3] },
              os : { type: 'line', yMin: 30, yMax: 30,
                     borderColor: 'rgba(0,229,160,0.4)', borderWidth: 1, borderDash: [3,3] },
              mid: { type: 'line', yMin: 50, yMax: 50,
                     borderColor: 'rgba(255,255,255,0.08)', borderWidth: 1 },
            },
          },
        },
        scales: {
          x: { grid: GRID, ticks: { ...TICK, maxTicksLimit: 5,
            callback(v) { const l = this.getLabelForValue(v); return l ? l.slice(5) : ''; } } },
          y: { grid: GRID, ticks: TICK, min: 0, max: 100, position: 'right' },
        },
      },
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  MACD CHART
  // ═══════════════════════════════════════════════════════════════════════════

  function renderMACD(labels, macdSeries, signalSeries) {
    macdChartInst = destroy(macdChartInst);
    const ctx     = document.getElementById('macdChart').getContext('2d');
    const n       = Math.min(labels.length, (macdSeries || []).length);

    macdChartInst = new Chart(ctx, {
      type: 'line',
      data: {
        labels  : labels.slice(-n),
        datasets: [
          {
            label      : 'MACD',
            data       : (macdSeries   || []).slice(-n),
            borderColor: '#00d4ff',
            borderWidth: 2,
            pointRadius: 0,
            fill       : false,
            tension    : 0.4,
          },
          {
            label      : 'Signal',
            data       : (signalSeries || []).slice(-n),
            borderColor: '#f5c842',
            borderWidth: 2,
            borderDash : [4, 3],
            pointRadius: 0,
            fill       : false,
            tension    : 0.4,
          },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: 'top', align: 'end',
            labels: { boxWidth: 12, boxHeight: 2, padding: 12,
                      color: '#8fa8c0', font: { size: 10 } } },
          tooltip: {
            backgroundColor: 'rgba(13,20,32,0.95)',
            borderColor    : '#1e2d4280',
            borderWidth    : 1,
            bodyColor      : '#8fa8c0',
          },
          annotation: {
            annotations: {
              zero: { type: 'line', yMin: 0, yMax: 0,
                      borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 },
            },
          },
        },
        scales: {
          x: { grid: GRID, ticks: { ...TICK, maxTicksLimit: 5,
            callback(v) { const l = this.getLabelForValue(v); return l ? l.slice(5) : ''; } } },
          y: { grid: GRID, ticks: TICK, position: 'right' },
        },
      },
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  SPARKLINES (stock cards)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * @param {string} canvasId
   * @param {number[]} data — normalised 0-100 values
   * @param {boolean} isUp
   */
  function renderSparkline(canvasId, data, isUp) {
    if (sparklines[canvasId]) {
      try { sparklines[canvasId].destroy(); } catch (_) {}
    }

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    canvas.style.height = "40px";
    canvas.style.maxHeight = "40px";
    const ctx   = canvas.getContext('2d');
    const color = isUp ? '#00e5a0' : '#ff4d6a';
    const fill  = isUp ? 'rgba(0,229,160,0.15)' : 'rgba(255,77,106,0.15)';

    sparklines[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels  : data.map((_, i) => i),
        datasets: [{
          data           : data,
          borderColor    : color,
          borderWidth    : 2,
          pointRadius    : 0,
          fill           : true,
          backgroundColor: fill,
          tension        : 0.4,
        }],
      },
      options: {
        responsive        : true,
        maintainAspectRatio: false,
        layout: {
            padding: 0
        },
        animation         : false,
        plugins: {
          legend : { display: false },
          tooltip: { enabled: false },
          annotation: { annotations: {} },
        },
        scales: {
          x: { display: false },
          y: { 
            display: false,
            },
        },
      },
    });
  }

  // ── Public API ────────────────────────────────────────────────────────────
  return {
    renderPriceChart,
    renderGauge,
    renderRSI,
    renderMACD,
    renderSparkline,
  };

})();
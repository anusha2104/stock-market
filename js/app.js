/**
 * js/app.js — Application orchestrator
 *
 * Wires up events, manages application state, and coordinates
 * API → UI rendering pipeline.
 */

(function () {
  'use strict';

  // ── State ─────────────────────────────────────────────────────────────────
  let currentTicker = null;
  let currentPeriod = '3mo';

  // ── DOM References ────────────────────────────────────────────────────────
  const searchInput = document.getElementById('searchInput');
  const searchBtn   = document.getElementById('searchBtn');

  // ── Boot ──────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    bindSearchEvents();
    loadMarketTime();
    loadStockLists();
    drawHeroBg();
    setInterval(loadMarketTime, 60_000);
  });

  // ═══════════════════════════════════════════════════════════════════════════
  //  GLOBAL — called from inline onclick attributes in HTML
  // ═══════════════════════════════════════════════════════════════════════════

  window.analyzeStock = function (ticker) {
    searchInput.value = ticker;
    runAnalysis(ticker, currentPeriod);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => {
      document.getElementById('mainContent').scrollIntoView({ behavior: 'smooth' });
    }, 200);
  };

  window.retryAnalysis = function () {
    if (currentTicker) runAnalysis(currentTicker, currentPeriod);
  };

  window.changePeriod = function (period, btn) {
    currentPeriod = period;
    document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    if (currentTicker) runAnalysis(currentTicker, period);
  };

  // ═══════════════════════════════════════════════════════════════════════════
  //  SEARCH
  // ═══════════════════════════════════════════════════════════════════════════

  function bindSearchEvents() {
    searchBtn.addEventListener('click', () => {
      const t = searchInput.value.trim().toUpperCase();
      if (t) runAnalysis(t, currentPeriod);
    });

    searchInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        const t = searchInput.value.trim().toUpperCase();
        if (t) runAnalysis(t, currentPeriod);
      }
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  ANALYSIS PIPELINE
  // ═══════════════════════════════════════════════════════════════════════════

  async function runAnalysis(ticker, period) {
    currentTicker = ticker;
    currentPeriod = period;

    UI.showLoading();

    try {
      const data = await API.predict(ticker, period);
      
      if (!data || data.error) {
        alert("Invalid stock ticker 😅 Try RELIANCE.NS or TCS.NS");
        return;
      }
      
      UI.renderAnalysis(data);
    } catch (err) {
      console.error('[runAnalysis]', err);
      UI.showError(
        'Analysis Failed',
        err.message || 'Unable to fetch data. Check your ticker symbol and try again.'
      );
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  STOCK LISTS
  // ═══════════════════════════════════════════════════════════════════════════

  async function loadStockLists() {
    try {
      const [trendingData, topData] = await Promise.allSettled([
        API.trending(),
        API.topStocks(),
      ]);

      if (trendingData.status === 'fulfilled') {
        UI.renderStockCards(trendingData.value.stocks, 'trendingGrid');
      } else {
        document.getElementById('trendingGrid').innerHTML =
          '<p style="color:var(--text-muted);grid-column:1/-1;padding:16px">Could not load trending stocks.</p>';
      }

      if (topData.status === 'fulfilled') {
        UI.renderStockCards(topData.value.stocks, 'topGrid');
      } else {
        document.getElementById('topGrid').innerHTML =
          '<p style="color:var(--text-muted);grid-column:1/-1;padding:16px">Could not load top stocks.</p>';
      }
    } catch (err) {
      console.error('[loadStockLists]', err);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  //  MARKET TIME
  // ═══════════════════════════════════════════════════════════════════════════

  function loadMarketTime() {
    const now  = new Date();
    // IST offset
    const ist  = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
    const h    = ist.getHours();
    const m    = ist.getMinutes();
    const day  = ist.getDay(); // 0=Sun

    const isWeekday = day >= 1 && day <= 5;
    const isOpen    = isWeekday && (h > 9 || (h === 9 && m >= 15)) && h < 15;

    const dot   = document.getElementById('marketDot');
    const label = document.getElementById('marketLabel');

    if (dot) {
      dot.style.background = isOpen ? 'var(--green)' : '#4a6377';
      dot.style.animation  = isOpen ? 'pulse 1.5s infinite' : 'none';
    }
    if (label) {
      const timeStr = ist.toLocaleTimeString('en-IN',
        { hour: '2-digit', minute: '2-digit', hour12: true, timeZone: 'Asia/Kolkata' });
      label.textContent = `NSE · ${timeStr} IST`;
    }
  }

  

  // ═══════════════════════════════════════════════════════════════════════════
  //  HERO BACKGROUND CANVAS
  // ═══════════════════════════════════════════════════════════════════════════

  function drawHeroBg() {
    const canvas = document.getElementById('heroBg');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let w, h, particles;

    function resize() {
      w = canvas.width  = canvas.offsetWidth;
      h = canvas.height = canvas.offsetHeight;
      initParticles();
    }

    function initParticles() {
      particles = Array.from({ length: 60 }, () => ({
        x  : Math.random() * w,
        y  : Math.random() * h,
        vx : (Math.random() - 0.5) * 0.3,
        vy : (Math.random() - 0.5) * 0.3,
        r  : Math.random() * 1.5 + 0.5,
        a  : Math.random() * 0.5 + 0.1,
      }));
    }

    // Fake price wave
    const wavePts = Array.from({ length: 80 }, (_, i) => ({
      x: (i / 79) * (w || 1200),
      y: 0,
      base: Math.random() * 60 + 40,
      speed: Math.random() * 0.02 + 0.005,
      phase: Math.random() * Math.PI * 2,
    }));

    let t = 0;
    function draw() {
      ctx.clearRect(0, 0, w, h);

      // Draw animated price wave
      const mid = h * 0.5;
      ctx.beginPath();
      wavePts.forEach((pt, i) => {
        pt.y = mid + Math.sin(t * pt.speed * 40 + pt.phase) * pt.base;
        if (i === 0) ctx.moveTo(pt.x, pt.y);
        else         ctx.lineTo(pt.x, pt.y);
      });
      ctx.strokeStyle = 'rgba(0,212,255,0.3)';
      ctx.lineWidth   = 1.5;
      ctx.stroke();

      // Second wave
      ctx.beginPath();
      wavePts.forEach((pt, i) => {
        const y = mid + 80 + Math.sin(t * pt.speed * 30 + pt.phase + 1) * (pt.base * 0.6);
        if (i === 0) ctx.moveTo(pt.x, y);
        else         ctx.lineTo(pt.x, y);
      });
      ctx.strokeStyle = 'rgba(0,229,160,0.15)';
      ctx.lineWidth   = 1;
      ctx.stroke();

      // Particles
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,212,255,${p.a})`;
        ctx.fill();
      });

      t++;
      requestAnimationFrame(draw);
    }

    resize();
    window.addEventListener('resize', resize);
    draw();
  }

})();
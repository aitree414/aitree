const API_BASE = "http://localhost:8000/api";

async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!response.ok) {
    let errMsg = `HTTP ${response.status}`;
    try {
      const err = await response.json();
      errMsg = err.detail || JSON.stringify(err);
    } catch (_) {}
    throw new Error(errMsg);
  }

  return response.json();
}

const api = {
  health() {
    return apiFetch("/health");
  },

  searchStocks(query) {
    return apiFetch(`/stocks/search?q=${encodeURIComponent(query)}`);
  },

  getStock(symbol) {
    return apiFetch(`/stocks/${encodeURIComponent(symbol)}`);
  },

  runBacktest(payload) {
    return apiFetch("/backtest", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  runMABacktest(payload) {
    return apiFetch("/ma-backtest", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getTodayReport() {
    return apiFetch("/screener/report/today");
  },

  runHorseRace() {
    return apiFetch("/screener/horse-race");
  },

  getPaperPortfolio() {
    return apiFetch("/screener/paper-portfolio");
  },
};

const CHART_COLORS = [
  "#2563eb", "#16a34a", "#d97706", "#dc2626",
  "#7c3aed", "#0891b2", "#be185d", "#4f46e5",
];

let portfolioChart = null;
let returnChart = null;
let radarChart = null;
let drawdownChart = null;
let maChart = null;

function destroyChart(chart) {
  if (chart) {
    chart.destroy();
  }
  return null;
}

function renderPortfolioChart(results) {
  portfolioChart = destroyChart(portfolioChart);
  const ctx = document.getElementById("portfolio-chart").getContext("2d");

  const datasets = results
    .filter((r) => !r.error && r.portfolio_history)
    .map((r, i) => ({
      label: `${r.symbol} (${r.name || r.symbol})`,
      data: r.portfolio_history.map((h) => ({ x: h.date, y: h.value })),
      borderColor: CHART_COLORS[i % CHART_COLORS.length],
      backgroundColor: "transparent",
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.2,
    }));

  portfolioChart = new Chart(ctx, {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: $${ctx.parsed.y.toLocaleString()}`,
          },
        },
      },
      scales: {
        x: {
          type: "time",
          time: { unit: "month", tooltipFormat: "yyyy-MM-dd" },
          ticks: { maxTicksLimit: 12 },
        },
        y: {
          ticks: {
            callback: (v) => `$${(v / 1000).toFixed(0)}K`,
          },
        },
      },
    },
  });
}

function renderReturnChart(results) {
  returnChart = destroyChart(returnChart);
  const ctx = document.getElementById("return-chart").getContext("2d");

  const valid = results.filter((r) => !r.error);
  const labels = valid.map((r) => r.symbol);
  const returns = valid.map((r) => (r.total_return * 100).toFixed(2));
  const colors = returns.map((v) => (parseFloat(v) >= 0 ? "#16a34a" : "#dc2626"));

  returnChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Total Return (%)",
          data: returns,
          backgroundColor: colors,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: "y",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.x}%`,
          },
        },
      },
      scales: {
        x: {
          ticks: { callback: (v) => `${v}%` },
        },
      },
    },
  });
}

function renderRiskRadar(results) {
  radarChart = destroyChart(radarChart);
  const ctx = document.getElementById("radar-chart").getContext("2d");

  const valid = results.filter((r) => !r.error);
  const datasets = valid.map((r, i) => ({
    label: r.symbol,
    data: [
      Math.min(r.cagr * 100, 100),
      Math.max(100 + r.max_drawdown * 100, 0),
      Math.max(100 - r.volatility * 100, 0),
      Math.min(Math.max(r.sharpe_ratio * 20, 0), 100),
      Math.min(r.total_return * 20, 100),
    ],
    borderColor: CHART_COLORS[i % CHART_COLORS.length],
    backgroundColor: `${CHART_COLORS[i % CHART_COLORS.length]}33`,
    borderWidth: 2,
    pointRadius: 3,
  }));

  radarChart = new Chart(ctx, {
    type: "radar",
    data: {
      labels: ["CAGR", "Drawdown Resistance", "Low Volatility", "Sharpe", "Return"],
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: { display: false },
        },
      },
    },
  });
}

function renderDrawdownChart(results) {
  drawdownChart = destroyChart(drawdownChart);
  const ctx = document.getElementById("drawdown-chart").getContext("2d");

  const datasets = results
    .filter((r) => !r.error && r.portfolio_history)
    .map((r, i) => {
      const values = r.portfolio_history.map((h) => h.value);
      let peak = values[0];
      const drawdowns = r.portfolio_history.map((h) => {
        if (h.value > peak) peak = h.value;
        const dd = peak > 0 ? ((h.value - peak) / peak) * 100 : 0;
        return { x: h.date, y: parseFloat(dd.toFixed(2)) };
      });

      return {
        label: r.symbol,
        data: drawdowns,
        borderColor: CHART_COLORS[i % CHART_COLORS.length],
        backgroundColor: `${CHART_COLORS[i % CHART_COLORS.length]}22`,
        fill: true,
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.1,
      };
    });

  drawdownChart = new Chart(ctx, {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top" } },
      scales: {
        x: {
          type: "time",
          time: { unit: "month", tooltipFormat: "yyyy-MM-dd" },
          ticks: { maxTicksLimit: 12 },
        },
        y: {
          ticks: { callback: (v) => `${v}%` },
        },
      },
    },
  });
}

function renderMAChart(data) {
  maChart = destroyChart(maChart);
  const ctx = document.getElementById("ma-chart").getContext("2d");

  const history = data.portfolio_history;
  const buyTrades = data.trades.filter((t) => t.type === "buy");
  const sellTrades = data.trades.filter((t) => t.type === "sell");

  const priceData = history.map((h) => ({ x: h.date, y: h.price }));
  const shortMAData = history.map((h) => ({ x: h.date, y: h.ma_short }));
  const longMAData = history.map((h) => ({ x: h.date, y: h.ma_long }));

  // Build point annotation arrays for buy/sell signals overlaid on price
  const buyPoints = history
    .filter((h) => buyTrades.some((t) => t.date === h.date))
    .map((h) => ({ x: h.date, y: h.price }));
  const sellPoints = history
    .filter((h) => sellTrades.some((t) => t.date === h.date))
    .map((h) => ({ x: h.date, y: h.price }));

  maChart = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [
        {
          label: "Price",
          data: priceData,
          borderColor: "#94a3b8",
          borderWidth: 1,
          pointRadius: 0,
          tension: 0.1,
        },
        {
          label: `MA${history[0]?.ma_short !== undefined ? "" : ""} Short`,
          data: shortMAData,
          borderColor: "#2563eb",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
        },
        {
          label: "MA Long",
          data: longMAData,
          borderColor: "#d97706",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
        },
        {
          label: "Buy Signal",
          data: buyPoints,
          borderColor: "#16a34a",
          backgroundColor: "#16a34a",
          borderWidth: 0,
          pointRadius: 8,
          pointStyle: "triangle",
          showLine: false,
          type: "scatter",
        },
        {
          label: "Sell Signal",
          data: sellPoints,
          borderColor: "#dc2626",
          backgroundColor: "#dc2626",
          borderWidth: 0,
          pointRadius: 8,
          pointStyle: "rectRot",
          showLine: false,
          type: "scatter",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top" } },
      scales: {
        x: {
          type: "time",
          time: { unit: "month", tooltipFormat: "yyyy-MM-dd" },
          ticks: { maxTicksLimit: 12 },
        },
        y: {},
      },
    },
  });
}

function renderMAPortfolioChart(data) {
  const ctx = document.getElementById("ma-portfolio-chart").getContext("2d");
  const existing = Chart.getChart(ctx);
  if (existing) existing.destroy();

  const maValues = data.portfolio_history.map((h) => ({ x: h.date, y: h.value }));
  const initial = data.metrics.total_invested;
  const bh = data.buy_hold_comparison;

  // Reconstruct buy & hold line using same history dates
  const bhInitialPrice = data.portfolio_history[0]?.price || 1;
  const bhShares = initial / bhInitialPrice;
  const bhValues = data.portfolio_history.map((h) => ({ x: h.date, y: parseFloat((h.price * bhShares).toFixed(2)) }));

  new Chart(ctx, {
    type: "line",
    data: {
      datasets: [
        {
          label: "MA Strategy",
          data: maValues,
          borderColor: "#2563eb",
          backgroundColor: "#2563eb22",
          fill: true,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
        },
        {
          label: "Buy & Hold",
          data: bhValues,
          borderColor: "#d97706",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top" } },
      scales: {
        x: {
          type: "time",
          time: { unit: "month", tooltipFormat: "yyyy-MM-dd" },
          ticks: { maxTicksLimit: 12 },
        },
        y: {
          ticks: { callback: (v) => `$${(v / 1000).toFixed(0)}K` },
        },
      },
    },
  });
}

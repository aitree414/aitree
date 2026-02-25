// Selected stocks
let selectedStocks = [];
let searchDebounceTimer = null;

const QUICK_STOCKS = [
  { symbol: "2330.TW", label: "台積電" },
  { symbol: "0050.TW", label: "元大50" },
  { symbol: "0056.TW", label: "元大高股息" },
  { symbol: "SPY", label: "S&P 500" },
  { symbol: "QQQ", label: "Nasdaq" },
  { symbol: "AAPL", label: "Apple" },
  { symbol: "NVDA", label: "NVIDIA" },
];

function init() {
  renderQuickButtons();
  setupSearchInput();
  setupForm();
  setDefaultDates();

  document.getElementById("export-btn").addEventListener("click", exportReport);
}

function setDefaultDates() {
  const today = new Date();
  const fiveYearsAgo = new Date(today.getFullYear() - 5, today.getMonth(), today.getDate());
  document.getElementById("start-date").value = fiveYearsAgo.toISOString().split("T")[0];
  document.getElementById("end-date").value = today.toISOString().split("T")[0];
}

function renderQuickButtons() {
  const container = document.getElementById("quick-buttons");
  container.innerHTML = QUICK_STOCKS.map(
    (s) =>
      `<button class="stock-quick-btn" data-symbol="${s.symbol}" onclick="toggleQuickStock('${s.symbol}', '${s.label}')">
        ${s.symbol}
      </button>`
  ).join("");
}

function toggleQuickStock(symbol, name) {
  if (selectedStocks.some((s) => s.symbol === symbol)) {
    removeStock(symbol);
  } else {
    addStock(symbol, name);
  }
}

function addStock(symbol, name) {
  if (selectedStocks.some((s) => s.symbol === symbol)) return;
  selectedStocks.push({ symbol, name });
  renderSelectedStocks();
  updateQuickButtonState(symbol, true);
}

function removeStock(symbol) {
  selectedStocks = selectedStocks.filter((s) => s.symbol !== symbol);
  renderSelectedStocks();
  updateQuickButtonState(symbol, false);
}

function updateQuickButtonState(symbol, active) {
  document.querySelectorAll(".stock-quick-btn").forEach((btn) => {
    if (btn.dataset.symbol === symbol) {
      btn.classList.toggle("active", active);
    }
  });
}

function renderSelectedStocks() {
  const container = document.getElementById("selected-stocks");
  if (selectedStocks.length === 0) {
    container.innerHTML = '<span class="text-muted small">尚未選擇標的</span>';
    return;
  }
  container.innerHTML = selectedStocks
    .map(
      (s) =>
        `<span class="stock-chip">
          ${s.symbol}
          <span class="remove-btn" onclick="removeStock('${s.symbol}')">&times;</span>
        </span>`
    )
    .join("");
}

function setupSearchInput() {
  const input = document.getElementById("stock-search");
  const dropdown = document.getElementById("search-dropdown");

  input.addEventListener("input", () => {
    clearTimeout(searchDebounceTimer);
    const q = input.value.trim();
    if (q.length < 1) {
      dropdown.style.display = "none";
      return;
    }
    searchDebounceTimer = setTimeout(() => doSearch(q), 400);
  });

  document.addEventListener("click", (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = "none";
    }
  });
}

async function doSearch(query) {
  const dropdown = document.getElementById("search-dropdown");
  dropdown.innerHTML = '<div class="search-item text-muted small">搜尋中...</div>';
  dropdown.style.display = "block";

  try {
    const data = await api.searchStocks(query);
    if (!data.results || data.results.length === 0) {
      dropdown.innerHTML = '<div class="search-item text-muted small">找不到相關股票</div>';
      return;
    }
    dropdown.innerHTML = data.results
      .map(
        (r) =>
          `<div class="search-item" onclick="selectSearchResult('${r.symbol}', '${escapeAttr(r.name)}')">
            <span class="symbol-badge">${r.symbol}</span>
            <span class="small">${r.name || ""}</span>
          </div>`
      )
      .join("");
  } catch (err) {
    dropdown.innerHTML = `<div class="search-item text-danger small">${err.message}</div>`;
  }
}

function escapeAttr(str) {
  return (str || "").replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

function selectSearchResult(symbol, name) {
  addStock(symbol, name);
  document.getElementById("stock-search").value = "";
  document.getElementById("search-dropdown").style.display = "none";
}

function setupForm() {
  const form = document.getElementById("backtest-form");
  const strategySelect = document.getElementById("strategy");
  const dcaOptions = document.getElementById("dca-options");

  strategySelect.addEventListener("change", () => {
    dcaOptions.style.display = strategySelect.value === "dca" ? "block" : "none";
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    await runBacktest();
  });
}

async function runBacktest() {
  if (selectedStocks.length === 0) {
    showAlert("請至少選擇一個標的", "warning");
    return;
  }

  const startDate = document.getElementById("start-date").value;
  const endDate = document.getElementById("end-date").value;
  const strategy = document.getElementById("strategy").value;
  const amount = parseFloat(document.getElementById("amount").value);
  const frequency = document.getElementById("frequency").value;

  if (!startDate || !endDate) {
    showAlert("請設定起訖日期", "warning");
    return;
  }
  if (new Date(startDate) >= new Date(endDate)) {
    showAlert("開始日期必須早於結束日期", "warning");
    return;
  }
  if (isNaN(amount) || amount <= 0) {
    showAlert("請輸入有效的投資金額", "warning");
    return;
  }

  showLoading(true);
  hideResults();

  try {
    const payload = {
      stocks: selectedStocks.map((s) => s.symbol),
      start_date: startDate,
      end_date: endDate,
      strategy,
      amount,
      frequency,
    };

    const data = await api.runBacktest(payload);
    displayResults(data, strategy, amount);
  } catch (err) {
    showAlert(`回測失敗: ${err.message}`, "danger");
  } finally {
    showLoading(false);
  }
}

function displayResults(data, strategy, amount) {
  const { results, comparison } = data;
  if (!results || results.length === 0) {
    showAlert("無回測結果", "warning");
    return;
  }

  renderSummaryCards(results, comparison);
  renderResultsTable(results, strategy, amount);

  const valid = results.filter((r) => !r.error);
  if (valid.length > 0) {
    renderPortfolioChart(valid);
    renderReturnChart(valid);
    if (valid.length > 1) renderRiskRadar(valid);
    renderDrawdownChart(valid);
  }

  document.getElementById("results-section").style.display = "block";
  document.getElementById("charts-section").style.display = "block";
  document.getElementById("export-btn").style.display = "inline-block";
}

function renderSummaryCards(results, comparison) {
  const valid = results.filter((r) => !r.error);
  if (valid.length === 0) return;

  const comp = comparison || {};

  const best = valid.find((r) => r.symbol === comp.best_performer) || valid[0];
  const lowestRisk = valid.find((r) => r.symbol === comp.lowest_risk) || valid[0];
  const bestSharpe = valid.find((r) => r.symbol === comp.best_sharpe) || valid[0];
  const topReturn = valid.reduce((a, b) => (a.total_return > b.total_return ? a : b));

  document.getElementById("summary-cards").innerHTML = `
    <div class="col-md-3 col-6 mb-3">
      <div class="summary-card">
        <div class="icon">🏆</div>
        <div class="label">最佳標的</div>
        <div class="value">${best.symbol}</div>
        <div class="sub">${best.name || ""}</div>
      </div>
    </div>
    <div class="col-md-3 col-6 mb-3">
      <div class="summary-card">
        <div class="icon">📈</div>
        <div class="label">最高報酬</div>
        <div class="value text-success">${(topReturn.total_return * 100).toFixed(1)}%</div>
        <div class="sub">${topReturn.symbol}</div>
      </div>
    </div>
    <div class="col-md-3 col-6 mb-3">
      <div class="summary-card">
        <div class="icon">🛡️</div>
        <div class="label">最低風險</div>
        <div class="value text-primary">${(lowestRisk.volatility * 100).toFixed(1)}%</div>
        <div class="sub">${lowestRisk.symbol}</div>
      </div>
    </div>
    <div class="col-md-3 col-6 mb-3">
      <div class="summary-card">
        <div class="icon">⚡</div>
        <div class="label">最高 Sharpe</div>
        <div class="value text-warning">${bestSharpe.sharpe_ratio.toFixed(2)}</div>
        <div class="sub">${bestSharpe.symbol}</div>
      </div>
    </div>
  `;
}

function renderResultsTable(results, strategy, amount) {
  const strategyLabel = strategy === "lump_sum" ? "單筆投資" : "定期定額";

  const rows = results
    .map((r) => {
      if (r.error) {
        return `<tr>
          <td><strong>${r.symbol}</strong></td>
          <td colspan="7" class="text-danger">${r.error}</td>
        </tr>`;
      }

      const returnPct = (r.total_return * 100).toFixed(2);
      const returnClass = parseFloat(returnPct) >= 0 ? "positive" : "negative";

      return `<tr>
        <td><strong>${r.symbol}</strong><br><small class="text-muted">${r.name || ""}</small></td>
        <td>$${r.total_invested.toLocaleString()}</td>
        <td>$${r.final_value.toLocaleString()}</td>
        <td class="${returnClass}">${returnPct}%</td>
        <td>${(r.cagr * 100).toFixed(2)}%</td>
        <td class="negative">${(r.max_drawdown * 100).toFixed(2)}%</td>
        <td>${(r.volatility * 100).toFixed(2)}%</td>
        <td>${r.sharpe_ratio.toFixed(2)}</td>
      </tr>`;
    })
    .join("");

  document.getElementById("results-table").innerHTML = `
    <div class="d-flex justify-content-between align-items-center mb-2">
      <span class="badge bg-primary strategy-badge">${strategyLabel}</span>
      <small class="text-muted">投資金額：$${amount.toLocaleString()}</small>
    </div>
    <div class="table-responsive">
      <table class="table table-hover table-sm">
        <thead class="table-light">
          <tr>
            <th>標的</th>
            <th>投入金額</th>
            <th>最終價值</th>
            <th>總報酬</th>
            <th>CAGR</th>
            <th>最大回撤</th>
            <th>年化波動</th>
            <th>Sharpe</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function showAlert(msg, type = "info") {
  const alert = document.getElementById("alert-box");
  alert.className = `alert alert-${type}`;
  alert.textContent = msg;
  alert.style.display = "block";
  setTimeout(() => (alert.style.display = "none"), 5000);
}

function showLoading(show) {
  document.getElementById("loading-overlay").classList.toggle("show", show);
}

function hideResults() {
  document.getElementById("results-section").style.display = "none";
  document.getElementById("charts-section").style.display = "none";
  document.getElementById("export-btn").style.display = "none";
}

function exportReport() {
  window.print();
}

document.addEventListener("DOMContentLoaded", init);

let selectedMAStock = null;

const MA_QUICK_STOCKS = [
  { symbol: "2330.TW", label: "台積電" },
  { symbol: "0050.TW", label: "元大50" },
  { symbol: "SPY", label: "S&P 500" },
  { symbol: "NVDA", label: "NVIDIA" },
  { symbol: "AAPL", label: "Apple" },
];

function init() {
  renderQuickButtons();
  setupSearchInput();
  setupForm();
  setDefaultDates();
}

function setDefaultDates() {
  const today = new Date();
  const fiveYearsAgo = new Date(today.getFullYear() - 5, today.getMonth(), today.getDate());
  document.getElementById("start-date").value = fiveYearsAgo.toISOString().split("T")[0];
  document.getElementById("end-date").value = today.toISOString().split("T")[0];
}

function renderQuickButtons() {
  const container = document.getElementById("quick-buttons");
  container.innerHTML = MA_QUICK_STOCKS.map(
    (s) =>
      `<button class="stock-quick-btn${selectedMAStock === s.symbol ? " active" : ""}"
        onclick="selectMAStock('${s.symbol}', '${s.label}')">
        ${s.symbol}
      </button>`
  ).join("");
}

function selectMAStock(symbol, name) {
  selectedMAStock = symbol;
  document.getElementById("selected-stock-display").textContent = `已選: ${symbol} (${name})`;
  document.querySelectorAll(".stock-quick-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.textContent.trim() === symbol);
  });
}

function setupSearchInput() {
  const input = document.getElementById("stock-search");
  const dropdown = document.getElementById("search-dropdown");
  let debounce = null;

  input.addEventListener("input", () => {
    clearTimeout(debounce);
    const q = input.value.trim();
    if (!q) { dropdown.style.display = "none"; return; }
    debounce = setTimeout(() => doSearch(q), 400);
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
    if (!data.results?.length) {
      dropdown.innerHTML = '<div class="search-item text-muted small">找不到相關股票</div>';
      return;
    }
    dropdown.innerHTML = data.results
      .map(
        (r) =>
          `<div class="search-item" onclick="selectFromSearch('${r.symbol}', '${escapeAttr(r.name)}')">
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

function selectFromSearch(symbol, name) {
  selectMAStock(symbol, name);
  document.getElementById("stock-search").value = "";
  document.getElementById("search-dropdown").style.display = "none";
}

function setupForm() {
  document.getElementById("ma-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    await runMABacktest();
  });
}

async function runMABacktest() {
  if (!selectedMAStock) {
    showAlert("請選擇標的", "warning");
    return;
  }

  const startDate = document.getElementById("start-date").value;
  const endDate = document.getElementById("end-date").value;
  const shortWindow = parseInt(document.getElementById("short-window").value);
  const longWindow = parseInt(document.getElementById("long-window").value);
  const amount = parseFloat(document.getElementById("amount").value);

  if (shortWindow >= longWindow) {
    showAlert("短期均線必須小於長期均線", "warning");
    return;
  }

  showLoading(true);
  document.getElementById("results-section").style.display = "none";

  try {
    const data = await api.runMABacktest({
      symbol: selectedMAStock,
      start_date: startDate,
      end_date: endDate,
      short_window: shortWindow,
      long_window: longWindow,
      amount,
    });

    displayMAResults(data, shortWindow, longWindow, amount);
  } catch (err) {
    showAlert(`回測失敗: ${err.message}`, "danger");
  } finally {
    showLoading(false);
  }
}

function displayMAResults(data, shortWindow, longWindow, amount) {
  const { metrics, buy_hold_comparison: bh, trades } = data;

  document.getElementById("ma-strategy-label").textContent =
    `MA(${shortWindow}, ${longWindow}) 策略`;

  // Metrics comparison
  const maReturn = (metrics.total_return * 100).toFixed(2);
  const bhReturn = (bh.total_return * 100).toFixed(2);
  const maReturnClass = parseFloat(maReturn) >= 0 ? "text-success" : "text-danger";
  const bhReturnClass = parseFloat(bhReturn) >= 0 ? "text-success" : "text-danger";

  document.getElementById("metrics-comparison").innerHTML = `
    <div class="table-responsive">
      <table class="table table-sm table-hover">
        <thead class="table-light">
          <tr>
            <th>指標</th>
            <th>MA 策略</th>
            <th>Buy &amp; Hold</th>
            <th>差異</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>最終價值</td>
            <td>$${metrics.final_value.toLocaleString()}</td>
            <td>$${bh.final_value.toLocaleString()}</td>
            <td class="${metrics.final_value > bh.final_value ? "text-success" : "text-danger"}">
              ${metrics.final_value > bh.final_value ? "+" : ""}$${(metrics.final_value - bh.final_value).toLocaleString()}
            </td>
          </tr>
          <tr>
            <td>總報酬</td>
            <td class="${maReturnClass}">${maReturn}%</td>
            <td class="${bhReturnClass}">${bhReturn}%</td>
            <td class="${metrics.total_return > bh.total_return ? "text-success" : "text-danger"}">
              ${metrics.total_return > bh.total_return ? "+" : ""}${((metrics.total_return - bh.total_return) * 100).toFixed(2)}%
            </td>
          </tr>
          <tr>
            <td>CAGR</td>
            <td>${(metrics.cagr * 100).toFixed(2)}%</td>
            <td>${(bh.cagr * 100).toFixed(2)}%</td>
            <td>-</td>
          </tr>
          <tr>
            <td>最大回撤</td>
            <td class="text-danger">${(metrics.max_drawdown * 100).toFixed(2)}%</td>
            <td class="text-danger">${(bh.max_drawdown * 100).toFixed(2)}%</td>
            <td class="${Math.abs(metrics.max_drawdown) < Math.abs(bh.max_drawdown) ? "text-success" : "text-danger"}">
              ${Math.abs(metrics.max_drawdown) < Math.abs(bh.max_drawdown) ? "MA 勝" : "B&H 勝"}
            </td>
          </tr>
          <tr>
            <td>年化波動</td>
            <td>${(metrics.volatility * 100).toFixed(2)}%</td>
            <td>${(bh.volatility * 100).toFixed(2)}%</td>
            <td>-</td>
          </tr>
          <tr>
            <td>Sharpe Ratio</td>
            <td>${metrics.sharpe_ratio.toFixed(2)}</td>
            <td>${bh.sharpe_ratio.toFixed(2)}</td>
            <td class="${metrics.sharpe_ratio > bh.sharpe_ratio ? "text-success" : "text-danger"}">
              ${metrics.sharpe_ratio > bh.sharpe_ratio ? "MA 勝" : "B&H 勝"}
            </td>
          </tr>
          <tr>
            <td>交易次數</td>
            <td>${metrics.num_trades}</td>
            <td>0 (持有)</td>
            <td>-</td>
          </tr>
        </tbody>
      </table>
    </div>
  `;

  // Trades table
  const tradeRows = trades
    .map(
      (t) =>
        `<tr>
          <td>${t.date}</td>
          <td class="${t.type === "buy" ? "trade-buy" : "trade-sell"}">
            ${t.type === "buy" ? "買入 (黃金交叉)" : "賣出 (死亡交叉)"}
          </td>
          <td>$${t.price.toLocaleString()}</td>
          <td>${t.shares.toFixed(4)}</td>
          <td>${t.value ? "$" + t.value.toLocaleString() : "-"}</td>
        </tr>`
    )
    .join("");

  document.getElementById("trades-table").innerHTML = trades.length
    ? `<div class="table-responsive">
        <table class="table table-sm table-hover">
          <thead class="table-light">
            <tr><th>日期</th><th>信號</th><th>價格</th><th>股數</th><th>價值</th></tr>
          </thead>
          <tbody>${tradeRows}</tbody>
        </table>
      </div>`
    : '<p class="text-muted">無交易記錄（均線未產生交叉信號）</p>';

  renderMAChart(data);
  renderMAPortfolioChart(data);

  document.getElementById("results-section").style.display = "block";
}

function showAlert(msg, type = "info") {
  const el = document.getElementById("alert-box");
  el.className = `alert alert-${type}`;
  el.textContent = msg;
  el.style.display = "block";
  setTimeout(() => (el.style.display = "none"), 5000);
}

function showLoading(show) {
  document.getElementById("loading-overlay").classList.toggle("show", show);
}

document.addEventListener("DOMContentLoaded", init);

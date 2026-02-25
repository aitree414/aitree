const STRATEGY_CONFIG = {
  pullback: {
    label: "拉回買點",
    color: "#f97316",
    lightBg: "#fff7ed",
    border: "#fed7aa",
  },
  momentum: {
    label: "動能",
    color: "#3b82f6",
    lightBg: "#eff6ff",
    border: "#bfdbfe",
  },
  quality: {
    label: "品質",
    color: "#22c55e",
    lightBg: "#f0fdf4",
    border: "#bbf7d0",
  },
  value: {
    label: "價值",
    color: "#8b5cf6",
    lightBg: "#faf5ff",
    border: "#ddd6fe",
  },
};

function scoreBar(score, width) {
  var w = width || 10;
  var filled = Math.max(0, Math.min(w, Math.round(score * w)));
  return "\u2588".repeat(filled) + "\u2591".repeat(w - filled);
}

function renderStrategyCard(entry) {
  var cfg = STRATEGY_CONFIG[entry.strategy] || {
    label: entry.strategy.toUpperCase(),
    color: "#64748b",
    lightBg: "#f8fafc",
    border: "#e2e8f0",
  };

  var wr = ((entry.win_rate_30d || 0) * 100).toFixed(0);
  var avgRet = ((entry.avg_return_30d || 0) * 100).toFixed(2);
  var avgRetNum = parseFloat(avgRet);
  var retClass = avgRetNum >= 0 ? "text-success" : "text-danger";
  var retPrefix = avgRetNum >= 0 ? "+" : "";

  var topPicks = (entry.top_picks || []).slice(0, 3);
  var topScore = topPicks.length > 0 ? topPicks[0].score || 0 : 0;
  var bar = scoreBar(topScore);
  var topSignals =
    topPicks.length > 0
      ? (topPicks[0].signals || []).slice(0, 2).join(" \u00b7 ")
      : "";

  var pickBadgesHtml = topPicks
    .map(function (p) {
      return (
        '<span class="hr-pick-badge" style="' +
        "--badge-color:" +
        cfg.lightBg +
        ";" +
        "--badge-border:" +
        cfg.border +
        ";" +
        "--badge-text:" +
        cfg.color +
        '">' +
        p.symbol +
        " <small>(" +
        (p.score || 0).toFixed(2) +
        ")</small>" +
        "</span>"
      );
    })
    .join(" ");

  return (
    '<div class="col-md-6 col-xl-3 mb-4">' +
    '<div class="hr-strategy-card" style="' +
    "--strategy-color:" +
    cfg.color +
    ";" +
    "--strategy-bg:" +
    cfg.lightBg +
    ";" +
    "--strategy-border:" +
    cfg.border +
    '">' +
    '<div class="hr-card-header">' +
    '<span class="hr-strategy-label">' +
    cfg.label +
    "</span>" +
    '<span class="hr-pick-count">' +
    (entry.pick_count || 0) +
    " 支選股</span>" +
    "</div>" +
    '<div class="hr-metrics">' +
    '<div class="hr-metric">' +
    '<div class="hr-metric-label">勝率</div>' +
    '<div class="hr-metric-value">' +
    wr +
    "%</div>" +
    "</div>" +
    '<div class="hr-metric">' +
    '<div class="hr-metric-label">平均報酬</div>' +
    '<div class="hr-metric-value ' +
    retClass +
    '">' +
    retPrefix +
    avgRet +
    "%</div>" +
    "</div>" +
    "</div>" +
    '<div class="hr-score-row">' +
    '<span class="hr-score-bar">' +
    bar +
    "</span>" +
    '<span class="hr-score-num">' +
    topScore.toFixed(2) +
    "</span>" +
    "</div>" +
    '<div class="hr-picks-section">' +
    '<div class="hr-picks-label">前三名</div>' +
    '<div class="hr-picks">' +
    pickBadgesHtml +
    "</div>" +
    "</div>" +
    (topSignals ? '<div class="hr-signals">' + topSignals + "</div>" : "") +
    "</div>" +
    "</div>"
  );
}

function findOverlaps(leaderboard) {
  var symbolMap = {};
  leaderboard.forEach(function (entry) {
    var top5 = (entry.top_picks || []).slice(0, 5);
    top5.forEach(function (pick) {
      if (!symbolMap[pick.symbol]) symbolMap[pick.symbol] = [];
      symbolMap[pick.symbol].push(entry.strategy);
    });
  });
  return Object.entries(symbolMap)
    .filter(function (kv) {
      return kv[1].length >= 2;
    })
    .sort(function (a, b) {
      return b[1].length - a[1].length;
    });
}

function renderOverlaps(overlaps) {
  if (overlaps.length === 0) return "";
  var items = overlaps
    .slice(0, 6)
    .map(function (kv) {
      var sym = kv[0];
      var strats = kv[1];
      var badges = strats
        .map(function (s) {
          var cfg = STRATEGY_CONFIG[s] || {
            color: "#64748b",
            lightBg: "#f8fafc",
            border: "#e2e8f0",
          };
          return (
            '<span class="hr-overlap-badge" style="' +
            "background:" +
            cfg.lightBg +
            ";" +
            "border-color:" +
            cfg.border +
            ";" +
            "color:" +
            cfg.color +
            '">' +
            (cfg.label || s.toUpperCase()) +
            "</span>"
          );
        })
        .join(" ");
      return (
        '<div class="hr-overlap-item">' +
        '<span class="hr-overlap-symbol">' +
        sym +
        "</span>" +
        '<span class="hr-overlap-strats">' +
        badges +
        "</span>" +
        "</div>"
      );
    })
    .join("");

  return (
    '<div class="section-card mb-4">' +
    '<div class="section-title">跨策略重疊選股</div>' +
    '<div class="hr-overlaps">' +
    items +
    "</div>" +
    "</div>"
  );
}

function renderPortfolioSummary(portfolio) {
  if (!portfolio) return "";
  var stats = portfolio.strategy_stats || {};
  var openPos = portfolio.open_positions || 0;

  var rows = Object.entries(stats)
    .map(function (kv) {
      var strat = kv[0];
      var s = kv[1];
      var cfg = STRATEGY_CONFIG[strat] || { color: "#64748b", label: strat };
      var wr = ((s.win_rate_30d || 0) * 100).toFixed(0);
      var avg = ((s.avg_return_30d || 0) * 100).toFixed(2);
      var avgNum = parseFloat(avg);
      var avgClass = avgNum >= 0 ? "positive" : "negative";
      var best = ((s.best || 0) * 100).toFixed(2);
      var worst = ((s.worst || 0) * 100).toFixed(2);
      return (
        "<tr>" +
        "<td>" +
        '<span class="hr-strat-dot" style="background:' +
        cfg.color +
        '"></span>' +
        (cfg.label || strat.toUpperCase()) +
        "</td>" +
        "<td>" +
        s.count +
        "</td>" +
        "<td>" +
        wr +
        "%</td>" +
        '<td class="' +
        avgClass +
        '">' +
        (avgNum >= 0 ? "+" : "") +
        avg +
        "%</td>" +
        '<td class="positive">+' +
        best +
        "%</td>" +
        '<td class="negative">' +
        worst +
        "%</td>" +
        "</tr>"
      );
    })
    .join("");

  return (
    '<div class="section-card">' +
    '<div class="section-title">模擬投資組合 &mdash; ' +
    openPos +
    " 筆持倉</div>" +
    '<div class="table-responsive">' +
    '<table class="table table-sm table-hover">' +
    '<thead class="table-light">' +
    "<tr>" +
    "<th>策略</th><th>持倉數</th>" +
    "<th>勝率</th><th>平均報酬</th>" +
    "<th>最佳</th><th>最差</th>" +
    "</tr>" +
    "</thead>" +
    "<tbody>" +
    rows +
    "</tbody>" +
    "</table>" +
    "</div>" +
    "</div>"
  );
}

function renderReport(data) {
  var leaderboard = data.leaderboard || [];
  var reportDate = data.date || new Date().toISOString().split("T")[0];

  document.getElementById("report-date").textContent = reportDate;
  document.getElementById("cards-grid").innerHTML = leaderboard
    .map(renderStrategyCard)
    .join("");

  var overlaps = findOverlaps(leaderboard);
  document.getElementById("overlap-section").innerHTML =
    renderOverlaps(overlaps);

  var portfolio = data.portfolio_summary;
  document.getElementById("portfolio-section").innerHTML =
    renderPortfolioSummary(portfolio);

  document.getElementById("report-section").style.display = "block";
  clearAlert();
}

async function loadTodayReport() {
  showLoading(true);
  clearAlert();
  try {
    var data = await api.getTodayReport();
    renderReport(data);
  } catch (err) {
    if (err.message && err.message.includes("404")) {
      showAlert(
        "今日報告尚未生成，請先執行 scheduler_job，或點「即時掃描」。",
        "warning",
      );
    } else {
      showAlert("載入失敗: " + err.message, "danger");
    }
  } finally {
    showLoading(false);
  }
}

async function runLiveScan() {
  showLoading(true);
  showAlert("即時掃描中，約需 30–60 秒...", "info");
  try {
    var data = await api.runHorseRace();
    renderReport(data);
  } catch (err) {
    showAlert("掃描失敗: " + err.message, "danger");
  } finally {
    showLoading(false);
  }
}

function showAlert(msg, type) {
  var el = document.getElementById("alert-box");
  el.className = "alert alert-" + (type || "info");
  el.textContent = msg;
  el.style.display = "block";
}

function clearAlert() {
  document.getElementById("alert-box").style.display = "none";
}

function showLoading(show) {
  document.getElementById("loading-overlay").classList.toggle("show", show);
}

document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("btn-today")
    .addEventListener("click", loadTodayReport);
  document.getElementById("btn-live").addEventListener("click", runLiveScan);
  loadTodayReport();
});

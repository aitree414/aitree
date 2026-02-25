# BackTester — Claude Code Skills

Zero-token investment horse race system. All computation runs in Python;
Claude acts as interface only.

## Project Structure

```
backend/
  screener/          4 stock screening strategies (value/momentum/pullback/quality)
  horse_race/        Parallel runner + paper portfolio tracker
  api/
    screener_routes.py  REST endpoints
  scheduler_job.py   Daily cron (zero token)
config/
  thresholds.yaml    Tunable strategy parameters
  watchlist.json     US + TW symbols to screen
reports/             Daily JSON outputs + paper_portfolio.json
```

## Available Skills (slash commands)

### /screen
Run all 4 screener strategies against the watchlist and show today's signals.
```bash
cd backend && python3 -c "
import sys, json
sys.path.insert(0, '.')
from horse_race.runner import HorseRaceRunner
r = HorseRaceRunner().run()
for entry in r['leaderboard']:
    top = [p['symbol'] for p in entry['top_picks'][:5]]
    print(f\"[{entry['strategy'].upper()}] {', '.join(top)}\")
"
```

### /horse-race
Show strategy leaderboard (30-day win rate from paper portfolio).
```bash
cd backend && python3 -c "
import sys, json
sys.path.insert(0, '.')
from horse_race.paper_portfolio import PaperPortfolio
stats = PaperPortfolio().get_strategy_stats()
for strat, s in sorted(stats.items(), key=lambda x: -x[1].get('win_rate_30d', 0)):
    print(f\"{strat}: WR={s['win_rate_30d']*100:.0f}%  avgRet={s['avg_return_30d']*100:.2f}%  n={s['count']}\")
"
```

### /paper-portfolio
View open paper positions and P&L.
```bash
cd backend && python3 -c "
import sys, json
sys.path.insert(0, '.')
from horse_race.paper_portfolio import PaperPortfolio
p = PaperPortfolio()
p.update_prices()
for pos in p.get_open_positions():
    pnl = pos['pnl_pct'] * 100
    print(f\"{pos['symbol']:8s} [{pos['strategy']:9s}] entry={pos['entry_price']:.2f}  now={pos['current_price']:.2f}  PnL={pnl:+.2f}%\")
"
```

### /daily-report
Generate (or display) today's full report.
```bash
cd backend && python3 scheduler_job.py --now
cat ../reports/$(date +%Y-%m-%d).json | python3 -m json.tool
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/screener/run?strategy=all | Run all strategies |
| GET | /api/screener/run?strategy=value | Run value strategy only |
| GET | /api/screener/horse-race | Full parallel race + report |
| GET | /api/screener/paper-portfolio | Open positions + stats |
| GET | /api/screener/report/today | Today's cached report |

## Zero Token Principle

| Step | Method | Tokens |
|------|--------|--------|
| Screening | Python pandas rules | 0 |
| Indicator calc | pandas / numpy | 0 |
| Race ranking | Pure math sort | 0 |
| Portfolio update | yfinance | 0 |
| Daily report | JSON serialization | 0 |
| Natural language query | Claude Code Skills | 1 call (user-initiated) |

## Scheduler

```bash
# Run once immediately
python3 backend/scheduler_job.py --now

# Start daemon (runs every day at 08:30)
python3 backend/scheduler_job.py

# Set Telegram notifications
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
python3 backend/scheduler_job.py --now
```

## Tuning

Edit `config/thresholds.yaml` to adjust strategy parameters without code changes.
Edit `config/watchlist.json` to add/remove symbols.

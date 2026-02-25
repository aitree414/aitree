import time
import yfinance as yf
import pandas as pd

_cache: dict = {}
CACHE_TTL = 3600


def _is_cache_valid(symbol: str) -> bool:
    if symbol not in _cache:
        return False
    ts, _ = _cache[symbol]
    return time.time() - ts < CACHE_TTL


def search_stocks(query: str) -> list[dict]:
    results = []
    query_lower = query.lower()

    # Quick look up by direct ticker
    try:
        ticker = yf.Ticker(query.upper())
        info = ticker.info
        if info and info.get("symbol"):
            results.append({
                "symbol": info.get("symbol", query.upper()),
                "name": info.get("longName") or info.get("shortName") or query.upper(),
                "exchange": info.get("exchange", ""),
                "type": info.get("quoteType", "EQUITY"),
            })
    except Exception:
        pass

    # Also try with .TW suffix for Taiwan stocks if query looks like a number
    if query.isdigit() and not query.endswith(".TW"):
        tw_symbol = f"{query}.TW"
        try:
            ticker = yf.Ticker(tw_symbol)
            info = ticker.info
            if info and info.get("symbol"):
                already = any(r["symbol"] == tw_symbol for r in results)
                if not already:
                    results.append({
                        "symbol": info.get("symbol", tw_symbol),
                        "name": info.get("longName") or info.get("shortName") or tw_symbol,
                        "exchange": info.get("exchange", "TWSE"),
                        "type": info.get("quoteType", "EQUITY"),
                    })
        except Exception:
            pass

    # Fallback: yfinance Search (for US stocks)
    if not results:
        try:
            search = yf.Search(query, max_results=5)
            for item in (search.quotes or []):
                results.append({
                    "symbol": item.get("symbol", ""),
                    "name": item.get("longname") or item.get("shortname") or item.get("symbol", ""),
                    "exchange": item.get("exchange", ""),
                    "type": item.get("quoteType", "EQUITY"),
                })
        except Exception:
            pass

    return results[:8]


def get_stock_history(symbol: str, start: str, end: str) -> pd.DataFrame:
    cache_key = f"{symbol}:{start}:{end}"
    if _is_cache_valid(cache_key):
        _, data = _cache[cache_key]
        return data

    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, auto_adjust=True)
    if df.empty:
        df = yf.download(symbol, start=start, end=end, auto_adjust=True, progress=False)

    _cache[cache_key] = (time.time(), df)
    return df


def get_stock_price(symbol: str) -> dict:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        fast = ticker.fast_info
        price = None
        try:
            price = fast.last_price
        except Exception:
            pass
        if price is None:
            price = info.get("regularMarketPrice") or info.get("previousClose")

        return {
            "symbol": info.get("symbol", symbol),
            "name": info.get("longName") or info.get("shortName") or symbol,
            "price": price,
            "currency": info.get("currency", "USD"),
        }
    except Exception as e:
        return {"symbol": symbol, "name": symbol, "price": None, "currency": "USD", "error": str(e)}

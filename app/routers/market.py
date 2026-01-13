from fastapi import APIRouter
import httpx
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/market", tags=["market"])

# Cache to avoid too many requests
cache = {
    'sensex': {'price': 81234.50, 'prev': 80900, 'updated': None},
    'nifty': {'price': 24856.50, 'prev': 24600, 'updated': None},
    'banknifty': {'price': 52340.25, 'prev': 52000, 'updated': None}
}

@router.get("/indices")
async def get_indices():
    """Fetch Sensex, NIFTY and Bank NIFTY data"""
    global cache
    
    now = datetime.now()
    # Update cache every 30 seconds
    if cache['nifty']['updated'] and (now - cache['nifty']['updated']).seconds < 30:
        return format_response()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try Yahoo Finance
            for symbol, key in [("^BSESN", "sensex"), ("^NSEI", "nifty"), ("^NSEBANK", "banknifty")]:
                try:
                    response = await client.get(
                        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                        params={"interval": "1d", "range": "1d"},
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        result = data.get("chart", {}).get("result", [{}])[0]
                        meta = result.get("meta", {})
                        price = meta.get("regularMarketPrice", cache[key]['price'])
                        prev = meta.get("previousClose", meta.get("chartPreviousClose", cache[key]['prev']))
                        cache[key] = {'price': price, 'prev': prev, 'updated': now}
                except Exception as e:
                    print(f"Yahoo fetch error for {symbol}: {e}")
                    
    except Exception as e:
        print(f"Market data fetch error: {e}")
    
    return format_response()

def format_response():
    sensex = cache['sensex']
    nifty = cache['nifty']
    bn = cache['banknifty']
    
    sensex_change = sensex['price'] - sensex['prev']
    sensex_pct = (sensex_change / sensex['prev']) * 100 if sensex['prev'] else 0
    
    nifty_change = nifty['price'] - nifty['prev']
    nifty_pct = (nifty_change / nifty['prev']) * 100 if nifty['prev'] else 0
    
    bn_change = bn['price'] - bn['prev']
    bn_pct = (bn_change / bn['prev']) * 100 if bn['prev'] else 0
    
    return {
        "sensex": {
            "price": round(sensex['price'], 2),
            "change": round(sensex_change, 2),
            "change_percent": round(sensex_pct, 2),
            "is_up": sensex_change >= 0
        },
        "nifty": {
            "price": round(nifty['price'], 2),
            "change": round(nifty_change, 2),
            "change_percent": round(nifty_pct, 2),
            "is_up": nifty_change >= 0
        },
        "banknifty": {
            "price": round(bn['price'], 2),
            "change": round(bn_change, 2),
            "change_percent": round(bn_pct, 2),
            "is_up": bn_change >= 0
        }
    }

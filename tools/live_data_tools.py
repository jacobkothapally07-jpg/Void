import urllib.request
import json
import urllib.parse
import ssl

def _get_ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

def get_live_weather(city: str = 'Hyderabad') -> dict:
    try:
        clean_city = city.strip()
        if clean_city.lower() in ["current_location", "current", "here", "auto", "my location", ""]:
            try:
                from tools.utility_tools import get_current_location
                loc_info = get_current_location()
                clean_city = loc_info.get("city", "Hyderabad")
            except Exception:
                clean_city = "Hyderabad"

        geo_url = 'https://geocoding-api.open-meteo.com/v1/search?name=' + urllib.parse.quote(clean_city) + '&count=1&language=en&format=json'
        req = urllib.request.Request(geo_url, headers={'User-Agent': 'JARVIS/1.0'})
        with urllib.request.urlopen(req, timeout=8, context=_get_ssl_ctx()) as res:
            geo_data = json.loads(res.read().decode('utf-8'))
        
        if not geo_data.get('results'):
            return {'status': 'error', 'message': f'Location {city} not found.'}
            
        loc = geo_data['results'][0]
        lat, lon = loc['latitude'], loc['longitude']
        loc_name = loc.get('name', city)
        country = loc.get('country', '')
        
        weather_url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m'
        req_w = urllib.request.Request(weather_url, headers={'User-Agent': 'JARVIS/1.0'})
        with urllib.request.urlopen(req_w, timeout=8, context=_get_ssl_ctx()) as res_w:
            w_data = json.loads(res_w.read().decode('utf-8'))
            
        curr = w_data.get('current', {})
        temp_c = curr.get('temperature_2m', 'N/A')
        feels_c = curr.get('apparent_temperature', 'N/A')
        humidity = curr.get('relative_humidity_2m', 'N/A')
        wind = curr.get('wind_speed_10m', 'N/A')
        
        detail = f'Atmospheric telemetry for {loc_name}, {country}: Temperature is {temp_c}°C (feels like {feels_c}°C), humidity at {humidity}%, and wind speed {wind} km/h.'
        return {
            'status': 'success',
            'city': loc_name,
            'temperature_c': temp_c,
            'feels_like_c': feels_c,
            'humidity': humidity,
            'wind_kmh': wind,
            'detail': detail
        }
    except Exception as e:
        return {'status': 'error', 'message': f'Weather scan failed: {str(e)}'}

def get_stock_price(symbol: str = 'AAPL') -> dict:
    try:
        clean_sym = symbol.upper().strip()
        aliases = {'TESLA': 'TSLA', 'APPLE': 'AAPL', 'GOOGLE': 'GOOGL', 'MICROSOFT': 'MSFT', 'NVIDIA': 'NVDA', 'BITCOIN': 'BTC-USD', 'ETHEREUM': 'ETH-USD'}
        sym = aliases.get(clean_sym, clean_sym)
        
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        with urllib.request.urlopen(req, timeout=8, context=_get_ssl_ctx()) as res:
            data = json.loads(res.read().decode('utf-8'))
            
        meta = data['chart']['result'][0]['meta']
        price = meta.get('regularMarketPrice', 'N/A')
        currency = meta.get('currency', 'USD')
        prev_close = meta.get('chartPreviousClose', price)
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0.0
        sign = '+' if change_pct >= 0 else ''
        
        detail = f'{sym} is trading at {price:.2f} {currency} ({sign}{change_pct:.2f}% today), Sir.'
        return {
            'status': 'success',
            'symbol': sym,
            'price': price,
            'currency': currency,
            'change_pct': f'{sign}{change_pct:.2f}%',
            'detail': detail
        }
    except Exception as e:
        return {'status': 'error', 'message': f'Market scan for {symbol} failed: {str(e)}'}

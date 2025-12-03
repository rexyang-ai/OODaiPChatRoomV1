import requests
import datetime

API_KEY = "97c99a148fd06528"

def fetch(city: str) -> dict:
    url = f"https://v2.xxapi.cn/api/weatherDetails?city={city}&key={API_KEY}"
    r = requests.get(url, headers={'User-Agent': 'xiaoxiaoapi/1.0.0'})
    if r.status_code == 200:
        j = r.json()
        if j.get('code') == 200 and j.get('data'):
            all_data = j.get('data', {})
            items = all_data.get('data', [])
            if items:
                today = items[0]
                return {
                    'nickname': '天气小助手',
                    'time': datetime.datetime.now().strftime('%H:%M'),
                    'city': all_data.get('city', city),
                    'date': today.get('date', ''),
                    'week': today.get('day', ''),
                    'weather': today.get('weather_from', ''),
                    'temp_low': today.get('low_temp', ''),
                    'temp_high': today.get('high_temp', ''),
                    'wind': today.get('wind_from', '') + ' ' + today.get('wind_level_from', '')
                }
    raise Exception('未获取到天气详情数据')


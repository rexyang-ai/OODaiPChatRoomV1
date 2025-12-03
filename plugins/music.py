import requests
import datetime

def handle():
    url = "https://api.qqsuu.cn/api/dm-randmusic?sort=%E7%83%AD%E6%AD%8C%E6%A6%9C&format=json"
    r = requests.get(url)
    if r.status_code == 200:
        j = r.json()
        if j.get('code') == 1:
            d = j.get('data', {})
            return {
                'nickname': '系统',
                'time': datetime.datetime.now().strftime('%H:%M'),
                'name': d.get('name', '未知歌曲'),
                'singer': d.get('artistsname', '未知歌手'),
                'url': d.get('url', ''),
                'image': d.get('picurl', '')
            }
    raise Exception('音乐获取失败')


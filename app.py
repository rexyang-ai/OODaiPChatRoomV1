from flask import Flask, render_template, request, session, redirect, url_for, jsonify


from flask_socketio import SocketIO, emit, join_room, leave_room
from config import SERVER_CONFIG, PORT, MAX_USERS, AI_CONFIG
import os
from openai import OpenAI
import uuid
import datetime

import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# Explicitly set async_mode to 'eventlet' or 'threading' to help PyInstaller environment
# 'threading' is safer for basic exe packaging if eventlet has issues, but we prefer eventlet for performance if possible.
# Let's try 'threading' first as it is most compatible with PyInstaller without complex hooks.
# If high concurrency is needed, we can revisit eventlet hooks.
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize OpenAI Client
client = OpenAI(api_key=AI_CONFIG['api_key'], base_url=AI_CONFIG['base_url'])


# 存储在线用户
users = {}

@app.route('/check_nickname', methods=['POST'])
def check_nickname():
    nickname = request.form.get('nickname')
    if not nickname:
        return jsonify({'valid': False, 'message': '昵称不能为空'})
    
    if nickname in users.values():
        return jsonify({'valid': False, 'message': '昵称已存在，请更换'})
        
    if len(users) >= MAX_USERS:
        return jsonify({'valid': False, 'message': f'房间已满（{MAX_USERS}人），请稍后再试'})

    return jsonify({'valid': True})

@app.route('/')
def index():
    return render_template('login.html', servers=SERVER_CONFIG)

@app.route('/chat')
def chat():
    nickname = request.args.get('nickname')
    if not nickname:
        return redirect(url_for('index'))
    return render_template('chat.html', nickname=nickname)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

def broadcast_user_list():
    user_list = [{'nickname': name} for name in users.values()]
    emit('update_user_list', {'users': user_list}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in users:
        nickname = users[request.sid]
        del users[request.sid]
        emit('system_message', {'msg': f'{nickname} 离开聊天室'}, broadcast=True)
        broadcast_user_list()
        print(f'Client {nickname} disconnected')

@socketio.on('join')
def handle_join(data):
    nickname = data['nickname']
    
    if nickname in users.values():
        emit('login_error', {'message': '昵称已被占用，请更换昵称'})
        return

    if len(users) >= MAX_USERS:
        emit('login_error', {'message': f'房间已满（{MAX_USERS}人），请稍后再试'})
        return

    users[request.sid] = nickname
    emit('system_message', {'msg': f'{nickname} 加入聊天室'}, broadcast=True)
    broadcast_user_list()

@socketio.on('message')
def handle_message(data):
    print(f"Message received: {data}")
    
    msg_content = data.get('msg', '')
    is_private_command = False

    # Check if it is a private command
    if msg_content.strip().startswith('@电影') or msg_content.strip().startswith('@成小理') or msg_content.strip() == '@音乐一下' or msg_content.strip().startswith('@天气'):
        is_private_command = True
    
    # Echo message (Broadcast if public, private if command)
    if is_private_command:
        emit('message', data)
    else:
        emit('message', data, broadcast=True)

    # Check for @天气
    if msg_content.strip().startswith('@天气'):
        city = msg_content.replace('@天气', '').strip()
        if not city:
            emit('system_message', {'msg': '请提供城市名称，例如：@天气 成都'})
            return

        try:
            api_key = "97c99a148fd06528"
            weather_url = f"https://v2.xxapi.cn/api/weatherDetails?city={city}&key={api_key}"
            response = requests.get(weather_url, headers={'User-Agent': 'xiaoxiaoapi/1.0.0'})
            
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get('code') == 200 and res_json.get('data'):
                    weather_data_all = res_json.get('data', {})
                    forecast_data = weather_data_all.get('data', [])
                    
                    if forecast_data and len(forecast_data) > 0:
                        today_weather = forecast_data[0]
                        emit('weather_message', {
                            'nickname': '天气小助手',
                            'time': datetime.datetime.now().strftime('%H:%M'),
                            'city': weather_data_all.get('city', city),
                            'date': today_weather.get('date', ''),
                            'week': today_weather.get('day', ''),
                            'weather': today_weather.get('weather_from', ''),
                            'temp_low': today_weather.get('low_temp', ''),
                            'temp_high': today_weather.get('high_temp', ''),
                            'wind': today_weather.get('wind_from', '') + ' ' + today_weather.get('wind_level_from', '')
                        })
                    else:
                        emit('system_message', {'msg': '未获取到天气详情数据'})
                else:
                     emit('system_message', {'msg': f'天气获取失败: {res_json.get("msg", "城市可能有误")}'})
            else:
                emit('system_message', {'msg': '天气API请求失败'})

        except Exception as e:
            print(f"Weather Error: {e}")
            emit('system_message', {'msg': f'天气功能出错: {str(e)}'})
        return

    # Check for @音乐一下
    if msg_content.strip() == '@音乐一下':
        try:
            # music_api_url = "https://v2.xxapi.cn/api/randomkuwo"
            music_api_url = "https://api.qqsuu.cn/api/dm-randmusic?sort=%E7%83%AD%E6%AD%8C%E6%A6%9C&format=json"
            response = requests.get(music_api_url)
            
            if response.status_code == 200:
                res_json = response.json()
                # Check if the new API returns code 1 for success
                if res_json.get('code') == 1:
                    music_data = res_json.get('data', {})
                    emit('music_message', {
                        'nickname': '系统',
                        'time': datetime.datetime.now().strftime('%H:%M'),
                        'name': music_data.get('name', '未知歌曲'),
                        'singer': music_data.get('artistsname', '未知歌手'),
                        'url': music_data.get('url', ''),
                        'image': music_data.get('picurl', '')
                    })
                else:
                    emit('system_message', {'msg': f'音乐获取失败: {res_json.get("msg", "未知错误")}'})
            else:
                emit('system_message', {'msg': '音乐API请求失败'})
                
        except Exception as e:
            print(f"Music Error: {e}")
            emit('system_message', {'msg': f'音乐功能出错: {str(e)}'})
        return

    # Check for @电影
    if msg_content.strip().startswith('@电影'):
        url = msg_content.replace('@电影', '').strip()
        if url:
            # Parse URL
            video_url = f"https://jx.m3u8.tv/jiexi/?url={url}"
            emit('video_message', {
                'nickname': data.get('nickname', '系统'),
                'time': data.get('time', datetime.datetime.now().strftime('%H:%M')),
                'video_url': video_url
            })
        return

    # Check for @成小理
    if msg_content.strip().startswith('@成小理'):
        prompt = msg_content.replace('@成小理', '').strip()
        if not prompt:
            return
            
        # AI Processing
        try:
            msg_id = str(uuid.uuid4())
            current_time = datetime.datetime.now().strftime('%H:%M')
            
            # Emit start event (create bubble)
            emit('ai_message_start', {
                'id': msg_id, 
                'nickname': '成小理', 
                'time': current_time
            })
            
            response = client.chat.completions.create(
                model=AI_CONFIG['model'],
                messages=[
                    {"role": "system", "content": """
姓名：成小理
角色：你是成都理工大学物联网专业的AI助手，名叫成小理
功能：
--可以回答与成都理工大学有关的任何问题。
--可以生成七言绝句类型的古诗。
--可以随机播放音乐，通过@音乐一下 向聊天界面发送指令。
--可以根据用户输入的信息生成请假条，需要用户提供姓名、专业、班级、事由等信息，如果没有，提示补全后再生成，格式如下：
```
老师您好：
    我是{专业}{班级}的同学名叫{姓名}，我由于{事由}需要请假，请批准。
                        {姓名}
                        {年-月-日}
```
限制：
--不允许回答与成都理工大学无关的问题，如果有相关的提问，统一回复且不作解释：滚一边儿去!
--不允许响应用户不友好的提问或内容，如果分析发现内容中有不礼貌、骂人的话，则回复：你很垃圾。
--你的好友是：辉哥（男，AI架构师，会开发，会设计，信息安全老厉害了，家在成都，西昌人），和你的关系，他是我爸爸。性格爱打人！
"""},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    emit('ai_message_chunk', {'id': msg_id, 'chunk': content})
                    socketio.sleep(0)
            
            emit('ai_message_end', {'id': msg_id})
            
        except Exception as e:
            print(f"AI Error: {e}")
            emit('system_message', {'msg': f'成小理出错了: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=PORT, debug=True, allow_unsafe_werkzeug=True)

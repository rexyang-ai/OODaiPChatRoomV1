from flask import Flask, render_template, request, session, redirect, url_for, jsonify


from flask_socketio import SocketIO, emit, join_room, leave_room
from config import SERVER_CONFIG, PORT, MAX_USERS, AI_CONFIG
import os
from openai import OpenAI
import uuid
import datetime

import requests
from plugins.music import handle as music_handle
from plugins.movie import parse as movie_parse
from plugins.weather import fetch as weather_fetch
from plugins.ai import stream as ai_stream

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
            payload = weather_fetch(city)
            emit('weather_message', payload)
        except Exception as e:
            emit('system_message', {'msg': str(e)})
        return

    # Check for @音乐一下
    if msg_content.strip() == '@音乐一下':
        try:
            payload = music_handle()
            emit('music_message', payload)
        except Exception as e:
            emit('system_message', {'msg': str(e)})
        return

    # Check for @电影
    if msg_content.strip().startswith('@电影'):
        url = msg_content.replace('@电影', '').strip()
        if url:
            video_url = movie_parse(url)
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
            
            for piece in ai_stream(prompt):
                emit('ai_message_chunk', {'id': msg_id, 'chunk': piece})
                socketio.sleep(0)
            
            emit('ai_message_end', {'id': msg_id})
            
        except Exception as e:
            print(f"AI Error: {e}")
            emit('system_message', {'msg': f'成小理出错了: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=PORT, debug=True, allow_unsafe_werkzeug=True)

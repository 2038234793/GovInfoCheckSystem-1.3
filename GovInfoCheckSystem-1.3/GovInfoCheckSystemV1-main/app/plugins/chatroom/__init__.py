from flask import Blueprint, render_template, request, jsonify, current_app
from flask_socketio import emit, join_room, leave_room
from app import socketio
from flask_login import current_user, login_required
from datetime import datetime
import threading
import requests
import json
import uuid

chatroom_bp = Blueprint('chatroom', __name__, template_folder='templates', static_folder='static', url_prefix='/chatroom')

# Store online users and history
# Note: In a real production app, use Redis or Database
online_users = {}
chat_history = []
MAX_HISTORY = 100

SILICONFLOW_API_KEY = "sk-qnhvpfxfxwmcfqywwjmqravexflvuneiqdumqcwgeojpilyr"
SILICONFLOW_MODEL = "Qwen/Qwen2.5-7B-Instruct"

@chatroom_bp.route('/')
@login_required
def index():
    # Use current_user.username as nickname
    return render_template('chat_plugin.html', nickname=current_user.username)

# --- SocketIO Events ---

@socketio.on('connect', namespace='/chat')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('join_room', namespace='/chat')
def handle_join(data):
    nickname = data['nickname']
    room = 'general' # Group chat room
    join_room(room)
    
    # Map SID to User Info
    online_users[request.sid] = {'nickname': nickname, 'room': room}
    
    # Broadcast welcome
    welcome_msg = {
        'type': 'system',
        'content': f'{nickname} 加入了聊天室',
        'time': datetime.now().strftime('%H:%M')
    }
    emit('message', welcome_msg, room=room)
    
    # Update user list
    broadcast_user_list(room)
    
    # Send history
    emit('history', {'messages': chat_history})

@socketio.on('send_message', namespace='/chat')
def handle_message(data):
    nickname = data.get('nickname')
    message = data.get('message')
    room = 'general'
    
    # Basic validation
    if not message:
        return

    msg = {
        'type': 'user',
        'nickname': nickname,
        'content': message,
        'time': datetime.now().strftime('%H:%M')
    }
    
    # Save history
    chat_history.append(msg)
    if len(chat_history) > MAX_HISTORY:
        chat_history.pop(0)
        
    emit('message', msg, room=room)

@socketio.on('send_private_message', namespace='/chat')
def handle_private_message(data):
    nickname = data.get('nickname')
    to_nickname = data.get('to')
    message = data.get('message')
    
    if not message or not to_nickname:
        return

    # Find recipient SIDs
    recipient_sids = []
    for sid, user_info in online_users.items():
        if user_info['nickname'] == to_nickname:
            recipient_sids.append(sid)
            
    if not recipient_sids:
        # User not found
        emit('message', {
            'type': 'system',
            'content': f'用户 {to_nickname} 不在线',
            'time': datetime.now().strftime('%H:%M')
        })
        return

    msg = {
        'type': 'private',
        'from': nickname,
        'to': to_nickname,
        'content': message,
        'time': datetime.now().strftime('%H:%M')
    }
    
    # Send to sender
    emit('private_message', msg)
    
    # Send to recipient(s)
    for sid in recipient_sids:
        if sid != request.sid: # Don't send twice if sender is same (though logic above sends to sender specifically)
            emit('private_message', msg, room=sid)

    # Use sender's sid as room for command responses in private chat
    room = request.sid

    # Check for @AI command
    if '@AI' in message or '@ai' in message:
        # Remove @AI from message
        clean_msg = message.replace('@AI', '').replace('@ai', '').strip()
        if clean_msg:
            # Check if the user is asking for music (e.g., @AI 音乐)
            if clean_msg == '音乐' or clean_msg == '点歌' or clean_msg == '来首音乐':
                threading.Thread(target=process_music_request, args=(room,)).start()
            # Check if the user is asking for weather (e.g., @AI 天气 北京)
            elif clean_msg.startswith('天气'):
                city_name = clean_msg.replace('天气', '').strip()
                if city_name:
                    threading.Thread(target=process_weather_request, args=(city_name, room)).start()
                else:
                    socketio.emit('message', {
                        'type': 'system',
                        'content': '请指定城市，例如：@AI 天气 北京',
                        'time': datetime.now().strftime('%H:%M')
                    }, room=room, namespace='/chat')
            # Check if the user is asking for movie (e.g., @AI 电影 URL)
            elif clean_msg.startswith('电影'):
                video_url = clean_msg.replace('电影', '').strip()
                if video_url:
                    process_movie_request(video_url, room)
                else:
                    socketio.emit('message', {
                        'type': 'system',
                        'content': '请提供视频链接，例如：@AI 电影 https://example.com/video',
                        'time': datetime.now().strftime('%H:%M')
                    }, room=room, namespace='/chat')
            # Check if user is asking for charts (e.g., @AI 报表)
            elif '报表' in clean_msg or '统计' in clean_msg or '数据' in clean_msg:
                app_obj = current_app._get_current_object()
                threading.Thread(target=process_chart_request, args=(clean_msg, room, app_obj)).start()
            else:
                threading.Thread(target=process_ai_response, args=(clean_msg, room)).start()
    
    # Check for @音乐 command
    if message.strip() == '@音乐':
        threading.Thread(target=process_music_request, args=(room,)).start()
        
    # Check for @天气 command
    if message.strip().startswith('@天气'):
        city_name = message.replace('@天气', '').strip()
        if city_name:
            threading.Thread(target=process_weather_request, args=(city_name, room)).start()
        else:
            # Prompt user to enter city
             socketio.emit('message', {
                'type': 'system',
                'content': '请指定城市，例如：@天气 北京',
                'time': datetime.now().strftime('%H:%M')
            }, room=room, namespace='/chat')

    # Check for @电影 command
    if message.strip().startswith('@电影'):
        video_url = message.replace('@电影', '').strip()
        if video_url:
            process_movie_request(video_url, room)
        else:
            emit('message', {
                'type': 'system',
                'content': '请提供视频链接，例如：@电影 https://example.com/video',
                'time': datetime.now().strftime('%H:%M')
            }, room=room)
            return

def process_chart_request(prompt, room, app):
    """Process request for data charts"""
    from app.models import CrawlItem, ArticleDetail
    from app import db
    from sqlalchemy import func
    
    # We need app context since we are in a thread
    with app.app_context():
        try:
            # 1. Analyze intent (Simple keyword matching for now, can be AI driven)
            chart_type = 'bar'
            if '饼' in prompt: chart_type = 'pie'
            elif '线' in prompt: chart_type = 'line'
            
            title = "数据统计报表"
            data = {}
            
            # 2. Aggregate Data
            # Example: Count items by source
            if '来源' in prompt or '网站' in prompt or True: # Default to source stats
                results = db.session.query(CrawlItem.source, func.count(CrawlItem.id))\
                    .group_by(CrawlItem.source).limit(10).all()
                
                title = "各来源数据采集量统计"
                labels = [r[0] or '未知' for r in results]
                values = [r[1] for r in results]
                
                if chart_type == 'pie':
                    data = [{"name": l, "value": v} for l, v in zip(labels, values)]
                else:
                    data = {"categories": labels, "values": values}
            
            # 3. Construct Message
            msg = {
                'type': 'chart_card',
                'nickname': '数据助手',
                'content': {
                    'type': chart_type,
                    'title': title,
                    'data': data
                },
                'time': datetime.now().strftime('%H:%M')
            }
            
            socketio.emit('message', msg, room=room, namespace='/chat')
            
            # Save to history
            chat_history.append(msg)
            if len(chat_history) > MAX_HISTORY:
                chat_history.pop(0)
                
        except Exception as e:
            print(f"Chart Error: {e}")
            socketio.emit('message', {
                'type': 'system',
                'content': f'生成报表失败: {str(e)}',
                'time': datetime.now().strftime('%H:%M')
            }, room=room, namespace='/chat')

def process_movie_request(video_url, room):
    resolution_server = "https://jx.m3u8.tv/jiexi/?url="
    final_url = f"{resolution_server}{video_url}"
    
    msg = {
        'type': 'video_card',
        'nickname': '影视助手',
        'content': final_url,
        'time': datetime.now().strftime('%H:%M')
    }
    
    socketio.emit('message', msg, room=room, namespace='/chat')
    
    # Save history
    chat_history.append(msg)
    if len(chat_history) > MAX_HISTORY:
        chat_history.pop(0)

def process_weather_request(city, room):
    """Process Weather request"""
    url = "https://cn.apihz.cn/api/tianqi/tqyb.php"
    params = {
        "id": "10010469",
        "key": "ad17af3ed891d867568636d5597d9ca0",
        "place": city
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                # Extract weather info
                # Example format: "南京 — 当前天气：晴 温度：25℃ 湿度：60% 风向：西北风 3级 更新时间：12:30"
                now_info = data.get('nowinfo', {})
                weather = data.get('weather1', '未知')
                temp = now_info.get('temperature', '未知')
                humidity = now_info.get('humidity', '未知')
                wind_dir = now_info.get('windDirection', '未知')
                wind_scale = now_info.get('windScale', '未知')
                update_time = now_info.get('uptime', '').split(' ')[-1] if 'uptime' in now_info else datetime.now().strftime('%H:%M')
                
                weather_str = f"{city} — 当前天气：{weather}  温度：{temp}℃  湿度：{humidity}%  风向：{wind_dir} {wind_scale}  更新时间：{update_time}"
                
                msg = {
                    'type': 'system', # Use system type for now, or user type if we want it to look like a bot reply
                    'content': weather_str,
                    'time': datetime.now().strftime('%H:%M')
                }
                # Sending as a special system message or just a bot message. 
                # The user example output looks like a text response.
                # Let's use a bot avatar for better UX, similar to music bot?
                # Or just system message as requested? "助手输出：..." implies a message bubble.
                # Let's use a 'weather_bot' identity to make it consistent with music/AI.
                
                msg = {
                    'type': 'user',
                    'nickname': '天气助手',
                    'content': weather_str,
                    'time': datetime.now().strftime('%H:%M')
                }
                
                socketio.emit('message', msg, room=room, namespace='/chat')
                
                # Save to history
                chat_history.append(msg)
                if len(chat_history) > MAX_HISTORY:
                    chat_history.pop(0)
            else:
                socketio.emit('message', {
                    'type': 'system',
                    'content': f'无法获取{city}的天气信息，请检查城市名称是否正确',
                    'time': datetime.now().strftime('%H:%M')
                }, room=room, namespace='/chat')
        else:
            socketio.emit('message', {
                'type': 'system',
                'content': '天气API请求失败',
                'time': datetime.now().strftime('%H:%M')
            }, room=room, namespace='/chat')
    except Exception as e:
        print(f"Weather API Error: {e}")
        socketio.emit('message', {
            'type': 'system',
            'content': f'天气服务出错: {str(e)}',
            'time': datetime.now().strftime('%H:%M')
        }, room=room, namespace='/chat')

def process_music_request(room):
    """Process Music request and send back card"""
    url = "https://v2.xxapi.cn/api/randomkuwo"
    headers = {
        'User-Agent': 'xiaoxiaoapi/1.0.0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                music_data = data.get('data')
                msg = {
                    'type': 'music_card',
                    'nickname': '音乐助手',
                    'content': music_data,
                    'time': datetime.now().strftime('%H:%M')
                }
                # Use a proxy URL or replace image to avoid ORB blocking
                # The image URL from this API (tva1.sinaimg.cn) is often blocked by browser ORB/CORB policies
                # We can try to replace it with a placeholder or use a referrer policy in frontend, 
                # but simplest fix for now is to not rely on it if it breaks, or use a proxy.
                # Since we can't easily proxy image streaming here without more code, let's use a generic music icon if the image fails loading (handled in frontend via onerror)
                # OR we can try to use a different API or just pass the data.
                
                # Let's add a referer policy meta tag to the frontend template, that often fixes sinaimg issues.
                # But here we just pass the data.
                
                socketio.emit('message', msg, room=room, namespace='/chat')
                
                # Save to history
                chat_history.append(msg)
                if len(chat_history) > MAX_HISTORY:
                    chat_history.pop(0)
            else:
                socketio.emit('message', {
                    'type': 'system',
                    'content': '无法获取音乐数据',
                    'time': datetime.now().strftime('%H:%M')
                }, room=room, namespace='/chat')
        else:
            socketio.emit('message', {
                'type': 'system',
                'content': '音乐API请求失败',
                'time': datetime.now().strftime('%H:%M')
            }, room=room, namespace='/chat')
    except Exception as e:
        print(f"Music API Error: {e}")
        socketio.emit('message', {
            'type': 'system',
            'content': f'音乐服务出错: {str(e)}',
            'time': datetime.now().strftime('%H:%M')
        }, room=room, namespace='/chat')

def process_ai_response(prompt, room):
    """Process AI response in a separate thread and stream back via SocketIO"""
    print(f"Processing AI request: {prompt}")
    
    # Prepare request to SiliconFlow
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": SILICONFLOW_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant in a chatroom."},
            {"role": "user", "content": prompt}
        ],
        "stream": True
    }
    
    try:
        # Generate a unique ID for this AI message
        msg_id = str(uuid.uuid4())
        
        # Initial message to client to create bubble
        initial_msg = {
            'type': 'ai_stream_start',
            'nickname': 'AI助手',
            'id': msg_id,
            'time': datetime.now().strftime('%H:%M')
        }
        socketio.emit('message', initial_msg, room=room, namespace='/chat')
        
        response = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=60
        )
        
        full_content = ""
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data_json = json.loads(data_str)
                            if 'choices' in data_json and len(data_json['choices']) > 0:
                                delta = data_json['choices'][0]['delta']
                                if 'content' in delta:
                                    content = delta['content']
                                    full_content += content
                                    # Stream chunk
                                    socketio.emit('ai_stream_chunk', {
                                        'id': msg_id,
                                        'content': content
                                    }, room=room, namespace='/chat')
                        except json.JSONDecodeError:
                            pass
        else:
            socketio.emit('ai_stream_chunk', {
                'id': msg_id,
                'content': f"Error: {response.status_code} - {response.text}"
            }, room=room, namespace='/chat')
            
        # Save full message to history
        ai_msg_final = {
            'type': 'user', # Treat as user message for history
            'nickname': 'AI助手',
            'content': full_content,
            'time': datetime.now().strftime('%H:%M')
        }
        chat_history.append(ai_msg_final)
        if len(chat_history) > MAX_HISTORY:
            chat_history.pop(0)
            
    except Exception as e:
        print(f"AI Error: {e}")
        socketio.emit('message', {
            'type': 'system',
            'content': f'AI服务暂时不可用: {str(e)}',
            'time': datetime.now().strftime('%H:%M')
        }, room=room, namespace='/chat')

@socketio.on('disconnect', namespace='/chat')
def handle_disconnect():
    if request.sid in online_users:
        user_info = online_users.pop(request.sid)
        nickname = user_info['nickname']
        room = user_info['room']
        
        leave_msg = {
            'type': 'system',
            'content': f'{nickname} 离开了聊天室',
            'time': datetime.now().strftime('%H:%M')
        }
        emit('message', leave_msg, room=room)
        broadcast_user_list(room)

def broadcast_user_list(room):
    # Filter users in the room
    users = [u['nickname'] for u in online_users.values() if u['room'] == room]
    # Unique users (if multiple tabs open)
    users = list(set(users))
    emit('update_users', {'users': users}, room=room, namespace='/chat')

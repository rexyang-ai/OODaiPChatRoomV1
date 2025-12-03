# OODaiP 智能聊天室 (OODaiPChatRoomV1)

## 项目简介

OODaiP 聊天室是一个基于 B/S 架构的在线群聊 Web 应用。它支持多用户实时聊天、智能 AI 对话助手、多媒体内容嵌入（如视频）以及响应式界面设计。项目后端采用 Python Flask + Flask-SocketIO，前端使用 HTML5 + CSS3 (Tailwind CSS) + jQuery。

## 核心功能

### 已实现功能
1.  **用户登录**：
    *   昵称校验（唯一性、非空）。
    *   服务器节点选择（支持本地及内网穿透地址）。
    *   房间人数限制（默认 15 人）。
2.  **实时群聊**：
    *   基于 WebSocket 的低延迟消息传输。
    *   支持发送文本消息和 Emoji 表情。
    *   在线用户列表实时更新。
    *   系统通知（用户加入/离开）。
3.  **智能助手 (@成小理)**：
    *   集成 OpenAI API (SiliconFlow)。
    *   支持流式响应 (Streaming)，模拟打字机效果。
    *   定制化人设：成都理工大学物联网专业 AI 助手，具备古诗生成、请假条生成等特定功能。
    *   **私聊响应**：AI 回复仅对发送指令的用户可见。
4.  **多媒体互动 (@电影)**：
    *   通过发送 `@电影 [url]` 指令，在聊天窗口嵌入视频播放器。
    *   **私聊响应**：视频窗口仅对发送指令的用户可见。
5.  **界面交互**：
    *   响应式设计，适配移动端和桌面端。
    *   消息自动滚动到底部。
    *   自定义滚动条样式。
    *   Emoji 选择面板。

### 待开发/预留功能
*   **@音乐一下**、**@天气**、**@新闻**、**@小视频**：接口已预留，待实现逻辑。
*   **历史记录**：目前仅提示“正在建设中”。

## 技术栈

*   **后端**：
    *   Python 3.x
    *   Flask (Web 框架)
    *   Flask-SocketIO (WebSocket 通信)
    *   Eventlet (高性能并发网络库)
    *   OpenAI (AI 模型调用)
*   **前端**：
    *   HTML5 / CSS3
    *   Tailwind CSS (CDN 引入，用于样式布局)
    *   jQuery (DOM 操作)
    *   Socket.IO Client (前端 WebSocket 客户端)

## 项目结构

```text
OODaiPChatRoomV1/
├── app.py                  # 项目主入口，包含 Flask 路由和 SocketIO 事件处理逻辑
├── config.py               # 项目配置文件（服务器地址、AI Key、人数限制等）
├── requirements.txt        # Python 依赖包列表
├── static/                 # 静态资源目录
│   ├── css/                # 样式文件
│   └── js/                 # 脚本文件 (jquery-3.7.1.min.js)
└── templates/              # HTML 模板目录
    ├── login.html          # 登录页面
    └── chat.html           # 聊天室主页面
```

## 快速开始

### 1. 环境准备
确保本地已安装 Python 3.x。

### 2. 创建并激活虚拟环境
建议在项目根目录下创建虚拟环境以隔离依赖。

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
pip install openai  # 如果 requirements.txt 中未包含 openai，需单独安装
```

### 4. 启动项目
```bash
python app.py
```
启动成功后，控制台将显示运行端口（默认 5000）。

### 5. 访问应用
打开浏览器访问：
*   本地：`http://127.0.0.1:5000`
*   公网/穿透地址：请查看 `config.py` 中的配置。

## 配置说明 (config.py)

项目的所有关键配置均在 `config.py` 文件中管理：

```python
# WebSocket服务器配置列表（用于登录页下拉选择）
SERVER_CONFIG = [
    {"name": "本地服务器", "url": "http://127.0.0.1:5000"},
    {"name": "公网服务器", "url": "http://..."}, # 内网穿透地址
    ...
]

# 端口配置
PORT = 5000

# 房间限制
MAX_USERS = 15

# AI 配置 (OpenAI 兼容接口)
AI_CONFIG = {
    "api_key": "your-api-key-here",
    "base_url": "https://api.siliconflow.cn/v1/",
    "model": "Qwen/Qwen2.5-7B-Instruct"
}
```

## 开发指南

### 1. 添加新的 @ 指令
在 `app.py` 的 `handle_message` 函数中添加新的判断逻辑：

```python
# 示例：添加 @天气
if msg_content.strip().startswith('@天气'):
    city = msg_content.replace('@天气', '').strip()
    # 调用天气 API 获取数据...
    weather_info = get_weather(city)
    
    # 发送回显（私聊）
    emit('message', data) 
    
    # 发送结果（私聊）
    emit('weather_message', {'info': weather_info})
    return
```

### 2. 前端渲染新消息类型
在 `templates/chat.html` 中监听后端发送的新事件：

```javascript
socket.on('weather_message', (data) => {
    // 生成 HTML 并追加到消息列表
    const html = `<div class="...">天气信息：${data.info}</div>`;
    $('#messages').append(html);
    scrollToBottom();
});
```

### 3. 注意事项
*   **私聊 vs 广播**：对于个人查询类指令（如 @成小理, @电影），请使用 `emit('event', data)` 仅发送给当前 socket，不要加 `broadcast=True`。
*   **流式响应**：AI 对话使用了 WebSocket 事件分片传输 (`ai_message_chunk`)，前端需处理拼接逻辑。
*   **静态资源**：`jquery` 目前是本地文件，`tailwindcss` 和 `font-awesome` 使用了 CDN，如需离线运行需下载到 `static` 目录。

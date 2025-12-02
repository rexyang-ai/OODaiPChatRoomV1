# config.py

# WebSocket服务器配置列表
SERVER_CONFIG = [
    {"name": "本地服务器", "url": "http://127.0.0.1:5000"},
    {"name": "公网服务器", "url": "http://m3whw18h0zpn.ngrok.xiaomiqiu123.top"},
    {"name": "公网服务器2", "url": "http://testserver.yangzhenghui.cn"},
]

# 默认端口
PORT = 5000

# 房间最大人数限制
MAX_USERS = 15

# AI 配置
AI_CONFIG = {
    "api_key": "sk-qnhvpfxfxwmcfqywwjmqravexflvuneiqdumqcwgeojpilyr",
    "base_url": "https://api.siliconflow.cn/v1/",
    "model": "Qwen/Qwen2.5-7B-Instruct"
}

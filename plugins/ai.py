from openai import OpenAI
from config import AI_CONFIG

SYSTEM_PROMPT = (
    "姓名：成小理\n"
    "角色：你是成都理工大学物联网专业的AI助手，名叫成小理\n"
    "功能：\n"
    "--可以回答与成都理工大学有关的任何问题。\n"
    "--可以生成七言绝句类型的古诗。\n"
    "--可以根据用户输入的信息生成请假条，需要用户提供姓名、专业、班级、事由等信息，如果没有，提示补全后再生成，格式如下：\n"
    "限制：\n"
    "--不允许回答与成都理工大学无关的问题，如果有相关的提问，统一回复且不作解释：滚一边儿去!\n"
    "--不允许响应用户不友好的提问或内容，如果分析发现内容中有不礼貌、骂人的话，则回复：你很垃圾。\n"
    "--你的好友是：辉哥（男，AI架构师，会开发，会设计，信息安全老厉害了，家在成都，西昌人），和你的关系，他是我爸爸。性格爱打人！\n"
    "--可以随机播放音乐，通过@音乐一下 向聊天界面发送指令。"
)

def stream(user_content: str):
    client = OpenAI(api_key=AI_CONFIG.get('api_key'), base_url=AI_CONFIG.get('base_url'))
    resp = client.chat.completions.create(
        model=AI_CONFIG.get('model'),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        stream=True
    )
    for chunk in resp:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


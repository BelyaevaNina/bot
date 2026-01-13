import random
import asyncio
import aiohttp
import os
from telethon import TelegramClient, events
from aiohttp import web

api_id = 33100781
api_hash = "851e421911ca88d83e20e276c953453c"
phone = "+79897939606"
BOT_TOKEN = "8275700528:AAECybc5-QPbiXS4ZO9NmJ_-Hapk_GnexI0"
CHAT_ID = -1003204357813
BOT_USERNAME = "retransforgamebot"
BOT_ID = None

OLLAMA_URL = "http://localhost:11434/api/generate"
SEND_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

VOID_API_KEY = "sk-voidai-Io4dDslOL7WKyFsYZk5gYR15AjIcCZ4XU0wjPImO1ke-i5cSjdctY5US9Y5JILhaRwk8QpE_HuRmXqIHUMiRDLecpru1kx9t-Ehiqhsoj_5iNZKGvXKX4zd8131wDYftE6OZnQ"
VOID_API_URL = "https://api.voidai.app/v1/chat/completions"
VOID_MODEL = "gpt-5.1"  # пример, поменяешь если надо

# ---------------- CLIENTS -------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

user_client = TelegramClient(
    os.path.join(BASE_DIR, "user_reader"),
    api_id,
    api_hash,
    sequential_updates=True,
)

bot_client = TelegramClient(
    os.path.join(BASE_DIR, "bot_sender"),
    api_id,
    api_hash,
)

# ---------------- MEMORY --------------------------

chat_history = []
MAX_HISTORY = 10

current_prompt = "Ты милая няшка стесняшка. Максимум 3 предложения"

# ---------------- LLM -----------------------------

async def ask_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {VOID_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": VOID_MODEL,
        "messages": [
            {"role": "system", "content": "Привет бот"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.9,
        "max_tokens": 500,
        "top_p": 0.9,
        "n": 1,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                VOID_API_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=40),
            ) as resp:

                if resp.status != 200:
                    print("❌ VoidAI status:", resp.status)
                    return "Что-то пошло не так 😭"

                data = await resp.json()
                return (
                    data["choices"][0]["message"]["content"].strip()
                    or "я зависла и покраснела 😭"
                )

    except Exception as e:
        print("❌ LLM error:", e)
        return "Что-то сломалось 😭"

# ---------------- PROMPT --------------------------

def build_prompt(username: str, text: str) -> str:
    history = "\n".join(chat_history[-MAX_HISTORY:])
    return f"""{current_prompt}

Не говори что ты бот или ИИ.

История чата:
{history}

Новое сообщение от @{username}: "{text}"

Ответь от первого лица.
"""

# ---------------- TRIGGERS ------------------------

TRIGGERS_CALL = [
    f"@{BOT_USERNAME}",
    "бот",
    "ботик",
    "эй",
    "помоги",
    "вопрос",
]

TRIGGERS_EMO = [
    "бля",
    "пиздец",
    "устал",
    "устала",
    "плохо",
    "груст",
    "тяжко",
    "капец",
]

def should_reply(username: str, text: str) -> bool:
    txt = text.lower()

    if username == BOT_USERNAME.lower():
        return False

    if any(t in txt for t in TRIGGERS_CALL):
        return True

    if any(t in txt for t in TRIGGERS_EMO):
        return True

    return random.random() < 0.1

# ---------------- BOT SEND ------------------------

async def bot_send(text: str):
    await bot_client.send_message(CHAT_ID, text)

# ---------------- HANDLER (USER READS) ------------

@user_client.on(events.NewMessage)
async def handler(event):
    # фильтр по чату
    if event.chat_id != CHAT_ID:
        return

    sender = await event.get_sender()

    # игнорируем всех ботов (включая нашего)
    if sender.id == BOT_ID:
        return

    username = (sender.username or "").lower()
    text = event.raw_text or ""

    print(f">>> @{username}: {text}")

    chat_history.append(f"{username}: {text}")
    if len(chat_history) > MAX_HISTORY:
        chat_history.pop(0)

    if not should_reply(username, text):
        return

    prompt = build_prompt(username, text)
    answer = await ask_llm(prompt)

    print("<<< BOT:", answer)
    await bot_send(answer)
    await asyncio.sleep(1.5)

async def user_alive_monitor():
    while True:
        try:
            await user_client.get_me()
        except Exception as e:
            print("⚠️ USER CLIENT LOST:", e)
        await asyncio.sleep(30)

# ---------------- HEALTH SERVER -------------------

async def healthcheck(request):
    return web.Response(text="ok")

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", healthcheck)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"🌍 Health server listening on port {port}")

# ---------------- START ---------------------------

async def main():
    global BOT_ID

    await start_health_server()

    await user_client.start(phone=phone)
    me = await user_client.get_me()
    print("👤 USER LOGGED IN AS:", me.id, me.username)

    await bot_client.start(bot_token=BOT_TOKEN)
    print("🤖 BOT CLIENT CONNECTED")

    asyncio.create_task(user_alive_monitor())

    bot_me = await bot_client.get_me()
    BOT_ID = bot_me.id

    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected(),
    )

asyncio.run(main())

import random
import time
import requests
import json
import asyncio
from telethon import TelegramClient, events
import atexit

api_id = 33100781
api_hash = "851e421911ca88d83e20e276c953453c"
phone = "+79897939606"
BOT_TOKEN = "8275700528:AAECybc5-QPbiXS4ZO9NmJ_-Hapk_GnexI0"
CHAT_ID = -1001183977989
BOT_USERNAME = "retransforgamebot"

OLLAMA_URL = "http://localhost:11434/api/generate"
SEND_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

VOID_API_KEY = "sk-voidai-Io4dDslOL7WKyFsYZk5gYR15AjIcCZ4XU0wjPImO1ke-i5cSjdctY5US9Y5JILhaRwk8QpE_HuRmXqIHUMiRDLecpru1kx9t-Ehiqhsoj_5iNZKGvXKX4zd8131wDYftE6OZnQ"
VOID_API_URL = "https://api.voidai.app/v1/chat/completions"
VOID_MODEL = "gpt-5.1"  # пример, поменяешь если надо

client = TelegramClient("boychat", api_id, api_hash,
    sequential_updates=True)
loop = asyncio.get_event_loop()

# ---------------- MEMORY --------------------------

chat_history = []
MAX_HISTORY = 10

current_prompt = "Ты милая няшка стесняшка. Максимум 3 предложения"

# ---------------- LLM -----------------------------

def ask_llm_sync(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {VOID_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": VOID_MODEL,
        "messages": [
            {"role": "system", "content": "Привет бот"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 500,
        "top_p": 0.9,
        "n": 1
    }

    try:
        r = requests.post(VOID_API_URL, json=data, headers=headers, timeout=40)
        print("LLM status:", r.status_code)

        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"].strip()
            return content or "я зависла, прости 😭"
        return "что-то пошло не так 😭"
    except Exception as e:
        print("LLM error:", e)
        return "мне плохо, попробуй позже 😭"

async def ask_llm(prompt: str) -> str:
    return await loop.run_in_executor(None, ask_llm_sync, prompt)

# ---------------- PROMPT --------------------------

def build_prompt(username, text):
    history_block = "\n".join(chat_history[-MAX_HISTORY:])
    return f"""{current_prompt}

Не говори что ты бот или ИИ.

История чата:
{history_block}

Новое сообщение от @{username}: "{text}"

Ответь от первого лица.
"""

# ---------------- TRIGGERS ------------------------

TRIGGERS_CALL = [
    "@retransforgamebot", "бот", "ботик", "эй", "помоги"
]

TRIGGERS_EMO = [
    "бля", "пиздец", "устал", "устала", "плохо",
    "груст", "капец", "не понимаю", "смешно"
]

def should_reply(username, text):
    txt = text.lower()

    if username == BOT_USERNAME.lower():
        return False

    if any(t in txt for t in TRIGGERS_CALL):
        return True

    if any(t in txt for t in TRIGGERS_EMO):
        return True

    return random.random() < 0.1

# ---------------- SEND ----------------------------

async def send_message(text):
    await client.send_message(CHAT_ID, text)

# ---------------- HANDLER -------------------------

@client.on(events.NewMessage(chats=CHAT_ID))
async def handler(event):
    global chat_history, current_prompt

    sender = await event.get_sender()
    username = (sender.username or "").lower()
    text = event.raw_text or ""

    print(f">>> @{username}: {text}")

    # /help
    if text == "/help@retransforgamebot":
        await send_message(
            "Привет долбаеб! Спроси меня что угодно. "
            "Отзываюсь на @retransforgamebot, бот, ботик, эй, помоги"
        )
        return

    # /setprompt
    if text.startswith("/setprompt@retransforgamebot"):
        parts = text.split(" ", 1)
        if len(parts) > 1 and parts[1].strip():
            current_prompt = " ".join(parts[1].split())
            chat_history.clear()
            await send_message("Промт обновлён.")
        else:
            await send_message("Текст для промта не может быть пустым.")
        return

    # /resetprompt
    if text == "/resetprompt@retransforgamebot":
        current_prompt = "Ты милая няшка стесняшка. Максимум 3 предложения"
        chat_history.clear()
        await send_message("Промт сброшен.")
        return

    # /showprompt
    if text == "/showprompt@retransforgamebot":
        await send_message(current_prompt)
        return

    # локальные реакции
    if "томат" in text.lower():
        await send_message("Томат лучший <3")
        return

    # if "сглып" in text.lower():
    #     await send_message("Сглыпа хуесос")
    #     return

    # память
    chat_history.append(f"{username}: {text}")
    if len(chat_history) > MAX_HISTORY:
        chat_history.pop(0)

    if not should_reply(username, text):
        return

    prompt = build_prompt(username, text)
    answer = await ask_llm(prompt)

    print("<<< BOT:", answer)
    await send_message(answer)

    # мягкий антифлуд
    await asyncio.sleep(1.5)

# ---------------- START ---------------------------

print("⚡ бот запускается")
client.start()
client.run_until_disconnected()

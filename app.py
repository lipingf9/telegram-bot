import os
from flask import Flask, request, jsonify
import requests
from openai import OpenAI

app = Flask(__name__)

# Railway の Variables と名前を完全一致させる
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 起動時チェック
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    print("Incoming webhook data:", data)

    if not data or "message" not in data:
        return jsonify({"ok": True})

    message = data["message"]
    chat_id = message["chat"]["id"]
    user_message = message.get("text", "")

    if not user_message:
        send_message(chat_id, "テキストメッセージを送ってください。")
        return jsonify({"ok": True})

    if user_message == "/start":
        send_message(chat_id, "こんにちは。@Lilianf_bot です。質問をどうぞ。")
        return jsonify({"ok": True})

    try:
        response = client.responses.create(
            model="gpt-5.4",
            input=user_message
        )
        reply = response.output_text.strip() if response.output_text else "返答を生成できませんでした。"
    except Exception as e:
        print("OpenAI error:", str(e))
        reply = f"エラーが発生しました: {str(e)}"

    send_message(chat_id, reply)
    return jsonify({"ok": True})


def send_message(chat_id, text):
    try:
        response = requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=30
        )
        print("Telegram sendMessage response:", response.status_code, response.text)
        response.raise_for_status()
    except Exception as e:
        print("Telegram sendMessage error:", str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

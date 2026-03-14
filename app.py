import os
from flask import Flask, request, jsonify
import requests
from openai import OpenAI

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"ok": True})

    chat_id = data["message"]["chat"]["id"]
    user_message = data["message"].get("text", "")

    if not user_message:
        send_message(chat_id, "テキストメッセージを送ってください。")
        return jsonify({"ok": True})

    if user_message == "/start":
        send_message(chat_id, "こんにちは。@Lilianf_botです。質問をどうぞ。")
        return jsonify({"ok": True})

    try:
        response = client.responses.create(
            model="gpt-5.4",
            input=user_message
        )
        reply = response.output_text
    except Exception as e:
        reply = f"エラーが発生しました: {str(e)}"

    send_message(chat_id, reply)
    return jsonify({"ok": True})

def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

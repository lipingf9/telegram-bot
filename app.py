import os
from flask import Flask, request, jsonify
import requests
from openai import OpenAI

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")
BOT_SYSTEM_PROMPT = os.getenv(
    "BOT_SYSTEM_PROMPT",
    "You are a helpful AI assistant. Reply in the user's language."
)

client = OpenAI(api_key=OPENAI_API_KEY)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_telegram_message(chat_id: int, text: str) -> None:
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()


def extract_text_from_update(update: dict) -> tuple[int | None, str | None]:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return None, None

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text")
    return chat_id, text


def ask_openai(user_text: str) -> str:
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=BOT_SYSTEM_PROMPT,
        input=user_text
    )

    # SDKでは output_text で簡単に取り出せる形が案内されています
    answer = getattr(response, "output_text", None)
    if answer:
        return answer.strip()

    return "すみません、返答の生成に失敗しました。もう一度お試しください。"


@app.route("/", methods=["GET"])
def healthcheck():
    return jsonify({"ok": True, "message": "LP's Bot server is running"})


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    chat_id, text = extract_text_from_update(update)

    if not chat_id:
        return jsonify({"ok": True})

    if not text:
        send_telegram_message(chat_id, "今はテキストメッセージに対応しています。")
        return jsonify({"ok": True})

    # 簡単なコマンド処理
    if text.startswith("/start"):
        welcome = (
            "こんにちは。Lilian's Botです。\n"
            "ロボティクス、スマートデバイス、国際ビジネス、日本での事業の進め方などをお手伝いします。"
        )
        send_telegram_message(chat_id, welcome)
        return jsonify({"ok": True})

    if text.startswith("/help"):
        help_text = (
            "使い方:\n"
            "・普通に質問する\n"
            "・日本語 / 中文 / English でOK\n"
            "例:\n"
            "  日本で会社設立する流れは？\n"
            "  ODMの進め方を教えて\n"
            "  What can you do?"
        )
        send_telegram_message(chat_id, help_text)
        return jsonify({"ok": True})

    try:
        answer = ask_openai(text)
    except Exception as e:
        answer = f"エラーが発生しました。設定を確認してください。\n{type(e).__name__}: {str(e)}"

    # TelegramはsendMessageで返信できます
    send_telegram_message(chat_id, answer)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))

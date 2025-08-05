import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from alerts.telegram_alert_bot import TelegramAlertBot

load_dotenv()

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

if not bot_token:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file. Please setup.")

app = Flask(__name__)
bot = TelegramAlertBot(bot_token)


def your_embedding_function(image_bytes):
    return [0.1, 0.2, 0.3]  # Replace with real embeddings


@app.route("/register", methods=["POST"])
def register():
    selected_chat = request.form.get("selected_chat")

    people = []
    idx = 0
    while True:
        person_name = request.form.get(f"people[{idx}][name]")
        if not person_name:
            break

        images = request.files.getlist(f"people[{idx}][images]")
        embeddings = []
        for img in images:
            img_bytes = img.read()
            emb = your_embedding_function(img_bytes)
            embeddings.append(emb)

        people.append({"name": person_name, "embeddings": embeddings})
        idx += 1

    return jsonify({"message": "Registered successfully", "people_count": len(people)})


@app.route("/")
def index():
    chats = bot.get_updates()
    return render_template("index.html", title="Registro", chats=chats)


if __name__ == "__main__":
    app.run(debug=True)

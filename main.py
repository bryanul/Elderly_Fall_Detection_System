import time

import numpy as np
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.alerts.telegram_alert_bot import TelegramAlertBot
from app.core.config import settings
from app.fall_and_face_tracker import FallAndFaceTracker
from app.modules.face_recognition import embed_face

app = Flask(__name__)
app.config.update(settings.app.dict())
app.secret_key = settings.app.secret_key

bot = TelegramAlertBot(settings.telegram.bot_token)

tracker = FallAndFaceTracker(**settings.get_tracker_config(), alert_bot=bot)
tracker.start_async()


@app.route("/register", methods=["POST"])
def register():
    selected_chat = request.form.get("caretaker_chat_id")

    bot.set_chat_id(selected_chat)
    people = {
        "Bryan Ugas": np.load("face_emb/bryan.npy"),
    }
    idx = 0
    while True:
        person_name = request.form.get(f"people[{idx}][name]")
        if not person_name:
            break

        img = request.files.get(f"people[{idx}][image]")

        img_bytes = img.read()
        embeddings = embed_face(img_bytes)

        people[person_name] = embeddings
        idx += 1

    tracker.set_face_db(people)

    session["registration_complete"] = True
    session["selected_chat"] = selected_chat
    session["registered_people"] = list(people.keys())

    return jsonify(
        {
            "message": "Registered successfully",
            "people_count": len(people),
            "chat_id": selected_chat,
            "people": list(people.keys()),
        }
    )


@app.route("/")
def index():
    chats = bot.get_updates()
    registration_state = {
        "selected_chat": session.get("selected_chat"),
        "registered_people": session.get("registered_people", []),
        "registration_complete": session.get("registration_complete", False),
    }
    return render_template(
        "index.html", title="Registro", chats=chats, state=registration_state
    )


@app.route("/video_feed")
def video_feed():
    def gen():
        while True:
            frame = tracker.get_latest_frame()
            if frame is not None:
                yield b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            time.sleep(settings.video.stream_sleep_interval)

    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/show_video")
def show_video():
    if not session.get("registration_complete"):
        return redirect(url_for("index"))
    return render_template("video.html")


@app.route("/update_chats", methods=["POST"])
def update_chats():
    try:
        chats = bot.get_updates()
        return jsonify({"success": True, "message": "Chats actualizados correctamente"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/clear_session")
def clear_session():
    """Clear session data and redirect to index."""
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(
        debug=settings.app.debug,
        host=settings.app.host,
        port=settings.app.port,
    )

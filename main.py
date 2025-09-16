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
from app.database.db_manager import DatabaseManager

app = Flask(__name__)
app.config.update(settings.app.dict())
app.secret_key = settings.app.secret_key

bot = TelegramAlertBot(settings.telegram.bot_token)
db_manager = DatabaseManager()

tracker = FallAndFaceTracker(**settings.get_tracker_config(), alert_bot=bot)
tracker.start_async()

people_db = db_manager.get_all_people()
if people_db:
    tracker.set_face_db(people_db)
@app.route("/register", methods=["POST"])
def register():
    selected_chat = request.form.get("caretaker_chat_id")

    bot.set_chat_id(selected_chat)

    people = db_manager.get_all_people()

    idx = 0
    while True:
        person_name = request.form.get(f"people[{idx}][name]")
        if not person_name:
            break

        img = request.files.get(f"people[{idx}][image]")

        if img:
            img_bytes = img.read()
            embeddings = embed_face(img_bytes)

            if db_manager.add_person(person_name, embeddings):
                people[person_name] = embeddings

        idx += 1

    tracker.set_face_db(people)

    session["registration_complete"] = True
    session["selected_chat"] = selected_chat
    session["registered_people"] = db_manager.get_people_list()

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
        "registered_people": db_manager.get_people_list(),
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


@app.route("/delete_person", methods=["POST"])
def delete_person():
    """Delete a person from the database."""
    person_name = request.json.get("name")
    if not person_name:
        return jsonify({"success": False, "error": "Name is required"}), 400

    if db_manager.delete_person(person_name):
        # Update tracker with new people list
        people = db_manager.get_all_people()
        tracker.set_face_db(people)

        return jsonify({
            "success": True,
            "message": f"Person {person_name} deleted successfully"
        })
    else:
        return jsonify({
            "success": False,
            "error": f"Failed to delete person {person_name}"
        }), 500

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

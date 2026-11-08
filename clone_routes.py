"""Ovoz klonlash — Flask yo'nalishlari (combined_app.py ga ulanadi)."""
import json
import threading

from flask import jsonify, request, send_from_directory, Response

import core
import voice_clone as vc

_SLOTS = threading.BoundedSemaphore(2)   # og'ir DSP/neyron ishlar parallel soni
MAX_UPLOAD = 40 * 1024 * 1024


def register(app, check_rate, client_ip, base_dir):
    def fail(msg, code=400):
        return jsonify({"status": "error", "message": msg}), code

    @app.route("/clone")
    def clone_page():
        return send_from_directory(base_dir, "clone.html")

    @app.route("/clone.css")
    def clone_css():
        return send_from_directory(base_dir, "clone.css", mimetype="text/css")

    @app.route("/clone.js")
    def clone_js():
        return send_from_directory(base_dir, "clone.js", mimetype="text/javascript")

    @app.route("/api/clone/status")
    def clone_status():
        return jsonify({
            "status": "success",
            "engines": vc.engines(),
            "reading_text": vc.READING_TEXT,
            "max_chars": vc.MAX_CLONE_CHARS,
            "profiles": vc.list_profiles() if not vc.DEPS_ERROR else [],
        })

    @app.route("/api/clone/profiles")
    def clone_profiles():
        return jsonify({"status": "success", "profiles": vc.list_profiles()})

    @app.route("/api/clone/profile/<pid>", methods=["GET", "DELETE"])
    def clone_profile(pid):
        try:
            if request.method == "DELETE":
                return jsonify({"status": "success", "deleted": vc.delete_profile(pid)})
            return jsonify({"status": "success", "profile": vc.load_profile(pid)})
        except ValueError as exc:
            return fail(str(exc), 404)

    @app.route("/api/clone/profile/<pid>/ref.wav")
    def clone_ref(pid):
        try:
            return send_from_directory(vc._pdir(pid), "ref.wav", mimetype="audio/wav")
        except Exception:
            return fail("Topilmadi", 404)

    @app.route("/api/clone/profile", methods=["POST"])
    def clone_create():
        if request.form.get("consent") != "1":
            return fail("Faqat o'z ovozingizni (yoki egasining roziligi bilan) yuklashingiz mumkin. Tasdiqlang.", 400)
        files = request.files.getlist("audio")
        if not files:
            return fail("Audio fayl yuborilmadi.", 400)
        if (request.content_length or 0) > MAX_UPLOAD:
            return fail("Fayl juda katta (maks. 40 MB).", 413)
        try:
            check_rate(client_ip())
            chunks = []
            for f in files[:6]:
                suffix = "." + (f.filename.rsplit(".", 1)[-1] if f.filename and "." in f.filename else "webm")
                chunks.append(vc.decode_audio(f.read(), suffix))
            with _SLOTS:
                prof = vc.create_profile(chunks, request.form.get("name", ""))
            return jsonify({"status": "success", "profile": prof})
        except core.Busy as exc:
            return fail(str(exc), 429)
        except ValueError as exc:
            return fail(str(exc), 400)
        except Exception as exc:
            print(f"❌ Clone profile error: {type(exc).__name__}: {exc}", flush=True)
            return fail(str(exc), 500)

    @app.route("/api/clone/tts", methods=["POST"])
    def clone_tts():
        d = request.get_json(silent=True) or {}
        try:
            with _SLOTS:
                data, mime, info = vc.synthesize(
                    str(d.get("text", "")),
                    str(d.get("profile_id", "")),
                    voice=d.get("voice") or None,
                    engine=str(d.get("engine", "auto")),
                    prosody=float(d.get("prosody", 1.0)),
                    match=float(d.get("match", 1.0)),
                    fmt="wav" if d.get("format") == "wav" else "mp3",
                    on_miss=lambda: check_rate(client_ip()),
                )
        except core.Busy as exc:
            r = jsonify({"status": "error", "message": str(exc)})
            r.status_code, r.headers["Retry-After"] = 429, "10"
            return r
        except ValueError as exc:
            return fail(str(exc), 400)
        except Exception as exc:
            print(f"❌ Clone TTS error: {type(exc).__name__}: {exc}", flush=True)
            return fail(str(exc), 502)
        resp = Response(data, mimetype=mime)
        resp.headers["X-Clone-Info"] = json.dumps(info, ensure_ascii=True)
        resp.headers["Access-Control-Expose-Headers"] = "X-Clone-Info"
        resp.headers["Content-Disposition"] = f'inline; filename="mening_ovozim.{"mp3" if "mpeg" in mime else "wav"}"'
        return resp

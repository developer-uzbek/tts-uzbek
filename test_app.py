"""Tezkor tekshiruv (internet va Telegram kerak emas):  python test_app.py"""
import time
import unittest
from types import SimpleNamespace

import core
import combined_app
import bot as B


class FakeComm:
    calls = 0

    def __init__(self, text, voice, rate="+0%", pitch="+0Hz", volume="+0%", **_):
        FakeComm.calls += 1
        self.text, self.voice = text, voice

    async def stream(self):
        yield {"type": "WordBoundary"}
        yield {"type": "audio", "data": b"ID3" + self.text.encode()[:50]}
        yield {"type": "audio", "data": b"-" + self.voice.encode()}


core.edge_tts.Communicate = FakeComm
core.edge_tts.list_voices = lambda: (_ for _ in ()).throw(OSError("offline"))  # zaxira ro'yxatni sinash
c = combined_app.app.test_client()


class Web(unittest.TestCase):
    def test_q_and_r(self):
        for k in ("q", "r"):
            r = c.get(f"/?{k}=Salom%20dunyo&voice=madina")
            self.assertEqual((r.status_code, r.mimetype), (200, "audio/mpeg"))
            self.assertTrue(r.data.startswith(b"ID3Salom dunyo") and r.data.endswith(b"MadinaNeural"))

    def test_cache_and_range(self):
        FakeComm.calls = 0
        c.get("/?q=kesh+sinovi")
        r = c.get("/?q=kesh+sinovi", headers={"Range": "bytes=0-2"})
        self.assertEqual(FakeComm.calls, 1)                 # ikkinchi so'rov keshdan
        self.assertEqual((r.status_code, r.data), (206, b"ID3"))  # iOS Safari uchun Range

    def test_download_and_post(self):
        self.assertIn("attachment", c.get("/?q=a&dl=1&name=my%20file").headers["Content-Disposition"])
        self.assertIn("my_file.mp3", c.get("/?q=a&dl=1&name=my%20file").headers["Content-Disposition"])
        r = c.post("/api/tts", json={"text": "Привет", "voice": "ru", "style": "hype", "rate": 10})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data.endswith(b"DmitryNeural"))

    def test_errors(self):
        self.assertEqual(c.get("/?q=").status_code, 400)
        self.assertEqual(c.get("/?q=" + "a" * (core.MAX_CHARS + 1)).status_code, 413)
        self.assertEqual(c.get("/?q=a&voice=yoq-ovoz").status_code, 400)
        self.assertEqual(c.get("/?q=a&style=yoq").status_code, 400)

    def test_rate_limit(self):
        combined_app._hits.clear()
        combined_app.RATE_PER_MIN = 3
        codes = [c.get(f"/?q=limit{i}").status_code for i in range(5)]
        self.assertEqual(codes, [200, 200, 200, 429, 429])
        self.assertEqual(c.get("/?q=limit0").status_code, 200)  # keshdagi so'rov limitga kirmaydi
        combined_app.RATE_PER_MIN = 40

    def test_pages(self):
        self.assertIn(b"VoiceCraft", c.get("/").data)
        self.assertIn(b"argparse", c.get("/tts.py").data)
        self.assertIn(b"s2d", c.get("/guide").data)                      # qo'llanma sahifasi
        self.assertIn(b"--bw", c.get("/theme.css").data)                 # umumiy mavzular
        self.assertIn("github_url", c.get("/health").get_json())
        j = c.get("/api/voices").get_json()
        self.assertTrue(any(v["id"] == "uz-UZ-SardorNeural" for v in j["voices"]) and len(j["styles"]) == 5)
        self.assertEqual({v["gender"] for v in j["voices"]}, {"male", "female"})

    def test_options(self):
        o = core.opts({"style": "deep", "rate": "+10%", "pitch": -5, "voice": "sardor"})
        self.assertEqual((o["rate"], o["pitch"], o["volume"], o["voice"]), ("-10%", "-45Hz", "+10%", "uz-UZ-SardorNeural"))
        self.assertEqual(len(core.STYLES), 5)

    def test_language_and_gender(self):
        V = lambda **d: core.opts(d)["voice"]
        self.assertEqual(V(lang="ru", gender="female"), "ru-RU-SvetlanaNeural")
        self.assertEqual(V(lang="uz", gender="ayol"), "uz-UZ-MadinaNeural")
        self.assertEqual(V(lang="tr", gender="erkak"), "tr-TR-AhmetNeural")
        self.assertEqual(V(voice="uz-female"), "uz-UZ-MadinaNeural")
        self.assertEqual(V(voice="ru_male"), "ru-RU-DmitryNeural")
        self.assertEqual(V(voice="en"), "en-US-AndrewNeural")
        self.assertEqual(V(voice="madina", gender="male"), "uz-UZ-MadinaNeural")   # ism ustun
        self.assertEqual(V(gender="female"), "uz-UZ-MadinaNeural")                  # til berilmasa — o'zbek
        self.assertEqual(V(), core.DEFAULT_VOICE)
        self.assertEqual(c.get("/?q=a&lang=ru&gender=female").data[-13:], b"SvetlanaNeural"[-13:])
        self.assertEqual(c.get("/tts.mp3?r=a&voice=ru-male").status_code, 200)
        self.assertEqual(c.get("/?q=a&lang=zz").status_code, 400)


class Bot(unittest.TestCase):
    def setUp(self):
        self.sent = []
        B.bot.send_message = lambda chat, text, **kw: self.sent.append(text)
        B.ADMINS[:] = [1]
        B.S.update(users={}, sub_on=False, channels=[], pause_until=0)

    def test_duration(self):
        P = B.parse_dur
        self.assertEqual([P("30"), P("45m"), P("2 soat"), P("3d"), P("1 kun"), P("5 daqiqa"), P("x")], [1800, 2700, 7200, 259200, 86400, 300, 0])

    def test_pause_blocks_users_not_admins(self):
        B.S["pause_until"] = time.time() + 3600
        self.assertFalse(B.allowed(2, 2))
        self.assertIn("to'xtatilgan", self.sent[-1])
        self.assertTrue(B.allowed(1, 1))
        B.S["pause_until"] = time.time() - 1
        self.assertTrue(B.allowed(2, 2))                     # vaqt o'tgach o'zi ochiladi

    def test_subscription_gate(self):
        B.S.update(sub_on=True, channels=["@kanal"])
        member = type("M", (), {"status": "left"})()
        B.bot.get_chat_member = lambda ch, uid: member
        B.OK_UNTIL.clear()
        self.assertFalse(B.allowed(5, 5))
        member.status = "member"
        self.assertTrue(B.allowed(5, 5))
        B.S["sub_on"] = False
        B.OK_UNTIL.clear(); member.status = "left"
        self.assertTrue(B.allowed(6, 6))                     # obuna o'chiq bo'lsa tekshirilmaydi

    def test_users_and_stats(self):
        for u in (10, 11, 10):
            B.touch(u)
        self.assertEqual(len(B.S["users"]), 2)
        self.assertIn("Jami foydalanuvchi: <b>2</b>", B.stats_text())
        self.assertEqual(B.norm_channel("https://t.me/My_Channel1"), "@My_Channel1")
        self.assertIsNone(B.norm_channel("ab"))
        B.home_view(); B.sub_view(); B.pause_view()          # klaviaturalar xatosiz yasaladi

    def test_throttle(self):
        B.throttle(1, 2, "t"); B.throttle(1, 2, "t")
        with self.assertRaises(core.Busy):
            B.throttle(1, 2, "t")

    def _inline_env(self):
        B.INLINE_DELAY = 0
        self.answers, self.uploads = [], []
        B.FILE_IDS.clear()

        def send_audio(chat, f, **kw):
            self.uploads.append((chat, kw.get("title")))
            return SimpleNamespace(message_id=len(self.uploads), audio=SimpleNamespace(file_id=f"FID{len(self.uploads)}"))
        B.bot.send_audio, B.bot.delete_message = send_audio, lambda *a, **k: True
        B.bot.answer_inline_query = lambda qid, res, **kw: self.answers.append((res, kw))
        return lambda text, uid=7, qid="q1": SimpleNamespace(id=qid, query=text, from_user=SimpleNamespace(id=uid))

    def test_inline_hints(self):
        q = self._inline_env()
        B.on_inline(q(""))                                    # bo'sh matn -> ko'rsatma
        B.on_inline(q("a" * 201))                             # juda uzun -> ogohlantirish
        self.assertEqual([a[0][0].id for a in self.answers], ["hint", "long"])
        B.S["pause_until"] = time.time() + 600                # pauza va obuna inline'da ham ishlaydi
        B.on_inline(q("salom", uid=8, qid="q3"))
        self.assertEqual(self.answers[-1][0][0].id, "pause")
        B.S.update(pause_until=0, sub_on=True, channels=["@kanal"])
        B.bot.get_chat_member = lambda ch, uid: SimpleNamespace(status="left")
        B.OK_UNTIL.clear()
        B.on_inline(q("salom", uid=9, qid="q4"))
        self.assertEqual(self.answers[-1][0][0].id, "sub")

    def test_inline_cached_audio(self):
        q = self._inline_env()
        B.on_inline(q("Salom dunyo", qid="q2"))               # sintez + Telegram'ga yuklash + file_id natija
        time.sleep(0.6)
        res, kw = self.answers[-1]
        self.assertEqual([type(r).__name__ for r in res], ["InlineQueryResultCachedAudio"] * 2)
        self.assertEqual(sorted(r.audio_file_id for r in res), ["FID1", "FID2"])
        self.assertEqual((res[0].caption, kw["cache_time"], kw["is_personal"]), ("@" + B.BOT_USERNAME, 300, True))
        self.assertEqual(self.uploads[0], (1, "Salom dunyo"))      # saqlash chati = birinchi admin
        B.on_inline(q("Salom dunyo", qid="q5"))               # bir xil matn: qayta yuklanmaydi
        time.sleep(0.6)
        self.assertEqual((len(self.uploads), len(self.answers[-1][0])), (2, 2))
        n = len(self.answers)
        B.LATEST[7] = "yangisi"                               # eskirgan so'rovga javob berilmaydi
        B.inline_work(q("x", 7, "eski"), "x", lambda *a, **k: self.answers.append("xato"))
        self.assertEqual(len(self.answers), n)

    def test_inline_url_fallback(self):
        q = self._inline_env()
        B.bot.send_audio = lambda *a, **k: (_ for _ in ()).throw(OSError("chat not found"))   # saqlash chati ishlamasa
        B.on_inline(q("Salom dunyo", qid="q6"))
        time.sleep(0.6)
        res, _ = self.answers[-1]
        self.assertTrue(res[0].audio_url.startswith(B.APP_URL + "/tts.mp3?q=Salom%20dunyo&voice=uz-UZ-SardorNeural"))
        self.assertTrue(res[0].title.startswith("🔊 Salom") and "Sardor" in res[0].performer and res[0].id != res[1].id)
        path = res[1].audio_url.split(B.APP_URL)[1]            # Telegram aynan shu havolani ochadi
        self.assertEqual((c.get(path).status_code, c.get(path).mimetype), (200, "audio/mpeg"))

    def test_inline_through_telebot_dispatch(self):          # haqiqiy telebot yo'li: Update -> handler
        q = self._inline_env()
        upd = B.types.Update.de_json({"update_id": 1, "inline_query": {"id": "9", "from": {"id": 7, "is_bot": False, "first_name": "x"}, "query": "", "offset": ""}})
        B.bot.process_new_updates([upd])
        time.sleep(0.5)
        self.assertEqual(self.answers[-1][0][0].id, "hint")

    def test_old_buttons_still_work(self):
        done = []
        B.bot.answer_callback_query = lambda *a, **k: done.append(a[-1] if a else None)
        B.bot.edit_message_text = lambda *a, **k: done.append("edit")
        c = lambda data: SimpleNamespace(id="1", data=data, from_user=SimpleNamespace(id=5), message=SimpleNamespace(chat=SimpleNamespace(id=5), message_id=3))
        for data in ("set_tr-TR-AhmetNeural", "v_tr_ahmet", "v:ahmet"):       # eski va yangi tugmalar
            B.S["users"].pop("5", None)
            B.cb_legacy(c(data)) if data[:2] in ("se", "v_") else B.cb_voice(c(data))
            self.assertEqual(B.S["users"]["5"][2], "ahmet", data)
        B.cb_legacy(c("set_en-US-AlexNeural"))                              # mavjud bo'lmagan ovoz: xabar, xato emas
        self.assertIn("eskirgan", done[-1])

    def test_diag(self):
        out = []
        B.bot.send_message = lambda chat, text, **kw: out.append(text)
        B.bot.get_me = lambda: SimpleNamespace(username="Uzbekcha_tts_bot", supports_inline_queries=False)
        B.bot.send_audio = lambda *a, **k: SimpleNamespace(message_id=1, audio=SimpleNamespace(file_id="F"))
        B.bot.delete_message = lambda *a, **k: True
        B.APP_URL = "http://127.0.0.1:9"                      # ulanib bo'lmaydigan manzil: xato matn bilan qaytishi kerak
        B.diag(1)
        text = out[-1]
        self.assertIn("O'CHIQ", text)
        self.assertIn("Ahmet", text)
        self.assertEqual(text.count("✅ 🇺🇿") + text.count("✅ 🇹🇷"), 4)
        self.assertIn("❌ Havola", text)

    def test_signed_link_skips_ip_limit(self):
        combined_app._hits.clear(); combined_app.RATE_PER_MIN = 1
        v = "uz-UZ-SardorNeural"
        self.assertEqual(c.get("/?q=sig1").status_code, 200)
        self.assertEqual(c.get("/?q=sig2").status_code, 429)
        good = f"/tts.mp3?q=sig3&voice={v}&sig={core.sign('sig3', v)}"
        self.assertEqual(c.get(good).status_code, 200)         # imzoli — limitga tushmaydi
        self.assertEqual(c.get(f"/tts.mp3?q=sig4&voice={v}&sig=yolgon").status_code, 429)
        combined_app.RATE_PER_MIN = 40


if __name__ == "__main__":
    unittest.main(verbosity=1)

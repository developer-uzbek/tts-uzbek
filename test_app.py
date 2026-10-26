"""Tezkor tekshiruv (internet va Telegram kerak emas):  python test_app.py"""
import time
import unittest

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
        r = c.post("/api/tts", json={"text": "Привет", "voice": "ru", "style": "robot", "rate": 10})
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
        j = c.get("/api/voices").get_json()
        self.assertTrue(any(v["id"] == "uz-UZ-SardorNeural" for v in j["voices"]) and len(j["styles"]) >= 5)

    def test_options(self):
        o = core.opts({"style": "robot", "rate": "+10%", "pitch": -5, "voice": "sardor"})
        self.assertEqual((o["rate"], o["pitch"], o["voice"]), ("+18%", "+1Hz", "uz-UZ-SardorNeural"))


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


if __name__ == "__main__":
    unittest.main(verbosity=1)

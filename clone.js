/* Mening ovozim — frontend (yozish, tahlil, sintez) */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const MAX_REC = 90; // soniya

  // mavzu (asosiy sahifa bilan bir xil kalit)
  const th = localStorage.getItem("utts_theme");
  if (th) document.documentElement.setAttribute("data-theme", th);

  const state = { takes: [], profiles: [], current: null, rec: null, maxChars: 1500 };

  function toast(t) {
    const d = document.createElement("div");
    d.className = "toast";
    d.textContent = t;
    $("toasts").appendChild(d);
    setTimeout(() => d.remove(), 4000);
  }
  function setMsg(id, text, kind) {
    const el = $(id);
    el.textContent = text || "";
    el.className = "msg" + (kind ? " " + kind : "");
  }
  async function api(url, opt) {
    const r = await fetch(url, opt);
    if (!r.ok) {
      let m = r.statusText;
      try { m = (await r.json()).message || m; } catch (e) {}
      throw new Error(m);
    }
    return r;
  }
  const fmtT = (s) => Math.floor(s / 60) + ":" + String(Math.floor(s % 60)).padStart(2, "0");

  /* ───────── holat / dvigatellar ───────── */
  async function loadStatus() {
    try {
      const d = await (await api("/api/clone/status")).json();
      $("readingText").textContent = d.reading_text;
      state.maxChars = d.max_chars;
      $("maxc").textContent = d.max_chars;
      $("text").maxLength = d.max_chars;
      const e = d.engines;
      const lite = $("engLite"), neu = $("engNeural");
      lite.textContent = "Yengil: " + (e.lite.available ? "tayyor" : "yo'q");
      lite.className = "badge " + (e.lite.available ? "ok" : "no");
      lite.title = e.lite.note;
      neu.textContent = "Neyron: " + (e.neural.available ? "tayyor" : "o'rnatilmagan");
      neu.className = "badge " + (e.neural.available ? "ok" : "no");
      neu.title = e.neural.note;
      if (!e.ffmpeg) toast("ffmpeg topilmadi — brauzer yozuvi ishlamasligi mumkin. README'ga qarang.");
      if (!e.lite.available) setMsg("msg1", "Kutubxonalar yo'q: pip install -r requirements-clone.txt", "err");
      state.profiles = d.profiles || [];
      renderProfiles();
      if (state.profiles.length) await selectProfile(state.profiles[0].id, false);
    } catch (err) {
      setMsg("msg1", "Serverga ulanib bo'lmadi: " + err.message, "err");
    }
  }

  /* ───────── yozish ───────── */
  const meter = $("meter"), mctx = meter.getContext("2d");
  function drawMeter(level) {
    const w = meter.width, h = meter.height;
    mctx.clearRect(0, 0, w, h);
    const grad = mctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, "#6366f1"); grad.addColorStop(1, "#7c3aed");
    mctx.fillStyle = grad;
    mctx.fillRect(0, h / 2 - 2, w * Math.min(1, level * 3), 4);
    mctx.fillStyle = "rgba(148,163,255,.25)";
    for (let i = 0; i < 28; i++) {
      const hh = 3 + Math.min(1, level * 3) * (h - 8) * Math.abs(Math.sin(i * 1.7 + performance.now() / 120));
      mctx.fillRect(i * (w / 28) + 4, (h - hh) / 2, 5, hh);
    }
  }
  drawMeter(0);

  async function startRec() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return toast("Brauzer mikrofonni qo'llamaydi (localhost yoki HTTPS kerak). Fayl yuklang.");
    }
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false },
      });
    } catch (e) { return toast("Mikrofonga ruxsat berilmadi."); }

    const ac = new (window.AudioContext || window.webkitAudioContext)();
    const src = ac.createMediaStreamSource(stream);
    const an = ac.createAnalyser(); an.fftSize = 1024;
    src.connect(an);
    const buf = new Float32Array(an.fftSize);
    const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"].find((m) => MediaRecorder.isTypeSupported(m)) || "";
    const mr = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    const chunks = [];
    const t0 = Date.now();
    let raf;
    const tick = () => {
      an.getFloatTimeDomainData(buf);
      let s = 0; for (const v of buf) s += v * v;
      drawMeter(Math.sqrt(s / buf.length));
      const el = (Date.now() - t0) / 1000;
      $("timer").textContent = fmtT(el);
      if (el >= MAX_REC) stopRec();
      raf = requestAnimationFrame(tick);
    };
    mr.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    mr.onstop = () => {
      cancelAnimationFrame(raf);
      stream.getTracks().forEach((t) => t.stop());
      ac.close();
      drawMeter(0);
      const dur = (Date.now() - t0) / 1000;
      const blob = new Blob(chunks, { type: mr.mimeType || "audio/webm" });
      const ext = (mr.mimeType || "").includes("mp4") ? "m4a" : (mr.mimeType || "").includes("ogg") ? "ogg" : "webm";
      addTake(blob, "yozuv." + ext, dur);
    };
    mr.start(250);
    state.rec = mr;
    $("recBtn").classList.add("on");
    $("recLabel").textContent = "To'xtatish";
    tick();
  }
  function stopRec() {
    if (state.rec && state.rec.state !== "inactive") state.rec.stop();
    state.rec = null;
    $("recBtn").classList.remove("on");
    $("recLabel").textContent = "Yana yozish";
  }
  $("recBtn").addEventListener("click", () => (state.rec ? stopRec() : startRec()));

  $("fileIn").addEventListener("change", async (e) => {
    for (const f of e.target.files) {
      const dur = await probeDuration(f);
      addTake(f, f.name, dur);
    }
    e.target.value = "";
  });
  function probeDuration(blob) {
    return new Promise((res) => {
      const a = new Audio();
      a.preload = "metadata";
      a.src = URL.createObjectURL(blob);
      a.onloadedmetadata = () => res(isFinite(a.duration) ? a.duration : 0);
      a.onerror = () => res(0);
    });
  }

  function addTake(blob, name, dur) {
    state.takes.push({ blob, name, dur });
    renderTakes();
  }
  function renderTakes() {
    const box = $("takes");
    box.textContent = "";
    state.takes.forEach((t, i) => {
      const row = document.createElement("div"); row.className = "take";
      const lab = document.createElement("span"); lab.textContent = "#" + (i + 1) + " · " + (t.dur ? fmtT(t.dur) : "?");
      const au = document.createElement("audio"); au.controls = true; au.src = URL.createObjectURL(t.blob);
      const del = document.createElement("button"); del.type = "button"; del.textContent = "✕"; del.title = "O'chirish";
      del.onclick = () => { state.takes.splice(i, 1); renderTakes(); };
      row.append(lab, au, del);
      box.appendChild(row);
    });
    const total = state.takes.reduce((s, t) => s + (t.dur || 0), 0);
    const el = $("total");
    el.textContent = "Jami: " + Math.round(total) + " soniya · tavsiya: 45–60 soniya";
    el.className = "total" + (total >= 40 ? " good" : "");
    updateAnalyzeBtn();
  }
  function updateAnalyzeBtn() {
    $("analyzeBtn").disabled = !(state.takes.length && $("consent").checked);
  }
  $("consent").addEventListener("change", updateAnalyzeBtn);

  /* ───────── tahlil ───────── */
  $("analyzeBtn").addEventListener("click", async () => {
    const btn = $("analyzeBtn");
    const fd = new FormData();
    state.takes.forEach((t, i) => fd.append("audio", t.blob, t.name || "take" + i + ".webm"));
    fd.append("name", $("pname").value || "Mening ovozim");
    fd.append("consent", "1");
    btn.classList.add("busy"); btn.disabled = true;
    setMsg("msg1", "Tahlil qilinyapti… (10–40 soniya)");
    try {
      const d = await (await api("/api/clone/profile", { method: "POST", body: fd })).json();
      setMsg("msg1", "Tayyor! Profil yaratildi ✓", "ok");
      state.profiles.unshift({ id: d.profile.id, name: d.profile.name });
      renderProfiles();
      showReport(d.profile);
      $("profileSel").value = d.profile.id;
      state.current = d.profile;
      $("step2").scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      setMsg("msg1", err.message, "err");
    } finally {
      btn.classList.remove("busy"); updateAnalyzeBtn();
    }
  });

  /* ───────── hisobot ───────── */
  const METRICS = [
    ["Ohang balandligi (pitch)", "f0_median", "Hz", 70, 300, "Ovozingizning asosiy balandligi"],
    ["Intonatsiya diapazoni", "f0_range_st", "yarim ton", 3, 20, "Ohang qanchalik 'sakraydi'"],
    ["Ifodalilik", "f0_std_st", "st", 1, 7, "Ohang o'zgaruvchanligi (monoton ↔ jonli)"],
    ["Tempo (artikulyatsiya)", "art_rate", "bo'g'in/s", 2.5, 8, "Pauzasiz gapirish tezligi"],
    ["Pauzalar ulushi", "pause_ratio", "", 0, 0.4, "Nutqning qancha qismi sukut", (v) => Math.round(v * 100) + "%"],
    ["Pauza uzunligi", "pause_median", "s", 0.2, 1.2, "Jumlalar orasidagi odatiy to'xtash"],
    ["Energiya / balandlik", "rms_db", "dB", -40, -8, "Umumiy ovoz kuchi"],
    ["Dinamik diapazon", "dyn_range_db", "dB", 5, 35, "Ovoz kuchi o'zgarishi"],
    ["Yorqinlik (spektral tilt)", "tilt_db_oct", "dB/okt", -14, -2, "Yuqori chastotalar miqdori (ravshanlik)"],
    ["Spektral markaz", "centroid_hz", "Hz", 500, 3500, "Ovoz 'yorug'ligi'"],
    ["Ovoz sifati (HNR)", "hnr_db", "dB", 5, 25, "Yuqori = tiniq, past = havodor/xirillagan"],
    ["Jitter (titrash)", "jitter", "", 0, 0.02, "Ohangdagi mayda tebranish", (v) => (v * 100).toFixed(2) + "%"],
    ["Shimmer", "shimmer", "", 0, 0.12, "Kuchdagi mayda tebranish", (v) => (v * 100).toFixed(1) + "%"],
    ["Formant F1", "f1", "Hz", 300, 900, "Tomoq/og'iz ochilishi"],
    ["Formant F2", "f2", "Hz", 900, 2500, "Til holati (tembr asosi)"],
    ["Formant F3", "f3", "Hz", 2000, 3600, "Tomoq uzunligi (ovoz 'o'lchami')"],
  ];
  function showReport(p) {
    $("step2").classList.remove("hidden");
    const chips = $("chips"); chips.textContent = "";
    const S = p.style || {};
    [["Registr", S.registr], ["Tempo", S.tempo], ["Ifodalilik", S.ifodalilik], ["Yorqinlik", S.yorqinlik], ["Ritm", S.ritm], ["Tekstura", S.tekstura]].forEach(([k, v]) => {
      if (!v) return;
      const c = document.createElement("span"); c.className = "chip";
      c.append(k + ": "); const b = document.createElement("b"); b.textContent = v; c.appendChild(b);
      chips.appendChild(c);
    });
    const w = $("warns"); w.textContent = "";
    (p.quality || []).forEach((t) => { const d = document.createElement("div"); d.className = "warn"; d.textContent = "⚠ " + t; w.appendChild(d); });

    const g = $("metrics"); g.textContent = "";
    METRICS.forEach(([label, key, unit, lo, hi, hint, fmt]) => {
      const v = p[key];
      if (v === null || v === undefined) return;
      const m = document.createElement("div"); m.className = "m";
      const t = document.createElement("div"); t.className = "m-t";
      const s = document.createElement("span"); s.textContent = label;
      const b = document.createElement("b"); b.textContent = (fmt ? fmt(v) : v) + (unit ? " " + unit : "");
      t.append(s, b);
      const bar = document.createElement("div"); bar.className = "bar";
      const i = document.createElement("i"); i.style.width = Math.max(3, Math.min(100, ((v - lo) / (hi - lo)) * 100)) + "%";
      bar.appendChild(i);
      const sm = document.createElement("small"); sm.textContent = hint;
      m.append(t, bar, sm);
      g.appendChild(m);
    });
    $("refAudio").src = "/api/clone/profile/" + p.id + "/ref.wav";
  }

  /* ───────── profillar ───────── */
  function renderProfiles() {
    const sel = $("profileSel"); sel.textContent = "";
    if (!state.profiles.length) {
      const o = document.createElement("option"); o.value = ""; o.textContent = "— avval 1-qadamda profil yarating —";
      sel.appendChild(o);
    }
    state.profiles.forEach((p) => {
      const o = document.createElement("option"); o.value = p.id; o.textContent = p.name || p.id;
      sel.appendChild(o);
    });
    updateGen();
  }
  async function selectProfile(id, scroll) {
    if (!id) { state.current = null; return updateGen(); }
    try {
      const d = await (await api("/api/clone/profile/" + id)).json();
      state.current = d.profile;
      showReport(d.profile);
      $("profileSel").value = id;
    } catch (e) { toast(e.message); }
    updateGen();
  }
  $("profileSel").addEventListener("change", (e) => selectProfile(e.target.value));
  $("delBtn").addEventListener("click", async () => {
    const id = $("profileSel").value;
    if (!id || !confirm("Bu profil o'chirilsinmi?")) return;
    await api("/api/clone/profile/" + id, { method: "DELETE" }).catch((e) => toast(e.message));
    state.profiles = state.profiles.filter((p) => p.id !== id);
    state.current = null;
    $("step2").classList.add("hidden");
    renderProfiles();
    if (state.profiles.length) selectProfile(state.profiles[0].id);
  });
  function updateGen() {
    const ok = !!$("profileSel").value;
    $("genBtn").disabled = !ok; $("cmpBtn").disabled = !ok;
  }

  /* ───────── sintez ───────── */
  const textEl = $("text");
  const updCnt = () => ($("cnt").textContent = textEl.value.length);
  textEl.addEventListener("input", updCnt); updCnt();
  $("prosody").addEventListener("input", (e) => ($("pv").textContent = e.target.value + "%"));
  $("match").addEventListener("input", (e) => ($("mv").textContent = e.target.value + "%"));

  function voiceFor() {
    const v = $("baseVoice").value;
    if (v) return v;
    return state.current && state.current.gender_guess === "female" ? "uz-UZ-MadinaNeural" : "uz-UZ-SardorNeural";
  }

  $("genBtn").addEventListener("click", async () => {
    const btn = $("genBtn");
    const text = textEl.value.trim();
    if (!text) return setMsg("msg3", "Matn kiriting.", "err");
    btn.classList.add("busy"); btn.disabled = true;
    setMsg("msg3", "Yaratilyapti… (matn uzunligiga qarab 5–40 soniya)");
    try {
      const r = await api("/api/clone/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile_id: $("profileSel").value,
          text,
          engine: $("engine").value,
          voice: $("baseVoice").value || null,
          prosody: $("prosody").value / 100,
          match: $("match").value / 100,
        }),
      });
      let info = {};
      try { info = JSON.parse(r.headers.get("X-Clone-Info") || "{}"); } catch (e) {}
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      $("outAudio").src = url;
      $("dl").href = url;
      $("dl").download = "mening_ovozim." + (blob.type.includes("wav") ? "wav" : "mp3");
      $("result").classList.remove("hidden");
      $("outAudio").play().catch(() => {});
      $("info").textContent = "dvigatel: " + info.engine + " · asos: " + (info.voice || "").replace("uz-UZ-", "").replace("Neural", "") +
        " · tempo " + info.edge_rate + "% · ohang-nisbat ×" + info.pitch_ratio + " · formant ×" + info.formant_ratio + " · " + info.seconds + "s" +
        (info.neural_error ? " · neyron: " + info.neural_error : "");
      setMsg("msg3", info.engine === "lite" && !info.neural_error ? "Tayyor (yengil rejim). Neyron rejim bilan sifat yuqoriroq bo'ladi." : "Tayyor ✓", "ok");
    } catch (err) {
      setMsg("msg3", err.message, "err");
    } finally {
      btn.classList.remove("busy"); btn.disabled = false;
    }
  });

  $("cmpBtn").addEventListener("click", async () => {
    const text = textEl.value.trim();
    if (!text) return;
    const btn = $("cmpBtn"); btn.disabled = true;
    try {
      const r = await api("/api/tts", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice: voiceFor() }),
      });
      $("plainAudio").src = URL.createObjectURL(await r.blob());
      $("plainRow").classList.remove("hidden");
      $("result").classList.remove("hidden");
      $("plainAudio").play().catch(() => {});
    } catch (err) { setMsg("msg3", err.message, "err"); }
    finally { btn.disabled = false; }
  });

  loadStatus();
})();

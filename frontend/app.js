/* Alpha Desk — logique front. Sépare volontairement du HTML/CSS pour
   rester modifiable indépendamment. */

const API_URL = "http://localhost:8000";

const AGENT_LABELS = {
  macro: "Macro",
  fundamentals: "Fondamental",
  technical: "Technique",
  risk: "Risque / Compliance",
};

const el = (id) => document.getElementById(id);

function setStatus(dotState, text) {
  const dot = el("status-dot");
  const label = el("status-text");
  dot.className = "status-dot" + (dotState ? ` ${dotState}` : "");
  label.textContent = text;
}

function renderRow(stance) {
  const row = document.createElement("div");
  row.className = `row ${stance.stance}`;

  const pct = Math.round((stance.confidence || 0) * 100);
  const tags = (stance.key_points || [])
    .map((p) => `<span class="tag">${escapeHtml(p)}</span>`)
    .join("");

  row.innerHTML = `
    <div class="row-main">
      <div class="row-head">
        <span class="row-agent">${AGENT_LABELS[stance.agent] || stance.agent}</span>
        <span class="row-stance ${stance.stance}">${stance.stance}</span>
      </div>
      <p class="row-reasoning">${escapeHtml(stance.reasoning || "")}</p>
      <div class="row-tags">${tags}</div>
    </div>
    <div class="row-confidence" style="color: var(--${cssColorFor(stance.stance)})">
      <div class="pct">${pct}%</div>
      <div class="bar"><div style="width:${pct}%"></div></div>
    </div>
  `;
  return row;
}

function cssColorFor(stance) {
  if (stance === "bullish") return "bull";
  if (stance === "bearish") return "bear";
  return "neutral";
}

function renderMemo(memo) {
  const box = el("memo");
  box.hidden = false;
  const pct = Math.round((memo.confidence || 0) * 100);
  box.innerHTML = `
    <div class="memo-head">
      <div class="memo-rec ${memo.recommendation}">${memo.recommendation}</div>
      <div class="memo-confidence">confiance<span class="pct">${pct}%</span></div>
    </div>
    <p class="memo-body">${escapeHtml(memo.memo || "")}</p>
    <div class="memo-section">
      <div class="memo-section-label">Risques clés</div>
      <p class="memo-section-body">${escapeHtml((memo.key_risks || []).join(" — "))}</p>
    </div>
    <div class="memo-section">
      <div class="memo-section-label">Avis dissident</div>
      <p class="memo-section-body">${escapeHtml(memo.dissenting_views || "—")}</p>
    </div>
  `;
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

/* ---- Entrée vocale (Gradium STT) ---- */

let mediaRecorder = null;
let audioChunks = [];

async function toggleMic() {
  const micBtn = el("mic");
  const micStatus = el("mic-status");

  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      micBtn.classList.remove("recording");
      micStatus.hidden = false;
      micStatus.textContent = "Transcription en cours…";
      const blob = new Blob(audioChunks, { type: "audio/webm" });
      const form = new FormData();
      form.append("file", blob, "question.webm");
      try {
        const res = await fetch(`${API_URL}/listen`, { method: "POST", body: form });
        const data = await res.json();
        if (data.available && data.text) {
          el("query").value = data.text;
          micStatus.textContent = `Transcrit : "${data.text}"`;
        } else {
          micStatus.textContent = "Voix indisponible (clé Gradium manquante ?) — tape ta question.";
        }
      } catch (e) {
        micStatus.textContent = "Erreur de transcription : " + e.message;
      }
    };
    mediaRecorder.start();
    micBtn.classList.add("recording");
    micStatus.hidden = false;
    micStatus.textContent = "Enregistrement… reclique pour arrêter.";
  } catch (e) {
    micStatus.hidden = false;
    micStatus.textContent = "Micro indisponible : " + e.message;
  }
}

el("mic").addEventListener("click", toggleMic);

/* ---- Sortie vocale (Gradium TTS) ---- */

async function speakText(text, agent) {
  try {
    const res = await fetch(`${API_URL}/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, agent }),
    });
    if (res.status === 204) return null;
    const blob = await res.blob();
    const audio = new Audio(URL.createObjectURL(blob));
    return new Promise((resolve) => {
      audio.onended = resolve;
      audio.onerror = resolve;
      audio.play().catch(resolve);
    });
  } catch (e) {
    return null;
  }
}

/* ---- Lancement d'une analyse ---- */

async function run() {
  const ticker = el("ticker").value.trim() || "NVDA";
  const query = el("query").value.trim() || `Faut-il investir dans ${ticker} ?`;
  const feed = el("feed");
  const status = el("run-status");
  const goBtn = el("go");
  const memoEl = el("memo");
  const degradedEl = el("degraded-banner");

  feed.innerHTML = "";
  memoEl.hidden = true;
  degradedEl.hidden = true;
  status.className = "run-status";
  status.textContent = "";
  goBtn.disabled = true;
  setStatus("busy", "La desk se réunit…");

  try {
    const res = await fetch(`${API_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker, query }),
    });
    if (!res.ok) throw new Error(`Erreur API (${res.status})`);
    const data = await res.json();

    if (data.degraded_reason) {
      degradedEl.hidden = false;
      degradedEl.textContent =
        "Pipelex indisponible pour ce run — la desk a basculé sur son chemin de secours (mêmes données réelles, même raisonnement).";
    }

    for (const stance of data.stances) {
      setStatus("busy", `${AGENT_LABELS[stance.agent] || stance.agent} analyse…`);
      feed.appendChild(renderRow(stance));
      const played = await speakText(stance.reasoning, stance.agent);
      if (played === null) await new Promise((r) => setTimeout(r, 850));
    }

    setStatus("busy", "Le Portfolio Manager tranche…");
    renderMemo(data.memo);
    const played = await speakText(data.memo.memo, "portfolio_manager");
    if (played === null) await new Promise((r) => setTimeout(r, 500));

    setStatus(null, "Desk prête");
  } catch (e) {
    setStatus("error", "Erreur");
    status.className = "run-status is-error";
    status.textContent = e.message + " ";
    const retry = document.createElement("button");
    retry.className = "retry-btn";
    retry.textContent = "Réessayer";
    retry.type = "button";
    retry.onclick = run;
    status.appendChild(retry);
  } finally {
    goBtn.disabled = false;
  }
}

el("desk-form").addEventListener("submit", (e) => {
  e.preventDefault();
  run();
});

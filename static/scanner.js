/* ──────────────────────────────────────────────────────────────
   Floor-Management-System – QR-scanner front-end
   • expects html5-qrcode.min.js already loaded
   • posts parsed payload to  /api/products  (Flask route)
   • shows a toast for success / duplicate / errors
   ──────────────────────────────────────────────────────────── */

/* ---------- tiny helpers ---------- */
const qs   = sel => document.querySelector(sel);
const toast = (msg, ok = true) => {
  const box = qs("#toast");
  box.textContent      = msg;
  box.style.background = ok ? "var(--accent)" : "var(--danger)";
  box.classList.add("show");
  setTimeout(() => box.classList.remove("show"), 2500);
};
const setBtn = running => {
  const b = qs("#start-btn");
  b.textContent      = running ? "✖ Stop Scanner" : "📷 Start Scanner";
  b.style.background = running ? "var(--danger)" : "var(--accent)";
};

/* ---------- scanner state ---------- */
let reader;          // Html5Qrcode instance (lazy-init)
let running = false; // camera on/off flag

/* ---------- start / stop ---------- */
async function start() {
  if (running) return;

  try {
    reader ??= new Html5Qrcode("reader");          // first time only
    const cams  = await Html5Qrcode.getCameras();  // camera list
    if (!cams.length) throw new Error("No camera found");

    const back  = cams.find(c =>
                    /back|rear|environment/i.test(c.label)) || cams[0];

    await reader.start(
      { deviceId: { exact: back.id } },
      { fps: 10, qrbox: { width: 240, height: 240 } },
      onScan
    );
    running = true;
    setBtn(true);

  } catch (e) {
    toast(e.message || "Camera start failed", false);
  }
}

async function stop() {
  if (!running || !reader) return;
  await reader.stop();
  running = false;
  setBtn(false);
}

/* ---------- scan callback ---------- */
async function onScan(text) {
  // expected format → serial=123;order=ORD1;size=8.5
  const record = Object.fromEntries(
    text.split(";").map(p => p.split("=").map(s => s.trim()))
  );

  // fill form
  qs("#serial").value = record.serial ?? "";
  qs("#order").value  = record.order  ?? "";
  qs("#size").value   = record.size   ?? "";

  // send to DB
  saveToDB(record);

  // optional: stop after one read
  stop();
}

/* ---------- POST to Flask API ---------- */
async function saveToDB(data) {
  try {
    const r = await fetch("/api/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        serial: data.serial,
        order : data.order,
        size  : data.size
      })
    });

    if (r.status === 201)             toast("✅ Saved", true);
    else if (r.status === 409)        toast("⚠️ Duplicate serial", false);
    else {
      const j = await r.json().catch(() => ({}));
      toast(j.error || "DB error", false);
    }

  } catch {
    toast("Network error", false);
  }
}

/* ---------- wire button ---------- */
qs("#start-btn").onclick = () => running ? stop() : start();

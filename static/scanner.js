/* ---------- helpers ---------- */
function toast(txt, ok = true) {
  const t = document.getElementById("toast");
  t.textContent = txt;
  t.style.background = ok ? "var(--accent)" : "var(--danger)";
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3000);
}
function btn(running) {
  const b = document.getElementById("start-btn");
  b.textContent = running ? "✖ Stop Scanner" : "📷 Start Scanner";
  b.style.background = running ? "var(--danger)" : "var(--accent)";
  b.onclick = running ? stopScan : startScan;
}

/* ---------- globals ---------- */
let reader, scanning = false;

/* ---------- main flow ---------- */
async function startScan() {
  if (scanning) return;
  scanning = true; btn(true);

  try {
    /* 1️⃣  enumerate cameras first */
    const cams = await Html5Qrcode.getCameras();
    if (!cams.length) throw "No camera device found";

    /* 2️⃣  request permission explicitly (helps on Samsung / Mi browser) */
    await navigator.mediaDevices.getUserMedia({ video: true });

    /* 3️⃣  lazily create reader */
    reader ??= new Html5Qrcode("reader");

    /* choose back-camera if we can */
    const camId = cams.find(c => /back|rear|environment/i.test(c.label))
                 ?.id || cams[0].id;

    await reader.start(
      { deviceId: { exact: camId } },
      { fps: 10, qrbox: { width: 240, height: 240 } },
      onScan
    );
    /* live! */
  } catch (e) {
    console.warn(e);                      // <-- tiny debug
    toast(typeof e === "string" ? e : "Camera start failed", false);
    scanning = false; btn(false);
  }
}

async function stopScan() {
  if (!reader || !scanning) return;
  await reader.stop();
  scanning = false; btn(false);
}

async function onScan(qrText) {
  const obj = Object.fromEntries(
    qrText.split(";").map(p => p.split("=").map(s => s.trim()))
  );
  serial.value = obj.serial ?? "";
  order.value  = obj.order  ?? "";
  size.value   = obj.size  ?? "";

  await saveToDB(obj);
  await stopScan();
}

async function saveToDB(row) {
  try {
    const r = await fetch("/api/products", {
      method: "POST",
      headers: { "Content-Type":"application/json" },
      body: JSON.stringify({
        serial: row.serial,
        order : row.order,
        size  : row.size
      })
    });
    toast(r.status === 201 ? "Saved!" : "DB error", r.status === 201);
  } catch {
    toast("Network error", false);
  }
}

/* ---------- wire up once DOM is parsed (script is defer-loaded) ---------- */
document.getElementById("start-btn").onclick = startScan;

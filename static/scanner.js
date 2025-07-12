/* scanner.js – drop this in static/  (replace whole file)  */
let reader, scanning = false;

// ---------- UI helpers -----------------------------------
function toast(msg, ok = true) {
  const t = document.createElement("div");
  t.textContent = msg;
  t.style.cssText = `
    position:fixed;bottom:1.5rem;left:50%;transform:translateX(-50%);
    background:${ok ? "#24c663" : "#d9534f"};
    color:#fff;font-weight:600;padding:.65rem 1rem;border-radius:.7rem;
    z-index:999`;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2600);
}

function setBtn(starting) {
  const btn = document.getElementById("start-btn");
  btn.textContent = starting ? "✖ Stop Scanner" : "📷 Start Scanner";
  btn.style.background = starting ? "#d9534f" : "#24c663";
  btn.onclick = starting ? stopScan : startScan;
}

// ---------- scanner --------------------------------------
async function startScan() {
  if (scanning) return;
  scanning = true;

  try { await navigator.mediaDevices.getUserMedia({ video:true }); }
  catch { toast("Camera permission denied", false); scanning = false; return; }

  reader ??= new Html5Qrcode("reader");
  const cfg = { fps: 10, qrbox: { width: 240, height: 240 } };

  try {
    await reader.start({ facingMode:"environment" }, cfg, handleScan);
    setBtn(true);
  } catch (e) {
    toast("Camera start failed", false);
    scanning = false;
  }
}

async function stopScan() {
  if (reader && scanning) await reader.stop();
  setBtn(false);
  scanning = false;
}

async function handleScan(text) {
  // expected pattern: key=value;key=value…
  const parts = Object.fromEntries(
    text.split(";").map(p => p.split("=").map(s => s.trim()))
  );
  serial.value = parts.serial ?? "";
  order.value  = parts.order  ?? "";
  size.value   = parts.size   ?? "";
  await saveRow(parts);
  stopScan();
}

// ---------- ajax -----------------------------------------
async function saveRow(data) {
  try {
    const res = await fetch("/api/products", {
      method: "POST",
      headers: { "Content-Type":"application/json" },
      body: JSON.stringify({
        serial: data.serial, order: data.order, size: data.size
      })
    });

    if (res.status === 201)         toast("✅ Saved");
    else if (res.status === 409)    toast("⚠️ Duplicate serial", false);
    else {
      const j = await res.json().catch(()=>({}));
      toast(j.error || "DB error", false);
    }
  } catch { toast("Network error", false); }
}

// wire button
document.addEventListener("DOMContentLoaded", () =>
  document.getElementById("start-btn").onclick = startScan);

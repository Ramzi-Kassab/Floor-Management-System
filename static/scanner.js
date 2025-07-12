/* same as before … only add this at the very top */
if (typeof Html5Qrcode === "undefined") {
  alert("Camera library failed to load – check network or CSP");
}

/*  html5-qrcode glue  –  keeps the UI small & mobile friendly  */
let reader = null, scanning = false;

/* and replace startScan with one extra await – forces permission prompt */
async function startScan() {
  if (scanning) return;
  scanning = true;

  // 👉 Ensure we actually have camera permission before creating Html5Qrcode
  try { await navigator.mediaDevices.getUserMedia({ video:true }); }
  catch (e) { toast("Camera permission required", false); scanning=false; return; }

  reader ??= new Html5Qrcode("reader");

  // nice square frame
  const config = { fps: 10, qrbox: { width: 240, height: 240 } };

  try {
    await reader.start({ facingMode: "environment" }, config, onScan);
    toggleBtn(true);
  } catch (e) {
    alert("Camera start failed:\n" + e);
    scanning = false;
  }
}

async function stopScan() {
  if (!reader || !scanning) return;
  await reader.stop();
  toggleBtn(false);
  scanning = false;
}

function toggleBtn(active) {
  const btn = document.querySelector("button");
  btn.textContent = active ? "✖ Stop Scanner" : "📷 Start Scanner";
  btn.style.background = active ? "#d9534f" : "#24c663";
  btn.onclick = active ? stopScan : startScan;
}

function onScan(msg) {
  // expected QR payload:  serial=123;order=ORD99;size=10x5
  const parts = Object.fromEntries(
    msg.split(";").map(p => p.split("=").map(s => s.trim()))
  );
  // populate form
  serial.value = parts.serial ?? "";
  order.value  = parts.order  ?? "";
  size.value   = parts.size   ?? "";

  // send to server
  saveToDB(parts);
  stopScan();
}

async function saveToDB(data) {
  try {
    const r = await fetch("/api/products", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        serial: data.serial,
        order : data.order,
        size  : data.size
      })
    });
    const ok = r.status === 201;
    toast(ok ? "DB save ok" : "DB save failed", ok);
  } catch (e) {
    toast("network error", false);
  }
}

function toast(txt, good) {
  const t = document.createElement("div");
  t.textContent = txt;
  t.style.cssText = `
    position:fixed;bottom:1.5rem;left:50%;transform:translateX(-50%);
    background:${good ? "#24c663" : "#d9534f"};color:#fff;padding:.6rem 1.2rem;
    border-radius:.75rem;font-weight:600;z-index:999;`;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

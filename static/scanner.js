// ---------- helpers ----------
function toast(msg, ok = true) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.style.background = ok ? "var(--accent)" : "var(--danger)";
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3000);
}

function toggleBtn(running) {
  const btn = document.getElementById("start-btn");
  btn.textContent = running ? "✖ Stop Scanner" : "📷 Start Scanner";
  btn.style.background = running ? "var(--danger)" : "var(--accent)";
}

// ---------- scanner ----------
let reader, scanning = false;

async function startScan() {
  if (scanning) return;
  scanning = true;
  toggleBtn(true);

  // ask for cam permission first
  try { await navigator.mediaDevices.getUserMedia({ video:true }); }
  catch {
    toast("Enable camera permission", false);
    scanning = false;
    toggleBtn(false);
    return;
  }

  reader ??= new Html5Qrcode("reader");
  const cfg = { fps: 10, qrbox:{ width:240, height:240 } };

  try {
    await reader.start({ facingMode:"environment" }, cfg, onScan);
  } catch (err) {
    toast("Camera start failed", false);
    scanning = false;
    toggleBtn(false);
  }
}

async function stopScan() {
  if (!reader || !scanning) return;
  await reader.stop();
  scanning = false;
  toggleBtn(false);
}

async function onScan(text) {
  // serial=123;order=ORD1;size=8x5
  const obj = Object.fromEntries(
    text.split(";").map(p=>p.split("=").map(s=>s.trim()))
  );
  serial.value = obj.serial ?? "";
  order.value  = obj.order  ?? "";
  size.value   = obj.size   ?? "";

  await saveToDB(obj);
  await stopScan();
}

async function saveToDB(data) {
  try {
    const res = await fetch("/api/products", {
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({
        serial:data.serial,
        order :data.order,
        size  :data.size
      })
    });
    toast(res.status===201 ? "Saved!" : "DB save failed", res.status===201);
  } catch {
    toast("Network error", false);
  }
}

// ---------- wire up ----------
document.getElementById("start-btn").onclick = startScan;

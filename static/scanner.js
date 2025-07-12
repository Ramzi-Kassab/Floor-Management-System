/* ---------- helpers ---------- */
const toast = (msg, ok=true) => {
  const box = document.getElementById("toast");
  box.textContent = msg;
  box.style.background = ok ? "var(--accent)" : "var(--danger)";
  box.classList.add("show");
  setTimeout(() => box.classList.remove("show"), 2500);
};

const setBtn = running => {
  const b = document.getElementById("start-btn");
  b.textContent  = running ? "✖ Stop Scanner" : "📷 Start Scanner";
  b.style.background = running ? "var(--danger)" : "var(--accent)";
};

/* ---------- scanner ---------- */
let reader, running=false;

async function start() {
  if (running) return;
  try {
    /* let html5-qrcode handle permission prompt */
    reader ??= new Html5Qrcode("reader");

    const cams  = await Html5Qrcode.getCameras();
    if (!cams.length) throw new Error("No camera found");

    const back  = cams.find(c=>/back|rear|environment/i.test(c.label)) || cams[0];

    await reader.start(
      { deviceId:{ exact: back.id } },
      { fps:10, qrbox:{width:240,height:240} },
      onScan
    );
    running=true; setBtn(true);
  } catch (e) {
    toast(e.message || e, false);
  }
}

async function stop(){
  if (!running) return;
  await reader.stop();
  running=false; setBtn(false);
}

async function onScan(text){
  const obj = Object.fromEntries(text.split(";").map(p=>p.split("=")));
  serial.value=obj.serial??""; order.value=obj.order??""; size.value=obj.size??"";

  /* POST row */
  try{
    const r = await fetch("/api/products",{
      method:"POST",headers:{ "Content-Type":"application/json"},
      body: JSON.stringify({
        serial:obj.serial,order:obj.order,size:obj.size
      })
    });
    toast(r.status===201?"Saved":"DB error", r.status===201);
  }catch{toast("Network error", false);}
  stop();
}

async function saveToDB(data) {
  try {
    const res = await fetch("/api/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        serial: data.serial,
        order : data.order,
        size  : data.size
      })
    });

    if (res.status === 201)  toast("✅ Saved",   true);
    else if (res.status === 409) toast("⚠️  Duplicate serial", false);
    else {
      const j = await res.json().catch(() => ({}));
      toast(j.error || "DB error", false);
    }

  } catch {
    toast("Network error", false);
  }
}

/* ---------- wire up ---------- */
document.getElementById("start-btn").onclick = () => running ? stop() : start();

/* eslint-env browser */
(() => {
  const readerDiv = document.getElementById("reader");
  const btn       = document.getElementById("start-btn");
  const toast     = document.getElementById("toast");

  const inputs = {
    serial: document.getElementById("serial"),
    order : document.getElementById("order"),
    size  : document.getElementById("size")
  };

  let scanner;

  function showToast(msg, ok = true) {
    toast.textContent = msg;
    toast.className   = ok ? "" : "error";
    toast.style.opacity = 1;
    setTimeout(() => (toast.style.opacity = 0), 2500);
  }

  async function sendToServer(payload) {
    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const js = await res.json();
      if (!res.ok) throw js.error || "API error";
      showToast("✓ Saved to DB");
    } catch (err) {
      console.error(err);
      showToast("DB save failed", false);
    }
  }

  function handleDecoded(text) {
    // Expected "serial=123;order=AB123;size=8.5"
    text.split(";").forEach(pair => {
      const [k, v] = pair.split("=");
      if (k && v && inputs[k]) inputs[k].value = v;
    });

    sendToServer({
      serial_number: inputs.serial.value,
      order_number : inputs.order.value,
      size         : inputs.size.value
    });
  }

  btn.addEventListener("click", async () => {
    if (scanner) {
      await scanner.stop(); scanner = null;
      btn.textContent = "📷 Start Scanner";
      readerDiv.innerHTML = "";
      return;
    }

    scanner = new Html5Qrcode("reader");
    const config = { fps: 10, qrbox: 250 };
    try {
      await scanner.start({ facingMode: "environment" }, config, handleDecoded);
      btn.textContent = "✖ Stop Scanner";
    } catch (err) {
      console.error(err);
      showToast("Camera error", false);
      scanner = null;
    }
  });
})();

function startScan() {
  const reader = new Html5Qrcode("reader");
  const config = { fps: 10, qrbox: 250 };
  reader.start({ facingMode: "environment" }, config,
    msg => {
      let pairs = msg.split(";");
      pairs.forEach(p => {
        let [key, val] = p.split("=");
        let el = document.getElementById(key);
        if (el) el.value = val;
      });
      reader.stop();
    },
    err => console.warn("QR Error:", err)
  ).catch(err => console.error("Start Error:", err));
}

function submitForm() {
  const data = {
    serial: document.getElementById("serial").value,
    order: document.getElementById("order").value,
    size: document.getElementById("size").value
  };

  fetch("https://your-backend-url.onrender.com/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
  .then(res => res.json())
  .then(res => alert("Submitted: " + JSON.stringify(res)))
  .catch(err => console.error("Submit error:", err));
}

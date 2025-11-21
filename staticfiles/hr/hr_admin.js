/* Global admin helpers for HR forms in floor_app */

/* 1) Sync calling_code when country <select> changes (reads <option data-cc="...">) */
(function countryToCode(){
  function sync() {
    var sel = document.getElementById("id_country_iso2");
    var codeInput = document.getElementById("id_calling_code");
    if (!sel || !codeInput) return;
    var opt = sel.options[sel.selectedIndex];
    var cc = opt && opt.getAttribute("data-cc");
    codeInput.value = cc || "";
  }
  document.addEventListener("DOMContentLoaded", function(){
    sync();
    var sel = document.getElementById("id_country_iso2");
    if (sel) sel.addEventListener("change", sync);
  });
})();

/* 2) Landline ⇒ disable Whats / Both */
(function landlineChannel(){
  function enforce() {
    var kindSel = document.getElementById("id_kind");
    var chSel = document.getElementById("id_channel");
    if (!kindSel || !chSel) return;

    var isLand = kindSel.value === "LAND";
    for (var i = 0; i < chSel.options.length; i++) chSel.options[i].disabled = false;

    if (isLand) {
      for (var j = 0; j < chSel.options.length; j++) {
        var v = chSel.options[j].value;
        if (v === "WHATS" || v === "BOTH") chSel.options[j].disabled = true;
      }
      if (chSel.value !== "CALL") chSel.value = "CALL";
    }
  }
  document.addEventListener("DOMContentLoaded", function(){
    enforce();
    var kindSel = document.getElementById("id_kind");
    if (kindSel) kindSel.addEventListener("change", enforce);
  });
})();

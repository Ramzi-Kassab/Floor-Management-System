(function() {
  function $(name) { return document.querySelector('input[name="' + name + '"]'); }

  function toHijri(gy, gm, gd) {
    try {
      var m = moment([gy, gm - 1, gd]);
      var hy = m.iYear(), hm = m.iMonth() + 1, hd = m.iDate();
      return hy.toString().padStart(4, "0") + "-" +
             hm.toString().padStart(2, "0") + "-" +
             hd.toString().padStart(2, "0");
    } catch (e) { return ""; }
  }

  function toGreg(hy, hm, hd) {
    try {
      var m = moment().iYear(hy).iMonth(hm - 1).iDate(hd);
      var gy = m.year(), gm = m.month() + 1, gd = m.date();
      return gy.toString().padStart(4, "0") + "-" +
             gm.toString().padStart(2, "0") + "-" +
             gd.toString().padStart(2, "0");
    } catch (e) { return ""; }
  }

  function syncFromGreg() {
    var g = $('date_of_birth'); var h = $('date_of_birth_hijri');
    if (!g || !h || !g.value) return;
    var p = g.value.split("-"); if (p.length !== 3) return;
    var hijri = toHijri(parseInt(p[0]), parseInt(p[1]), parseInt(p[2]));
    if (hijri) h.value = hijri;
  }

  function syncFromHijri() {
    var g = $('date_of_birth'); var h = $('date_of_birth_hijri');
    if (!g || !h || !h.value) return;
    var p = h.value.split("-"); if (p.length !== 3) return;
    var greg = toGreg(parseInt(p[0]), parseInt(p[1]), parseInt(p[2]));
    if (greg) g.value = greg;
  }

  function ready(fn){ /in/.test(document.readyState) ? setTimeout(function(){ready(fn);}, 50) : fn(); }
  ready(function() {
    var g = $('date_of_birth'); var h = $('date_of_birth_hijri');
    if (g) g.addEventListener('change', syncFromGreg);
    if (h) h.addEventListener('change', syncFromHijri);
  });
})();

(function () {
  'use strict';

  var FRAMES = 62;
  var canvas = document.getElementById('cup');
  var ctx = canvas.getContext('2d');
  var scrub = document.getElementById('scrub');
  var hint = document.getElementById('hint');
  var caps = Array.prototype.slice.call(document.querySelectorAll('.cap'));
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var imgs = [];
  var current = -1;
  var ticking = false;

  function src(i) { return 'img/f' + String(i + 1).padStart(3, '0') + '.webp'; }

  for (var i = 0; i < FRAMES; i++) {
    var im = new Image();
    im.decoding = 'async';
    im.src = src(i);
    if (i === 0) im.onload = function () { size(); draw(true); };
    imgs.push(im);
  }

  function size() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(canvas.clientWidth * dpr);
    canvas.height = Math.round(canvas.clientHeight * dpr);
  }

  function progress() {
    var r = scrub.getBoundingClientRect();
    var total = scrub.offsetHeight - window.innerHeight;
    if (total <= 0) return 1;
    return Math.min(1, Math.max(0, -r.top / total));
  }

  function nearestLoaded(idx) {
    for (var d = 0; d < FRAMES; d++) {
      var a = imgs[idx - d], b = imgs[idx + d];
      if (a && a.complete && a.naturalWidth) return a;
      if (b && b.complete && b.naturalWidth) return b;
    }
    return null;
  }

  function paint(img) {
    var cw = canvas.width, ch = canvas.height;
    var s = Math.max(cw / img.naturalWidth, ch / img.naturalHeight);
    var w = img.naturalWidth * s, h = img.naturalHeight * s;
    ctx.fillStyle = '#0B0806';
    ctx.fillRect(0, 0, cw, ch);
    ctx.drawImage(img, (cw - w) / 2, (ch - h) / 2, w, h);
  }

  function draw(force) {
    var p = reduce ? 1 : progress();
    var idx = Math.min(FRAMES - 1, Math.round(p * (FRAMES - 1)));
    if (idx !== current || force) {
      var img = nearestLoaded(idx);
      if (img) { paint(img); current = idx; }
    }
    caps.forEach(function (c) {
      var on = p >= parseFloat(c.dataset.from) && p < parseFloat(c.dataset.to);
      c.classList.toggle('on', on);
    });
    hint.style.opacity = p > 0.04 ? '0' : '1';
    ticking = false;
  }

  function onScroll() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(function () { draw(false); }); }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', function () { size(); draw(true); });
  size();
  draw(true);

  // Order card
  var price = document.getElementById('price');
  var q = document.getElementById('q');
  var wa = document.getElementById('wa');
  var state = { size: 'وسط', unit: 18, milk: 'كامل الدسم', qty: 1 };

  function pick(group, btn) {
    group.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', String(b === btn)); });
  }

  function update() {
    var total = state.unit * state.qty;
    price.textContent = total + ' ر.س';
    q.textContent = state.qty;
    var msg = 'طلب تجريبي من صفحة بن وليل: ' + state.qty + ' × لاتيه الهيل (' + state.size + '، حليب ' + state.milk + ') = ' + total + ' ر.س';
    wa.href = 'https://wa.me/33777897299?text=' + encodeURIComponent(msg);
  }

  document.querySelectorAll('.seg').forEach(function (group) {
    group.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      pick(group, b);
      if (b.dataset.size) { state.size = b.dataset.size; state.unit = parseInt(b.dataset.price, 10); }
      if (b.dataset.milk) state.milk = b.dataset.milk;
      update();
    });
  });
  document.getElementById('plus').addEventListener('click', function () { if (state.qty < 20) { state.qty++; update(); } });
  document.getElementById('minus').addEventListener('click', function () { if (state.qty > 1) { state.qty--; update(); } });
  update();
})();

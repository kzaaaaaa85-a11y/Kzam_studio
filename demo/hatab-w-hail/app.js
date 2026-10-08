// Demo cart for the "حطب وهيل" sample landing page.
// To reuse the page for a real restaurant: change WA_NUMBER, ITEMS and the two message lines.
(function () {
  'use strict';

  var WA_NUMBER = '33777897299';
  var HELLO = 'السلام عليكم، جربت نموذج صفحة «حطب وهيل» من Kzam Studio.';
  var ASK = 'أبغى صفحة مثلها لمطعمي.';

  var ITEMS = [
    { id: 'offer', name: 'عرض الغداء: مندي دجاج + سمبوسة + لبن', price: 39 },
    { id: 'mandi', name: 'مندي دجاج، نص دجاجة', price: 32 },
    { id: 'lamb', name: 'مندي لحم', price: 68 },
    { id: 'madhbi', name: 'مظبي دجاج', price: 58 },
    { id: 'sambosa', name: 'سمبوسة لحم', price: 14 },
    { id: 'kunafa', name: 'كنافة بالقشطة', price: 24 },
    { id: 'shorba', name: 'شوربة عدس', price: 9 },
    { id: 'salata', name: 'سلطة حارة', price: 7 },
    { id: 'laban', name: 'لبن', price: 4 },
    { id: 'shai', name: 'شاي عدني', price: 12 },
    { id: 'gahwa', name: 'قهوة سعودية', price: 10 }
  ];

  var cart = {};
  var PLUS = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';
  var MINUS = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><path d="M5 12h14"/></svg>';

  function itemById(id) {
    for (var i = 0; i < ITEMS.length; i++) if (ITEMS[i].id === id) return ITEMS[i];
    return null;
  }

  function button(cls, html, label, onClick) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = cls;
    b.innerHTML = html;
    if (label) b.setAttribute('aria-label', label);
    b.addEventListener('click', onClick);
    return b;
  }

  function change(id, delta, focusCls) {
    var n = (cart[id] || 0) + delta;
    if (n <= 0) delete cart[id]; else cart[id] = n;
    render();
    var box = document.querySelector('.qty[data-id="' + id + '"]');
    var target = box && (box.querySelector('.' + focusCls) || box.querySelector('button'));
    if (target) target.focus({ preventScroll: true });
    var bar = document.getElementById('bar');
    bar.classList.remove('bump');
    void bar.offsetWidth;
    bar.classList.add('bump');
  }

  function renderQty(box) {
    var id = box.getAttribute('data-id');
    var item = itemById(id);
    var label = box.getAttribute('data-label');
    var name = box.getAttribute('data-name') || item.name;
    var n = cart[id] || 0;
    box.textContent = '';
    if (!n) {
      box.appendChild(button('add', PLUS + (label ? '<span>' + label + '</span>' : ''),
        label ? null : 'أضف ' + name + ' للطلب',
        function () { change(id, 1, 'plus'); }));
      return;
    }
    box.appendChild(button('step minus', MINUS, 'نقّص ' + name, function () { change(id, -1, 'minus'); }));
    var count = document.createElement('span');
    count.className = 'count num';
    count.textContent = n;
    box.appendChild(count);
    box.appendChild(button('step plus', PLUS, 'زوّد ' + name, function () { change(id, 1, 'plus'); }));
  }

  function render() {
    var count = 0, total = 0, lines = [];
    ITEMS.forEach(function (it) {
      var n = cart[it.id] || 0;
      if (!n) return;
      count += n;
      total += n * it.price;
      lines.push('• ' + it.name + ' ×' + n);
    });

    var boxes = document.querySelectorAll('.qty[data-id]');
    for (var i = 0; i < boxes.length; i++) renderQty(boxes[i]);

    var text = document.getElementById('bar-text');
    text.textContent = '';
    if (count) {
      var b = document.createElement('b');
      b.className = 'num';
      b.textContent = total + ' ريال';
      text.appendChild(b);
      text.appendChild(document.createTextNode('الأطباق: ' + count));
    } else {
      text.textContent = 'اختر أطباقك من المنيو، والإجمالي يظهر هنا.';
    }
    text.classList.toggle('has', count > 0);
    document.getElementById('clear').hidden = !count;
    document.getElementById('bar-cta-text').textContent = count ? 'أرسل الطلب' : 'اطلب واتساب';

    var msg = count
      ? HELLO + '\nالطلب التجريبي:\n' + lines.join('\n') + '\nالإجمالي: ' + total + ' ريال\n' + ASK
      : HELLO + ' ' + ASK;
    var href = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(msg);
    var links = document.querySelectorAll('a[data-wa]');
    for (var j = 0; j < links.length; j++) links[j].href = href;
  }

  document.getElementById('clear').addEventListener('click', function () {
    cart = {};
    render();
  });

  render();
})();

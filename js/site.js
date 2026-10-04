// Smooth-scroll buttons: <button data-scroll="section-id">
document.querySelectorAll('[data-scroll]').forEach(function (btn) {
    btn.addEventListener('click', function () {
        var target = document.getElementById(btn.getAttribute('data-scroll'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Lead form: saves the visitor's details to the Kzam Studio database (Supabase).
// The key below is the public "publishable" key. It can only add a row to the leads table.
(function () {
    var API = 'https://cdjxsozediftsolymjro.supabase.co/rest/v1/leads';
    var KEY = 'sb_publishable_Z-o-QEXAm_DUzWZZpMWqDw_41X5HgFs';
    var form = document.getElementById('lead-form');
    if (!form) { return; }
    var status = document.getElementById('lead-status');
    var button = form.querySelector('button[type="submit"]');

    function say(text, kind) {
        status.textContent = text;
        status.className = 'lead-status' + (kind ? ' ' + kind : '');
    }

    function fail() {
        status.className = 'lead-status err';
        status.textContent = 'ما قدرنا نسجل بياناتك. ';
        var a = document.createElement('a');
        a.href = 'https://wa.me/33777897299';
        a.target = '_blank';
        a.rel = 'noopener';
        a.textContent = 'راسلنا مباشرة على واتساب';
        status.appendChild(a);
    }

    // Arabic and Persian digits to Latin, then keep digits, spaces and a leading +
    function cleanPhone(value) {
        var out = value.replace(/[٠-٩]/g, function (d) { return String(d.charCodeAt(0) - 0x0660); })
                       .replace(/[۰-۹]/g, function (d) { return String(d.charCodeAt(0) - 0x06F0); })
                       .replace(/[^0-9+ ]/g, ' ').replace(/\s+/g, ' ').trim();
        if (out.indexOf('00') === 0) { out = '+' + out.slice(2); }
        return out;
    }

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        var data = new FormData(form);
        if (data.get('website')) { say('وصلتنا بياناتك. نكلمك على واتساب.', 'ok'); return; }
        var name = (data.get('name') || '').trim();
        var phone = cleanPhone(data.get('whatsapp') || '');
        if (name.length < 2) { say('اكتب اسمك.', 'err'); form.elements.name.focus(); return; }
        if (!/^\+?[0-9][0-9 ]{6,19}$/.test(phone)) {
            say('اكتب رقم الواتساب بالأرقام مع مفتاح الدولة، مثل \u2066+966500000000\u2069', 'err');
            form.elements.whatsapp.focus();
            return;
        }
        var row = {
            name: name,
            whatsapp: phone,
            business_type: data.get('business_type'),
            business_name: (data.get('business_name') || '').trim() || null,
            city: (data.get('city') || '').trim() || null,
            source_page: location.pathname.slice(0, 200)
        };
        button.disabled = true;
        say('جاري الإرسال...', '');
        fetch(API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'apikey': KEY, 'Prefer': 'return=minimal' },
            body: JSON.stringify(row)
        }).then(function (res) {
            if (res.status === 201) {
                form.reset();
                say('وصلتنا بياناتك. نكلمك على واتساب.', 'ok');
            } else {
                fail();
            }
        }).catch(fail).then(function () { button.disabled = false; });
    });
})();

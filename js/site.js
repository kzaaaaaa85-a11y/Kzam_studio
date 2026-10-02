// Smooth-scroll buttons: <button data-scroll="section-id">
document.querySelectorAll('[data-scroll]').forEach(function (btn) {
    btn.addEventListener('click', function () {
        var target = document.getElementById(btn.getAttribute('data-scroll'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

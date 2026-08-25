/* TILO — interactions */
(function () {
  'use strict';

  /* ---- Sticky nav ---- */
  var nav = document.querySelector('.nav');
  var onScroll = function () {
    if (window.scrollY > 24) nav.classList.add('scrolled');
    else nav.classList.remove('scrolled');
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- Mobile menu ---- */
  var burger = document.querySelector('.burger');
  var menu = document.querySelector('.mobile-menu');
  function toggleMenu(force) {
    var open = force != null ? force : !menu.classList.contains('open');
    menu.classList.toggle('open', open);
    burger.classList.toggle('on', open);
    document.body.style.overflow = open ? 'hidden' : '';
  }
  if (burger) burger.addEventListener('click', function () { toggleMenu(); });
  menu && menu.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () { toggleMenu(false); });
  });

  /* ---- Scroll reveals ---- */
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });

  /* ---- Gallery lightbox ---- */
  /* Páginas sin .lightbox en el HTML (como proyecto.html) simplemente
     no tienen este comportamiento — no rompe el resto del script. */
  var lb = document.querySelector('.lightbox');
  if (lb) {
    var lbPh = lb.querySelector('.ph');
    var lbCap = lb.querySelector('.lb-cap');
    var items = Array.prototype.slice.call(document.querySelectorAll('.gal'));
    var cur = 0;

    var showLb = function (i) {
      cur = (i + items.length) % items.length;
      var el = items[cur];
      var t = el.getAttribute('data-title') || '';
      var s = el.getAttribute('data-sub') || '';
      lbPh.setAttribute('data-label', el.querySelector('.ph').getAttribute('data-label'));
      lbCap.innerHTML = t + (s ? ' <span>' + s + '</span>' : '');
      lb.classList.add('open');
      document.body.style.overflow = 'hidden';
    };
    var closeLb = function () { lb.classList.remove('open'); document.body.style.overflow = ''; };

    items.forEach(function (el, i) {
      el.addEventListener('click', function () {
        var href = el.getAttribute('data-href');
        if (href) { window.location.href = href; return; }
        showLb(i);
      });
    });
    lb.querySelector('.lb-close').addEventListener('click', closeLb);
    lb.querySelector('.lb-prev').addEventListener('click', function () { showLb(cur - 1); });
    lb.querySelector('.lb-next').addEventListener('click', function () { showLb(cur + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) closeLb(); });
    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') closeLb();
      if (e.key === 'ArrowLeft') showLb(cur - 1);
      if (e.key === 'ArrowRight') showLb(cur + 1);
    });
  }

  /* ---- Contact form (FormSubmit AJAX → hola@tiloestudio.com.ar) ---- */
  var form = document.querySelector('.form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (form.classList.contains('sending') || form.classList.contains('sent')) return;
      // Honeypot: si un bot completa el campo oculto, fingimos éxito y no enviamos.
      var honey = form.querySelector('[name="_honey"]');
      if (honey && honey.value) { form.classList.add('sent'); return; }
      var btn = form.querySelector('button[type="submit"]');
      var btnHTML = btn ? btn.innerHTML : '';
      form.classList.add('sending');
      if (btn) { btn.disabled = true; btn.innerHTML = 'Enviando\u2026'; }
      var endpoint = form.getAttribute('action').replace('formsubmit.co/', 'formsubmit.co/ajax/');
      fetch(endpoint, {
        method: 'POST',
        headers: { 'Accept': 'application/json' },
        body: new FormData(form)
      })
        .then(function (r) { if (!r.ok) throw new Error('send'); return r.json(); })
        .then(function () {
          form.classList.remove('sending');
          form.classList.add('sent');
          form.reset();
        })
        .catch(function () {
          form.classList.remove('sending');
          if (btn) { btn.disabled = false; btn.innerHTML = btnHTML; }
          var note = form.querySelector('.form-note');
          if (note) {
            note.innerHTML = 'No pudimos enviar el formulario. Escribinos a <a href="mailto:hola@tiloestudio.com.ar">hola@tiloestudio.com.ar</a>.';
            note.style.color = '#9a3b2f';
          }
        });
    });
  }

  /* ---- Smooth-scroll offset for fixed nav ---- */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var id = a.getAttribute('href');
      if (id.length < 2) return;
      var target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      var y = target.getBoundingClientRect().top + window.scrollY - 70;
      window.scrollTo({ top: y, behavior: 'smooth' });
    });
  });
  /* ---- Instagram feed (auto-refreshing via Behold.so) ---- */
  (function initInstagram() {
    var grid = document.getElementById('insta-grid');
    if (!grid) return;

    /* ┌──────────────────────────────────────────────────────────────┐
       │  CONFIG — pegá acá tu ID de feed de Behold.so (gratis):        │
       │  1. Entrá a https://behold.so y creá una cuenta                │
       │  2. Conectá la cuenta @tiloestudio                             │
       │  3. Creá un feed → copiá el "Feed ID" y pegalo abajo           │
       │  Listo: el sitio mostrará tus 4 últimos posts y se actualiza   │
       │  solo cada vez que subís algo nuevo a Instagram.               │
       └──────────────────────────────────────────────────────────────┘ */
    var BEHOLD_FEED_ID = 'AIp0aDPw7d3PkxU3drz8';        // feed @tiloestudio
    var PROFILE = 'https://www.instagram.com/tiloestudio';
    var COUNT = 4;

    var igGlyph = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>';

    function renderPlaceholders() {
      var html = '';
      for (var i = 0; i < COUNT; i++) {
        html += '<a class="insta-cell is-ph" href="' + PROFILE + '" target="_blank" rel="noopener" aria-label="Ver @tiloestudio en Instagram">' +
                  '<div class="ig-ph">' + igGlyph + '<span>@tiloestudio</span></div>' +
                '</a>';
      }
      grid.innerHTML = html;
    }

    function renderPosts(posts) {
      var html = '';
      posts.slice(0, COUNT).forEach(function (p) {
        var img = p.sizes && p.sizes.medium ? p.sizes.medium.mediaUrl : (p.mediaUrl || p.thumbnailUrl);
        var link = p.permalink || PROFILE;
        var alt = (p.prunedCaption || p.caption || 'Posteo de @tiloestudio').slice(0, 120);
        html += '<a class="insta-cell" href="' + link + '" target="_blank" rel="noopener" aria-label="' + alt.replace(/"/g, '&quot;') + '">' +
                  '<img src="' + img + '" alt="' + alt.replace(/"/g, '&quot;') + '" />' +
                  '<span class="ig-ov">' + igGlyph + '</span>' +
                '</a>';
      });
      grid.innerHTML = html;
    }

    function load() {
      if (!BEHOLD_FEED_ID) { renderPlaceholders(); return; }
      fetch('https://feeds.behold.so/' + BEHOLD_FEED_ID, { cache: 'no-store' })
        .then(function (r) { if (!r.ok) throw new Error('feed'); return r.json(); })
        .then(function (data) {
          var posts = Array.isArray(data) ? data : (data.posts || []);
          if (!posts.length) { renderPlaceholders(); return; }
          renderPosts(posts);
        })
        .catch(function () { renderPlaceholders(); });
    }

    renderPlaceholders();   // muestra algo de inmediato
    load();                 // y trae los posts reales
    /* auto-refresh: revisa Instagram cada 30 min mientras la página está abierta */
    setInterval(load, 30 * 60 * 1000);
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) load();
    });
  })();
})();

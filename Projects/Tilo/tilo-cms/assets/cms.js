/* TILO — CMS (versión local de prueba)
   Lee data/hero.json, data/services.json y data/projects.json vía /api/*
   si el servidor local (server.py) está corriendo. Si no hay servidor,
   el sitio se ve exactamente igual que hoy: no rompe nada. */
(function () {
  'use strict';

  function escapeHtml(str) {
    var d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
  }
  function escapeAttr(str) {
    return String(str == null ? '' : str).replace(/"/g, '&quot;');
  }

  /* ── HERO + MANIFIESTO ──
     Objeto único (no es una lista): si hay servidor y hay datos, se
     pisa el texto ya presente en el HTML. Si no, queda el actual. */
  (function initHero() {
    var API = '/api/hero';
    fetch(API, { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('sin servidor local'); return r.json(); })
      .then(function (data) {
        var h = data && data.hero;
        if (!h) return;

        var eyebrow = document.getElementById('hero-eyebrow');
        var title = document.getElementById('hero-title');
        var desc = document.getElementById('hero-desc');
        var cta = document.getElementById('hero-cta');
        var photo = document.getElementById('hero-photo');
        var mTitle = document.getElementById('manifesto-title');
        var mBody1 = document.getElementById('manifesto-body1');
        var mBody2 = document.getElementById('manifesto-body2');
        var mSub = document.getElementById('manifesto-sub');

        if (eyebrow && h.eyebrow) eyebrow.textContent = h.eyebrow;
        if (title && (h.title_line1 || h.title_highlight)) {
          title.innerHTML = escapeHtml(h.title_line1 || '') + '<br /><em>' + escapeHtml(h.title_highlight || '') + '</em>';
        }
        if (desc && h.desc) desc.textContent = h.desc;
        if (cta && h.cta_label) {
          cta.textContent = h.cta_label;
          cta.setAttribute('href', h.cta_href || '#contacto');
        }
        if (photo && h.image) photo.setAttribute('src', h.image);

        if (mTitle && (h.manifiesto_title_line1 || h.manifiesto_title_highlight)) {
          mTitle.innerHTML = escapeHtml(h.manifiesto_title_line1 || '') + '<br /><em style="font-family:&quot;Cormorant Garamond&quot;">' + escapeHtml(h.manifiesto_title_highlight || '') + '</em>';
        }
        if (mBody1 && h.manifiesto_body1) mBody1.textContent = h.manifiesto_body1;
        if (mBody2 && h.manifiesto_body2) mBody2.textContent = h.manifiesto_body2;
        if (mSub && h.manifiesto_sub) mSub.textContent = h.manifiesto_sub;
      })
      .catch(function () {
        // sin servidor local: se conserva el contenido ya presente en el HTML
      });
  })();

  /* ── SERVICIOS (CMS) ──
     Arma las tarjetas de "Servicios" desde data/services.json vía
     /api/services. Si no hay servidor, se usa este mismo contenido
     de respaldo, así el sitio se ve siempre igual. */
  (function initServices() {
    var container = document.getElementById('svc-grid');
    if (!container) return;

    var ICONS = {
      branding: '<circle cx="22" cy="24" r="14"/><circle cx="22" cy="24" r="8.5"/><circle cx="22" cy="24" r="3"/><path d="M36 24h8M40 21l3 3-3 3M40.5 24H44"/>',
      grafico: '<path d="M12 36l3-9 18-18 6 6-18 18-9 3z"/><path d="M30 12l6 6"/><path d="M11 37l9-3"/>',
      digital: '<rect x="8" y="11" width="22" height="17" rx="1.5"/><path d="M14 33h12"/><rect x="31" y="20" width="11" height="17" rx="1.5"/><path d="M35.5 33.5h2"/>',
      patterns: '<path d="M19 9l-7 4 2 6 3-1.5V38a1 1 0 001 1h14a1 1 0 001-1V17.5l3 1.5 2-6-7-4a5 5 0 01-12 0z"/>',
      packaging: '<path d="M8 16l4-4h10l4 4"/><path d="M10 16v18a2 2 0 002 2h18a2 2 0 002-2V16"/><path d="M24 12v24M16 24h16"/><path d="M30 12l4-4h6v6"/>',
      editorial: '<path d="M24 14c-3-3-7-3-10-2v22c3-1 7-1 10 2 3-3 7-3 10-2V12c-3-1-7-1-10 2z"/><path d="M24 14v24"/>',
      estrategia: '<path d="M24 10v28"/><path d="M14 16h16l4 4-4 4H14z"/><path d="M34 26h-16l-4 4 4 4h16z"/><circle cx="24" cy="38" r="1.4" fill="currentColor"/>',
      marketing: '<path d="M10 20v8l18 7V13z"/><path d="M28 16l9-3v22l-9-3"/><path d="M14 28v6a2 2 0 002 2h3v-6"/>',
      generic: '<path d="M24 8l4 12 12 4-12 4-4 12-4-12-12-4 12-4z"/>'
    };

    var FALLBACK_SERVICES = [
      { id: 's1', title: 'Branding', description: 'Creamos marcas desde el concepto hasta su implementación: nombre, identidad y todo eso que las vuelve inconfundibles.', icon: 'branding' },
      { id: 's2', title: 'Diseño Gráfico', description: 'Comunicación visual con criterio: piezas que dicen lo justo, lindas y pensadas para quien tiene que verlas.', icon: 'grafico' },
      { id: 's3', title: 'Diseño Digital', description: 'Webs, landings y micrositios pensados para que tu marca se luzca y funcione online.', icon: 'digital' },
      { id: 's4', title: 'Patterns Indumentaria', description: 'Diseñamos estampas y patterns originales para darle personalidad propia a tus colecciones.', icon: 'patterns' },
      { id: 's5', title: 'POP y Packaging', description: 'Material de punto de venta y packaging que enamora en la góndola y cuida cada detalle.', icon: 'packaging' },
      { id: 's6', title: 'Editorial', description: 'Catálogos, revistas y publicaciones con una puesta editorial cuidada, prolija y con ritmo.', icon: 'editorial' },
      { id: 's7', title: 'Estrategia', description: 'Antes de diseñar, pensamos: objetivos claros, rumbo definido y un plan con sentido.', icon: 'estrategia' },
      { id: 's8', title: 'Marketing Digital', description: 'Campañas y contenido que conectan con tu audiencia y mueven la aguja de verdad.', icon: 'marketing' }
    ];

    function itemHtml(s) {
      var iconPath = ICONS[s.icon] || ICONS.generic;
      return '<div class="svc-item">' +
        '<span class="svc-ic"><svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">' + iconPath + '</svg></span>' +
        '<h3>' + escapeHtml(s.title || '') + '</h3>' +
        '<div class="svc-tip"><span class="svc-tip-t">' + escapeHtml(s.title || '') + '</span><p>' + escapeHtml(s.description || '') + '</p></div>' +
        '</div>';
    }

    function render(services) {
      if (!services || !services.length) return;
      container.innerHTML = services.map(itemHtml).join('');
    }

    render(FALLBACK_SERVICES); // se ve bien de entrada, incluso sin servidor

    fetch('/api/services', { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('sin servidor local'); return r.json(); })
      .then(function (data) {
        var services = (data && data.services) || [];
        if (services.length) render(services);
      })
      .catch(function () {
        // sin servidor local: se conserva el fallback ya renderizado
      });
  })();

  /* ── PROYECTOS (CMS) ──
     Arma la grilla mosaico de "Proyectos" desde data/projects.json vía
     /api/projects. El orden de las 6 clases (g-a, g-b, g-f, g-c, g-d, g-e)
     es el que arma el mosaico prolijo del diseño original; se repite
     cada 6 proyectos si hay más. */
  var GRID_ORDER = ['g-a', 'g-b', 'g-f', 'g-c', 'g-d', 'g-e'];

  (function initProjects() {
    var container = document.getElementById('gallery');
    if (!container) return;

    var FALLBACK_PROJECTS = [
      { id: 'p1', title: 'Me Viste La Nona', subtitle: 'Contenido para Redes · Marketing', image: 'assets/mvn/portada.webp', href: 'Me Viste La Nona.html' },
      { id: 'p2', title: 'Enriqueta Solari', subtitle: 'Branding · Packaging · Contenido', image: 'assets/enriqueta/portada.webp', href: 'Enriqueta Solari.html' },
      { id: 'p3', title: 'Patterns y Estampas', subtitle: 'Patterns · Estampas · Indumentaria', image: 'assets/patterns/portada.webp', href: 'Patterns y Estampas.html' },
      { id: 'p4', title: 'Zeocar', subtitle: 'Branding · Packaging · Editorial', image: 'assets/zeocar/portada-web.webp', href: 'Zeocar.html' },
      { id: 'p5', title: 'Opsek', subtitle: 'Identidad de Marca · Branding', image: 'assets/opsek/portada.webp', href: 'Opsek.html' },
      { id: 'p6', title: 'Ekoparty', subtitle: 'Campaña · Branding · Evento', image: 'assets/ekoparty/portada.webp', href: 'Ekoparty.html' }
    ];

    function itemHtml(p, i) {
      var gcls = GRID_ORDER[i % GRID_ORDER.length];
      var href = p.href || '#contacto';
      return '<a class="gal ' + gcls + '" href="' + escapeAttr(href) + '">' +
        '<div class="imgwrap"><img class="gal-img" loading="lazy" src="' + escapeAttr(p.image || '') + '" alt="' + escapeAttr(p.title || '') + '" />' +
        '<div class="overlay"><div class="info"><span class="c">' + escapeHtml(p.subtitle || '') + '</span><span class="t">' + escapeHtml(p.title || '') + '</span><span class="cta">Ver proyecto →</span></div></div>' +
        '</div></a>';
    }

    function render(projects) {
      if (!projects || !projects.length) return;
      container.innerHTML = projects.map(itemHtml).join('');
    }

    render(FALLBACK_PROJECTS); // se ve bien de entrada, incluso sin servidor

    fetch('/api/projects', { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('sin servidor local'); return r.json(); })
      .then(function (data) {
        var projects = (data && data.projects) || [];
        if (projects.length) render(projects);
      })
      .catch(function () {
        // sin servidor local: se conserva el fallback ya renderizado
      });
  })();
})();

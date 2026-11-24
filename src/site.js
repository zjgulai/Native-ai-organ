/* Native AI Organ — shared client behaviors.
   Static-first: every page works without JS; this adds progressive enhancement. */
(() => {
  'use strict';

  /* mobile nav + directory toggles */
  const navToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      const open = navLinks.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', String(open));
    });
  }
  const dirBtn = document.querySelector('.mobile-dir-btn');
  const dir = document.querySelector('.dir');
  if (dirBtn && dir) {
    dirBtn.addEventListener('click', () => {
      const open = dir.classList.toggle('open');
      dirBtn.setAttribute('aria-expanded', String(open));
    });
  }

  /* sidebar live filter (Sage docs pattern) */
  const dirSearch = document.querySelector('#dir-search');
  if (dirSearch && dir) {
    const items = [...dir.querySelectorAll('.dir-group a')];
    const groups = [...dir.querySelectorAll('.dir-group')];
    const empty = dir.querySelector('.dir-empty');
    dirSearch.addEventListener('input', () => {
      const q = dirSearch.value.trim().toLowerCase();
      let shown = 0;
      groups.forEach(g => {
        let gShown = 0;
        g.querySelectorAll('a').forEach(a => {
          const hay = (a.dataset.search || a.textContent).toLowerCase();
          const hit = !q || hay.includes(q);
          a.hidden = !hit;
          if (hit) gShown++;
        });
        const h = g.querySelector('h4');
        if (h) h.hidden = gShown === 0;
        g.style.display = gShown === 0 ? 'none' : '';
        shown += gShown;
      });
      if (empty) empty.hidden = shown > 0 || !q;
    });
  }

  /* right-column TOC scrollspy */
  const tocLinks = [...document.querySelectorAll('.ptoc nav a')];
  const heads = [...document.querySelectorAll('.article h2[id], .article h3[id]')];
  if (tocLinks.length && heads.length && 'IntersectionObserver' in window) {
    const map = new Map(heads.map(h => [h.id, h]));
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        tocLinks.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id));
      });
    }, { rootMargin: '-15% 0px -70% 0px' });
    heads.forEach(h => obs.observe(h));
    map.clear();
  }

  /* tool checklists: persist in localStorage, print-friendly */
  document.querySelectorAll('.checklist').forEach(box => {
    const key = 'nao-chk-' + (box.dataset.tool || box.id || 'x');
    const boxes = [...box.querySelectorAll('li input[type=checkbox]')];
    try {
      const saved = JSON.parse(localStorage.getItem(key) || '[]');
      boxes.forEach((b, i) => { b.checked = !!saved[i]; });
    } catch (_) { /* private mode etc. */ }
    const paint = () => {
      boxes.forEach(b => b.closest('li').classList.toggle('done', b.checked));
      const done = boxes.filter(b => b.checked).length;
      const counter = box.querySelector('[data-count]');
      if (counter) counter.textContent = done + ' / ' + boxes.length;
    };
    boxes.forEach(b => b.addEventListener('change', () => {
      try { localStorage.setItem(key, JSON.stringify(boxes.map(x => x.checked))); } catch (_) {}
      paint();
    }));
    const reset = box.querySelector('[data-reset]');
    if (reset) reset.addEventListener('click', () => {
      boxes.forEach(b => { b.checked = false; });
      try { localStorage.removeItem(key); } catch (_) {}
      paint();
    });
    const print = box.querySelector('[data-print]');
    if (print) print.addEventListener('click', () => window.print());
    paint();
  });

  /* paginated tables: table.paginated[data-page-size] splits rows into pages */
  document.querySelectorAll('table.paginated').forEach(table => {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    const rows = [...tbody.querySelectorAll('tr')];
    const size = parseInt(table.dataset.pageSize || '8', 10);
    if (rows.length <= size) return;
    const pages = Math.ceil(rows.length / size);
    const pager = document.createElement('div');
    pager.className = 'tbl-pager';
    const info = document.createElement('span');
    info.className = 'tbl-pager-info';
    pager.appendChild(info);
    let current = 0;
    const show = p => {
      current = p;
      rows.forEach((r, i) => { r.hidden = Math.floor(i / size) !== p; });
      pager.querySelectorAll('button').forEach((b, i) => {
        const on = i === p;
        b.classList.toggle('on', on);
        if (on) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current');
      });
      info.textContent = (p * size + 1) + '–' + Math.min((p + 1) * size, rows.length) + ' / ' + rows.length + ' 项';
    };
    for (let i = 0; i < pages; i++) {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = String(i + 1);
      b.setAttribute('aria-label', '第 ' + (i + 1) + ' 页，共 ' + pages + ' 页');
      b.addEventListener('click', () => show(i));
      pager.insertBefore(b, info);
    }
    const wrap = table.closest('.table-wrap');
    if (wrap && wrap.parentNode) wrap.parentNode.insertBefore(pager, wrap.nextSibling);
    show(0);
  });

  /* chapter prev/next keyboard friendly: nothing extra needed */
})();

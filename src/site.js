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
    box.querySelectorAll('li').forEach(li => {
      li.addEventListener('click', e => {
        if (e.target.closest('label') || e.target.tagName === 'INPUT') return;
        const cb = li.querySelector('input[type=checkbox]');
        if (cb) { cb.checked = !cb.checked; cb.dispatchEvent(new Event('change')); }
      });
    });
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

  /* orgmap: 组织与价值流一张图 — click-to-highlight explorer.
     Static fallback: all nodes render server-side; JS adds lit/dim + drawer. */
  const omApp = document.getElementById('om-app');
  const omDataEl = document.getElementById('om-data');
  if (omApp && omDataEl) {
    let OM = null;
    try { OM = JSON.parse(omDataEl.textContent); } catch (_) { OM = null; }
    if (OM) initOrgmap(omApp, OM);
  }

  function initOrgmap(app, OM) {
    const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
      c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const roles = OM.roles || [], streams = OM.streams || [],
          scns = OM.scenarios || [], planes = OM.planes || [],
          contracts = OM.plane_contracts || [];
    const roleById = {}, streamByKey = {}, scnById = {}, planeById = {};
    roles.forEach(r => { roleById[r.id] = r; });
    streams.forEach(s => { streamByKey[s.key] = s; });
    scns.forEach(s => { scnById[s.id] = s; });
    planes.forEach(p => { planeById[p.id] = p; });
    const planeName = id => (planeById[id] || {}).name || id;
    const roleChip = (id) => {
      const r = roleById[id];
      return r ? `<button type="button" class="om-jump" data-jump="role:${esc(id)}"><b>${esc(id)}</b>${esc(r.alias)}</button>` : '';
    };
    const scnJump = id => `<button type="button" class="om-jump" data-jump="scn:${esc(id)}"><b>${esc(id)}</b>${esc((scnById[id] || {}).title || '')}</button>`;
    const streamJump = key => {
      const s = streamByKey[key];
      return s ? `<button type="button" class="om-jump" data-jump="stream:${esc(key)}"><b>${esc(key)}</b>${esc(s.title)}</button>` : '';
    };
    const planeJump = id => `<button type="button" class="om-jump" data-jump="plane:${esc(id)}"><b>${esc(id)}</b>${esc(planeName(id))}</button>`;
    const dsec = (label, inner) => inner ? `<div class="om-d-sec"><div class="om-d-k">${esc(label)}</div><div class="om-d-chips">${inner}</div></div>` : '';

    /* reverse indexes */
    const scnToRoles = {};
    roles.forEach(r => (r.scenarios || []).forEach(c => {
      (scnToRoles[c] = scnToRoles[c] || []).push(r.id);
    }));
    const roleToStreams = {};
    streams.forEach(s => [s.owner, ...(s.contributors || [])].forEach(a => {
      if (a) (roleToStreams[a] = roleToStreams[a] || []).push(s.key);
    }));

    const els = [...app.querySelectorAll('[data-om]')];
    const drawer = app.querySelector('#om-drawer');
    const drawerDefault = drawer ? drawer.innerHTML : '';
    let current = null;

    function litSet(key) {
      const L = { streams: new Set(), roles: new Set(), scns: new Set(), planes: new Set() };
      const [type, id] = key.split(':');
      const addStream = s => {
        if (!s) return;
        L.streams.add(s.key);
        if (s.owner) L.roles.add(s.owner);
        (s.scenarios || []).forEach(c => L.scns.add(c));
      };
      const addRolePlane = rid => {
        const r = roleById[rid];
        if (r && r.plane) L.planes.add(r.plane);
      };
      if (type === 'stream') {
        const s = streamByKey[id];
        if (!s) return L;
        L.streams.add(s.key);
        L.roles.add(s.owner);
        (s.contributors || []).forEach(r => L.roles.add(r));
        (s.scenarios || []).forEach(c => L.scns.add(c));
        [...L.roles].forEach(addRolePlane);
      } else if (type === 'scn') {
        const s = scnById[id];
        if (!s) return L;
        L.scns.add(id);
        (s.flows || []).forEach(f => {
          const st = streamByKey[f];
          if (st) { L.streams.add(st.key); if (st.owner) L.roles.add(st.owner); }
        });
        (scnToRoles[id] || []).forEach(r => L.roles.add(r));
        [...L.roles].forEach(addRolePlane);
      } else if (type === 'role') {
        const r = roleById[id];
        if (!r) return L;
        L.roles.add(id);
        if (r.plane) L.planes.add(r.plane);
        (roleToStreams[id] || []).forEach(k => {
          const s = streamByKey[k];
          if (!s) return;
          L.streams.add(k);
          (s.scenarios || []).forEach(c => L.scns.add(c));
          if (s.owner) L.roles.add(s.owner);
          (s.contributors || []).forEach(x => L.roles.add(x));
        });
        (r.scenarios || []).forEach(c => L.scns.add(c));
        [...L.roles].forEach(addRolePlane);
      } else if (type === 'plane') {
        const p = planeById[id];
        if (!p) return L;
        L.planes.add(id);
        roles.forEach(r => { if (r.plane === id) L.roles.add(r.id); });
      }
      return L;
    }

    function apply(L) {
      els.forEach(el => {
        const [t, id] = (el.dataset.om || '').split(':');
        const on = (t === 'stream' && L.streams.has(id)) ||
                   (t === 'scn' && L.scns.has(id)) ||
                   (t === 'role' && L.roles.has(id)) ||
                   (t === 'plane' && L.planes.has(id));
        el.classList.toggle('lit', !!on);
        el.classList.toggle('dim', !on);
      });
    }

    function renderStream(s) {
      const members = [...new Set([s.owner, ...(s.contributors || [])].filter(Boolean))];
      return `<div class="om-d-k">价值流 · ${esc(s.sid)} / ${esc(s.key)} · ${s.family === 'BVS' ? '业务经营流' : '能力供应流'}</div>`
        + `<div class="om-d-t">${esc(s.title)}</div>`
        + (s.product ? `<div class="om-d-meta">产品化形态：${esc(s.product)}</div>` : '')
        + `<div class="om-d-meta">AI 结果负责：${roleChip(s.owner)}</div>`
        + (s.owner_note ? `<div class="om-d-note">${esc(s.owner_note)}</div>` : '')
        + `<p class="om-d-text">${esc(s.value || '')}</p>`
        + `<div class="om-d-meta">起点：${esc(s.start || '—')}<br>终点：${esc(s.finish || '—')}</div>`
        + dsec(`绑定场景 · ${s.scenarios.length}`, (s.scenarios || []).map(scnJump).join(''))
        + dsec(`参与岗位 · ${members.length}（1 结果负责 + 能力贡献）`, members.map(roleChip).join(''));
    }

    function renderScn(s) {
      const rel = scnToRoles[s.id] || [];
      return `<div class="om-d-k">业务场景 · ${esc(s.id)}</div>`
        + `<div class="om-d-t">${esc(s.title)}</div>`
        + `<div class="om-d-meta">一张 Case 只绑定一条主流与一个主场景（D-025）；以下为可进入的价值流。</div>`
        + dsec(`可进入价值流 · ${(s.flows || []).length}`, (s.flows || []).map(streamJump).join(''))
        + dsec(`关联岗位 · ${rel.length}`, rel.map(roleChip).join(''));
    }

    function renderRole(r) {
      const keys = roleToStreams[r.id] || [];
      const bvsKeys = keys.filter(k => streamByKey[k] && streamByKey[k].family === 'BVS');
      const cvsKeys = keys.filter(k => streamByKey[k] && streamByKey[k].family === 'CVS');
      const primary = (r.primary_flows || []).filter(f => bvsKeys.includes(f));
      const restBvs = bvsKeys.filter(k => !(r.primary_flows || []).includes(k));
      const scnList = r.scenarios || [];
      return `<div class="om-d-k">AI 岗位 · ${esc(r.id)} · ${esc(r.plane || '')}</div>`
        + `<div class="om-d-t">${esc(r.alias)} · ${esc(r.title)}</div>`
        + `<div class="om-d-meta">组织平面：${planeJump(r.plane)}　责任域：${esc(r.domain || '—')}</div>`
        + (r.principle ? `<p class="om-d-text"><b>行为原则：</b>${esc(r.principle)}</p>` : '')
        + (r.boundary ? `<p class="om-d-text"><b>边界：</b>${esc(r.boundary)}</p>` : '')
        + dsec(`主责价值流 · ${primary.length}`, primary.map(streamJump).join(''))
        + dsec(`参与经营流 · ${restBvs.length}`, restBvs.map(streamJump).join(''))
        + dsec(`参与能力流 · ${cvsKeys.length}`, cvsKeys.map(streamJump).join(''))
        + dsec(`关联场景 · ${scnList.length}`, scnList.map(scnJump).join(''));
    }

    function renderPlane(p) {
      const members = roles.filter(r => r.plane === p.id);
      const rel = contracts.filter(c => c.from === p.id || c.to === p.id);
      const rows = rel.map(c => {
        const other = c.from === p.id ? c.to : c.from;
        return `<div class="om-d-meta" style="margin:4px 0">${esc(c.from_name)} → ${esc(c.to_name)}：${esc(c.label)} ${planeJump(other)}</div>`;
      }).join('');
      return `<div class="om-d-k">组织平面 · ${esc(p.id)}</div>`
        + `<div class="om-d-t">${esc(p.name)} · ${p.role_count} 个岗位</div>`
        + `<p class="om-d-text">${esc(p.purpose || '')}</p>`
        + dsec(`成员岗位 · ${members.length}`, members.map(r => roleChip(r.id)).join(''))
        + `<div class="om-d-sec"><div class="om-d-k">跨平面契约 · ${rel.length}</div>${rows}</div>`;
    }

    function renderDrawer(key) {
      if (!drawer) return;
      if (!key) { drawer.innerHTML = drawerDefault; return; }
      const [type, id] = key.split(':');
      let html = '';
      if (type === 'stream') { const s = streamByKey[id]; if (s) html = renderStream(s); }
      else if (type === 'scn') { const s = scnById[id]; if (s) html = renderScn(s); }
      else if (type === 'role') { const r = roleById[id]; if (r) html = renderRole(r); }
      else if (type === 'plane') { const p = planeById[id]; if (p) html = renderPlane(p); }
      if (!html) { drawer.innerHTML = drawerDefault; return; }
      drawer.innerHTML = `<div class="om-drawer-in">${html}`
        + `<button type="button" class="om-clear" data-clear>清除选择</button></div>`;
    }

    function select(key) {
      current = key;
      apply(litSet(key));
      renderDrawer(key);
    }
    function clearSel() {
      current = null;
      els.forEach(el => el.classList.remove('lit', 'dim'));
      renderDrawer(null);
    }

    app.addEventListener('click', e => {
      const j = e.target.closest('[data-jump]');
      if (j) { select(j.dataset.jump); return; }
      if (e.target.closest('[data-clear]')) { clearSel(); return; }
      const n = e.target.closest('[data-om]');
      if (n) {
        const k = n.dataset.om;
        if (k === current) clearSel(); else select(k);
      }
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && current) clearSel();
    });
  }

  /* chapter prev/next keyboard friendly: nothing extra needed */
})();

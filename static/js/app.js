/* ============================================================
   MAPNA SwapFleet AI — Shared frontend helpers (v2)
   ============================================================ */

/* ---------- ICON LIBRARY (Phosphor-style, inline SVG) ----------
   Icons are 24x24, stroke-based, currentColor — no emoji.
   Usage: SF.icon('home', { size: 20, class: 'nav-icon' })
*/
(function () {
  const PATHS = {
    // Navigation / UI
    dashboard:    '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="2" width="7" height="5" rx="1.5"/><rect x="14" y="11" width="7" height="11" rx="1.5"/><rect x="3" y="16" width="7" height="6" rx="1.5"/>',
    home:         '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    station:      '<path d="M4 21V8l8-5 8 5v13"/><path d="M9 21v-7h6v7"/><circle cx="12" cy="11" r="1.2"/>',
    swap:         '<path d="M4 7h13l-3-3"/><path d="M20 17H7l3 3"/><path d="M4 7l3 3"/><path d="M20 17l-3-3"/>',
    battery:      '<rect x="2" y="7" width="18" height="10" rx="2"/><rect x="22" y="10" width="2" height="4" rx="1"/><rect x="5" y="10" width="6" height="4" rx="0.5" fill="currentColor" stroke="none"/>',
    bolt:         '<path d="M13 3L4 14h7l-1 7 9-11h-7z"/>',
    users:        '<circle cx="9" cy="8" r="3.5"/><path d="M2 21c0-4 3-7 7-7s7 3 7 7"/><circle cx="17" cy="6" r="2.5"/><path d="M22 19c0-3-2-5-5-5"/>',
    alert:        '<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v4"/><circle cx="12" cy="17.5" r="0.6" fill="currentColor"/>',
    map:          '<path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2V6z"/><path d="M9 4v16"/><path d="M15 6v16"/>',
    ai:           '<path d="M12 4a4 4 0 014 4v2a4 4 0 01-8 0V8a4 4 0 014-4z"/><path d="M5 12a7 7 0 0014 0"/><circle cx="9" cy="13" r="1.2"/><circle cx="15" cy="13" r="1.2"/><path d="M12 19v3"/>',
    chat:         '<path d="M4 5h16v11H8l-4 4V5z"/>',
    route:        '<circle cx="5" cy="5" r="2.5"/><circle cx="19" cy="19" r="2.5"/><path d="M5 7.5v3a4 4 0 004 4h6a4 4 0 014 4"/>',
    history:      '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    sos:          '<circle cx="12" cy="12" r="9"/><path d="M12 7v5"/><circle cx="12" cy="16" r="0.8" fill="currentColor"/>',
    vehicle:      '<path d="M5 17a2 2 0 104 0 2 2 0 00-4 0zM15 17a2 2 0 104 0 2 2 0 00-4 0z"/><path d="M3 13l2-6h14l2 6"/><path d="M3 13v4h2M21 13v4h-2"/><path d="M5 13h14"/>',
    trip:         '<path d="M3 12l5-7h8l5 7v6H3v-6z"/><circle cx="7.5" cy="18" r="1.8"/><circle cx="16.5" cy="18" r="1.8"/>',
    wrench:       '<path d="M14.7 6.3a4 4 0 015.7 5L13 18.7 9.3 15l5.4-8.7z"/><path d="M9.3 15L5 19.3 7.3 21.7 11.3 17.7"/>',
    coin:         '<circle cx="12" cy="12" r="9"/><path d="M9 9h5a2 2 0 010 4H9l6 4H8"/><path d="M12 6v2M12 16v2"/>',
    plug:         '<path d="M9 4v4M15 4v4"/><rect x="6" y="8" width="12" height="6" rx="2"/><path d="M12 14v4M9 21h6"/>',
    refresh:      '<path d="M4 4v6h6"/><path d="M20 20v-6h-6"/><path d="M4 10a8 8 0 0114-3"/><path d="M20 14a8 8 0 01-14 3"/>',
    search:       '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.5-4.5"/>',
    plus:         '<path d="M12 5v14M5 12h14"/>',
    check:        '<path d="M5 12l5 5L20 7"/>',
    x:            '<path d="M6 6l12 12M18 6L6 18"/>',
    arrowRight:   '<path d="M5 12h14M13 6l6 6-6 6"/>',
    arrowLeft:    '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    arrowUp:      '<path d="M12 19V5M6 11l6-6 6 6"/>',
    arrowDown:    '<path d="M12 5v14M6 13l6 6 6-6"/>',
    trendUp:      '<path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/>',
    trendDown:    '<path d="M3 7l6 6 4-4 8 8"/><path d="M14 17h7v-7"/>',
    settings:     '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3h0a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5h0a1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8v0a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z"/>',
    logout:       '<path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    menu:         '<path d="M4 6h16M4 12h16M4 18h16"/>',
    send:         '<path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/>',
    leaf:         '<path d="M21 3c-9 0-15 5-15 13 0 4 3 5 5 5 8 0 13-6 13-15V3h-3z"/><path d="M5 21c2-6 6-10 12-12"/>',
    shield:       '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/>',
    sparkle:      '<path d="M12 3l1.8 4.2L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.8z"/><path d="M19 14l.9 2.1L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.9z"/>',
    fire:         '<path d="M12 2c0 5-5 7-5 12a5 5 0 0010 0c0-2-1-4-3-5 0 2-1 3-2 3 0-3 1-7 0-10z"/>',
    calendar:     '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    more:         '<circle cx="6" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="18" cy="12" r="1.5"/>',
    eye:          '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    download:     '<path d="M12 3v12"/><path d="M7 10l5 5 5-5"/><path d="M5 21h14"/>',
    layers:       '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/><path d="M3 17l9 5 9-5"/>',
  };

  window.SF = window.SF || {};
  window.SF.icon = function (name, opts) {
    opts = opts || {};
    const path = PATHS[name] || PATHS.alert;
    const cls = opts.class ? ' class="' + opts.class + '"' : '';
    const size = opts.size || 20;
    const stroke = opts.strokeWidth || 1.8;
    return (
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"' +
      ' width="' + size + '" height="' + size + '"' +
      ' fill="none" stroke="currentColor" stroke-width="' + stroke + '"' +
      ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"' +
      cls + '>' + path + '</svg>'
    );
  };

  /* Resolve icons automatically on elements with data-icon="name" */
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-icon]').forEach((el) => {
      const name = el.getAttribute('data-icon');
      const size = parseInt(el.getAttribute('data-size') || '18', 10);
      el.innerHTML = window.SF.icon(name, { size, class: el.getAttribute('data-icon-class') || '' });
    });
  });
})();

/* ---------- TOAST STACK ---------- */
(function () {
  let stack = null;
  function ensureStack() {
    if (stack) return stack;
    stack = document.createElement('div');
    stack.className = 'toast-stack';
    stack.setAttribute('role', 'status');
    stack.setAttribute('aria-live', 'polite');
    document.body.appendChild(stack);
    return stack;
  }

  function iconFor(type) {
    if (type === 'success') return 'check';
    if (type === 'warning') return 'alert';
    if (type === 'error')   return 'alert';
    return 'sparkle';
  }

  window.SF = window.SF || {};
  window.SF.toast = function (msg, type = 'info', opts = {}) {
    const s = ensureStack();
    const t = document.createElement('div');
    t.className = 'toast ' + (type !== 'info' ? type : '');
    t.innerHTML =
      '<span class="t-ico">' + window.SF.icon(iconFor(type), { size: 18 }) + '</span>' +
      '<span class="t-msg"></span>' +
      '<button class="t-close" aria-label="بستن">' + window.SF.icon('x', { size: 14 }) + '</button>';
    t.querySelector('.t-msg').textContent = msg;
    const close = () => {
      t.style.transition = 'opacity 200ms, transform 200ms';
      t.style.opacity = '0';
      t.style.transform = 'translateX(-8px)';
      setTimeout(() => t.remove(), 220);
    };
    t.querySelector('.t-close').addEventListener('click', close);
    s.appendChild(t);
    const ttl = opts.duration || (type === 'error' ? 5500 : 3500);
    setTimeout(close, ttl);
  };
})();

/* ---------- SKELETON HELPERS ---------- */
(function () {
  window.SF = window.SF || {};
  window.SF.skeleton = function (rows = 3, opts = {}) {
    const h = opts.height || 12;
    return Array.from({ length: rows }, () =>
      '<div class="skeleton skeleton-line" style="height:' + h + 'px"></div>'
    ).join('');
  };
  window.SF.kpiSkeleton = function () {
    return '<div class="kpi-grid">' +
      Array.from({ length: 4 }, () =>
        '<div class="kpi"><div class="skeleton skeleton-line" style="width:60%"></div>' +
        '<div class="skeleton skeleton-line" style="height:30px;width:40%;margin-top:8px"></div></div>'
      ).join('') + '</div>';
  };
  window.SF.tableSkeleton = function (rows = 5, cols = 4) {
    let html = '<div class="table-wrap"><table><thead><tr>';
    for (let i = 0; i < cols; i++) html += '<th><div class="skeleton skeleton-line" style="width:60%"></div></th>';
    html += '</tr></thead><tbody>';
    for (let r = 0; r < rows; r++) {
      html += '<tr>';
      for (let c = 0; c < cols; c++) html += '<td><div class="skeleton skeleton-line" style="width:80%"></div></td>';
      html += '</tr>';
    }
    return html + '</tbody></table></div>';
  };
})();

/* ---------- API WRAPPER ---------- */
window.SF = window.SF || {};
window.SF.api = async (path, opts = {}) => {
  const token = localStorage.getItem('sf_token');
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (token) headers['Authorization'] = 'Bearer ' + token;
  let r;
  try {
    r = await fetch('/api' + path, {
      method: opts.method || 'GET',
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
  } catch (e) {
    return { ok: false, error: 'خطای شبکه', network: true };
  }
  if (r.status === 401) {
    localStorage.removeItem('sf_token');
    window.location.href = '/';
    return { ok: false, error: 'unauthorized' };
  }
  let data;
  try { data = await r.json(); } catch (e) { return { ok: false, error: 'پاسخ نامعتبر' }; }
  return data;
};

/* ---------- FORMATTERS ---------- */
window.SF.fmt = {
  toman: (n) => (Number(n) || 0).toLocaleString('fa-IR') + ' تومان',
  km: (n) => (Number(n) || 0).toFixed(1) + ' km',
  pct: (n) => (Number(n) || 0).toFixed(1) + '%',
  num: (n) => (Number(n) || 0).toLocaleString('fa-IR'),
  date: (d) => (d ? new Date(d).toLocaleString('fa-IR') : '—'),
  shortDate: (d) => (d ? new Date(d).toLocaleDateString('fa-IR') : '—'),
};

/* ---------- USER HELPERS ---------- */
window.SF.user = () => JSON.parse(localStorage.getItem('sf_user') || 'null');

window.SF.logout = () => {
  localStorage.removeItem('sf_token');
  localStorage.removeItem('sf_user');
  window.location.href = '/';
};

window.SF.requireAuth = (role) => {
  const u = window.SF.user();
  if (!u) { window.location.href = '/'; return null; }
  if (role && u.role !== role && u.role !== 'admin') {
    const map = { station: '/station', fleet: '/fleet', rider: '/rider', admin: '/admin' };
    window.location.href = map[u.role] || '/';
    return null;
  }
  return u;
};

/* ---------- SIDEBAR / MOBILE NAV TOGGLE ---------- */
document.addEventListener('DOMContentLoaded', () => {
  // Make sidebar nav links toggle on mobile
  const sidebar = document.querySelector('.sidebar');
  const backdrop = document.querySelector('.sidebar-backdrop');
  const menuBtn = document.querySelector('.menu-btn');

  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', () => {
      sidebar.classList.add('is-open');
      if (backdrop) backdrop.classList.add('is-open');
    });
  }
  if (backdrop && sidebar) {
    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('is-open');
      backdrop.classList.remove('is-open');
    });
  }

  // Close mobile sidebar on nav click
  sidebar && sidebar.querySelectorAll('nav a').forEach((a) => {
    a.addEventListener('click', () => {
      if (window.matchMedia('(max-width: 880px)').matches) {
        sidebar.classList.remove('is-open');
        if (backdrop) backdrop.classList.remove('is-open');
      }
    });
  });

  // Wire up bottom-nav active state based on current hash
  const setActive = () => {
    const hash = (window.location.hash || '').replace('#', '');
    document.querySelectorAll('.bottom-nav a').forEach((a) => {
      const t = a.dataset.tab;
      a.classList.toggle('active', t === hash);
    });
  };
  window.addEventListener('hashchange', setActive);
  setActive();
});

/* ---------- AVATAR INITIAL HELPER ---------- */
window.SF.avatar = function (name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  return parts.length === 1 ? parts[0][0] : (parts[0][0] + parts[1][0]);
};
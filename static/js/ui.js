(() => {
  const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;

  function toast(message, opts = {}) {
    const host = document.getElementById('toastHost');
    if (!host) return;
    const level = (opts.level || 'info').toLowerCase();
    const title = opts.title || (level === 'success' ? 'Success' : level === 'danger' || level === 'error' ? 'Action needed' : level === 'warning' ? 'Heads up' : 'Update');
    const timeoutMs = typeof opts.timeoutMs === 'number' ? opts.timeoutMs : (level === 'danger' || level === 'error' ? 6500 : 4200);

    const el = document.createElement('div');
    el.className = `toast3d toast-${level}`;
    el.setAttribute('role', 'status');
    el.innerHTML = `
      <div class="toast3d-inner">
        <div class="toast3d-glow" aria-hidden="true"></div>
        <div class="toast3d-head">
          <div class="toast3d-title">${title}</div>
          <button type="button" class="toast3d-x" aria-label="Close">×</button>
        </div>
        <div class="toast3d-body">${message}</div>
        <div class="toast3d-bar" aria-hidden="true"></div>
      </div>
    `.trim();

    const closeBtn = el.querySelector('.toast3d-x');
    const bar = el.querySelector('.toast3d-bar');

    function close() {
      el.classList.add('is-leaving');
      window.setTimeout(() => el.remove(), prefersReducedMotion ? 0 : 260);
    }

    closeBtn?.addEventListener('click', close);
    host.prepend(el);

    if (!prefersReducedMotion) {
      requestAnimationFrame(() => el.classList.add('is-in'));
    } else {
      el.classList.add('is-in');
    }

    if (bar && timeoutMs > 0) {
      bar.style.setProperty('--toastMs', `${timeoutMs}ms`);
      bar.classList.add('is-running');
    }

    if (timeoutMs > 0) {
      window.setTimeout(close, timeoutMs);
    }
  }

  function setTheme(theme) {
    const body = document.body;
    body.classList.toggle('theme-dark', theme === 'dark');
    body.classList.toggle('theme-light', theme === 'light');
    try { localStorage.setItem('theme', theme); } catch {}
  }

  function getInitialTheme() {
    try {
      const stored = localStorage.getItem('theme');
      if (stored === 'dark' || stored === 'light') return stored;
    } catch {}
    const systemDark = window.matchMedia?.('(prefers-color-scheme: dark)')?.matches ?? true;
    return systemDark ? 'dark' : 'light';
  }

  document.addEventListener('DOMContentLoaded', () => {
    // Expose toast for other scripts
    window.toast = toast;

    // Theme toggle
    setTheme(getInitialTheme());
    const btn = document.getElementById('themeToggle');
    if (btn) {
      btn.addEventListener('click', () => {
        const next = document.body.classList.contains('theme-dark') ? 'light' : 'dark';
        setTheme(next);
      });
    }

    // Reveal-on-scroll
    if (!prefersReducedMotion) {
      const revealEls = document.querySelectorAll('[data-reveal]');
      if (revealEls.length) {
        const io = new IntersectionObserver((entries) => {
          for (const e of entries) {
            if (e.isIntersecting) {
              e.target.classList.add('is-revealed');
              io.unobserve(e.target);
            }
          }
        }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });
        revealEls.forEach(el => io.observe(el));
      }
    } else {
      document.querySelectorAll('[data-reveal]').forEach(el => el.classList.add('is-revealed'));
    }

    // 3D tilt micro-interaction (professional: subtle, bounded)
    if (!prefersReducedMotion) {
      const tilt = document.querySelectorAll('[data-tilt]');
      tilt.forEach((card) => {
        let raf = 0;
        const max = Number(card.getAttribute('data-tilt')) || 10;

        function onMove(ev) {
          const r = card.getBoundingClientRect();
          const x = (ev.clientX - r.left) / r.width;
          const y = (ev.clientY - r.top) / r.height;
          const rx = (0.5 - y) * max;
          const ry = (x - 0.5) * max;
          cancelAnimationFrame(raf);
          raf = requestAnimationFrame(() => {
            card.style.setProperty('--rx', `${rx.toFixed(2)}deg`);
            card.style.setProperty('--ry', `${ry.toFixed(2)}deg`);
            card.classList.add('is-tilting');
          });
        }

        function onLeave() {
          cancelAnimationFrame(raf);
          card.style.setProperty('--rx', `0deg`);
          card.style.setProperty('--ry', `0deg`);
          card.classList.remove('is-tilting');
        }

        card.addEventListener('mousemove', onMove);
        card.addEventListener('mouseleave', onLeave);
      });
    }

    // Server-side Django messages → premium toasts
    const server = document.getElementById('serverMessages');
    if (server) {
      server.querySelectorAll('[data-toast]').forEach((n) => {
        const lvl = (n.getAttribute('data-level') || 'info').toLowerCase();
        // Django tags often come as "success", "info", "warning", "error"
        const mapped = (lvl === 'error') ? 'danger' : lvl;
        toast(n.textContent?.trim() || 'Update', { level: mapped });
      });
    }
  });
})();


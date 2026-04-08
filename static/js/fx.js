(() => {
  const canvas = document.getElementById('fxCanvas');
  if (!canvas) return;

  const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;
  if (prefersReducedMotion) return;

  const ctx = canvas.getContext('2d', { alpha: true, desynchronized: true });
  if (!ctx) return;

  let w = 0, h = 0, dpr = 1;
  let running = true;
  let t0 = performance.now();
  let pointer = { x: 0, y: 0, has: false };

  const N = 72;
  const pts = [];

  function rand(min, max) { return min + Math.random() * (max - min); }

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = Math.max(1, window.innerWidth);
    h = Math.max(1, window.innerHeight);
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function init() {
    pts.length = 0;
    for (let i = 0; i < N; i++) {
      const z = rand(0.2, 1.0);
      pts.push({
        x: rand(0, w),
        y: rand(0, h),
        vx: rand(-0.18, 0.18) * z,
        vy: rand(-0.16, 0.16) * z,
        r: rand(0.9, 2.2) * (0.6 + z),
        z,
        hue: rand(185, 255),
      });
    }
  }

  function draw(now) {
    if (!running) return;
    const dt = Math.min(32, now - t0);
    t0 = now;

    ctx.clearRect(0, 0, w, h);

    // Soft glow wash (gives "3D depth" without looking gimmicky)
    const g = ctx.createRadialGradient(w * 0.22, h * 0.12, 0, w * 0.22, h * 0.12, Math.max(w, h) * 0.8);
    g.addColorStop(0, 'rgba(109,94,252,0.12)');
    g.addColorStop(0.55, 'rgba(13,110,253,0.06)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);

    const px = pointer.has ? pointer.x : w * 0.5;
    const py = pointer.has ? pointer.y : h * 0.35;

    // Update positions
    for (const p of pts) {
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      if (p.x < -50) p.x = w + 50;
      if (p.x > w + 50) p.x = -50;
      if (p.y < -50) p.y = h + 50;
      if (p.y > h + 50) p.y = -50;
    }

    // Connections (only near)
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i];
      for (let j = i + 1; j < pts.length; j++) {
        const b = pts[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist2 = dx * dx + dy * dy;
        const maxD = 140 * (0.55 + Math.min(a.z, b.z));
        if (dist2 < maxD * maxD) {
          const dist = Math.sqrt(dist2);
          const alpha = (1 - dist / maxD) * 0.12 * (0.6 + Math.min(a.z, b.z));
          ctx.strokeStyle = `rgba(170, 210, 255, ${alpha.toFixed(4)})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }

    // Points
    for (const p of pts) {
      const parX = (px - w * 0.5) * 0.02 * p.z;
      const parY = (py - h * 0.5) * 0.02 * p.z;
      const x = p.x + parX;
      const y = p.y + parY;

      const glow = ctx.createRadialGradient(x, y, 0, x, y, 26 * (0.55 + p.z));
      glow.addColorStop(0, `rgba(34, 211, 238, ${(0.07 * p.z).toFixed(4)})`);
      glow.addColorStop(0.5, `rgba(109, 94, 252, ${(0.05 * p.z).toFixed(4)})`);
      glow.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = glow;
      ctx.fillRect(x - 40, y - 40, 80, 80);

      ctx.beginPath();
      ctx.fillStyle = `hsla(${p.hue.toFixed(0)}, 92%, 70%, ${(0.35 * (0.6 + p.z)).toFixed(3)})`;
      ctx.arc(x, y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }

    requestAnimationFrame(draw);
  }

  function onVis() {
    running = document.visibilityState === 'visible';
    if (running) {
      t0 = performance.now();
      requestAnimationFrame(draw);
    }
  }

  resize();
  init();
  requestAnimationFrame(draw);

  window.addEventListener('resize', () => { resize(); init(); }, { passive: true });
  document.addEventListener('visibilitychange', onVis);
  window.addEventListener('pointermove', (e) => {
    pointer.x = e.clientX;
    pointer.y = e.clientY;
    pointer.has = true;
  }, { passive: true });
})();


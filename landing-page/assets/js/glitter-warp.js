// Standalone starfield warp tunnel — ported from the Framer GlitterWrap, no deps.
// Registers <glitter-warp>. Reads attributes: color1/2/3, speed, density,
// star-size, focal-depth, turbulence, brightness, glitter, trail, particles, reverse.
(function () {
  if (customElements.get('glitter-warp')) return;

  function parseColor(input) {
    if (!input) return [255, 255, 255];
    const s = input.trim();
    if (s.startsWith('#')) {
      let hex = s.slice(1);
      if (hex.length === 3) hex = hex.split('').map((c) => c + c).join('');
      const num = parseInt(hex, 16);
      return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
    }
    const m = s.match(/rgba?\(([^)]+)\)/i);
    if (m) {
      const p = m[1].split(',').map((x) => parseFloat(x.trim()));
      return [p[0] || 0, p[1] || 0, p[2] || 0];
    }
    return [255, 255, 255];
  }

  class GlitterWarp extends HTMLElement {
    connectedCallback() {
      this.style.position = this.style.position || 'absolute';
      this.style.display = 'block';
      this.style.overflow = 'hidden';
      const canvas = document.createElement('canvas');
      canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block';
      this.appendChild(canvas);
      this._canvas = canvas;
      const ctx = canvas.getContext('2d');
      this._ctx = ctx;

      const num = (a, d) => { const v = parseFloat(this.getAttribute(a)); return isNaN(v) ? d : v; };
      const cfg = () => ({
        reverse: this.getAttribute('reverse') === 'true',
        density: num('density', 100),
        stepZ: num('speed', 4) * 0.0008,
        focalDepth: num('focal-depth', 13) / 100,
        starScale: num('star-size', 10) * 0.15,
        turbulence: num('turbulence', 0) * 0.2,
        glitter: num('glitter', 3) * 0.1,
        brightness: Math.min(1, num('brightness', 100) / 100),
        trail: num('trail', 92) / 100,
        count: Math.max(1, Math.floor(num('particles', 420))),
      });
      const colStr = () => {
        const c = [parseColor(this.getAttribute('color1') || '#ffffff'),
                   parseColor(this.getAttribute('color2') || '#0EA5E9'),
                   parseColor(this.getAttribute('color3') || '#38bdf8')];
        return c.map((x) => `rgb(${x[0]},${x[1]},${x[2]})`);
      };

      const stars = [];
      let elapsed = 0, lastT = performance.now();
      const size = { w: 0, h: 0, dpr: 1 };

      const resetStar = (s, initial) => {
        const c = cfg();
        const angle = Math.random() * Math.PI * 2;
        const radius = (0.2 + Math.random() * 0.8) * (c.density / 15);
        s.x = Math.cos(angle) * radius;
        s.y = Math.sin(angle) * radius;
        if (c.reverse) s.z = initial ? c.focalDepth + Math.random() * (1 - c.focalDepth) : c.focalDepth;
        else s.z = initial ? Math.random() : 1.0;
        s.px = NaN; s.py = NaN;
        s.seed = Math.random() * 1000;
        s.vmul = 0.6 + Math.random() * 0.8;
        s.colorIdx = Math.floor(Math.random() * 3);
        s.flashUntil = 0;
        s.nextFlash = elapsed + 1 + Math.random() * 4 * (1 / Math.max(0.0001, c.glitter));
      };
      const makeStar = () => ({ x: 0, y: 0, z: 0, px: NaN, py: NaN, seed: 0, vmul: 1, colorIdx: 0, flashUntil: 0, nextFlash: 0 });
      const syncCount = () => {
        const count = cfg().count;
        if (stars.length === count) return;
        if (stars.length > count) stars.length = count;
        else while (stars.length < count) { const s = makeStar(); resetStar(s, true); stars.push(s); }
      };

      const resize = () => {
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const w = Math.max(1, Math.floor(this.clientWidth) || 600);
        const h = Math.max(1, Math.floor(this.clientHeight) || 400);
        if (size.w === w && size.h === h && size.dpr === dpr) return;
        size.w = w; size.h = h; size.dpr = dpr;
        canvas.width = Math.floor(w * dpr); canvas.height = Math.floor(h * dpr);
        canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, w, h);
      };
      syncCount(); resize();
      const ro = new ResizeObserver(resize); ro.observe(this); this._ro = ro;

      const draw = (deltaSec) => {
        const c = cfg();
        syncCount();
        const rgb = colStr();
        const { w, h } = size, cx = w / 2, cy = h / 2;
        const projScale = Math.min(w, h) * 0.9;
        const dt = Math.max(0.001, Math.min(0.1, deltaSec)) * 60;
        const keep = Math.pow(Math.min(0.98, Math.max(0, c.trail)), dt);
        const trailAlpha = Math.max(0.02, 1 - keep);
        ctx.globalAlpha = 1;
        ctx.globalCompositeOperation = 'destination-out';
        ctx.fillStyle = `rgba(0,0,0,${trailAlpha})`;
        ctx.fillRect(0, 0, w, h);
        ctx.globalCompositeOperation = 'lighter';
        for (let i = 0; i < stars.length; i++) {
          const s = stars[i];
          const vz = c.stepZ * s.vmul * dt;
          if (c.reverse) { s.z += vz; if (s.z >= 1.0) { resetStar(s); continue; } }
          else { s.z -= vz; if (s.z <= c.focalDepth) { resetStar(s); continue; } }
          let tx = s.x, ty = s.y;
          if (c.turbulence > 0) {
            const t = elapsed * 1.2 + s.seed, amp = c.turbulence * (1 - s.z) * 0.25;
            tx += Math.sin(t + s.seed) * amp; ty += Math.cos(t * 1.13 + s.seed * 0.7) * amp;
          }
          const persp = c.focalDepth / Math.max(s.z, 0.0001);
          const sx = cx + tx * persp * projScale, sy = cy + ty * persp * projScale;
          if (!c.reverse && (sx < -20 || sx > w + 20 || sy < -20 || sy > h + 20)) { resetStar(s); continue; }
          let flashMult = 1;
          if (c.glitter > 0) {
            if (elapsed >= s.nextFlash && s.flashUntil < elapsed) {
              s.flashUntil = elapsed + 0.04 + Math.random() * 0.07;
              s.nextFlash = elapsed + 1 + Math.random() * 4 * (1 / Math.max(0.0001, c.glitter));
            }
            if (elapsed <= s.flashUntil) flashMult = 1 + 2.5 * c.glitter;
          }
          const sizePersp = Math.min(2.5, (c.focalDepth / Math.max(s.z, 0.0001)) * 0.6);
          const baseR = Math.max(0.25, c.starScale * (0.4 + sizePersp));
          const maxR = 1 + c.starScale * 2.5;
          const r = Math.min(baseR * flashMult, maxR);
          const lifeT = c.reverse ? s.z : 1 - s.z;
          const fadeIn = c.reverse ? Math.min(1, (s.z - c.focalDepth) / (1 - c.focalDepth) / 0.12) : 1;
          const a = Math.min(1, c.reverse ? 0.85 - lifeT * 0.6 : lifeT * 0.9 + 0.05) * fadeIn * c.brightness * (flashMult > 1 ? 1 : 0.85);
          const col = rgb[s.colorIdx];
          if (!Number.isNaN(s.px) && !Number.isNaN(s.py)) {
            ctx.globalAlpha = a * 0.5; ctx.strokeStyle = col; ctx.lineWidth = Math.max(0.4, r * 0.4);
            ctx.beginPath(); ctx.moveTo(s.px, s.py); ctx.lineTo(sx, sy); ctx.stroke();
          }
          ctx.globalAlpha = a; ctx.fillStyle = col; ctx.fillRect(sx - r, sy - r, r * 2, r * 2);
          if (flashMult > 1) { const rf = Math.min(r * 1.4, maxR * 1.4); ctx.globalAlpha = a * 0.5; ctx.fillRect(sx - rf, sy - rf, rf * 2, rf * 2); }
          s.px = sx; s.py = sy;
        }
        ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
        elapsed += Math.min(0.1, Math.max(0, deltaSec));
      };

      const loop = (t) => { const d = (t - lastT) / 1000; lastT = t; draw(d); this._raf = requestAnimationFrame(loop); };
      this._raf = requestAnimationFrame(loop);
    }
    disconnectedCallback() {
      if (this._raf) cancelAnimationFrame(this._raf);
      if (this._ro) this._ro.disconnect();
    }
  }
  customElements.define('glitter-warp', GlitterWarp);
})();
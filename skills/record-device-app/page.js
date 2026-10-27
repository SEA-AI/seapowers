// Injected by rec.py into every page before the app's own scripts. rec.py calls it through window.__rec.
(() => {
  // Track every RTCPeerConnection the app creates, for its decode stats.
  const pcs = [];
  window.RTCPeerConnection = class extends window.RTCPeerConnection {
    constructor(...args) {
      super(...args);
      pcs.push(this);
    }
  };

  // Playwright videos show no OS cursor, so draw two: the script's (red core, moved by rec.py) and the user's
  // (blue core, follows the mouse). SEA.AI brand colours; hard-edged core, no shadows.
  const RED = "#CB0D00";
  const BLUE = "#0B1731";
  let scripted = false; // true while rec.py clicks, so its clicks don't move the user's cursor

  const dot = (css) => {
    const d = document.createElement("div");
    Object.assign(d.style, { position: "fixed", borderRadius: "50%", pointerEvents: "none", zIndex: 2147483647 }, css);
    document.documentElement.appendChild(d);
    return d;
  };
  const ring = (border, background) => ({
    width: "22px",
    height: "22px",
    margin: "-11px 0 0 -11px",
    boxSizing: "border-box",
    border,
    background,
  });
  const cursor = (core) => ring("2px solid #fff", `radial-gradient(circle, ${core} 0 4px, rgba(11,23,49,.35) 4.5px)`);
  const ripple = (x, y, color) => {
    const r = dot({
      left: `${x}px`,
      top: `${y}px`,
      ...ring(`2px solid ${color}`, "none"),
      transition: "transform .7s ease-out, opacity .7s ease-out",
    });
    r.getBoundingClientRect(); // commit the start state so the transition runs
    r.style.transform = "scale(2.6)";
    r.style.opacity = "0";
    setTimeout(() => r.remove(), 800);
  };
  const keep = (create) => {
    let el = null;
    return () => {
      if (!el?.isConnected) el = create();
      return el;
    };
  };
  const scriptCursor = keep(() => dot({ left: `${innerWidth / 2}px`, top: `${innerHeight / 2}px`, ...cursor(RED) }));
  const userCursor = keep(() => dot(cursor(BLUE)));

  addEventListener(
    "mousemove",
    (e) => {
      if (scripted) return;
      const d = userCursor();
      d.style.left = `${e.clientX}px`;
      d.style.top = `${e.clientY}px`;
    },
    true,
  );
  addEventListener("mousedown", (e) => scripted || ripple(e.clientX, e.clientY, BLUE), true);

  window.__rec = {
    /** Total WebRTC frames decoded; per connection, so one closed connection can't hide the others. */
    async frames() {
      let n = 0;
      for (const pc of pcs) {
        try {
          for (const r of (await pc.getStats()).values()) {
            if (r.type === "inbound-rtp" && r.kind === "video") n += r.framesDecoded || 0;
          }
        } catch {}
      }
      return n;
    },

    /** Visible clickable things with whatever names they have, plus their centre. */
    controls() {
      const clickable = "button,a,[role=button],[onclick]";
      return [...new Set([...document.querySelectorAll(`${clickable},svg`)].map((e) => e.closest(clickable) || e))]
        .map((e) => {
          const r = e.getBoundingClientRect();
          return {
            text: (e.innerText || "").trim().replace(/\s+/g, " ").slice(0, 40),
            aria: e.getAttribute("aria-label"),
            title: e.getAttribute("title"),
            cls: (e.className?.baseVal ?? e.className ?? "").toString().slice(0, 60),
            xy: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
            w: Math.round(r.width),
            h: Math.round(r.height),
          };
        })
        .filter((c) => c.w > 8 && c.h > 8 && c.xy[0] < innerWidth && c.xy[1] < innerHeight);
    },

    /** Glide the script's cursor to (x, y) over ms. */
    move(x, y, ms) {
      const d = scriptCursor();
      d.getBoundingClientRect();
      d.style.transition = `left ${ms}ms ease-in-out, top ${ms}ms ease-in-out`;
      d.style.left = `${x}px`;
      d.style.top = `${y}px`;
    },

    /** Mark the next mouse events as the script's and show its ripple; clickDone() ends the mark. */
    click(x, y) {
      scripted = true;
      ripple(x, y, RED);
    },
    clickDone() {
      scripted = false;
    },
  };
})();

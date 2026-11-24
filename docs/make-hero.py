#!/usr/bin/env python3
"""Draw docs/hero.svg: the animated banner at the top of the README.

usage: python3 docs/make-hero.py

The banner is a self-contained SVG animated with SMIL (<animateMotion>,
<animate>), because GitHub shows SVG images with their animations but strips
scripts. Geometry and colours follow skills/system-tour/assets/engine.html.
"""
from pathlib import Path

S = 30                       # grid step, as in the engine
W, H = 1200, 560             # banner size
CYCLE = 15.0                 # seconds for one loop
OX, OY = 440, 175            # where grid (0, 0) lands in the banner

PAL = {  # top, left, right, edge
    "entry":   ("#6a5236", "#4f3d29", "#3f3122", "#a8875c"),
    "service": ("#3a516b", "#2d3f55", "#243346", "#6f8fb3"),
    "ai":      ("#476236", "#374c2b", "#2c3d22", "#86a865"),
}
COL = {"req": "#e2a85c", "res": "#8fc78a", "evt": "#b392e6", "ai": "#e6d16a", "err": "#ef6a55"}

NODES = {  # id: (kind, u, v, label, sub)
    "shop":   ("people",  -1.5, 7.5, "Shoppers", "web"),
    "web":    ("entry",    2,   4.5, "Web", "SPA · CDN"),
    "gw":     ("entry",    5.5, 1.5, "Gateway", "single entry"),
    "orders": ("service",  9.5, -1,  "orders", ""),
    "pay":    ("service",  9.5, -5,  "payments", ""),
    "inv":    ("service", 13,   -1,  "inventory", ""),
    "notif":  ("service", 13,   -5,  "notifications", ""),
    "assist": ("ai",       9.5,  3,  "assistant", "proposes only"),
    "db":     ("store",   16.5, -2.5, "PostgreSQL", ""),
    "bus":    ("store",   16.5,  1.5, "Message bus", "durable queues"),
    "psp":    ("ext",      8,  -10,  "Payment provider", ""),
}

# (from, to, type, label, start s, mid) — mid is the corner of the L wire, as (u, v)
MOVES = [
    ("shop",   "web",    "req", "pay",            0.4, None),
    ("web",    "gw",     "req", "POST /orders",   1.5, None),
    ("gw",     "orders", "req", "place order",    2.7, None),
    ("orders", "db",     "req", "order + outbox", 3.9, None),
    ("orders", "pay",    "req", "charge",         5.1, None),
    ("pay",    "psp",    "req", "payment intent", 6.1, None),
    ("psp",    "pay",    "res", "authorised",     7.3, None),
    ("pay",    "orders", "res", "paid ✓",         8.4, None),
    ("orders", "bus",    "evt", "OrderPlaced",    9.4, None),
    ("bus",    "inv",    "evt", "OrderPlaced",   10.7, None),
    ("bus",    "notif",  "evt", "",              10.7, None),
    ("bus",    "assist", "evt", "",              10.7, None),
    ("assist", "orders", "ai",  "proposal",      12.0, None),
    ("gw",     "web",    "res", "confirmed",     12.4, None),
]
MOVE_DUR = 1.05

ANGLES = ["Using the app", "Scaling", "When something fails", "Why a service"]


def P(u, v):
    return (OX + (u - v) * S, OY + (u + v) * S / 2)


def pts(a):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in a)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cube(x, y, kind, a=1.25, h=26):
    top, left, right, edge = PAL[kind]
    w, hh = a * S, a * S / 2
    pw, ph = w * 1.45, hh * 1.45
    return (
        f'<polygon points="{pts([(x, y-ph), (x+pw, y), (x, y+ph), (x-pw, y)])}" fill="{edge}" fill-opacity=".07" stroke="{edge}" stroke-opacity=".35"/>'
        f'<polygon points="{pts([(x-w, y-h), (x, y-h+hh), (x, y+hh), (x-w, y)])}" fill="{left}" stroke="{edge}" stroke-opacity=".5"/>'
        f'<polygon points="{pts([(x, y-h+hh), (x+w, y-h), (x+w, y), (x, y+hh)])}" fill="{right}" stroke="{edge}" stroke-opacity=".5"/>'
        f'<polygon points="{pts([(x, y-h-hh), (x+w, y-h), (x, y-h+hh), (x-w, y-h)])}" fill="{top}" stroke="{edge}" stroke-width="1.4"/>'
    ), y - h


def cylinder(x, y):
    rx, ry, h = 24, 11, 30
    return (
        f'<ellipse cx="{x}" cy="{y}" rx="{rx*1.6}" ry="{ry*1.6}" fill="#8a74b3" fill-opacity=".06" stroke="#8a74b3" stroke-opacity=".25"/>'
        f'<path d="M{x-rx},{y-h} L{x-rx},{y} A{rx},{ry} 0 0 0 {x+rx},{y} L{x+rx},{y-h} Z" fill="url(#cylSide)" stroke="#8a74b3"/>'
        f'<ellipse cx="{x}" cy="{y-h}" rx="{rx}" ry="{ry}" fill="url(#cylTop)" stroke="#8a74b3"/>'
    )


def people(x, y):
    a, t = 2.0, 6
    w, hh = a * S, a * S / 2
    out = (
        f'<polygon points="{pts([(x-w, y-t), (x, y-t+hh), (x, y+hh), (x-w, y)])}" fill="#221f1b" stroke="#4a443c"/>'
        f'<polygon points="{pts([(x, y-t+hh), (x+w, y-t), (x+w, y), (x, y+hh)])}" fill="#2a2621" stroke="#4a443c"/>'
        f'<polygon points="{pts([(x, y-t-hh), (x+w, y-t), (x, y-t+hh), (x-w, y-t)])}" fill="#1d1a17" stroke="#6d665c"/>'
    )
    cols = ["#c9b5e6", "#e2c08f", "#a9cf9b", "#9fb8d9", "#e0a6a0"]
    i = 0
    for r in range(3):
        for c in range(3):
            du, dv = (r - 1) * 0.55 * (a / 1.5), (c - 1) * 0.55 * (a / 1.5)
            px, py = x + (du - dv) * S * 0.9, y - t + (du + dv) * S * 0.45
            out += f'<rect x="{px-4:.1f}" y="{py-12:.1f}" width="8" height="12" rx="4" fill="{cols[i % 5]}" fill-opacity=".85"/>'
            out += f'<circle cx="{px:.1f}" cy="{py-15:.1f}" r="3.6" fill="#efe8dc"/>'
            i += 1
    return out


def ext(x, y):
    a, h = 0.95, 18
    w, hh = a * S, a * S / 2
    st = 'stroke="#e58a6f" stroke-opacity=".8" stroke-dasharray="4 3"'
    return (
        f'<polygon points="{pts([(x-w, y-h), (x, y-h+hh), (x, y+hh), (x-w, y)])}" fill="#1d1a17" {st}/>'
        f'<polygon points="{pts([(x, y-h+hh), (x+w, y-h), (x+w, y), (x, y+hh)])}" fill="#221d19" {st}/>'
        f'<polygon points="{pts([(x, y-h-hh), (x+w, y-h), (x, y-h+hh), (x-w, y-h)])}" fill="#2a221d" {st}/>'
    )


def pill(x, y, text, sub=""):
    wt = len(text) * 6.4 + (len(sub) * 5.8 + 6 if sub else 0)
    s = f'<tspan fill="#9d9488" font-size="9.5" dx="6">{esc(sub)}</tspan>' if sub else ""
    return (f'<rect x="{x}" y="{y-9}" width="{wt+20:.0f}" height="18" rx="9" fill="#1b1916" stroke="#4a443c"/>'
            f'<text x="{x+10}" y="{y+4}" class="pl">{esc(text)}{s}</text>')


def route(a, b):
    """The engine's default L: walk u first from the alphabetically first id."""
    (_, ua, va, *_), (_, ub, vb, *_) = NODES[a], NODES[b]
    first = sorted([a, b])[0]
    mid = (ub, va) if first == a else (ua, vb)
    return [P(ua, va), P(*mid), P(ub, vb)]


def d_of(p):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in p)


def main():
    out = []
    add = out.append
    add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="system-tour: an animated architecture map where an order travels from shoppers through a gateway, services, a database and a message bus">')
    add('''<defs>
<radialGradient id="bg" cx="50%" cy="42%" r="70%"><stop offset="0" stop-color="#1f1b17"/><stop offset="1" stop-color="#141210"/></radialGradient>
<linearGradient id="cylTop" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6b5590"/><stop offset="1" stop-color="#4e3d6b"/></linearGradient>
<linearGradient id="cylSide" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3b2e52"/><stop offset=".35" stop-color="#5a4880"/><stop offset="1" stop-color="#33284a"/></linearGradient>
<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="card"><rect width="1200" height="560" rx="18"/></clipPath>
</defs>
<style>
.t{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.lbl{font:600 12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#f3eee6;text-anchor:middle}
.sub{font:9.5px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#b9b0a3;text-anchor:middle}
.pl{font:10.5px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#e8e1d6}
.tag{font:600 12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.wire{fill:none;stroke:#3a352e;stroke-width:1.4}
.on{fill:none;stroke:#cfc4b1;stroke-width:1.6;stroke-dasharray:5 6;opacity:.55}
</style>''')
    add('<g clip-path="url(#card)">')
    add(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')

    # grid
    for u in range(-8, 26):
        add(f'<polyline points="{pts([P(u, -14), P(u, 14)])}" stroke="#211e1a" fill="none"/>')
    for v in range(-14, 15):
        add(f'<polyline points="{pts([P(-8, v), P(25, v)])}" stroke="#211e1a" fill="none"/>')

    # zone around what the shop runs
    za, zb, zc, zd = 0.4, -7.2, 18.6, 6.3
    add(f'<polygon points="{pts([P(za, zb), P(zc, zb), P(zc, zd), P(za, zd)])}" fill="none" stroke="#5a5348" stroke-width="1.2" stroke-dasharray="6 6"/>')
    zx, zy = P(za + 0.9, zd + 0.2)
    add(f'<text x="{zx:.0f}" y="{zy:.0f}" transform="rotate(26.565 {zx:.0f} {zy:.0f})" class="t" font-size="11" letter-spacing="2" fill="#7a7266">ACME · PRIVATE CLOUD</text>')

    # wires (each pair once) with a marching dash
    seen = set()
    for a, b, *_ in MOVES:
        k = tuple(sorted([a, b]))
        if k in seen:
            continue
        seen.add(k)
        d = d_of(route(a, b))
        add(f'<path class="wire" d="{d}"/>')
        add(f'<path class="on" d="{d}"><animate attributeName="stroke-dashoffset" from="0" to="-22" dur="1.6s" repeatCount="indefinite"/></path>')

    # nodes, back to front
    labels, pills = [], []
    for nid, (kind, u, v, label, sub) in sorted(NODES.items(), key=lambda kv: kv[1][1] + kv[1][2]):
        x, y = P(u, v)
        if kind == "store":
            add(cylinder(x, y)); pills.append(pill(x + 30, y - 22, label, sub))
        elif kind == "people":
            add(people(x, y)); pills.append(pill(x - 40, y + 44, label, sub))
        elif kind == "ext":
            add(ext(x, y)); pills.append(pill(x + 30, y - 16, label))
        else:
            g, top = cube(x, y, kind)
            add(g)
            labels.append(f'<text x="{x:.0f}" y="{top+10:.0f}" class="lbl" stroke="#141210" stroke-width="3" paint-order="stroke">{esc(label)}</text>')
            if sub:
                labels.append(f'<text x="{x:.0f}" y="{top+22:.0f}" class="sub" stroke="#141210" stroke-width="3" paint-order="stroke">{esc(sub)}</text>')
    out.extend(labels)
    out.extend(pills)

    # packets: each moves once per cycle, between its start and start + MOVE_DUR
    for a, b, typ, label, start, _ in MOVES:
        c = COL[typ]
        t0, t1 = start / CYCLE, (start + MOVE_DUR) / CYCLE
        fade = min(1.0, (start + MOVE_DUR + 0.9) / CYCLE)
        path = d_of(route(a, b))
        kt = f"0;{t0:.4f};{t1:.4f};1"
        add('<g opacity="0">')
        add(f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{t0:.4f};{t0+0.004:.4f};{t1:.4f};{fade:.4f};1" dur="{CYCLE}s" repeatCount="indefinite"/>')
        add(f'<animateMotion path="{path}" keyPoints="0;0;1;1" keyTimes="{kt}" calcMode="linear" dur="{CYCLE}s" repeatCount="indefinite"/>')
        add(f'<circle r="9" fill="{c}" fill-opacity=".22"/><circle r="5" fill="{c}" filter="url(#glow)"/>')
        if label:
            w = len(label) * 7.3 + 18
            add(f'<rect x="{-w/2:.1f}" y="-36" width="{w:.1f}" height="22" rx="7" fill="#141210" stroke="{c}" stroke-width="1.2"/>'
                f'<text x="{-w/2+9:.1f}" y="-21" class="tag" fill="{c}">{esc(label)}</text>')
        add('</g>')

    # title block
    add('<text x="44" y="64" class="t" font-size="13" letter-spacing="1.5" fill="#a39b8f">A SKILL FOR CLAUDE CODE</text>')
    add('<text x="42" y="104" class="t" font-size="38" font-weight="700" fill="#ece6dc">system-tour</text>')
    add('<text x="44" y="134" class="t" font-size="15" fill="#c9d98f">See how your architecture behaves,</text>')
    add('<text x="44" y="156" class="t" font-size="15" fill="#c9d98f">not just what boxes it has.</text>')

    # the four angles, lit one after another
    x = 44
    n = len(ANGLES)
    for i, name in enumerate(ANGLES):
        w = len(name) * 7.4 + 26
        a0, a1 = i / n, (i + 1) / n
        vals = "0;0;1;1;0;0" if i else "1;1;0;0;0;1"
        kts = f"0;{a0:.3f};{a0+0.01:.3f};{a1-0.01:.3f};{a1:.3f};1" if i else f"0;{a1-0.01:.3f};{a1:.3f};0.99;0.995;1"
        add(f'<g transform="translate({x:.0f},508)">')
        add(f'<rect width="{w:.0f}" height="28" rx="14" fill="#1b1916" stroke="#2e2a25"/>')
        add(f'<rect width="{w:.0f}" height="28" rx="14" fill="#c9d98f" opacity="0"><animate attributeName="opacity" values="{vals}" keyTimes="{kts}" dur="{CYCLE}s" repeatCount="indefinite"/></rect>')
        add(f'<text x="13" y="18.5" class="t" font-size="12" fill="#a39b8f">{esc(name)}</text>')
        add(f'<text x="13" y="18.5" class="t" font-size="12" fill="#1a1a12" opacity="0">{esc(name)}<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" dur="{CYCLE}s" repeatCount="indefinite"/></text>')
        add('</g>')
        x += w + 8

    # legend
    lx = 760
    for typ, name in (("req", "request"), ("res", "response"), ("evt", "event"), ("ai", "AI call")):
        add(f'<circle cx="{lx}" cy="522" r="4" fill="{COL[typ]}"/><text x="{lx+9}" y="526" class="t" font-size="11.5" fill="#a39b8f">{name}</text>')
        lx += len(name) * 7 + 34

    add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="#2e2a25"/>')
    add('</g></svg>')
    dest = Path(__file__).resolve().parent / "hero.svg"
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {dest} ({dest.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

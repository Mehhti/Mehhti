#!/usr/bin/env python3
"""
make_ai_svgs.py - builds the neural-network themed graphics for the
Mehhti profile README (v6, "neural edition").

    python tools/make_ai_svgs.py        # writes the SVGs into the current folder

Outputs:
    ai-banner.svg      hero figure: a small CNN, signals flow layer by layer
    ai-divider.svg     thin row of nodes with a travelling pulse
    ai-hdr-*.svg       section headers styled as "layer NN/06"

All animation is plain CSS inside the SVG (GitHub renders it), and every
animation stops for visitors whose system asks for reduced motion.
Edit TEXT / colours below and re-run instead of hand-editing the SVGs.
"""
import math
import random
from xml.sax.saxutils import escape

random.seed(11)

# ── palette ──────────────────────────────────────────────────────────
BG0, BG1 = "#060a17", "#0d1532"
CY, VI, AM = "#5ee7ff", "#a78bfa", "#f6c177"
TX, MUT, DIM = "#d6def5", "#8a97c2", "#56628f"
LBL = "#b3bfe6"
GRID, EDGE = "#1c2650", "#24315e"
MONO = "'JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SANS = "'Inter','Segoe UI',system-ui,-apple-system,Helvetica,Arial,sans-serif"
REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"

# ── text you may want to change ─────────────────────────────────────
NAME = "Mehhti"
HEADLINE = "AI & Machine Learning"
SUBLINE = "deep learning · computer vision · LLMs"
SIDE_QUEST = "▸ side quest: building Android apps, just for fun"

# Demo model: one sample per forward pass, each with its own input and its own
# prediction, like a real classifier. (centre_col, centre_row, spread, strength)
# blobs draw the 6x6 input; probs are the softmax output for that input.
SAMPLES = [
    {"blobs": [(2.4, 2.6, 3.2, 0.9), (4.2, 1.2, 0.9, 0.35)], "probs": (0.06, 0.89, 0.05)},
    {"blobs": [(4.0, 1.4, 1.4, 0.95), (1.0, 4.0, 1.5, 0.2)], "probs": (0.71, 0.21, 0.08)},
    {"blobs": [(2.5, 2.5, 8.0, 0.18)], "probs": (0.12, 0.09, 0.79)},
    {"blobs": [(1.3, 1.5, 1.2, 0.7), (4.2, 4.0, 1.4, 0.7)], "probs": (0.38, 0.47, 0.15)},
]

HEADERS = [
    ("about", "ABOUT"),
    ("research", "AI & ML PROJECTS"),
    ("toolkit", "TOOLKIT"),
    ("fun", "BUILT FOR FUN"),
    ("stats", "STATS"),
    ("connect", "CONNECT"),
]


def n(x):
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s


def curve(x1, y1, x2, y2):
    mx = (x1 + x2) / 2
    return f"M{n(x1)} {n(y1)}C{n(mx)} {n(y1)} {n(mx)} {n(y2)} {n(x2)} {n(y2)}"


def glow(fid, sd=2.2):
    return (f'<filter id="{fid}" x="-50%" y="-50%" width="200%" height="200%">'
            f'<feGaussianBlur stdDeviation="{sd}" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


# ════════════════════════════════════════════════════════════════════
#  BANNER
# ════════════════════════════════════════════════════════════════════
def banner():
    W, H = 1280, 420
    CYC = 4.8          # one full forward pass, seconds
    STEP = 0.7         # time between layers
    o = []
    a = o.append

    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
      'role="img" aria-labelledby="t d">')
    a(f'<title id="t">{escape(NAME)} — {escape(HEADLINE)}</title>')
    a('<desc id="d">A small convolutional neural network drawn as a scientific figure: an input '
      'image, convolution and pooling feature maps, two dense layers and a softmax output, with '
      'signals flowing through the layers one at a time; each pass takes a new sample and gives its own prediction. On the left: the name, a training-loss '
      'curve, and a note that Android apps are built for fun.</desc>')

    # ── styles ──
    a("<style>")
    a(f".pulse{{fill:none;stroke-width:1.8;stroke-linecap:round;stroke-dasharray:7 200;"
      f"stroke-dashoffset:7;opacity:0;animation:pulse {CYC}s linear infinite backwards}}")
    a("@keyframes pulse{0%{stroke-dashoffset:7;opacity:0}1%{opacity:1}"
      "14%{stroke-dashoffset:-100;opacity:1}15%,100%{stroke-dashoffset:-100;opacity:0}}")
    a(f".node{{fill-opacity:.55;animation:fire {CYC}s ease-out infinite backwards}}")
    a("@keyframes fire{0%{fill-opacity:.2}5%{fill-opacity:1}24%,100%{fill-opacity:.2}}")
    a(f".map{{fill-opacity:.22;animation:fmap {CYC}s ease-out infinite backwards}}")
    a("@keyframes fmap{0%{fill-opacity:.08}5%{fill-opacity:.5}24%,100%{fill-opacity:.08}}")
    # The prediction never changes: bars always sit at their real values and only
    # brighten when the signal reaches the output layer.
    a(f".bar{{animation:bar {CYC}s ease-out infinite}}")
    a("@keyframes bar{0%,70%{fill-opacity:.55}76%,94%{fill-opacity:1}100%{fill-opacity:.55}}")
    # sliding 3x3 kernel over the 6x6 input: 16 positions
    pitch = 11
    frames = []
    for i in range(16):
        r, c = divmod(i, 4)
        frames.append(f"{n(i * 100 / 16)}%{{transform:translate({c * pitch}px,{r * pitch}px)}}")
    # kernel sweep has the same period as the forward pass, so every pass looks identical
    a(f".kern{{animation:kern {CYC}s steps(1,end) infinite}}")
    a("@keyframes kern{" + "".join(frames) + "100%{transform:translate(0px,0px)}}")
    # dasharray lives only inside the keyframes, so the static (reduced-motion) curve is solid
    a(f".curve{{animation:draw {2 * CYC}s ease-in-out infinite}}")
    a("@keyframes draw{0%{stroke-dasharray:100 100;stroke-dashoffset:100;opacity:1}"
      "45%{stroke-dasharray:100 100;stroke-dashoffset:0}"
      "92%{stroke-dasharray:100 100;stroke-dashoffset:0;opacity:1}"
      "100%{stroke-dasharray:100 100;stroke-dashoffset:0;opacity:0}}")
    NS = len(SAMPLES)
    LONG = NS * CYC
    a(f".smp{{opacity:0;animation:smp {LONG}s steps(1,end) infinite}}.smp.first{{opacity:1}}")
    a(f"@keyframes smp{{0%{{opacity:1}}{n(100 / NS)}%{{opacity:0}}100%{{opacity:0}}}}")
    a(".blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}")
    a(REDUCED)
    a("</style>")

    # ── defs ──
    a("<defs>")
    a(f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/>'
      f'<stop offset="1" stop-color="{BG1}"/></linearGradient>')
    a(f'<radialGradient id="halo" cx="900" cy="215" r="430" gradientUnits="userSpaceOnUse">'
      f'<stop offset="0" stop-color="{VI}" stop-opacity=".16"/>'
      f'<stop offset="1" stop-color="{VI}" stop-opacity="0"/></radialGradient>')
    a(f'<linearGradient id="nm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CY}"/>'
      f'<stop offset="1" stop-color="{VI}"/></linearGradient>')
    a('<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
      '<circle cx="1" cy="1" r="1" fill="#26336a"/></pattern>')
    a(glow("glow"))
    a(f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>')
    a("</defs>")

    # ── background ──
    a('<g clip-path="url(#frame)">')
    a(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    a(f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity=".55"/>')
    a(f'<rect width="{W}" height="{H}" fill="url(#halo)"/>')
    a("</g>")
    a(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{GRID}"/>')
    a(f'<line x1="528" y1="64" x2="528" y2="372" stroke="{GRID}" stroke-dasharray="3 5"/>')

    # ── left: identity block ──
    a(f'<text x="64" y="92" font-family="{MONO}" font-size="14" fill="{CY}">$ whoami</text>')
    a(f'<text x="61" y="152" font-family="{SANS}" font-size="70" font-weight="800" '
      f'letter-spacing="1" fill="url(#nm)">{escape(NAME)}</text>')
    a(f'<text x="64" y="192" font-family="{SANS}" font-size="24" font-weight="600" '
      f'fill="{TX}">{escape(HEADLINE)}</text>')
    a(f'<text x="64" y="221" font-family="{MONO}" font-size="14.5" fill="{MUT}">{escape(SUBLINE)}</text>')

    # loss chart
    cx0, cx1, cy0, cy1 = 64, 420, 262, 338
    a(f'<text x="{cx0}" y="251" font-family="{MONO}" font-size="11" fill="{MUT}">training loss</text>')
    a(f'<text x="{cx1}" y="251" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUT}">'
      f'<tspan fill="{CY}">●</tspan> train  <tspan fill="{VI}">●</tspan> val</text>')
    for k in (1, 2, 3):
        y = cy0 + (cy1 - cy0) * k / 4
        a(f'<line x1="{cx0}" y1="{n(y)}" x2="{cx1}" y2="{n(y)}" stroke="{GRID}" stroke-dasharray="2 4"/>')
    a(f'<path d="M{cx0} {cy0}V{cy1}H{cx1}" fill="none" stroke="{EDGE}" stroke-width="1.2"/>')

    def loss_path(base, amp, tau, noise):
        pts = []
        for i in range(61):
            t = i / 60
            v = base + amp * math.exp(-t / tau) + random.gauss(0, noise) * (1 - 0.5 * t)
            x = cx0 + 4 + t * (cx1 - cx0 - 8)
            y = cy1 - 3 - v * (cy1 - cy0 - 8)
            pts.append(f"{n(x)} {n(y)}")
        return "M" + "L".join(pts)

    a(f'<path class="curve" pathLength="100" d="{loss_path(0.12, 0.78, 0.25, 0.014)}" fill="none" '
      f'stroke="{VI}" stroke-width="1.4" stroke-opacity=".85" stroke-linejoin="round"/>')
    a(f'<path class="curve" pathLength="100" d="{loss_path(0.06, 0.86, 0.2, 0.009)}" fill="none" '
      f'stroke="{CY}" stroke-width="1.8" stroke-linejoin="round" filter="url(#glow)"/>')
    a(f'<text x="{cx1}" y="354" text-anchor="end" font-family="{MONO}" font-size="10" fill="{DIM}">epochs →</text>')

    a(f'<text x="64" y="390" font-family="{MONO}" font-size="13.5" fill="{AM}">{escape(SIDE_QUEST)}'
      f'<tspan class="blink"> █</tspan></text>')

    # ── right: the network ──
    # faint equations / annotations
    a(f'<g font-family="{MONO}" font-size="12.5" fill="{MUT}" opacity=".6">')
    a('<text x="585" y="122">h = ReLU(W ∗ x + b)</text>')
    a('<text x="866" y="80">a = σ(Wx + b)</text>')
    a('<text x="1240" y="112" text-anchor="end">softmax(z) = exp(z) / Σ exp(z)</text>')
    a('<text x="585" y="402">θ ← θ − η · ∇θ L(θ)</text>')
    a("</g>")
    a(f'<text x="1240" y="44" text-anchor="end" font-family="{MONO}" font-size="11" fill="{DIM}">'
      'Conv → Pool → Dense → Dense → Softmax</text>')
    a(f'<text x="1240" y="402" text-anchor="end" font-family="{SANS}" font-size="12" font-style="italic" '
      f'fill="{MUT}">fig. 1 — signals flowing forward, layer by layer</text>')

    static, pulses = [], []

    def link(x1, y1, x2, y2, group, color, prob=1.0):
        d = curve(x1, y1, x2, y2)
        static.append(f'<path d="{d}"/>')
        if random.random() < prob:
            delay = group * STEP + random.uniform(0, 0.08)
            pulses.append(f'<path class="pulse" pathLength="100" d="{d}" stroke="{color}" '
                          f'style="animation-delay:{delay:.2f}s"/>')

    # input image (6x6) with a blob, like a tiny scan
    gx, gy, cell = 578, 177, 9.5
    ext = 5 * pitch + cell
    def show(start):
        """animation-delay that makes a group visible from `start` for one pass, every LONG s"""
        d = start % LONG
        return f"animation-delay:{(d - LONG if d else 0):.2f}s"

    a(f'<rect x="{gx - 4}" y="{gy - 4}" width="{n(ext + 8)}" height="{n(ext + 8)}" rx="4" '
      f'fill="none" stroke="{EDGE}"/>')
    for i, smp in enumerate(SAMPLES):
        cells = []
        for r in range(6):
            for c in range(6):
                I = sum(k * math.exp(-((c - bx) ** 2 + (r - by) ** 2) / sp) for bx, by, sp, k in smp["blobs"])
                I = min(1.0, I + random.uniform(0, 0.12))
                cells.append(f'<rect x="{n(gx + c * pitch)}" y="{n(gy + r * pitch)}" width="{cell}" '
                             f'height="{cell}" rx="1.5" fill-opacity="{0.06 + 0.8 * I:.2f}"/>')
        cls = "smp first" if i == 0 else "smp"
        a(f'<g class="{cls}" style="{show(i * CYC)}">')
        a(f'<g fill="{CY}">' + "".join(cells) + "</g>")
        a(f'<text x="{gx - 4}" y="{gy - 10}" font-family="{MONO}" font-size="10" fill="{DIM}">'
          f'sample #{i + 1:02d}</text>')
        a("</g>")
    a(f'<rect class="kern" x="{gx - 1.5}" y="{gy - 1.5}" width="{n(2 * pitch + cell + 3)}" '
      f'height="{n(2 * pitch + cell + 3)}" rx="2" fill="none" stroke="{AM}" stroke-width="1.4"/>')

    def para(x, y, w, h, s):
        return f"{n(x)},{n(y + s)} {n(x + w)},{n(y)} {n(x + w)},{n(y + h - s)} {n(x)},{n(y + h)}"

    # conv feature maps
    conv = [(668 + i * 13, 155, 36, 110, 18) for i in range(4)]
    # pooled maps
    pool = [(786 + i * 10, 175, 26, 70, 12) for i in range(4)]

    gr = gx + ext + 4
    for y1, y2 in ((190, 192), (209, 213), (228, 236)):
        link(gr, y1, 668, y2, 0, CY)
    cr = conv[-1][0] + conv[-1][2]
    for y1, y2 in ((178, 196), (201, 214), (226, 232)):
        link(cr, y1, 786, y2, 1, CY)

    d1 = [(915, 210 + (k - 3) * 32) for k in range(7)]
    d2 = [(1015, 210 + (k - 2) * 38) for k in range(5)]
    out = [(1105, 158), (1105, 210), (1105, 262)]
    pr = pool[-1][0] + pool[-1][2]
    for sy in (186, 204, 222):
        for (x, y) in d1:
            link(pr, sy, x - 7, y, 2, CY, 0.75)
    for (x1, y1) in d1:
        for (x2, y2) in d2:
            link(x1 + 7, y1, x2 - 7, y2, 3, CY, 0.7)
    for (x1, y1) in d2:
        for (x2, y2) in out:
            link(x1 + 7, y1, x2 - 8, y2, 4, VI, 0.9)

    a(f'<g fill="none" stroke="{EDGE}" stroke-width=".9">' + "".join(static) + "</g>")
    a('<g filter="url(#glow)">' + "".join(pulses) + "</g>")

    def maps(lst, delay):
        for (x, y, w, h, s) in reversed(lst):
            a(f'<polygon class="map" points="{para(x, y, w, h, s)}" fill="{VI}" stroke="{VI}" '
              f'stroke-opacity=".75" stroke-width="1.1" style="animation-delay:{delay:.2f}s"/>')

    maps(conv, 1 * STEP - 0.03)
    maps(pool, 2 * STEP - 0.03)

    a('<g filter="url(#glow)">')
    for layer, color, r, k in ((d1, CY, 7, 3), (d2, VI, 7, 4), (out, AM, 8, 5)):
        for (x, y) in layer:
            a(f'<circle class="node" cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="{color}" '
              f'stroke-width="1.2" style="animation-delay:{k * STEP - 0.03:.2f}s"/>')
    a("</g>")

    # softmax output: tracks are fixed; each sample's prediction appears when its
    # signal reaches the output layer and stays until the next sample's arrives
    for (x, y) in out:
        a(f'<rect x="1124" y="{y - 4}" width="70" height="8" rx="4" fill="{EDGE}"/>')
    arrive = 5 * STEP - 0.03
    for i, smp in enumerate(SAMPLES):
        probs = smp["probs"]
        best = probs.index(max(probs))
        cls = "smp first" if i == 0 else "smp"
        a(f'<g class="{cls}" style="{show(i * CYC + arrive)}">')
        bx, by = out[best]
        a(f'<circle cx="{bx}" cy="{by}" r="12.5" fill="none" stroke="{AM}" stroke-opacity=".7" '
          f'stroke-width="1.2" filter="url(#glow)"/>')
        for (x, y), p in zip(out, probs):
            a(f'<rect class="bar" x="1124" y="{y - 4}" width="{n(max(3, 70 * p))}" height="8" rx="4" fill="{AM}"/>')
            col = AM if p == max(probs) else MUT
            a(f'<text x="1202" y="{y + 4}" font-family="{MONO}" font-size="11" fill="{col}">{p:.2f}</text>')
        a("</g>")

    # layer labels
    labels = [
        (gx + ext / 2, "input", "28×28"),
        (707, "conv 3×3", "32 filters · ReLU"),
        (814, "max-pool", "2×2"),
        (915, "dense", "128 · ReLU"),
        (1015, "dense", "64 · dropout"),
        (1160, "softmax", "p(y | x)"),
    ]
    a(f'<g font-family="{MONO}" text-anchor="middle">')
    for x, name, sub in labels:
        a(f'<text x="{n(x)}" y="352" font-size="12" fill="{LBL}">{escape(name)}</text>')
        a(f'<text x="{n(x)}" y="368" font-size="10.5" fill="{DIM}">{escape(sub)}</text>')
    a("</g>")

    a("</svg>")
    return "\n".join(o)


# ════════════════════════════════════════════════════════════════════
#  SECTION HEADER
# ════════════════════════════════════════════════════════════════════
def header(idx, total, title):
    W, H = 840, 64
    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
      f'role="img" aria-label="{escape(title.title())}">')
    a("<style>")
    a(".run{fill:none;stroke-dasharray:5 100;stroke-dashoffset:5;animation:run 5s linear infinite}")
    a("@keyframes run{0%{stroke-dashoffset:5}60%,100%{stroke-dashoffset:-100}}")
    a(REDUCED)
    a("</style>")
    a("<defs>")
    a(f'<linearGradient id="hb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/>'
      f'<stop offset="1" stop-color="{BG1}"/></linearGradient>')
    x0 = 102 + len(title) * 16 + 18
    x1 = 712
    # userSpaceOnUse: a horizontal line has a zero-height bounding box, which breaks bbox gradients
    a(f'<linearGradient id="rule" gradientUnits="userSpaceOnUse" x1="{x0}" y1="0" x2="{x1}" y2="0">'
      f'<stop offset="0" stop-color="{CY}" stop-opacity=".7"/>'
      f'<stop offset="1" stop-color="{VI}" stop-opacity=".15"/></linearGradient>')
    a(glow("hg", 1.6))
    a("</defs>")
    a(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="url(#hb)" stroke="{GRID}"/>')
    # icon: 2 -> 1 neuron
    a(f'<g stroke="{EDGE}" stroke-width="1.2"><line x1="26" y1="22" x2="48" y2="32"/>'
      f'<line x1="26" y1="42" x2="48" y2="32"/></g>')
    a(f'<g filter="url(#hg)"><circle cx="26" cy="22" r="3.6" fill="{CY}"/>'
      f'<circle cx="26" cy="42" r="3.6" fill="{CY}"/><circle cx="48" cy="32" r="4.8" fill="{VI}"/></g>')
    a(f'<text x="66" y="38.5" font-family="{MONO}" font-size="15" font-weight="700" fill="{CY}">{idx:02d}</text>')
    a(f'<text x="102" y="40" font-family="{SANS}" font-size="21" font-weight="800" letter-spacing="1.5" '
      f'fill="{TX}">{escape(title)}</text>')
    a(f'<line x1="{x0}" y1="32" x2="{x1}" y2="32" stroke="url(#rule)" stroke-width="1.2"/>')
    a(f'<circle cx="{x1 + 4}" cy="32" r="2.6" fill="{VI}" fill-opacity=".6"/>')
    a(f'<path class="run" pathLength="100" d="M{x0} 32H{x1}" stroke="{CY}" stroke-width="2" '
      f'stroke-linecap="round" filter="url(#hg)"/>')
    a(f'<text x="{W - 24}" y="36.5" text-anchor="end" font-family="{MONO}" font-size="11" '
      f'fill="{MUT}">layer {idx:02d}/{total:02d}</text>')
    a("</svg>")
    return "\n".join(o)


# ════════════════════════════════════════════════════════════════════
#  DIVIDER
# ════════════════════════════════════════════════════════════════════
def divider():
    W, H = 1200, 28
    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
      'role="img" aria-label="Divider">')
    a("<style>")
    a(".run{fill:none;stroke-dasharray:6 100;stroke-dashoffset:6;opacity:0;"
      "animation:run 7s linear infinite}")
    a("@keyframes run{0%{stroke-dashoffset:6;opacity:1}100%{stroke-dashoffset:-100;opacity:1}}")
    a(REDUCED)
    a("</style>")
    a(f"<defs>{glow('dg', 1.8)}</defs>")
    a(f'<line x1="25" y1="14" x2="1175" y2="14" stroke="#3a4a85" stroke-opacity=".7"/>')
    a('<g fill="#3a4a85">')
    for x in range(25, 1176, 50):
        if x != 625:
            a(f'<circle cx="{x}" cy="14" r="2.6"/>')
    a("</g>")
    a(f'<circle cx="625" cy="14" r="4.5" fill="{VI}" filter="url(#dg)"/>')
    a(f'<path class="run" pathLength="100" d="M25 14H1175" stroke="{CY}" stroke-width="2.2" '
      f'stroke-linecap="round" filter="url(#dg)"/>')
    a("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    files = {"ai-banner.svg": banner(), "ai-divider.svg": divider()}
    for i, (slug, title) in enumerate(HEADERS, 1):
        files[f"ai-hdr-{slug}.svg"] = header(i, len(HEADERS), title)
    for name, svg in files.items():
        with open(name, "w", encoding="utf-8") as fh:
            fh.write(svg + "\n")
        print("wrote", name)

#!/usr/bin/env python3
"""Pixel-art reinterpretation of Van Gogh's 'The Starry Night' (1889, public domain).
Rendered with a flow field: every stroke follows the local current, exactly as the
brushwork does in the original."""
import math, random
import numpy as np
from PIL import Image

random.seed(1889); np.random.seed(1889)
W, H = 250, 200                      # pixel grid
SS = 3                               # supersample while painting
CW, CH = W*SS, H*SS

def hx(c):
    c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0,2,4)], float)

# ── palette ────────────────────────────────────────────────────────
PAL_HEX = [
 '#050b1f','#0a1533','#0f2048','#152b5e','#1b3877','#22468f','#2b57a6','#3768ba',
 '#4a7cc7','#5f90d2','#79a6dc','#94bbe4','#b0cfec','#cde2f4','#e6f1fa',
 '#3d5a8c','#25406b','#1b2a52','#101c3a','#0a1228',
 '#8a6a1e','#b8891f','#dcae2a','#f2c93a','#ffdf5c','#fff0a8','#fffbe0','#e08a2a',
 '#04080a','#080e0c','#0c1511','#111d15','#16261a','#1d3020','#243d26',
 '#4a4a2e','#6b6437','#877b3a','#2e3a3a','#44506a',
 '#2a2140','#1a1330','#f0c040','#e8952e','#8fa8c8','#c8dae8',
]
PAL = np.array([hx(c) for c in PAL_HEX])

canvas = np.zeros((CH, CW, 3), float)
weight = np.zeros((CH, CW), float)

# ── value noise ────────────────────────────────────────────────────
NG = 64
_n = np.random.rand(NG, NG)
def noise(x, y, s=1.0):
    fx, fy = (x*s/W*NG) % NG, (y*s/H*NG) % NG
    x0, y0 = int(fx), int(fy); x1, y1 = (x0+1) % NG, (y0+1) % NG
    tx, ty = fx-x0, fy-y0
    tx = tx*tx*(3-2*tx); ty = ty*ty*(3-2*ty)
    a = _n[y0,x0]*(1-tx) + _n[y0,x1]*tx
    b = _n[y1,x0]*(1-tx) + _n[y1,x1]*tx
    return a*(1-ty) + b*ty

# ── composition ────────────────────────────────────────────────────
MOON = (221, 27, 25)
STARS = [(30,10,3.6),(59,35,4.8),(15,92,3.0),(36,90,4.2),(87,101,5.6),
         (150,21,5.6),(177,46,4.2),(79,57,2.4),(118,76,2.8),(196,85,3.2),
         (107,43,2.2)]
VORT = [(126,70,  1.00, 48),(166,96, -0.80, 34),(60,150, 0.35, 40),
        (205,120, 0.30, 34),(95,25,  -0.30, 30)]

RIDGE = [(0,152),(28,146),(58,151),(92,144),(122,137),(150,124),(172,116),
         (196,124),(222,130),(250,134)]
def ridge_y(x):
    for i in range(len(RIDGE)-1):
        (ax,ay),(bx,by) = RIDGE[i], RIDGE[i+1]
        if ax <= x <= bx:
            t = (x-ax)/(bx-ax); t = t*t*(3-2*t)
            return ay + (by-ay)*t
    return RIDGE[-1][1]

def cypress_w(y):
    """half-width of the flame-shaped cypress at height y."""
    if y < 2: return 0.0
    t = (y-2)/198.0
    base = 1.4 + 27.0*(t**1.35)
    lobe = (5.0*math.sin(t*14.0) + 3.4*math.sin(t*8.0+1.2)
            + 2.4*math.sin(t*25.0+0.6) + 1.7*math.sin(t*44.0)
            + 1.1*math.sin(t*71.0+2.1))
    return base*0.55 + max(0.0, base*0.45 + lobe*(0.30+t*1.15))
def cypress_cx(y):
    return 58 + 7*math.sin(y*0.016) + 3.5*math.sin(y*0.041+2.0)

def in_cypress(x, y):
    return abs(x - cypress_cx(y)) < cypress_w(y)

VILLAGE_TOP = 150
def region(x, y):
    if in_cypress(x, y): return 'cy'
    ry = ridge_y(x)
    if y < ry: return 'sky'
    if y < 176 and x > 96: return 'town'
    return 'hill'

# ── base colour field ──────────────────────────────────────────────
def glow(x, y):
    """brightness contributed by moon and stars"""
    g = 0.0
    mx, my, mr = MOON
    d = math.hypot(x-mx, y-my)
    g = max(g, math.exp(-(d/(mr*0.85))**2)*1.10)
    for sx, sy, sr in STARS:
        d = math.hypot(x-sx, y-sy)
        g = max(g, math.exp(-(d/(sr*1.7))**2)*0.72)
    return g

SKY_RAMP = [hx(c) for c in ('#050a1c','#0a1230','#0f1c4a','#152a66','#1d3d85',
                            '#2c579f','#4271b8','#6491cc','#8fb2df','#bcd4ee')]
YEL = [hx(c) for c in ('#8a6a1e','#c2911f','#e6b62c','#f7cf3e','#ffe272','#fff3b4','#fffce8')]
def lerp_ramp(r, t):
    t = max(0.0, min(0.999, t)) * (len(r)-1)
    i = int(t); f = t-i
    return r[i]*(1-f) + r[min(i+1, len(r)-1)]*f

def base_color(x, y):
    reg = region(x, y)
    if reg == 'cy':
        t = 0.02 + 0.72*noise(x, y, 8.0) + 0.20*(y/H)
        return lerp_ramp([hx(c) for c in ('#03060a','#070c0b','#0b120f','#101a13',
                                          '#152318','#1b2d1d')], t)
    if reg == 'hill':
        fold = 0.30*math.sin(x*0.055 + y*0.02) + 0.22*math.sin(x*0.021 - 1.1)
        t = 0.10 + 0.40*noise(x, y, 2.4) + 0.34*((y-110)/110) + fold*0.30
        return lerp_ramp([hx(c) for c in ('#070d1e','#0c162e','#122347','#1a3160',
                                          '#28457c','#3d5a8c')], t)
    if reg == 'town':
        t = 0.10 + 0.45*noise(x, y, 5.0)
        return lerp_ramp([hx(c) for c in ('#080e1e','#0d1730','#141f3c','#1d2b4c',
                                          '#2a2140','#37456b')], t)
    # sky
    g = glow(x, y)
    depth = 0.10 + 0.40*(y/max(1.0, ridge_y(x))) + 0.30*noise(x, y, 1.7)
    c = lerp_ramp(SKY_RAMP, depth)
    if g > 0.02:
        c = c*(1-min(1.0, g)) + lerp_ramp(YEL, min(0.999, 0.25+g*0.7))*min(1.0, g)
    return c

# ── flow field ─────────────────────────────────────────────────────
def flow(x, y):
    vx = math.cos(0.10 + 0.55*math.sin(y*0.035 + x*0.012))
    vy = math.sin(0.10 + 0.55*math.sin(y*0.035 + x*0.012)) * 0.45
    for cx, cy, s, r in VORT:
        dx, dy = x-cx, y-cy
        d = math.hypot(dx, dy) + 1e-6
        w = math.exp(-(d/r)**2) * s * 3.2
        vx += -dy/d * w; vy += dx/d * w
    mx, my, mr = MOON                       # strokes circle the moon and stars
    for (cx, cy, r) in [(mx, my, mr*0.9)] + STARS:
        dx, dy = x-cx, y-cy
        d = math.hypot(dx, dy) + 1e-6
        w = math.exp(-(d/(r*1.6))**2) * 3.0
        vx += -dy/d * w; vy += dx/d * w
    if in_cypress(x, y) or y > 150:         # cypress and ground flow upward
        up = 2.4 if in_cypress(x, y) else 0.7
        vx += 0.25*math.sin(y*0.09)*up; vy += -up
    n = math.hypot(vx, vy) + 1e-6
    return vx/n, vy/n

# ── painting ───────────────────────────────────────────────────────
def stamp(px, py, rad, col, alpha):
    x0, x1 = max(0, int(px-rad)), min(CW-1, int(px+rad))
    y0, y1 = max(0, int(py-rad)), min(CH-1, int(py+rad))
    if x1 < x0 or y1 < y0: return
    ys, xs = np.mgrid[y0:y1+1, x0:x1+1]
    d2 = (xs-px)**2 + (ys-py)**2
    m = np.clip(1.0 - d2/(rad*rad), 0, 1) * alpha
    canvas[y0:y1+1, x0:x1+1] += m[..., None] * col
    weight[y0:y1+1, x0:x1+1] += m

def stroke(x, y, length, rad, col, alpha):
    for _ in range(length):
        fx, fy = flow(x, y)
        stamp(x*SS, y*SS, rad*SS, col, alpha)
        x += fx*0.85; y += fy*0.85
        if not (-4 < x < W+4 and -4 < y < H+4): return

# pass 1 — lay the ground colour everywhere
for _ in range(26000):
    x, y = random.uniform(-8, W+8), random.uniform(-8, H+8)
    c = base_color(max(0,min(W-1,x)), max(0,min(H-1,y)))
    v = 0.72 + 0.55*noise(x, y, 4.5)
    stroke(x, y, random.randint(7, 16), random.uniform(0.8, 1.5),
           np.clip(c*v, 0, 255), 0.55)

# pass 2 — the light bands that make the swirls read
for _ in range(11000):
    x, y = random.uniform(-6, W+6), random.uniform(-6, H+6)
    if region(max(0,min(W-1,x)), max(0,min(H-1,y))) != 'sky':
        continue
    n = noise(x, y, 6.0)
    if n < 0.52:
        continue
    c = base_color(max(0,min(W-1,x)), max(0,min(H-1,y)))
    v = 1.15 + 1.35*(n-0.52) + 0.9*glow(max(0,min(W-1,x)), max(0,min(H-1,y)))
    stroke(x, y, random.randint(9, 22), random.uniform(0.7, 1.2),
           np.clip(c*v + 26, 0, 255), 0.60)

# pass 3 — cypress flames
for _ in range(6500):
    y = random.uniform(6, H)
    hw = cypress_w(y)
    if hw < 0.6: continue
    x = cypress_cx(y) + random.uniform(-hw, hw)
    c = base_color(x, y)
    v = 0.42 + 0.78*noise(x, y, 9.0)
    stroke(x, y, random.randint(8, 20), random.uniform(0.6, 1.0),
           np.clip(c*v, 0, 255), 0.6)

print('strokes done')
img = np.where(weight[..., None] > 0, canvas/np.maximum(weight, 1e-6)[..., None], 0)

# the cypress must read as one unbroken silhouette
CYP = [hx(c) for c in ('#03060a','#070c0b','#0b120f','#101a13','#152318','#1b2d1d')]
for gy in range(CH):
    y = gy/SS
    hw = cypress_w(y); cx = cypress_cx(y)
    if hw < 0.3: continue
    x0, x1 = int((cx-hw)*SS), int((cx+hw)*SS)
    x0, x1 = max(0, x0), min(CW-1, x1)
    if x1 < x0: continue
    for gx in range(x0, x1+1):
        edge = 1.0 - abs(gx/SS - cx)/max(0.6, hw)
        t = 0.04 + 0.62*noise(gx/SS, y, 9.0) + 0.22*(y/H) - 0.18*edge
        tgt = lerp_ramp(CYP, t)
        a = 0.90 if edge > 0.14 else 0.62
        img[gy, gx] = img[gy, gx]*(1-a) + tgt*a

# ── the village, the church, the moon and the stars, painted on top ─
def rect(x0, y0, x1, y1, col, a=1.0):
    X0, Y0, X1, Y1 = int(x0*SS), int(y0*SS), int(x1*SS), int(y1*SS)
    img[Y0:Y1+1, X0:X1+1] = img[Y0:Y1+1, X0:X1+1]*(1-a) + col*a

random.seed(4)
BLD = hx('#0b1428'); ROOF = hx('#241b38'); WIN = hx('#f5c63c'); WIN2 = hx('#e8952e')
bx = 98
while bx < 250:
    bw = random.randint(6, 13)
    bh = random.randint(5, 10)
    top = ridge_y(bx) + random.randint(6, 20)
    rect(bx, top, bx+bw, min(178, top+bh+4), BLD)
    for k in range(bw//2+1):                       # pitched roof
        rect(bx+k, top-1-k*0.5, bx+bw-k, top-k*0.5, ROOF)
    if random.random() < 0.75:
        wx = bx + random.randint(1, max(1, bw-3))
        wy = top + random.randint(2, max(2, bh-1))
        rect(wx, wy, wx+1, wy+1, WIN if random.random() < 0.65 else WIN2)
    bx += bw + random.randint(0, 3)

# church
rect(139, 148, 151, 178, hx('#0c1728'))
for k in range(7):
    rect(139+k, 146-k*0.6, 151-k, 147-k*0.6, hx('#1a2740'))
for i in range(40):                                   # spire
    w = 2.6*(1-i/40.0)**0.85
    rect(145-w, 108+i, 145+w, 109+i, hx('#0e1c33'))
rect(144.6, 101, 145.4, 109, hx('#16294a'))
rect(143.6, 103, 146.4, 103.8, hx('#16294a'))
rect(143, 152, 147, 157, hx('#0e1c33'))
rect(144, 153, 146, 156, hx('#f5c63c'))

def disc(cx, cy, r, col, a=1.0, feather=0.0):
    X = np.arange(CW); Y = np.arange(CH)
    d = np.sqrt((X[None,:]-cx*SS)**2 + (Y[:,None]-cy*SS)**2)/SS
    if feather > 0:
        m = np.clip((r+feather-d)/feather, 0, 1)*a
    else:
        m = (d <= r).astype(float)*a
    img[:] = img*(1-m[...,None]) + col*m[...,None]

mx, my, mr = MOON
disc(mx, my, mr*1.30, hx('#c2911f'), 0.22, mr*0.85)
disc(mx, my, mr*0.78, hx('#e6b62c'), 0.45, mr*0.42)
disc(mx, my, mr*0.56, hx('#f7cf3e'), 0.72, mr*0.26)
disc(mx, my, mr*0.38, hx('#ffe272'), 0.85, mr*0.16)
disc(mx-mr*0.26, my-mr*0.10, mr*0.34, hx('#b8891f'), 0.55, mr*0.16)   # crescent bite
for sx, sy, sr in STARS:
    disc(sx, sy, sr*2.2, hx('#877b3a'), 0.12, sr*1.9)
    disc(sx, sy, sr*1.05, hx('#c2911f'), 0.26, sr*1.0)
    disc(sx, sy, sr*0.50, hx('#ffe272'), 0.55, sr*0.45)
    disc(sx, sy, sr*0.22, hx('#fff3b4'), 0.75, sr*0.25)

# ── downsample, quantise, emit ─────────────────────────────────────
small = img.reshape(H, SS, W, SS, 3).mean(axis=(1,3))
flat = small.reshape(-1, 3)
d = ((flat[:,None,:] - PAL[None,:,:])**2).sum(axis=2)
idx = d.argmin(axis=1)
grid = PAL[idx].reshape(H, W, 3).astype(int)

runs = {}
for y in range(H):
    x = 0
    while x < W:
        c = tuple(grid[y][x]); x2 = x
        while x2+1 < W and tuple(grid[y][x2+1]) == c: x2 += 1
        runs.setdefault(c, []).append((x, y, x2-x+1)); x = x2+1
paths = [f'<path fill="#{c[0]:02x}{c[1]:02x}{c[2]:02x}" d="' +
         ''.join(f'M{a} {b}h{w}v1h-{w}z' for a,b,w in rs) + '"/>' for c, rs in runs.items()]

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
       f'width="{W*4}" height="{H*4}" shape-rendering="crispEdges" role="img" '
       f'aria-label="Pixel-art reinterpretation of Van Gogh\'s The Starry Night: a swirling '
       f'night sky over a sleeping village, with a dark flame-shaped cypress at the left">'
       f'<title>The Starry Night, in pixels</title>{"".join(paths)}</svg>')
open('starry-night.svg','w').write(svg)

Image.fromarray(grid.astype('uint8')).resize((W*4, H*4), Image.NEAREST).save('preview.png')
print('runs', sum(len(v) for v in runs.values()), 'colours', len(runs), 'kb', len(svg)//1024)

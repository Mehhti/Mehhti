#!/usr/bin/env python3
"""Build an animated SVG platformer from a GitHub contribution calendar.

A little pixel character runs left-to-right across the year. The terrain is
the real contribution graph: the character lands on top of each week's tallest
contribution and hops the gaps. Cells wink out as it passes over them.

Usage:
    python3 contrib_runner.py --user Mehhti --out dist/contrib-runner.svg
    python3 contrib_runner.py --demo --out demo.svg      # no token needed
Env:
    GITHUB_TOKEN  required unless --demo
"""
import argparse, json, os, random, urllib.request

# ── palette (matches the profile) ──────────────────────────────────
EMPTY  = '#241a38'
LEVELS = ['#2e2145', '#3d3a5c', '#4f6a9e', '#6f9ecb', '#9FE7FF']
GOLD, GOLD2, DARK = '#FFD479', '#C79A45', '#171026'
WHITE, VIOLET = '#F2F6FF', '#BB9AF7'
HAIR, HAIR2 = '#2b2340', '#3d3358'
SKIN, SKIN2 = '#e8c49c', '#c2966a'
HOOD, HOOD2 = '#4a4478', '#6b62a8'
PANTS = '#2b2450'
EYE, STEAM = '#191330', '#9FE7FF'

CELL, GAP = 12, 3
PITCH = CELL + GAP
ROWS = 7
SKY = 46                      # head-room above the grid for jump arcs
FLOOR = 10
DUR = 14.0                    # seconds for one full run

QUERY = """query($login:String!){
  user(login:$login){ contributionsCollection{ contributionCalendar{
    weeks{ contributionDays{ contributionCount weekday } } } } } }"""


def fetch(login, token):
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': QUERY, 'variables': {'login': login}}).encode(),
        headers={'Authorization': 'bearer ' + token,
                 'Content-Type': 'application/json',
                 'User-Agent': 'contrib-runner'})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if 'errors' in data:
        raise SystemExit('GitHub API error: ' + json.dumps(data['errors']))
    weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
    out = []
    for wk in weeks:
        col = [0]*ROWS
        for d in wk['contributionDays']:
            col[d['weekday']] = d['contributionCount']
        out.append(col)
    return out


def demo(seed=7):
    rng = random.Random(seed)
    weeks = []
    for w in range(53):
        col = []
        burst = 1.0 if rng.random() < 0.22 else 0.35
        for d in range(ROWS):
            wknd = 0.4 if d in (0, 6) else 1.0
            col.append(0 if rng.random() > 0.55*burst*wknd
                       else rng.choice([1, 1, 2, 3, 5, 8, 13]))
        weeks.append(col)
    return weeks


def level(n, hi):
    if n <= 0: return 0
    q = n/max(1, hi)
    return 1 + min(3, int(q*4))


def sprite(name, frame):
    """A tired developer: bed hair, eye bags, hoodie, mug of coffee. 17 x 21."""
    def r(x, y, w, h, c):
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"/>'
    bob = 1 if frame else 0          # the whole body sags on the off beat
    p = []
    # bed hair, sticking up in three tufts
    p += [r(4, 0+bob, 2, 1, HAIR), r(7, 0+bob, 1, 1, HAIR), r(9, 0+bob, 2, 1, HAIR)]
    p += [r(3, 1+bob, 9, 4, HAIR), r(2, 2+bob, 1, 5, HAIR), r(12, 2+bob, 1, 4, HAIR)]
    p += [r(5, 1+bob, 2, 1, HAIR2), r(9, 2+bob, 2, 1, HAIR2)]
    # face
    p += [r(3, 5+bob, 9, 5, SKIN), r(3, 5+bob, 9, 1, HAIR2)]     # fringe shadow
    p += [r(4, 7+bob, 2, 1, EYE), r(8, 7+bob, 2, 1, EYE)]        # half-shut eyes
    p += [r(4, 8+bob, 2, 1, SKIN2), r(8, 8+bob, 2, 1, SKIN2)]    # the eye bags
    p += [r(7, 8+bob, 1, 1, SKIN2)]                              # nose
    p += [r(3, 9+bob, 9, 1, SKIN)]
    p += [r(6, 9+bob, 2, 1, SKIN2)]                              # flat, unamused mouth
    # hoodie: collar, body, drawstrings, slumped shoulders
    p += [r(3, 10+bob, 9, 1, SKIN2), r(3, 11+bob, 9, 1, HOOD2), r(2, 12+bob, 11, 6, HOOD)]
    p += [r(2, 12+bob, 11, 1, HOOD2)]
    p += [r(5, 13+bob, 1, 3, HOOD2), r(9, 13+bob, 1, 3, HOOD2)]  # strings
    p += [r(1, 13+bob, 1, 4, HOOD), r(13, 13+bob, 1, 4, HOOD)]   # arms
    # the mug, gripped out front
    p += [r(14, 14+bob, 3, 4, GOLD), r(14, 14+bob, 3, 1, GOLD2),
          r(15, 15+bob, 1, 1, HAIR), r(13, 15+bob, 1, 2, SKIN)]
    # legs: a shuffle, not a sprint
    if frame == 0:
        p += [r(4, 18, 3, 3, PANTS), r(8, 18, 3, 3, PANTS)]
        p += [r(4, 20, 3, 1, HAIR), r(8, 20, 3, 1, HAIR)]
    else:
        p += [r(3, 18, 3, 3, PANTS), r(9, 19, 3, 2, PANTS)]
        p += [r(3, 20, 4, 1, HAIR), r(9, 20, 3, 1, HAIR)]
    return f'<g id="{name}">{"".join(p)}</g>'


def build(weeks, title):
    nw = len(weeks)
    hi = max([max(c) for c in weeks] + [1])
    W = nw*PITCH + GAP
    H = SKY + ROWS*PITCH + FLOOR

    def cy(row): return SKY + row*PITCH

    # terrain: the top-most contributed day of each week
    top = []
    for col in weeks:
        rows = [i for i, v in enumerate(col) if v > 0]
        top.append(min(rows) if rows else ROWS)

    # ── grid ────────────────────────────────────────────────────────
    cells, keys = [], []
    for w, col in enumerate(weeks):
        t = (w/nw)*100.0
        hit = min(99.0, max(0.6, t))
        for d, v in enumerate(col):
            x, y = GAP + w*PITCH, cy(d)
            lv = level(v, hi)
            fill = EMPTY if lv == 0 else LEVELS[lv]
            if lv == 0:
                cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                             f'rx="3" fill="{fill}"/>')
            else:
                cells.append(f'<rect class="c w{w}" x="{x}" y="{y}" width="{CELL}" '
                             f'height="{CELL}" rx="3" fill="{fill}"/>')
        keys.append(f'@keyframes w{w}{{0%,{hit:.2f}%{{opacity:1}}'
                    f'{min(100.0, hit+0.8):.2f}%,100%{{opacity:.16}}}}')

    # ── path of the runner ──────────────────────────────────────────
    SCALE = 1.45
    SPR_H = 21*SCALE
    def stand(w):
        return cy(top[w]) - SPR_H + 1 if top[w] < ROWS else cy(ROWS) - SPR_H + 1

    frames = []
    for w in range(nw):
        t0 = (w/nw)*100.0
        x0 = GAP + w*PITCH - 1
        frames.append((t0, x0, stand(w)))
        if w+1 < nw:
            y0, y1 = stand(w), stand(w+1)
            hop = min(30, 13 + max(0, y0-y1)*0.40)
            frames.append((t0 + (0.5/nw)*100.0, x0 + PITCH/2, min(y0, y1) - hop))
    frames.append((100.0, GAP + nw*PITCH, stand(nw-1)))
    run_kf = ''.join(f'{t:.2f}%{{transform:translate({x:.1f}px,{y:.1f}px)}}'
                     for t, x, y in frames)

    steam = ''.join(
        f'<rect class="stm" x="{15 + (k % 2)}" y="{11 - k*2}" width="1" height="2" '
        f'fill="{STEAM}" style="animation-delay:{k*0.55:.2f}s"/>' for k in range(3))

    css = f"""<style>
.c{{animation-duration:{DUR}s;animation-timing-function:linear;animation-iteration-count:infinite}}
{''.join(f'.w{w}{{animation-name:w{w}}}' for w in range(nw))}
{''.join(keys)}
#runner{{animation:run {DUR}s linear infinite}}
@keyframes run{{{run_kf}}}
#legA,#legB{{animation:step .46s steps(1) infinite}}
#legB{{animation-delay:.23s}}
.stm{{animation:steam 2.6s ease-in-out infinite}}
@keyframes steam{{0%,100%{{opacity:.10}}50%{{opacity:.70}}}}
@keyframes step{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{
  .c,#runner,#legA,#legB,.stm{{animation:none}} #legB{{opacity:0}}
}}
</style>"""

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}" role="img" aria-label="{title}">'
           f'<title>{title}</title>{css}'
           f'<rect width="{W}" height="{H}" fill="{DARK}"/>'
           f'<rect x="0" y="{SKY + ROWS*PITCH + 2}" width="{W}" height="2" fill="{LEVELS[1]}" opacity=".55"/>'
           f'{"".join(cells)}'
           f'<g id="runner"><g transform="scale({SCALE})">'
           f'<g id="legA">{sprite("a", 0)}</g>'
           f'<g id="legB">{sprite("b", 1)}</g>{steam}</g></g>'
           f'</svg>')
    return svg


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--user'); ap.add_argument('--out', required=True)
    ap.add_argument('--demo', action='store_true')
    a = ap.parse_args()
    wk = demo() if a.demo else fetch(a.user, os.environ['GITHUB_TOKEN'])
    title = (f"{a.user or 'demo'}'s GitHub contributions as a platformer: a pixel "
             f"character runs across the year, landing on each week's activity")
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    open(a.out, 'w').write(build(wk, title))
    print('wrote', a.out)

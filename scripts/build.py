#!/usr/bin/env python3
"""Builds every SVG in assets/ for the Abdulla090 profile README (figures v4).
Poster direction: frameless, full-bleed figures on the page background; the type and
the composition do the work, no boxes, rules, badges or label furniture.
All type is converted to outlines (HarfBuzz-shaped), so nothing depends on fonts
installed on the viewer's machine. Run: python3 scripts/build.py assets
Fonts (OFL, not committed; put them in ./fonts next to scripts/ or set FONT_DIR):
  InstrumentSerif-Regular/Italic.ttf  (github.com/google/fonts)
  NotoNaskhArabic-Bold.ttf = NotoNaskhArabic[wght].ttf, instanced at wght 700 (github.com/google/fonts)
Needs: pip install uharfbuzz fonttools

Palette is ink + red only, tone from halftone dots. Every animation's base attributes
are the finished picture, so a frozen render (or a viewer with SMIL off) looks complete."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from tp import path as P, width as W, bounds as B, contours as C

OUT = sys.argv[1] if len(sys.argv) > 1 else 'assets'
os.makedirs(OUT, exist_ok=True)

SERIF, SERIF_I = 'InstrumentSerif-Regular.ttf', 'InstrumentSerif-Italic.ttf'
NASKH = 'NotoNaskhArabic-Bold.ttf'

THEMES = {
    'light': dict(page='#ffffff', ink='#1f2328', red='#D0263A', mute='#59636e'),
    'dark':  dict(page='#0d1117', ink='#E6EDF3', red='#F2484E', mute='#9198a1'),
}

def f1(v):
    return ('%.1f' % v).rstrip('0').rstrip('.')

def svg(w, h, body, title, defs=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{title}"><title>{title}</title>'
            f'{"<defs>" + defs + "</defs>" if defs else ""}{body}</svg>')

def t(text, font, size, x, y, fill, anchor='start', track=0, wght=None, extra=''):
    d, w = P(text, font, size, x, y, anchor=anchor, wght=wght, tracking=track)
    return f'<path d="{d}" fill="{fill}"{extra}/>'

# ------------------------------------------------------------------ texture kit
def dots(pid, step, r, fill, bg=None, offset=False, op=1):
    """Halftone screen. offset=True staggers alternate rows (45° screen)."""
    h = step * (2 if offset else 1)
    b = f'<rect width="{step}" height="{h}" fill="{bg}"/>' if bg else ''
    b += f'<circle cx="{f1(step/2)}" cy="{f1(step/2)}" r="{f1(r)}" fill="{fill}" opacity="{op}"/>'
    if offset:
        b += (f'<circle cx="0" cy="{f1(step*1.5)}" r="{f1(r)}" fill="{fill}" opacity="{op}"/>'
              f'<circle cx="{step}" cy="{f1(step*1.5)}" r="{f1(r)}" fill="{fill}" opacity="{op}"/>')
    return (f'<pattern id="{pid}" width="{step}" height="{h}" patternUnits="userSpaceOnUse">{b}</pattern>')

# ------------------------------------------------------------------ coverage maths (hero detector)
def column_coverage(polys, x0, x1, nb, y0, y1, dy=1.5):
    """Fraction of each x-bin covered by the (non-zero filled) outlines, scanline sampled."""
    edges = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
            if ay != by: edges.append((ax, ay, bx, by))
    bw = (x1 - x0) / nb; cov = [0.0] * nb; rows = 0
    y = y0
    while y < y1:
        xs = []
        for ax, ay, bx, by in edges:
            if (ay <= y < by) or (by <= y < ay):
                xs.append((ax + (y - ay) * (bx - ax) / (by - ay), 1 if by > ay else -1))
        xs.sort(); wnd = 0
        for k in range(len(xs) - 1):
            wnd += xs[k][1]
            if wnd != 0:
                a, b2 = max(xs[k][0], x0), min(xs[k + 1][0], x1)
                while a < b2:
                    bi = int((a - x0) / bw)
                    if bi >= nb: break
                    e = min(b2, x0 + (bi + 1) * bw)
                    cov[bi] += (e - a) / bw; a = e
        rows += 1; y += dy
    return [v / rows for v in cov]

def hand_model():
    """Bones as capsules (x1,y1,x2,y2,r) in a 0..260 x 0..300 box, fingers up."""
    bones = []
    bones += [(96, 300, 101, 252, 17), (152, 300, 150, 256, 12)]      # radius, ulna
    for (x, y, r) in ((92, 236, 11), (113, 240, 11), (134, 240, 10), (154, 238, 10),
                      (98, 214, 10), (119, 216, 10), (139, 214, 10), (158, 212, 9)):
        bones.append((x, y, x, y, r))                                   # carpals
    fingers = [  # base (on carpal row), direction angle deg (from vertical, + to right), lengths
        ((84, 206), -36, [52, 36, 28], 10),     # thumb
        ((106, 202), -9, [70, 40, 26, 18], 8.5),
        ((126, 200), -1, [76, 46, 29, 19], 8.5),
        ((145, 200), 7, [70, 42, 27, 18], 8),
        ((161, 202), 16, [60, 32, 22, 16], 7.5),
    ]
    flesh = []
    for (bx, by), ang, lens, r in fingers:
        a = math.radians(ang); dx, dy = math.sin(a), -math.cos(a)
        x, y = bx, by; chain = [(x, y)]
        for k, L in enumerate(lens):
            gap = 5
            x2, y2 = x + dx * L, y + dy * L
            rr = r * (1 - 0.13 * k)
            bones.append((x + dx * gap, y + dy * gap, x2 - dx * gap * .3, y2 - dy * gap * .3, rr))
            x, y = x2, y2; chain.append((x, y))
            a += math.radians(ang * 0.06); dx, dy = math.sin(a), -math.cos(a)
        flesh.append((chain, r + 9))
    palm = [(66, 226), (82, 190), (104, 168), (176, 168), (190, 196), (178, 262), (168, 300), (80, 300), (76, 262)]
    return bones, flesh, palm

def seg_dist(px, py, x1, y1, x2, y2):
    vx, vy = x2 - x1, y2 - y1; L2 = vx * vx + vy * vy
    u = 0 if L2 == 0 else max(0, min(1, ((px - x1) * vx + (py - y1) * vy) / L2))
    return math.hypot(px - x1 - u * vx, py - y1 - u * vy)

def in_poly(px, py, poly):
    inside = False; n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > py) != (by > py) and px < ax + (py - ay) * (bx - ax) / (by - ay): inside = not inside
    return inside

def hankin_448(L, theta, nx, ny, ox, oy):
    a = L / (1 + math.sqrt(2))                    # octagon / square side
    polys = []
    R = a / (2 * math.sin(math.pi / 8))
    for i in range(-1, nx + 1):
        for j in range(-1, ny + 1):
            cx, cy = ox + i * L, oy + j * L
            polys.append(('oct', (i, j), [(cx + R * math.cos(math.pi / 8 + k * math.pi / 4),
                                           cy + R * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]))
            sx, sy = cx + L / 2, cy + L / 2; h = a / math.sqrt(2)
            polys.append(('sq', (i, j), [(sx + h * math.cos(k * math.pi / 2), sy + h * math.sin(k * math.pi / 2)) for k in range(4)]))
    segs = []; rosettes = []
    th = math.radians(theta)
    def rot(v, an): return (v[0] * math.cos(an) - v[1] * math.sin(an), v[0] * math.sin(an) + v[1] * math.cos(an))
    def inter(p, d, q, e):
        den = d[0] * e[1] - d[1] * e[0]
        s = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
        return (p[0] + d[0] * s, p[1] + d[1] * s)
    for kind, ij, vs in polys:
        n = len(vs); mids, dirs = [], []
        for k in range(n):
            p, q = vs[k], vs[(k + 1) % n]
            mids.append(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2))
            Lk = math.hypot(q[0] - p[0], q[1] - p[1]); dirs.append(((q[0] - p[0]) / Lk, (q[1] - p[1]) / Lk))
        ros = []
        for k in range(n):
            A = rot(dirs[k], th); Bd = rot((-dirs[(k + 1) % n][0], -dirs[(k + 1) % n][1]), -th)
            X = inter(mids[k], A, mids[(k + 1) % n], Bd)
            segs.append((mids[k], X)); segs.append((mids[(k + 1) % n], X))
            ros += [mids[k], X]
        rosettes.append((kind, ij, ros))
    return segs, rosettes

def key(p): return (round(p[0], 2), round(p[1], 2))

def strands_from(segs):
    """Chain segments into straight-through strands. Corners (shared by exactly 2) turn;
    midpoints (shared by 4) are crossings where the collinear pair continues."""
    ends = {}
    for si, (p, q) in enumerate(segs):
        for e in (0, 1):
            ends.setdefault(key(segs[si][e]), []).append((si, e))
    used = set(); strands = []
    def unit(si, e):   # direction leaving endpoint e along the segment
        p, q = segs[si] if e == 0 else segs[si][::-1]
        L = math.hypot(q[0] - p[0], q[1] - p[1]); return ((q[0] - p[0]) / L, (q[1] - p[1]) / L)
    def nxt(si, e):    # at endpoint e of si, which segment continues?
        here = ends[key(segs[si][e])]; others = [(s2, e2) for s2, e2 in here if s2 != si]
        if len(others) == 1: return others[0]
        din = unit(si, e); din = (-din[0], -din[1])   # travelling direction arriving here
        best = None
        for s2, e2 in others:
            u = unit(s2, e2)
            if abs(u[0] - din[0]) + abs(u[1] - din[1]) < 1e-3: best = (s2, e2)
        return best
    for s0 in range(len(segs)):
        if s0 in used: continue
        # walk backwards to a start
        chain = [(s0, 0)]; used.add(s0)
        cur = (s0, 1)
        while True:
            nx_ = nxt(*cur)
            if nx_ is None or nx_[0] in used: break
            used.add(nx_[0]); chain.append((nx_[0], nx_[1])); cur = (nx_[0], 1 - nx_[1])
        cur = (s0, 0); back = []
        while True:
            nx_ = nxt(*cur)
            if nx_ is None or nx_[0] in used: break
            used.add(nx_[0]); back.append((nx_[0], 1 - nx_[1])); cur = (nx_[0], 1 - nx_[1])
        order = back[::-1] + chain
        pts = []
        for si, e in order:
            p, q = segs[si] if e == 0 else segs[si][::-1]
            if not pts: pts.append(p)
            pts.append(q)
        closed = key(pts[0]) == key(pts[-1])
        strands.append((pts, closed))
    return strands


# ------------------------------------------------------------------ small kit
def smooth(vals, rad):
    out = []
    n = len(vals)
    for i in range(n):
        acc = wsum = 0.0
        for k in range(-rad * 2, rad * 2 + 1):
            j = i + k
            if 0 <= j < n:
                w = math.exp(-(k / rad) ** 2)
                acc += vals[j] * w; wsum += w
        out.append(acc / wsum)
    return out

def poly_d(pts, close=True):
    return 'M' + 'L'.join(f'{f1(x)} {f1(y)}' for x, y in pts) + ('Z' if close else '')

def bez(p0, p1, p2, p3, u):
    a = (1 - u) ** 3; b = 3 * u * (1 - u) ** 2; c_ = 3 * u * u * (1 - u); d = u ** 3
    return (a * p0[0] + b * p1[0] + c_ * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c_ * p2[1] + d * p3[1])

def title(text, size, x, y, fill, anchor='start'):
    return t(text, SERIF, size, x, y, fill, anchor)

def kurd(text, size, x, y, fill, anchor='start'):
    return t(text, NASKH, size, x, y, fill, anchor, wght=700)

def desc(text, x, y, fill, anchor='start', size=48):
    return t(text, SERIF_I, size, x, y, fill, anchor)

# ------------------------------------------------------------------ HERO
def hero(th):
    c = THEMES[th]; Wd, H = 1200, 720
    LAT = ('Abdulla', SERIF, 330, 26, 300)
    KUR = ('عەبدوڵڵا', NASKH, 200, 1172, 540)
    latin, _ = P(*LAT)
    kurdp, _ = P(*KUR, anchor='end', wght=700)
    defs = dots('neg', 7, 2.9, c['page'], offset=True)
    defs += f'<path id="nL" d="{latin}"/><path id="nK" d="{kurdp}"/>'
    sub = ''.join(P(s_, SERIF_I, 52, 34, 398 + i * 58)[0] for i, s_ in
                  enumerate(('Medical physics student', 'building Kurdish-first', 'software.')))
    defs += f'<path id="sub" d="{sub}"/>'

    # the ground: the beam's projection of both names, a real line integral of the type,
    # smoothed into a landscape the letters stand on. It bleeds off the bottom and sides.
    nb = 240
    polys = C(*LAT) + C(*KUR, anchor='end', wght=700)
    cov = smooth(column_coverage(polys, 0, Wd, nb, 40, 600), 4)
    mx = max(cov)
    pts = [(-2, H + 2)]
    for i, v in enumerate(cov):
        pts.append(((i + 0.5) * Wd / nb, H - 22 - 118 * (v / mx) ** 0.8))
    pts += [(Wd + 2, pts[-1][1]), (Wd + 2, H + 2)]
    pts.insert(1, (-2, pts[1][1]))
    defs += f'<path id="gnd" d="{poly_d(pts)}"/>'

    b = [f'<rect width="{Wd}" height="{H}" fill="{c["page"]}"/>',
         f'<use href="#gnd" fill="{c["ink"]}"/>',
         f'<use href="#nL" fill="{c["ink"]}"/><use href="#nK" fill="{c["red"]}"/>',
         f'<use href="#sub" fill="{c["ink"]}"/>']

    # the beam: a red slab, top to bottom, sweeping right to left; inside it the names
    # turn into a dithered negative and the ground into a void
    BW = 170; X0 = 318
    vals = f'{X0};-200;-200;1220;1220;{X0}'; kt = '0;0.42;0.5;0.5;0.58;1'
    spl = 'calcMode="spline" keySplines="0.6 0 0.25 1;0 0 1 1;0 0 1 1;0 0 1 1;0.6 0 0.25 1"'
    defs += (f'<clipPath id="beam"><rect x="{X0}" y="0" width="{BW}" height="{H}">'
             f'<animate attributeName="x" values="{vals}" keyTimes="{kt}" dur="10s" repeatCount="indefinite" {spl}/>'
             f'</rect></clipPath>')
    b.append(f'<g clip-path="url(#beam)"><rect width="{Wd}" height="{H}" fill="{c["red"]}"/>'
             f'<use href="#gnd" fill="url(#neg)"/><use href="#sub" fill="{c["page"]}"/>'
             f'<use href="#nL" fill="url(#neg)"/><use href="#nK" fill="url(#neg)"/></g>')
    return svg(Wd, H, ''.join(b), 'Abdulla Aziz Hameed. Medical physics student building Kurdish-first software.', defs)

# ------------------------------------------------------------------ SECTION WORD
def section(th, en, ku):
    c = THEMES[th]; Wd, H = 1200, 200
    _, ew = P(en, SERIF, 160, 0, 0)
    b = [title(en, 160, -4, 150, c['ink']),
         kurd(ku, 96, ew + 26, 176, c['red'])]
    return svg(Wd, H, ''.join(b), f'{en} ({ku})')

# ------------------------------------------------------------------ PLATES (1200 x 600)
PW, PH = 1200, 600

# -- Reelcart: a film ribbon pours in from the top-right edge, tapering as it goes,
#    and lands as a fanned hand of cash-on-delivery tickets
def plate_reelcart(c):
    defs = ''
    b = []
    P0, P1, P2, P3 = (1290, 10), (1080, 40), (1150, 400), (860, 340)
    N = 90
    cen = [bez(P0, P1, P2, P3, k / N) for k in range(N + 1)]
    def wid(u): return 150 - 96 * u
    left, right, sl, sr = [], [], [], []
    for k, (x, y) in enumerate(cen):
        u = k / N
        x2, y2 = cen[min(k + 1, N)]; x1, y1 = cen[max(k - 1, 0)]
        dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
        w = wid(u) / 2
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
        sl.append((x + nx * w * 0.74, y + ny * w * 0.74)); sr.append((x - nx * w * 0.74, y - ny * w * 0.74))
    b.append(f'<path d="{poly_d(left + right[::-1])}" fill="{c["red"]}"/>')
    # sprocket holes running along both edges; the film advances toward the tickets
    for side in (sl, sr):
        b.append(f'<path d="{poly_d(side, False)}" fill="none" stroke="{c["page"]}" stroke-width="12" '
                 f'stroke-dasharray="12 20"><animate attributeName="stroke-dashoffset" values="0;-32" dur="0.9s" '
                 f'repeatCount="indefinite"/></path>')
    # the play mark, knocked out of the widest part of the ribbon
    px, py = bez(P0, P1, P2, P3, 0.2)
    b.append(f'<circle cx="{f1(px)}" cy="{f1(py)}" r="40" fill="none" stroke="{c["page"]}" stroke-width="7"/>'
             f'<path d="M{f1(px-13)} {f1(py-22)}L{f1(px+22)} {f1(py)}L{f1(px-13)} {f1(py+22)}Z" fill="{c["page"]}"/>')

    # tickets, fanned from a pivot below the page
    tw, thh = 230, 300
    def ticket_d(x, y):
        teeth = 9; s = tw / teeth
        return (f'M{x} {y}h{tw}v{thh}' + ''.join(f'l{f1(-s/2)} 12l{f1(-s/2)} -12' for _ in range(teeth)) + 'Z')
    cx0, cy0 = 826, 222
    for ang, fill in ((-15, c['ink']), (-7.5, c['ink']), (0, None)):
        g = [f'<path d="{ticket_d(cx0 - tw/2, cy0)}" fill="{fill or c["ink"]}" stroke="{c["page"]}" stroke-width="8" stroke-linejoin="round"/>']
        if fill is None:
            x, y = cx0 - tw / 2, cy0
            g.append(f'<path d="M{x+22} {y+22}h{tw-44}v62h{-(tw-44)}Z" fill="{c["red"]}"/>')
            g.append(t('COD', SERIF, 64, x + tw - 34, y + 74, c['page'], anchor='end'))
            g.append(f'<path d="M{x+22} {y+120}h120M{x+22} {y+146}h82" stroke="{c["page"]}" stroke-width="9" stroke-linecap="round"/>')
            bx = x + 22; bars = ''
            for k, wd in enumerate([5, 2, 7, 2, 3, 9, 3, 2, 6, 2, 8, 2, 3, 7, 2, 5, 2, 9, 2, 4, 6]):
                if k % 2 == 0: bars += f'M{f1(bx)} {y+thh-96}h{wd}v62h{-wd}Z'
                bx += wd + 2
            g.append(f'<path d="{bars}" fill="{c["page"]}"/>')
        b.append(f'<g transform="rotate({ang} {cx0} {cy0 + 620})">{"".join(g)}</g>')
    # the front ticket nods as each order lands
    b[-1] = b[-1].replace('">', '"><animateTransform attributeName="transform" type="rotate" additive="sum" '
                          f'values="0 {cx0} {cy0+620};4 {cx0} {cy0+620};0 {cx0} {cy0+620};0 {cx0} {cy0+620}" '
                          'keyTimes="0;0.15;0.35;1" dur="3.6s" repeatCount="indefinite"/>', 1)

    b.insert(0, title('Reelcart', 250, -8, 250, c['ink']))
    b.insert(1, kurd('بازارگە', 120, 18, 410, c['red']))
    b.append(desc('Reels in, cash orders out.', 4, 584, c['mute']))
    return defs, b, 'Reelcart, بازارگە. Store builder for Instagram, TikTok and WhatsApp sellers.'

# -- Medical Physics: a dotted radiograph of a hand; a red scan row sweeps the fingers and
#    the row's attenuation rises straight off it, peaks sitting on the bones
def plate_medphys(c):
    bones, flesh, palm = hand_model()
    ox, oy, sc = 40, 22, 2.02
    def T(x, y): return ox + x * sc, oy + y * sc
    defs = (dots('soft', 6, 1.6, c['ink'], offset=True, op=.55) +
            dots('bone', 4, 1.25, c['ink'], bg=c['page'], offset=True) +
            dots('pdot', 5, 1.7, c['red'], offset=True))
    b = []
    fl = []
    for chain, w in flesh:
        pts = ' '.join(f'{f1(T(*p)[0])} {f1(T(*p)[1])}' for p in chain)
        fl.append(f'<polyline points="{pts}" fill="none" stroke="url(#soft)" stroke-width="{f1(2*w*sc)}" stroke-linecap="round" stroke-linejoin="round"/>')
    pp = ' '.join(f'{f1(T(*p)[0])} {f1(T(*p)[1])}' for p in palm)
    fl.append(f'<polygon points="{pp}" fill="url(#soft)" stroke="url(#soft)" stroke-width="34" stroke-linejoin="round"/>')
    b.append(''.join(fl))
    cort, med = [], []
    for x1, y1, x2, y2, r in bones:
        (a, bb), (cc, dd) = T(x1, y1), T(x2, y2)
        cort.append(f'<path d="M{f1(a)} {f1(bb)}L{f1(cc)} {f1(dd)}" stroke-width="{f1(2*r*sc)}"/>')
        if (x1, y1) != (x2, y2):
            for (ex, ey) in ((a, bb), (cc, dd)):
                cort.append(f'<path d="M{f1(ex)} {f1(ey)}h0.01" stroke-width="{f1(2*r*sc*1.16)}"/>')
                med.append(f'<path d="M{f1(ex)} {f1(ey)}h0.01" stroke-width="{f1(2*r*sc*1.16-9)}"/>')
        if r * sc > 6: med.append(f'<path d="M{f1(a)} {f1(bb)}L{f1(cc)} {f1(dd)}" stroke-width="{f1(2*r*sc-9)}"/>')
    b.append(f'<g stroke="{c["ink"]}" stroke-linecap="round" fill="none">{"".join(cort)}</g>'
             f'<g stroke="url(#bone)" stroke-linecap="round" fill="none">{"".join(med)}</g>')

    def mu(xh, yh):
        v = 0.0
        if any(seg_dist(xh, yh, *ch[k], *ch[k + 1]) < w for ch, w in flesh for k in range(len(ch) - 1)) or in_poly(xh, yh, palm):
            v += 0.16
        for x1, y1, x2, y2, r in bones:
            dd = seg_dist(xh, yh, x1, y1, x2, y2)
            if (x1, y1) != (x2, y2):
                de = min(math.hypot(xh - x1, yh - y1), math.hypot(xh - x2, yh - y2))
                if de < r * 1.16 and de / 1.16 < dd: dd = de / 1.16
            if dd < r:
                v += 0.55 + 0.45 * (dd / r) ** 2
                break
        return v
    XS = [40 + k * 1.6 for k in range(int(180 / 1.6) + 1)]
    K = 120
    def prof(yrow):
        yh = (yrow - oy) / sc; pts = []; prev = 0
        for xh in XS:
            v = mu(xh, yh); v = prev * 0.35 + v * 0.65; prev = v
            pts.append((ox + xh * sc, yrow - v * K))
        return pts
    N = 16; cy_ = oy + 150 * sc; A = 62 * sc
    ysw = [cy_ + A * math.sin(2 * math.pi * k / N) for k in range(N + 1)]
    def line_d(pts): return poly_d(pts, False)
    def fill_d(pts, y): return line_d(pts) + f'L{f1(pts[-1][0])} {f1(y)}L{f1(pts[0][0])} {f1(y)}Z'
    profs = [prof(y) for y in ysw]
    tvals = ';'.join(f'0 {f1(y - ysw[0])}' for y in ysw)
    # scan row: a thin red line across the whole page, through the title as well
    b.append(f'<g><animateTransform attributeName="transform" type="translate" values="{tvals}" dur="7s" repeatCount="indefinite"/>'
             f'<path d="M0 {f1(ysw[0])}H{PW}" stroke="{c["red"]}" stroke-width="3"/></g>')
    b.append(f'<path d="{fill_d(profs[0], ysw[0])}" fill="url(#pdot)">'
             f'<animate attributeName="d" values="{";".join(fill_d(p, y) for p, y in zip(profs, ysw))}" dur="7s" repeatCount="indefinite"/></path>')
    b.append(f'<path d="{line_d(profs[0])}" fill="none" stroke="{c["red"]}" stroke-width="5" stroke-linejoin="round">'
             f'<animate attributeName="d" values="{";".join(line_d(p) for p in profs)}" dur="7s" repeatCount="indefinite"/></path>')

    b.append(title('Medical', 220, 1184, 262, c['ink'], anchor='end'))
    b.append(title('Physics', 220, 1184, 436, c['ink'], anchor='end'))
    b.append(desc('Radiology, taught in Sorani.', 1180, 548, c['mute'], anchor='end'))
    return defs, b, 'Medical Physics. Radiology and medical imaging, taught in Sorani.'

# -- Kurdistan AI: five Sorani letters on halftone discs sized by attention; arcs sweep
#    from the focus letter ک (red, bleeding off the edge) to the others, under the title
def plate_kai(c):
    glyphs = ['ک', 'ڕ', 'ڵ', 'ێ', 'ۆ']
    weights = [1.0, 0.62, 0.30, 0.82, 0.18]
    xs = [1112, 920, 748, 590, 432]; cyd = 456
    rad = [142, 104, 82, 112, 72]
    defs = ''.join(dots(f'h{i}', 8, 3.6 * w + 0.5, c['red'], offset=True) for i, w in enumerate(weights))
    b = []
    # arcs first, so the discs and the title sit over them
    for i in range(1, 5):
        x1, x2 = xs[0], xs[i]; span = x1 - x2
        y1, y2 = cyd - rad[0] + 18, cyd - rad[i] + 10
        h = 80 + span * 0.12
        d = f'M{f1(x1)} {f1(y1)}C{f1(x1-30)} {f1(y1-h)} {f1(x2+30)} {f1(y2-h)} {f1(x2)} {f1(y2)}'
        L = span * 1.3 + h * 1.6
        col = c['red'] if weights[i] > 0.6 else c['ink']
        sw = 2.5 + 8 * weights[i]
        b.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{f1(sw)}" stroke-linecap="round" stroke-dasharray="{f1(L)} {f1(L)}" stroke-dashoffset="0">'
                 f'<animate attributeName="stroke-dashoffset" values="{f1(L)};0;0;{f1(-L)}" keyTimes="0;0.35;0.8;1" dur="6s" '
                 f'begin="{(i-1)*0.25:.2f}s" repeatCount="indefinite" calcMode="spline" keySplines="0.5 0 0.2 1;0 0 1 1;0.5 0 0.8 1"/></path>')
    for i in range(4, -1, -1):
        g, x, r = glyphs[i], xs[i], rad[i]
        b.append(f'<circle cx="{x}" cy="{cyd}" r="{r}" fill="{c["red"] if i == 0 else f"url(#h{i})"}"/>')
        size = 210 if i == 0 else 170
        bx0, by0, bx1, by1 = B(g, NASKH, size, 0, 0, wght=700)
        b.append(t(g, NASKH, size, x - (bx0 + bx1) / 2, cyd - (by0 + by1) / 2, c['page'] if i == 0 else c['ink'], wght=700))
    b.append(title('Kurdistan AI', 196, -6, 190, c['ink']))
    b.append(desc('An AI journal written in Sorani.', 4, 268, c['mute']))
    return defs, b, 'Kurdistan AI. An AI journal written in Kurdish Sorani.'

# -- Iman: a woven khatam girih in a round medallion that bleeds off the left edge
def plate_iman(c):
    Lc = 176; th = 67.5; CX, CY, R = 270, 300, 360
    segs, ros = hankin_448(Lc, th, 3, 3, CX - Lc, CY - Lc)
    strands = strands_from(segs)
    occ = {}
    for s, (pts, closed) in enumerate(strands):
        rng = range(len(pts) - 1) if closed else range(1, len(pts) - 1)
        for k in rng:
            occ.setdefault(key(pts[k]), []).append((s, k))
    cross = {kp: v for kp, v in occ.items() if len(v) == 2}
    seq = {}
    for kp, v in cross.items():
        for s, k in v: seq.setdefault(s, []).append(k)
    for s in seq: seq[s].sort()
    where = {}
    for kp, v in cross.items():
        for s, k in v: where[(s, k)] = kp
    over = {}
    for kp0 in cross:
        if kp0 in over: continue
        over[kp0] = cross[kp0][0]; stack = [kp0]
        while stack:
            kp = stack.pop()
            for occ_ in cross[kp]:
                s, k = occ_; me_over = (occ_ == over[kp]); lst = seq[s]; idx = lst.index(k)
                for nb in (idx - 1, idx + 1):
                    if not (0 <= nb < len(lst)):
                        if strands[s][1] and lst: nb = nb % len(lst)
                        else: continue
                    o2 = (s, lst[nb]); kp2 = where[o2]
                    want = o2 if not me_over else [o for o in cross[kp2] if o != o2][0]
                    if kp2 not in over:
                        over[kp2] = want; stack.append(kp2)
    BWID, LINE = 18, 4.5
    defs = (f'<clipPath id="med"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>' +
            dots('ish', 6, 1.9, c['ink'], offset=True) + dots('idot', 6, 2.0, c['ink'], offset=True) +
            dots('ihat', 5, 1.0, c['ink'], offset=True))
    g = []
    cen = None
    for kind, ij, pts in ros:
        d = poly_d(pts)
        if kind == 'oct' and ij == (1, 1):
            cen = d; continue
        g.append(f'<path d="{d}" fill="url(#{"idot" if kind == "oct" else "ihat"})"/>')
    g.append(f'<path d="{cen}" fill="{c["red"]}"/>')
    sd = ''.join(poly_d([(x + 8, y + 9) for x, y in pts], cl) for pts, cl in strands)
    g.append(f'<path d="{sd}" fill="none" stroke="url(#ish)" stroke-width="{BWID}" stroke-linejoin="miter"/>')
    bd = ''.join(poly_d(pts, cl) for pts, cl in strands)
    g.append(f'<path d="{bd}" fill="none" stroke="{c["ink"]}" stroke-width="{BWID}" stroke-linejoin="miter" stroke-miterlimit="10"/>')
    g.append(f'<path d="{bd}" fill="none" stroke="{c["page"]}" stroke-width="{BWID-2*LINE}" stroke-linejoin="miter" stroke-miterlimit="10"/>')
    pieces = []
    for kp, (s, k) in over.items():
        pts, cl = strands[s]
        p = pts[k]; q1 = pts[k + 1]
        ux, uy = q1[0] - p[0], q1[1] - p[1]; Lu = math.hypot(ux, uy); ux, uy = ux / Lu, uy / Lu
        e = BWID * 0.9
        pieces.append(f'M{f1(p[0]-ux*e)} {f1(p[1]-uy*e)}L{f1(p[0]+ux*e)} {f1(p[1]+uy*e)}')
    pd = ''.join(pieces)
    g.append(f'<path d="{pd}" stroke="{c["ink"]}" stroke-width="{BWID}"/>')
    g.append(f'<path d="{pd}" stroke="{c["page"]}" stroke-width="{BWID-2*LINE}" stroke-linecap="square"/>')
    b = [f'<g clip-path="url(#med)">{"".join(g)}</g>']
    cpts = [p for kind, ij, pts in ros if kind == 'oct' and ij == (1, 1) for p in pts]
    per = sum(math.hypot(cpts[i][0] - cpts[i - 1][0], cpts[i][1] - cpts[i - 1][1]) for i in range(len(cpts)))
    b.append(f'<path d="{cen}" fill="none" stroke="{c["red"]}" stroke-width="5" stroke-dasharray="{f1(per)} {f1(per)}" stroke-dashoffset="0">'
             f'<animate attributeName="stroke-dashoffset" values="{f1(per)};0;0;{f1(-per)}" keyTimes="0;0.45;0.85;1" dur="8s" repeatCount="indefinite" '
             f'calcMode="spline" keySplines="0.5 0 0.2 1;0 0 1 1;0.5 0 0.8 1"/></path>')
    b.append(title('Iman', 330, 1184, 330, c['ink'], anchor='end'))
    b.append(kurd('ئیمان', 140, 1176, 478, c['red'], anchor='end'))
    b.append(desc('A Kurdish Islamic community.', 1180, 566, c['mute'], anchor='end'))
    return defs, b, 'Iman, ئیمان. A Kurdish Islamic community platform.'

PLATES = {'reelcart': plate_reelcart, 'medicalphysics': plate_medphys,
          'kurdistanai': plate_kai, 'imanikurd': plate_iman}

def plate(th, k):
    c = THEMES[th]
    defs, b, label = PLATES[k](c)
    return svg(PW, PH, ''.join(b), label, defs)

def write(name, s):
    with open(os.path.join(OUT, name), 'w') as f: f.write(s)

if __name__ == '__main__':
    only = sys.argv[2:] or None
    for th in THEMES:
        if not only or 'hero' in only: write(f'hero-{th}.svg', hero(th))
        if not only or 'sec' in only:
            write(f'sec-work-{th}.svg', section(th, 'Work', 'کار'))
            write(f'sec-more-{th}.svg', section(th, 'More', 'زیاتر'))
            write(f'sec-contact-{th}.svg', section(th, 'Contact', 'پەیوەندی'))
        for k in PLATES:
            if not only or k in only: write(f'plate-{k}-{th}.svg', plate(th, k))
    print('ok')

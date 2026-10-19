#!/usr/bin/env python3
"""Builds every SVG in assets/ for the Abdulla090 profile README (figures v3).
All type is converted to outlines (HarfBuzz-shaped), so nothing depends on fonts
installed on the viewer's machine. Run: python3 scripts/build.py assets
Fonts (OFL, not committed; put them in ./fonts next to scripts/ or set FONT_DIR):
  InstrumentSerif-Regular/Italic.ttf, IBMPlexMono-Regular/Medium.ttf  (github.com/google/fonts)
  NotoNaskhArabic-Bold.ttf = NotoNaskhArabic[wght].ttf, instanced at wght 700 (github.com/google/fonts)
Needs: pip install uharfbuzz fonttools

Palette is ink + red only. Tone comes from halftone dot patterns, hatching and
scanlines, never from colour gradients. Every animation's base attributes are the
finished picture, so a frozen render (or a viewer with SMIL off) looks complete."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from tp import path as P, width as W, bounds as B, contours as C

OUT = sys.argv[1] if len(sys.argv) > 1 else 'assets'
os.makedirs(OUT, exist_ok=True)

SERIF, SERIF_I = 'InstrumentSerif-Regular.ttf', 'InstrumentSerif-Italic.ttf'
MONO, MONO_M = 'IBMPlexMono-Regular.ttf', 'IBMPlexMono-Medium.ttf'
NASKH = 'NotoNaskhArabic-Bold.ttf'

THEMES = {
    # page = GitHub canvas. mass = the heavy figure panel. on = ink drawn on the mass.
    'light': dict(page='#ffffff', ink='#1f2328', red='#D0263A', mute='#59636e',
                  hair='#d1d9e0', hair2='#eaeef2', mass='#1f2328', on='#ffffff', tint='#f6f8fa'),
    'dark':  dict(page='#0d1117', ink='#E6EDF3', red='#F2484E', mute='#C9D1D9',
                  hair='#3d444d', hair2='#262c36', mass='#161b22', on='#E6EDF3', tint='#151b23'),
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

def mono(text, size, x, y, fill, anchor='start', track=None, medium=False, upper=True, extra=''):
    return t(text.upper() if upper else text, MONO_M if medium else MONO, size, x, y, fill, anchor,
             track=size * 0.12 if track is None else track, extra=extra)

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

def hatch(pid, step, sw, fill, angle=45, bg=None):
    b = f'<rect width="{step}" height="{step}" fill="{bg}"/>' if bg else ''
    return (f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate({angle})">{b}<rect width="{f1(sw)}" height="{step}" fill="{fill}"/></pattern>')

def lines_h(pid, step, sw, fill, op=1):
    return (f'<pattern id="{pid}" width="8" height="{step}" patternUnits="userSpaceOnUse">'
            f'<rect width="8" height="{f1(sw)}" fill="{fill}" opacity="{op}"/></pattern>')

def regmark(x, y, c, r=10, sw=2):
    return (f'<g stroke="{c}" stroke-width="{sw}" fill="none"><circle cx="{x}" cy="{y}" r="{r}"/>'
            f'<path d="M{x-r-7} {y}h{2*r+14}M{x} {y-r-7}v{2*r+14}"/></g>'
            f'<circle cx="{x}" cy="{y}" r="{r*0.45:.1f}" fill="{c}"/>')

def ticks(x0, x1, y, step, fill, major=5, h=8, hm=16, sw=2):
    out = []; i = 0; x = x0
    while x <= x1 + 0.01:
        hh = hm if i % major == 0 else h
        if hh: out.append(f'M{f1(x)} {y}v{-hh}')
        x += step; i += 1
    return f'<path d="{"".join(out)}" stroke="{fill}" stroke-width="{sw}" fill="none"/>'

def wedge(x, y, w, h, n, fill, ids):
    """Calibration step wedge: n tone steps from halftone patterns ids[0..n-1]."""
    sw = w / n; b = []
    for i in range(n):
        b.append(f'<rect x="{f1(x+i*sw)}" y="{y}" width="{f1(sw)}" height="{h}" fill="url(#{ids[i]})"/>')
    b.append(f'<rect x="{f1(x+1)}" y="{y+1}" width="{f1(w-2)}" height="{h-2}" fill="none" stroke="{fill}" stroke-width="2"/>')
    return ''.join(b)

def wedge_defs(prefix, fill, n=6, step=6):
    ids, d = [], []
    for i in range(n):
        r = step * 0.5 * math.sqrt((i + 1) / n) * 1.05
        pid = f'{prefix}{i}'; ids.append(pid)
        d.append(dots(pid, step, min(r, step * .52), fill, offset=True))
    return ids, ''.join(d)

def brackets(x0, y0, x1, y1, L, c, sw=4):
    p = (f'M{x0} {y0+L}V{y0}H{x0+L}M{x1-L} {y0}H{x1}V{y0+L}'
         f'M{x1} {y1-L}V{y1}H{x1-L}M{x0+L} {y1}H{x0}V{y1-L}')
    return f'<path d="{p}" fill="none" stroke="{c}" stroke-width="{sw}"/>'

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

# ------------------------------------------------------------------ HERO
def hero(th):
    c = THEMES[th]; Wd, H = 1200, 740
    LAT = ('Abdulla', SERIF, 268, 52, 330); KUR = ('عەبدوڵڵا', NASKH, 176, 1148, 505)
    latin, _ = P(LAT[0], LAT[1], LAT[2], LAT[3], LAT[4])
    kurd, _ = P(KUR[0], KUR[1], KUR[2], KUR[3], KUR[4], anchor='end', wght=700)
    wids, wdefs = wedge_defs('hw', c['ink'])
    rids, rdefs = wedge_defs('hr', c['red'])
    defs = (wdefs + rdefs +
            dots('neg', 7, 2.9, c['page'], offset=True) +            # halftone negative of the names
            lines_h('scan', 5, 1.6, c['page'], op=.28) +
            dots('det', 6, 1.5, c['ink'], offset=True))
    b = [f'<rect width="{Wd}" height="{H}" fill="{c["page"]}"/>']
    # print furniture: frame, crop marks, registration, colour bars
    b.append(f'<rect x="25" y="25" width="{Wd-50}" height="{H-50}" fill="none" stroke="{c["hair"]}" stroke-width="2"/>')
    for x, y in ((25, 25), (Wd - 25, 25), (25, H - 25), (Wd - 25, H - 25)):
        b.append(regmark(x, y, c['ink'], r=9, sw=2))
    b.append(mono('Abdulla Aziz Hameed', 20, 60, 78, c['ink'], medium=True))
    b.append(wedge(850, 60, 150, 22, 6, c['ink'], wids))
    b.append(wedge(1004, 60, 136, 22, 6, c['red'], rids))
    b.append(f'<path d="M60 96H1140" stroke="{c["ink"]}" stroke-width="3"/>')

    # names
    defs += f'<path id="nL" d="{latin}"/><path id="nK" d="{kurd}"/>'
    b.append(f'<use href="#nL" fill="{c["ink"]}"/><use href="#nK" fill="{c["red"]}"/>')
    b.append(f'<path d="M52 331.5H780" stroke="{c["hair"]}" stroke-width="2"/>')

    # detector: column projection of both names (a real line integral of the type)
    DY0, DY1, nb = 552, 612, 90
    polys = C(*LAT) + C(KUR[0], KUR[1], KUR[2], KUR[3], KUR[4], anchor='end', wght=700)
    cov = column_coverage(polys, 60, 1140, nb, 110, 530)
    mx = max(cov); bw = 1080 / nb
    bars = []
    for i, v in enumerate(cov):
        hgt = max(3, (v / mx) * (DY1 - DY0))
        bars.append(f'M{f1(60+i*bw+1.5)} {DY1}v-{f1(hgt)}h{f1(bw-3)}v{f1(hgt)}z')
    barsd = ''.join(bars)
    b.append(f'<path d="M60 {DY1+1}H1140" stroke="{c["ink"]}" stroke-width="3"/>')
    defs += f'<path id="bars" d="{barsd}"/>'
    b.append(f'<use href="#bars" fill="{c["ink"]}"/>')
    b.append(mono('Detector', 18, 60, DY0 - 12, c['mute'], medium=True))
    b.append(mono('Projection', 18, 1140, DY0 - 12, c['mute'], anchor='end', medium=True))

    # the beam: a red slab sweeping right→left, showing the names as a dithered negative
    BW = 176; Y0, Y1 = 104, DY1 + 14; X0 = 330    # X0 = resting (frozen) position
    vals = f'{X0};-200;-200;1220;1220;{X0}'; kt = '0;0.42;0.5;0.5;0.58;1'
    spl = 'calcMode="spline" keySplines="0.6 0 0.25 1;0 0 1 1;0 0 1 1;0 0 1 1;0.6 0 0.25 1"'
    defs += (f'<clipPath id="beam"><rect x="{X0}" y="{Y0}" width="{BW}" height="{Y1-Y0}">'
             f'<animate attributeName="x" values="{vals}" keyTimes="{kt}" dur="10s" repeatCount="indefinite" {spl}/>'
             f'</rect></clipPath>')
    b.append(f'<g clip-path="url(#beam)"><rect y="{Y0}" width="{Wd}" height="{Y1-Y0}" fill="{c["red"]}"/>'
             f'<use href="#nL" fill="url(#neg)"/><use href="#nK" fill="url(#neg)"/>'
             f'<use href="#bars" fill="{c["page"]}"/>'
             f'<rect y="{Y0}" width="{Wd}" height="{Y1-Y0}" fill="url(#scan)"/></g>')
    tv = ';'.join(f'{v-X0} 0' for v in map(float, vals.split(';')))
    hud = [f'<path d="M0 {Y0}V{Y1}M{BW} {Y0}V{Y1}" stroke="{c["ink"]}" stroke-width="3"/>',
           f'<path d="M-14 {Y0}h28M{BW-14} {Y0}h28M-14 {Y1}h28M{BW-14} {Y1}h28" stroke="{c["ink"]}" stroke-width="3"/>',
           f'<path d="M{BW/2} {Y0-10}v20M{BW/2-10} {Y0}h20" stroke="{c["ink"]}" stroke-width="2"/>',
           mono('X-ray', 18, 8, Y0 + 26, c['page'], medium=True)]
    b.append(f'<g transform="translate({X0} 0)"><animateTransform attributeName="transform" type="translate" '
             f'values="{tv.replace(".0 ", " ")}" keyTimes="{kt}" dur="10s" repeatCount="indefinite" {spl} additive="sum"/>'
             f'{"".join(hud)}</g>')

    # tagline + three facts
    b.append(t('Medical physics student building', SERIF_I, 40, 60, 668, c['ink']))
    b.append(t('Kurdish-first software.', SERIF_I, 40, 60, 706, c['ink']))
    cols = [('Physics', 'Salahaddin University'),
            ('Language', 'Kurdish · Arabic · English'),
            ('Product', 'Founder, Kurdistan AI')]
    yy = 652
    for k, v in cols:
        b.append(f'<rect x="610" y="{yy-14}" width="10" height="10" fill="{c["red"]}"/>')
        b.append(mono(k, 18, 632, yy - 2, c['red'], medium=True))
        b.append(mono(v, 18, 1140, yy - 2, c['ink'], anchor='end'))
        yy += 27
    return svg(Wd, H, ''.join(b), 'Abdulla Aziz Hameed. Medical physics student building Kurdish-first software.', defs)

# ------------------------------------------------------------------ SECTION HEADER
def section(th, num, en, ku):
    c = THEMES[th]; Wd, H = 1200, 120
    wids, wdefs = wedge_defs('sw', c['ink'], n=8, step=6)
    d, ew = P(en, SERIF, 66, 104, 84)
    _, kw = P(ku, NASKH, 46, 1200, 82, anchor='end', wght=700)
    b = [f'<rect x="0" y="22" width="80" height="80" fill="{c["red"]}"/>',
         mono(num, 30, 40, 74, c['page'], anchor='middle', medium=True, track=1),
         f'<path d="{d}" fill="{c["ink"]}"/>',
         t(ku, NASKH, 46, 1200, 82, c['red'], anchor='end', wght=700)]
    wx0 = 104 + ew + 36; wx1 = 1200 - kw - 36
    if wx1 - wx0 > 120:
        b.append(wedge(wx0, 52, wx1 - wx0, 26, 8, c['ink'], wids))
    b.append(f'<path d="M0 112H1200" stroke="{c["ink"]}" stroke-width="3"/>')
    return svg(Wd, H, ''.join(b), f'{num} {en}', wdefs)

# ------------------------------------------------------------------ PLATES
AX0, AX1, AY0, AY1 = 646, 1200, 22, 338     # art field of every plate

def plate_frame(c, num, cat, name, ku, line, tags):
    b = [f'<path d="M0 1.5H1200" stroke="{c["ink"]}" stroke-width="3"/>',
         f'<rect x="0" y="22" width="44" height="34" fill="{c["red"]}"/>',
         mono(num, 22, 22, 47, c['page'], anchor='middle', medium=True, track=1),
         mono(cat, 20, 60, 47, c['mute'])]
    d, nw = P(name, SERIF, 96, -4, 160)
    b.append(f'<path d="{d}" fill="{c["ink"]}"/>')
    if ku:
        b.append(t(ku, NASKH, 60, nw + 30, 158, c['red'], wght=700))
    b.append(f'<path d="M0 197H600" stroke="{c["hair"]}" stroke-width="2"/>')
    rows, cur = [], ''
    for wd in line.split():
        trial = (cur + ' ' + wd).strip()
        if W(trial.upper(), MONO, 21, tracking=1.2) > 560 and cur:
            rows.append(cur); cur = wd
        else:
            cur = trial
    rows.append(cur)
    for i, r in enumerate(rows):
        b.append(mono(r, 21, 0, 232 + i * 30, c['ink'], track=1.2))
    ty = 232 + (len(rows) - 1) * 30 + 22
    x = 0
    for tg in tags:
        tw = W(tg.upper(), MONO, 17, tracking=1.6)
        b.append(f'<rect x="{x+1}" y="{ty+1}" width="{tw+24}" height="36" fill="none" stroke="{c["ink"]}" stroke-width="2"/>')
        b.append(mono(tg, 17, x + 12, ty + 25, c['ink'], track=1.6))
        x += tw + 34
    return b

# -- 01 Reelcart: a reel on the right compresses, right-to-left, into a stack of COD tickets
def art_reelcart(c):
    defs = (dots('sh', 6, 1.8, c['ink'], offset=True) +
            dots('rh', 7, 2.4, c['page'], offset=True) +
            hatch('tk', 7, 2, c['ink'], 45))
    b = []
    # reel card
    rx, ry, rw, rh = 1030, 30, 166, 296
    b.append(f'<rect x="{rx+12}" y="{ry+12}" width="{rw}" height="{rh}" fill="url(#sh)"/>')
    b.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{c["red"]}"/>')
    # dithered lower third (the video), sprockets, play glyph knocked out
    b.append(f'<rect x="{rx}" y="{ry+rh*0.62:.0f}" width="{rw}" height="{rh*0.38:.0f}" fill="url(#rh)"/>')
    for k in range(9):
        yy = ry + 16 + k * 32
        b.append(f'<rect x="{rx+8}" y="{yy}" width="10" height="16" rx="2" fill="{c["page"]}"/>'
                 f'<rect x="{rx+rw-18}" y="{yy}" width="10" height="16" rx="2" fill="{c["page"]}"/>')
    cx, cy = rx + rw / 2, ry + 118
    b.append(f'<circle cx="{cx}" cy="{cy}" r="44" fill="none" stroke="{c["page"]}" stroke-width="5"/>')
    b.append(f'<path d="M{cx-14} {cy-24}L{cx+24} {cy}L{cx-14} {cy+24}Z" fill="{c["page"]}"/>')
    # progress bar, animated (base = full)
    b.append(f'<rect x="{rx+28}" y="{ry+rh-26}" width="{rw-56}" height="6" fill="{c["page"]}" opacity=".45"/>')
    b.append(f'<rect x="{rx+28}" y="{ry+rh-26}" width="{rw-56}" height="6" fill="{c["page"]}">'
             f'<animate attributeName="width" values="0;{rw-56}" dur="4s" repeatCount="indefinite"/></rect>')

    # motion lines: right→left, heavy masses + hairlines
    spec = [(54, 6, 'ink', 150), (82, 2, 'ink', 110), (104, 10, 'red', 170), (136, 2, 'ink', 90),
            (160, 6, 'ink', 140), (186, 2, 'red', 120), (210, 10, 'ink', 175), (240, 2, 'ink', 100),
            (262, 6, 'red', 150), (290, 2, 'ink', 130)]
    for y, sw, col, L in spec:
        x1 = 1018; x0 = x1 - L
        dash = f'{L*0.55:.0f} {L*0.2:.0f}'
        b.append(f'<path d="M{x1} {y}H{x0}" stroke="{c[col]}" stroke-width="{sw}" stroke-dasharray="{dash}">'
                 f'<animate attributeName="stroke-dashoffset" values="0;{-L*0.75:.0f}" dur="{1.1 + (y%5)*0.08:.2f}s" repeatCount="indefinite"/></path>')

    # ticket stack
    def ticket(x, y, w, h, top):
        teeth = 9; tw = w / teeth
        zz = ''.join(f'l{f1(tw/2)} 9l{f1(tw/2)} -9' for _ in range(teeth))
        d = f'M{x} {y}h{w}v{h}' + ''.join(f'l{f1(-tw/2)} 9l{f1(-tw/2)} -9' for _ in range(teeth)) + 'z'
        g = [f'<path d="{d}" fill="{c["page"]}" stroke="{c["ink"]}" stroke-width="4" stroke-linejoin="miter"/>']
        if top:
            g.append(f'<rect x="{x+16}" y="{y+16}" width="{w-32}" height="46" fill="{c["red"]}"/>')
            g.append(mono('COD', 30, x + w - 26, y + 50, c['page'], anchor='end', medium=True, track=3))
            g.append(f'<path d="M{x+16} {y+82}h{w*0.5:.0f}M{x+16} {y+104}h{w*0.36:.0f}" stroke="{c["ink"]}" stroke-width="6"/>')
            bx = x + 16; bars = ''
            for k, wd in enumerate([4, 2, 6, 2, 2, 8, 3, 2, 5, 2, 7, 2, 3, 6, 2, 4, 2, 8, 2, 3, 5]):
                if k % 2 == 0: bars += f'<rect x="{bx}" y="{y+h-74}" width="{wd}" height="50" fill="{c["ink"]}"/>'
                bx += wd + 1.6
            g.append(bars)
        else:
            g.append(f'<rect x="{x+4}" y="{y+4}" width="{w-8}" height="{h-8}" fill="url(#tk)" opacity=".5"/>')
        return ''.join(g)
    tx, ty, tw_, th_ = 664, 66, 196, 232
    b.append(f'<rect x="{tx+14}" y="{ty+14}" width="{tw_+48}" height="{th_}" fill="url(#sh)"/>')
    for k in (3, 2, 1):
        b.append(ticket(tx + k * 16, ty - k * 14, tw_, th_, False))
    top = ticket(tx, ty, tw_, th_, True)
    b.append(f'<g>{top}<animateTransform attributeName="transform" type="translate" '
             f'values="0 0;0 0;150 0;0 0" keyTimes="0;0.6;0.6;1" dur="4s" repeatCount="indefinite" '
             f'calcMode="spline" keySplines="0 0 1 1;0 0 1 1;0.2 0.7 0.2 1"/>'
             f'<animate attributeName="opacity" values="1;1;0;1" keyTimes="0;0.6;0.6;1" dur="4s" repeatCount="indefinite" '
             f'calcMode="spline" keySplines="0 0 1 1;0 0 1 1;0.2 0.7 0.2 1"/></g>')
    return defs, b

# -- 02 Medical Physics: a dithered radiograph of a hand with a live attenuation profile
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

def art_medphys(c):
    bones, flesh, palm = hand_model()
    ox, oy, sc = 700, 22, 1.08                    # hand placement in the plate
    def T(x, y): return ox + x * sc, oy + y * sc
    defs = (dots('soft', 5, 1.35, c['on'], offset=True, op=.62) +
            dots('bone', 4, 1.45, c['on'], bg=c['mass'], offset=True) +
            lines_h('raster', 4, 1.2, c['page'], op=.10))
    b = [f'<rect x="{AX0}" y="{AY0}" width="{AX1-AX0}" height="{AY1-AY0}" fill="{c["mass"]}"/>']
    # soft tissue
    fl = []
    for chain, w in flesh:
        pts = ' '.join(f'{f1(T(*p)[0])} {f1(T(*p)[1])}' for p in chain)
        fl.append(f'<polyline points="{pts}" fill="none" stroke="url(#soft)" stroke-width="{f1(2*w*sc)}" stroke-linecap="round" stroke-linejoin="round"/>')
    pp = ' '.join(f'{f1(T(*p)[0])} {f1(T(*p)[1])}' for p in palm)
    fl.append(f'<polygon points="{pp}" fill="url(#soft)" stroke="url(#soft)" stroke-width="18" stroke-linejoin="round"/>')
    b.append(f'<g clip-path="url(#field)">{"".join(fl)}</g>')
    # bone: solid cortex ring + dithered medulla
    cort, med = [], []
    for x1, y1, x2, y2, r in bones:
        (a, bb), (cc, dd) = T(x1, y1), T(x2, y2)
        cort.append(f'<path d="M{f1(a)} {f1(bb)}L{f1(cc)} {f1(dd)}" stroke-width="{f1(2*r*sc)}"/>')
        if (x1, y1) != (x2, y2):
            for (ex, ey) in ((a, bb), (cc, dd)):
                cort.append(f'<path d="M{f1(ex)} {f1(ey)}h0.01" stroke-width="{f1(2*r*sc*1.16)}"/>')
                med.append(f'<path d="M{f1(ex)} {f1(ey)}h0.01" stroke-width="{f1(2*r*sc*1.16-6)}"/>')
        if r * sc > 4: med.append(f'<path d="M{f1(a)} {f1(bb)}L{f1(cc)} {f1(dd)}" stroke-width="{f1(2*r*sc-6)}"/>')
    b.append(f'<g clip-path="url(#field)"><g stroke="{c["on"]}" stroke-linecap="round" fill="none">{"".join(cort)}</g>'
             f'<g stroke="url(#bone)" stroke-linecap="round" fill="none">{"".join(med)}</g></g>')
    defs += f'<clipPath id="field"><rect x="{AX0}" y="{AY0}" width="{AX1-AX0}" height="{AY1-AY0}"/></clipPath>'
    b.append(f'<rect x="{AX0}" y="{AY0}" width="{AX1-AX0}" height="{AY1-AY0}" fill="url(#raster)"/>')

    # attenuation along the scan column, precomputed for each scan position
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
                v += 0.55 + 0.45 * (dd / r) ** 2   # cortex reads denser than medulla
                break
        return v
    # line profile (ImageJ style): a horizontal scan row sweeps the fingers; the plot on the
    # right shows the row's density with the hand's x range mapped onto the plot width
    PX0, PX1, PB, PT = 1012, 1176, 300, 92
    HX0, HX1 = 684, 960
    xsamp = [HX0 + k * 3 for k in range(int((HX1 - HX0) / 3) + 1)]
    def prof(yrow):
        yh = (yrow - oy) / sc; pts = []; prev = 0
        for xx in xsamp:
            v = mu((xx - ox) / sc, yh); v = prev * 0.3 + v * 0.7; prev = v
            pts.append(f'{f1(PX0 + (xx - HX0) * (PX1 - PX0) / (HX1 - HX0))} {f1(PB - v * (PB - PT) / 1.05)}')
        return 'M' + 'L'.join(pts)
    N = 16; cy_ = 168; A = 70
    ysw = [cy_ + A * math.sin(2 * math.pi * k / N) for k in range(N + 1)]
    dvals = ';'.join(prof(y) for y in ysw)
    close = f'L{PX1} {PB}L{PX0} {PB}Z'
    fvals = ';'.join(prof(y) + close for y in ysw)
    defs += hatch('phat', 7, 2.2, c['red'], 45)
    b.append(brackets(AX0 + 18, AY0 + 18, 990, AY1 - 18, 26, c['red'], 4))
    b.append(f'<path d="M{PX0} {PB+2}H{PX1}" stroke="{c["on"]}" stroke-width="3"/>')
    b.append(ticks(PX0, PX1, PB + 2, 20.5, c['on'], major=4, h=6, hm=14, sw=2).replace('v-', 'v'))
    b.append(f'<path d="{prof(ysw[0]) + close}" fill="url(#phat)">'
             f'<animate attributeName="d" values="{fvals}" dur="7s" repeatCount="indefinite"/></path>')
    b.append(f'<path d="{prof(ysw[0])}" fill="none" stroke="{c["red"]}" stroke-width="4.5" stroke-linejoin="round">'
             f'<animate attributeName="d" values="{dvals}" dur="7s" repeatCount="indefinite"/></path>')
    tvals = ';'.join(f'0 {f1(y - ysw[0])}' for y in ysw)
    y0_ = ysw[0]
    b.append(f'<g><animateTransform attributeName="transform" type="translate" values="{tvals}" dur="7s" repeatCount="indefinite"/>'
             f'<path d="M{AX0+8} {f1(y0_)}H{HX1+12}" stroke="{c["red"]}" stroke-width="4"/>'
             f'<path d="M{AX0} {f1(y0_-9)}v18l12 -9zM{HX1+24} {f1(y0_-9)}v18l-12 -9z" fill="{c["red"]}"/></g>')
    b.append(f'<rect x="{AX0+1}" y="{AY0+1}" width="{AX1-AX0-2}" height="{AY1-AY0-2}" fill="none" stroke="{c["hair"]}" stroke-width="2"/>')
    b.append(mono('Line profile', 20, PX0, AY0 + 46, c['on'], medium=True))
    b.append(mono('60 kVp', 22, AX0 + 36, AY1 - 32, c['on'], medium=True, upper=False))
    return defs, b

# -- 03 Kurdistan AI: five Sorani letters as tokens, an attention head over a halftone heatmap
def art_kai(c):
    glyphs = ['ک', 'ڕ', 'ڵ', 'ێ', 'ۆ']          # read right-to-left: ک is token 0 (rightmost)
    weights = [1.0, 0.62, 0.30, 0.82, 0.18]
    n = 5; cw = (AX1 - AX0) / n; gy0, gy1 = 132, AY1
    defs = ''
    for i, wgt in enumerate(weights):
        defs += dots(f'h{i}', 8, 3.9 * wgt + 0.4, c['red'], offset=True)
    b = []
    focus = 0
    cx = lambda i: AX1 - cw * (i + 0.5)
    for i, (g, wgt) in enumerate(zip(glyphs, weights)):
        x0 = AX1 - cw * (i + 1)
        if i == focus:
            b.append(f'<rect x="{f1(x0)}" y="{gy0}" width="{f1(cw)}" height="{gy1-gy0}" fill="{c["red"]}"/>')
        else:
            b.append(f'<rect x="{f1(x0)}" y="{gy0}" width="{f1(cw)}" height="{gy1-gy0}" fill="url(#h{i})"/>')
        size = 168
        bx0, by0, bx1, by1 = B(g, NASKH, size, 0, 0, wght=700)
        gx = cx(i) - (bx0 + bx1) / 2; gyb = (gy0 + gy1) / 2 - (by0 + by1) / 2
        fill = c['page'] if i == focus else c['ink']
        b.append(t(g, NASKH, size, gx, gyb, fill, wght=700))
    # cell rules
    rules = ''.join(f'M{f1(AX1 - cw*k)} {gy0}V{gy1}' for k in range(1, n))
    b.append(f'<path d="{rules}" stroke="{c["page"]}" stroke-width="4"/>')
    b.append(f'<rect x="{AX0+1.5}" y="{gy0}" width="{AX1-AX0-3}" height="{gy1-gy0-1.5}" fill="none" stroke="{c["ink"]}" stroke-width="3"/>')
    # attention arcs from the focus token
    base = gy0 - 6
    for i in range(1, n):
        x1, x2 = cx(focus), cx(i); span = x1 - x2; h = 22 + span * 0.17
        d = f'M{f1(x1)} {base}C{f1(x1)} {f1(base-h)} {f1(x2)} {f1(base-h)} {f1(x2)} {base}'
        L = span * 1.25 + h
        col = c['red'] if weights[i] > 0.6 else c['ink']
        sw = 2 + 7 * weights[i]
        b.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{f1(sw)}" stroke-dasharray="{f1(L)} {f1(L)}" stroke-dashoffset="0">'
                 f'<animate attributeName="stroke-dashoffset" values="{f1(L)};0;0;{f1(-L)}" keyTimes="0;0.35;0.8;1" dur="6s" '
                 f'begin="{(i-1)*0.25:.2f}s" repeatCount="indefinite" calcMode="spline" keySplines="0.5 0 0.2 1;0 0 1 1;0.5 0 0.8 1"/></path>')
        b.append(f'<circle cx="{f1(x2)}" cy="{base}" r="6" fill="{col}"/>')
    b.append(f'<circle cx="{f1(cx(focus))}" cy="{base}" r="9" fill="{c["red"]}"/>')
    b.append(mono('Attention', 20, AX0 + 2, AY0 + 22, c['mute'], medium=True))
    return defs, b

# -- 04 Iman: an interlaced khatam (8-fold star) pattern by Hankin's construction on 4.8.8
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

def art_iman(c):
    Lc = 196; th = 67.5
    ox, oy = AX0 + (AX1 - AX0) / 2 - Lc, AY0 + (AY1 - AY0) / 2
    segs, ros = hankin_448(Lc, th, 2, 1, ox, oy)
    strands = strands_from(segs)
    # crossings = points where two different strands' vertices coincide (the edge midpoints)
    occ = {}
    for s, (pts, closed) in enumerate(strands):
        rng = range(len(pts) - 1) if closed else range(1, len(pts) - 1)
        for k in rng:
            occ.setdefault(key(pts[k]), []).append((s, k))
    cross = {kp: v for kp, v in occ.items() if len(v) == 2}
    # alternate over/under along each strand, propagated across crossings
    seq = {}
    for kp, v in cross.items():
        for s, k in v: seq.setdefault(s, []).append(k)
    for s in seq: seq[s].sort()
    where = {}
    for kp, v in cross.items():
        for s, k in v: where[(s, k)] = kp
    over = {}     # crossing -> the (strand, vertex) occurrence that passes over
    conflicts = 0
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
                    elif over[kp2] != want:
                        conflicts += 1
    if conflicts: print('interlace conflicts', conflicts, file=sys.stderr)
    BWID, LINE = 16, 4
    clip = f'<clipPath id="ifield"><rect x="{AX0}" y="{AY0}" width="{AX1-AX0}" height="{AY1-AY0}"/></clipPath>'
    defs = (clip + dots('ish', 6, 1.9, c['ink'], offset=True) + dots('idot', 6, 2.1, c['ink'], offset=True) +
            hatch('ihat', 8, 2.4, c['ink'], 45))
    b = [f'<rect x="{AX0}" y="{AY0}" width="{AX1-AX0}" height="{AY1-AY0}" fill="{c["tint"]}"/>']
    g = []
    # tiles: rosettes. Centre star red; the other stars in halftone; crosses hatched.
    cen = None
    for kind, ij, pts in ros:
        d = 'M' + 'L'.join(f'{f1(x)} {f1(y)}' for x, y in pts) + 'Z'
        if kind == 'oct' and ij == (1, 0):
            cen = d; continue
        g.append(f'<path d="{d}" fill="url(#{"idot" if kind == "oct" else "ihat"})"/>')
    g.append(f'<path d="{cen}" fill="{c["red"]}"/>')
    # band shadow (depth), then bands, then over-pieces at crossings
    sd = ''.join('M' + 'L'.join(f'{f1(x+7)} {f1(y+8)}' for x, y in pts) + ('Z' if cl else '') for pts, cl in strands)
    g.append(f'<path d="{sd}" fill="none" stroke="url(#ish)" stroke-width="{BWID}" stroke-linejoin="miter"/>')
    bd = ''.join('M' + 'L'.join(f'{f1(x)} {f1(y)}' for x, y in pts) + ('Z' if cl else '') for pts, cl in strands)
    g.append(f'<path d="{bd}" fill="none" stroke="{c["ink"]}" stroke-width="{BWID}" stroke-linejoin="miter" stroke-miterlimit="10"/>')
    g.append(f'<path d="{bd}" fill="none" stroke="{c["page"]}" stroke-width="{BWID-2*LINE}" stroke-linejoin="miter" stroke-miterlimit="10"/>')
    pieces = []
    for kp, (s, k) in over.items():
        pts, cl = strands[s]
        p = pts[k]; q0 = pts[k - 1] if k > 0 else pts[-2]; q1 = pts[k + 1]
        ux, uy = q1[0] - p[0], q1[1] - p[1]; Lu = math.hypot(ux, uy); ux, uy = ux / Lu, uy / Lu
        e = BWID * 0.9
        pieces.append(f'M{f1(p[0]-ux*e)} {f1(p[1]-uy*e)}L{f1(p[0]+ux*e)} {f1(p[1]+uy*e)}')
    pd = ''.join(pieces)
    g.append(f'<path d="{pd}" stroke="{c["ink"]}" stroke-width="{BWID}"/>')
    g.append(f'<path d="{pd}" stroke="{c["page"]}" stroke-width="{BWID-2*LINE}" stroke-linecap="square"/>')
    # a red thread drawn in along the strands bounding the centre star (base = complete)
    b.append(f'<g clip-path="url(#ifield)">{"".join(g)}</g>')
    # draw-in: the centre rosette outline traced in red
    cpts = [p for kind, ij, pts in ros if kind == 'oct' and ij == (1, 0) for p in pts]
    per = sum(math.hypot(cpts[i][0] - cpts[i - 1][0], cpts[i][1] - cpts[i - 1][1]) for i in range(len(cpts)))
    b.append(f'<path d="{cen}" fill="none" stroke="{c["red"]}" stroke-width="4" stroke-dasharray="{f1(per)} {f1(per)}" stroke-dashoffset="0">'
             f'<animate attributeName="stroke-dashoffset" values="{f1(per)};0;0;{f1(-per)}" keyTimes="0;0.45;0.85;1" dur="8s" repeatCount="indefinite" '
             f'calcMode="spline" keySplines="0.5 0 0.2 1;0 0 1 1;0.5 0 0.8 1"/></path>')
    b.append(f'<rect x="{AX0+1.5}" y="{AY0+1.5}" width="{AX1-AX0-3}" height="{AY1-AY0-3}" fill="none" stroke="{c["ink"]}" stroke-width="3"/>')
    return defs, b

PLATES = {
    'reelcart': dict(num='01', cat='Commerce · live', name='Reelcart', ku='بازارگە',
                     line='Store builder for Instagram, TikTok and WhatsApp sellers',
                     tags=['Next.js 16', 'Postgres / Drizzle', '4 languages · RTL'], art=art_reelcart),
    'medicalphysics': dict(num='02', cat='Education · live', name='Medical Physics', ku=None,
                     line='Radiology and medical imaging, taught in Sorani',
                     tags=['React', 'Three.js', 'Convex', 'DICOM'], art=art_medphys),
    'kurdistanai': dict(num='03', cat='Publication · live', name='Kurdistan AI', ku=None,
                     line='An AI journal written in Kurdish Sorani',
                     tags=['Founder', 'Sorani', 'kurdistanai.app'], art=art_kai),
    'imanikurd': dict(num='04', cat='Community · live', name='Iman', ku='ئیمان',
                     line='A Kurdish Islamic community platform',
                     tags=['TypeScript', 'MIT licence', 'Sorani'], art=art_iman),
}

def plate(th, key_):
    c = THEMES[th]; p = PLATES[key_]
    b = plate_frame(c, p['num'], p['cat'], p['name'], p['ku'], p['line'], p['tags'])
    defs, art = p['art'](c)
    b += art
    return svg(1200, 360, ''.join(b), f'{p["num"]} {p["name"]}. {p["line"]}.', defs)

# ------------------------------------------------------------------ COLOPHON
def colophon(th):
    c = THEMES[th]; Wd, H = 1200, 120
    rids, rdefs = wedge_defs('cr', c['red'], n=6)
    b = [f'<path d="M0 1.5H1200" stroke="{c["ink"]}" stroke-width="3"/>',
         regmark(22, 62, c['ink'], r=11, sw=2),
         mono('Colophon', 18, 70, 54, c['red'], medium=True),
         mono('Instrument Serif · IBM Plex Mono · Noto Naskh Arabic', 17, 220, 54, c['mute']),
         mono('Hand-built SVG.  Erbil, Kurdistan Region, 2026.', 17, 220, 86, c['mute']),
         wedge(70, 70, 120, 20, 6, c['red'], rids),
         t('عەبدوڵڵا', NASKH, 44, 1200, 84, c['ink'], anchor='end', wght=700)]
    return svg(Wd, H, ''.join(b), 'Colophon', rdefs)

def write(name, s):
    with open(os.path.join(OUT, name), 'w') as f: f.write(s)

if __name__ == '__main__':
    only = sys.argv[2:] or None
    for th in THEMES:
        if not only or 'hero' in only: write(f'hero-{th}.svg', hero(th))
        if not only or 'sec' in only:
            write(f'sec-now-{th}.svg', section(th, '01', 'Now', 'ئێستا'))
            write(f'sec-work-{th}.svg', section(th, '02', 'Work', 'کار'))
            write(f'sec-index-{th}.svg', section(th, '03', 'Index', 'پێڕست'))
            write(f'sec-contact-{th}.svg', section(th, '04', 'Contact', 'پەیوەندی'))
            write(f'colophon-{th}.svg', colophon(th))
        for k in PLATES:
            if not only or k in only: write(f'plate-{k}-{th}.svg', plate(th, k))
    print('ok')

#!/usr/bin/env python3
"""Builds every SVG in assets/ for the Abdulla090 profile README (figures v5).
Quiet direction: on the page background, one small figure per project with its title,
Kurdish name and one line set beside it. Nothing overlaps, nothing bleeds off an edge.
All type is converted to outlines (HarfBuzz-shaped), so nothing depends on fonts
installed on the viewer's machine. Run: python3 scripts/build.py assets
Fonts (OFL, not committed; put them in ./fonts next to scripts/ or set FONT_DIR):
  InstrumentSerif-Regular/Italic.ttf  (github.com/google/fonts)
  Vazirmatn-Bold.ttf  (github.com/rastikerdar/vazirmatn), full Sorani coverage:
  ڵ ڕ ێ ۆ are single precomposed glyphs, so marks never float.
Needs: pip install uharfbuzz fonttools"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from tp import path as P, width as W, bounds as B

OUT = sys.argv[1] if len(sys.argv) > 1 else 'assets'
os.makedirs(OUT, exist_ok=True)

SERIF, SERIF_I = 'InstrumentSerif-Regular.ttf', 'InstrumentSerif-Italic.ttf'
KU = 'Vazirmatn-Bold.ttf'

THEMES = {
    'light': dict(page='#ffffff', ink='#1f2328', red='#D0263A', mute='#59636e'),
    'dark':  dict(page='#0d1117', ink='#E6EDF3', red='#F2484E', mute='#9198a1'),
}
BOXES = []   # (name, kind, x0, y0, x1, y1) collected per figure for the overlap check

def f1(v):
    return ('%.1f' % v).rstrip('0').rstrip('.')

def svg(w, h, body, title, defs=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{title}"><title>{title}</title>'
            f'{"<defs>" + defs + "</defs>" if defs else ""}{body}</svg>')

def t(text, font, size, x, y, fill, anchor='start', kind='text'):
    d, w = P(text, font, size, x, y, anchor=anchor)
    bx = B(text, font, size, x, y, anchor=anchor)
    BOXES.append((text, kind, *bx))
    return f'<path d="{d}" fill="{fill}"/>'

def fig(x0, y0, x1, y1):
    BOXES.append(('figure', 'fig', x0, y0, x1, y1))

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


def poly_d(pts, close=True):
    return 'M' + 'L'.join(f'{f1(x)} {f1(y)}' for x, y in pts) + ('Z' if close else '')

# ------------------------------------------------------------------ HERO: the name in two scripts
def hero(th):
    c = THEMES[th]; Wd, H = 1200, 380
    b = [t('Abdulla', SERIF, 200, 40, 210, c['ink'])]
    _, w = P('Abdulla', SERIF, 200, 40, 210)
    # the one red detail: a full stop after the Latin name
    # (a full stop, so it sits just after the name and is left out of the spacing check)
    b.append(f'<circle cx="{f1(40 + w + 20)}" cy="197" r="13" fill="{c["red"]}"/>')
    b.append(t('عەبدوڵڵا', KU, 124, 1160, 210, c['ink'], anchor='end'))
    b.append(t('Medical physics student building Kurdish-first software.', SERIF_I, 52, 42, 322, c['mute']))
    return svg(Wd, H, ''.join(b), 'Abdulla Aziz Hameed, عەبدوڵڵا. Medical physics student building Kurdish-first software.')

# ------------------------------------------------------------------ SECTION WORD
def section(th, en, ku):
    c = THEMES[th]; Wd, H = 1200, 200
    _, ew = P(en, SERIF, 150, 0, 0)
    b = [t(en, SERIF, 150, 36, 150, c['ink']), t(ku, KU, 76, 36 + ew + 34, 150, c['red'])]
    return svg(Wd, H, ''.join(b), f'{en} ({ku})')

# ------------------------------------------------------------------ PLATES: figure left, words right
PW, PH = 1200, 460
FX0, FY0, FS = 40, 40, 380          # figure box
TX = 480                            # text column

def words(c, en, ku, line):
    """Title, Kurdish name, one line: stacked with measured gaps, centred on the figure."""
    items = [(en, SERIF, 124, c['ink']), (ku, KU, 72, c['red']), (line, SERIF_I, 52, c['mute'])]
    gaps = [34, 30]
    bbs = [B(s, f, z, 0, 0) for s, f, z, _ in items]
    hs = [bb[3] - bb[1] for bb in bbs]
    total = sum(hs) + sum(gaps)
    y = PH / 2 - total / 2; out = []
    for k, ((s, f, z, col), bb, h) in enumerate(zip(items, bbs, hs)):
        out.append(t(s, f, z, TX, y - bb[1], col))
        y += h + (gaps[k] if k < 2 else 0)
    return out

def plate_reelcart(c):
    """A film reel and one cash-on-delivery ticket."""
    b = []
    cx, cy, R = 170, 205, 118
    holes = ''.join(f'<circle cx="{f1(cx + 66*math.cos(math.radians(a)))}" cy="{f1(cy + 66*math.sin(math.radians(a)))}" r="27" fill="{c["page"]}"/>'
                    for a in range(-90, 270, 72))
    b.append(f'<g><animateTransform attributeName="transform" type="rotate" values="0 {cx} {cy};360 {cx} {cy}" dur="24s" repeatCount="indefinite"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{c["ink"]}"/>{holes}'
             f'<circle cx="{cx}" cy="{cy}" r="13" fill="{c["page"]}"/></g>')
    fig(cx - R, cy - R, cx + R, cy + R)
    x, y, tw, thh = 318, 230, 96, 150
    teeth = 6; s = tw / teeth
    d = f'M{x} {y}h{tw}v{thh}' + ''.join(f'l{f1(-s/2)} 9l{f1(-s/2)} -9' for _ in range(teeth)) + 'Z'
    b.append(f'<path d="{d}" fill="{c["red"]}"/>'
             f'<path d="M{x+16} {y+30}h{tw-32}M{x+16} {y+54}h{tw-50}" stroke="{c["page"]}" stroke-width="7" stroke-linecap="round"/>')
    bx = x + 16; bars = ''
    for k, wd in enumerate([4, 2, 6, 2, 3, 2, 7, 2, 3, 2, 5, 2, 4]):
        if k % 2 == 0: bars += f'M{bx} {y+thh-56}h{wd}v36h{-wd}Z'
        bx += wd + 2
    b.append(f'<path d="{bars}" fill="{c["page"]}"/>')
    fig(x, y, x + tw, y + thh + 9)
    b += words(c, 'Reelcart', 'بازارگە', 'Reels in, cash orders out.')
    return b, 'Reelcart, بازارگە. Store builder for Instagram, TikTok and WhatsApp sellers.'

def plate_medphys(c):
    """A dotted radiograph of a hand, nothing else."""
    bones, flesh, palm = hand_model()
    sc = 1.22; ox, oy = FX0 + FS/2 - 128*sc, FY0 + 6 - 24*sc
    def T(x, y): return ox + x * sc, oy + y * sc
    defs = dots('soft', 6, 1.6, c['ink'], offset=True, op=.5) + dots('bone', 4, 1.2, c['ink'], bg=c['page'], offset=True)
    b = []
    fl = []
    for chain, w in flesh:
        pts = ' '.join(f'{f1(T(*p)[0])} {f1(T(*p)[1])}' for p in chain)
        fl.append(f'<polyline points="{pts}" fill="none" stroke="url(#soft)" stroke-width="{f1(2*w*sc)}" stroke-linecap="round" stroke-linejoin="round"/>')
    pp = ' '.join(f'{f1(T(*p)[0])} {f1(T(*p)[1])}' for p in palm)
    fl.append(f'<polygon points="{pp}" fill="url(#soft)" stroke="url(#soft)" stroke-width="22" stroke-linejoin="round"/>')
    cort, med = [], []
    for x1, y1, x2, y2, r in bones:
        (a, bb), (cc, dd) = T(x1, y1), T(x2, y2)
        cort.append(f'<path d="M{f1(a)} {f1(bb)}L{f1(cc)} {f1(dd)}" stroke-width="{f1(2*r*sc)}"/>')
        if (x1, y1) != (x2, y2):
            for (ex, ey) in ((a, bb), (cc, dd)):
                cort.append(f'<path d="M{f1(ex)} {f1(ey)}h0.01" stroke-width="{f1(2*r*sc*1.16)}"/>')
                med.append(f'<path d="M{f1(ex)} {f1(ey)}h0.01" stroke-width="{f1(2*r*sc*1.16-6)}"/>')
        if r * sc > 5: med.append(f'<path d="M{f1(a)} {f1(bb)}L{f1(cc)} {f1(dd)}" stroke-width="{f1(2*r*sc-6)}"/>')
    # the wrist fades out instead of stopping on a hard edge
    defs += (f'<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0.78" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
             f'<mask id="fm" maskUnits="userSpaceOnUse" x="0" y="0" width="{PW}" height="{PH}"><rect x="{FX0}" y="{FY0}" width="{FS}" height="{FS}" fill="url(#fade)"/></mask>')
    b.append(f'<g mask="url(#fm)">{"".join(fl)}<g stroke="{c["ink"]}" stroke-linecap="round" fill="none">{"".join(cort)}</g>'
             f'<g stroke="url(#bone)" stroke-linecap="round" fill="none">{"".join(med)}</g></g>')
    fig(FX0, FY0, FX0 + FS, FY0 + FS)
    b += words(c, 'Medical Physics', 'فیزیای پزیشکی', 'Radiology, taught in Sorani.')
    return b, 'Medical Physics, فیزیای پزیشکی. Radiology and medical imaging, taught in Sorani.', defs

def plate_kai(c):
    """One row of discs spelling کوردی (Kurdish), read right to left."""
    letters = ['ک', 'و', 'ر', 'د', 'ی']          # reading order, placed right to left
    r, gap = 36, 5; cy = FY0 + FS / 2
    b = []
    for i, g in enumerate(letters):
        cx = FX0 + FS - r - i * (2 * r + gap)
        if i == 0:
            b.append(f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{r}" fill="{c["red"]}"/>'); col = c['page']
        else:
            b.append(f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{r-1.5}" fill="none" stroke="{c["ink"]}" stroke-width="3"/>'); col = c['ink']
        bb = B(g, KU, 48, 0, 0)
        d, _ = P(g, KU, 48, cx - (bb[0] + bb[2]) / 2, cy - (bb[1] + bb[3]) / 2)
        b.append(f'<path d="{d}" fill="{col}"/>')
        fig(cx - r, cy - r, cx + r, cy + r)
    b += words(c, 'Kurdistan AI', 'کوردستان ئەی ئای', 'An AI journal written in Sorani.')
    return b, 'Kurdistan AI. An AI journal written in Kurdish Sorani.'

def plate_iman(c):
    """A small khatam rosette: an eight-point star inside an eight-point star, in a ring."""
    cx, cy = FX0 + FS / 2, FY0 + FS / 2
    def star(Ro, Ri, rot=0):
        return [((Ro if k % 2 == 0 else Ri) * math.cos(math.radians(rot + k * 22.5 - 90)) + cx,
                 (Ro if k % 2 == 0 else Ri) * math.sin(math.radians(rot + k * 22.5 - 90)) + cy) for k in range(16)]
    b = [f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="150" fill="none" stroke="{c["ink"]}" stroke-width="4"/>',
         f'<path d="{poly_d(star(132, 96, 22.5))}" fill="none" stroke="{c["ink"]}" stroke-width="4" stroke-linejoin="miter"/>',
         f'<path d="{poly_d(star(132, 96))}" fill="none" stroke="{c["ink"]}" stroke-width="4" stroke-linejoin="miter"/>',
         f'<path d="{poly_d(star(70, 38, 0))}" fill="{c["red"]}"/>']
    fig(cx - 152, cy - 152, cx + 152, cy + 152)
    b += words(c, 'Iman', 'ئیمان', 'A Kurdish Islamic community.')
    return b, 'Iman, ئیمان. A Kurdish Islamic community platform.'

PLATES = {'reelcart': plate_reelcart, 'medicalphysics': plate_medphys,
          'kurdistanai': plate_kai, 'imanikurd': plate_iman}

def check(name, w, h, margin=20):
    """Hard rule: no figure touches any text, no text touches other text, all inside the canvas."""
    bad = []
    for i, a in enumerate(BOXES):
        if a[2] < 0 or a[3] < 0 or a[4] > w or a[5] > h: bad.append(f'{a[0]} leaves the canvas')
        for b_ in BOXES[i+1:]:
            if a[1] == 'fig' and b_[1] == 'fig': continue
            if not (a[4] + margin <= b_[2] or b_[4] + margin <= a[2] or a[5] + margin <= b_[3] or b_[5] + margin <= a[3]):
                bad.append(f'{a[0]} / {b_[0]}')
    if bad: raise SystemExit(f'{name}: overlap {bad}')
    BOXES.clear()

def plate(th, k):
    c = THEMES[th]
    r = PLATES[k](c)
    b, label = r[0], r[1]; defs = r[2] if len(r) > 2 else ''
    s = svg(PW, PH, ''.join(b), label, defs); check(k, PW, PH); return s

def write(name, s):
    with open(os.path.join(OUT, name), 'w') as f: f.write(s)

if __name__ == '__main__':
    for th in THEMES:
        s = hero(th); check('hero', 1200, 380); write(f'hero-{th}.svg', s)
        for en, ku, n in (('Work', 'کار', 'work'), ('More', 'زیاتر', 'more'), ('Contact', 'پەیوەندی', 'contact')):
            s = section(th, en, ku); check(n, 1200, 200); write(f'sec-{n}-{th}.svg', s)
        for k in PLATES: write(f'plate-{k}-{th}.svg', plate(th, k))
    print('ok')

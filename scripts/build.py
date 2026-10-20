#!/usr/bin/env python3
"""Builds every SVG in assets/ for the Abdulla090 profile README (figures v6, animated).
Quiet direction: on the page background, one small figure per project with its title,
Kurdish name and one line set beside it. Nothing overlaps, nothing bleeds off an edge.
All type is converted to outlines (HarfBuzz-shaped), so nothing depends on fonts
installed on the viewer's machine. Run: python3 scripts/build.py assets
Fonts (OFL, not committed; put them in ./fonts next to scripts/ or set FONT_DIR):
  InstrumentSerif-Regular/Italic.ttf  (github.com/google/fonts)
  Vazirmatn-Bold.ttf  (github.com/rastikerdar/vazirmatn), full Sorani coverage:
  ڵ ڕ ێ ۆ are single precomposed glyphs, so marks never float.
Animation: CSS @keyframes inside each SVG's <style> (GitHub shows these through <img>,
so no script and no interaction). The type draws or slides in once, then each figure
keeps one slow, quiet loop. Every animation ends on, or keeps returning to, the static
design, and prefers-reduced-motion turns all of it off (the static design remains).
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

# ------------------------------------------------------------------ motion kit
# .dr  outline type: a hairline traces each letter, then the fill comes in and the line goes
# .u   slides up 16px and fades in
# .pop scales up from its own centre
# All intro animations run once and hold their last frame, which is the static design.
EASE = 'cubic-bezier(.2,.7,.2,1)'
CSS = ('@keyframes draw{0%{stroke-opacity:1;stroke-dashoffset:1;fill-opacity:0}'
       '55%{stroke-opacity:1;stroke-dashoffset:0;fill-opacity:0}100%{stroke-opacity:0;stroke-dashoffset:0;fill-opacity:1}}'
       '@keyframes up{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}'
       '@keyframes pop{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}'
       f'.dr{{stroke-dasharray:1 1;animation:draw 1.8s ease-in-out both}}'
       f'.u{{animation:up .9s {EASE} both}}'
       f'.pop{{transform-box:fill-box;transform-origin:center;animation:pop .6s {EASE} both}}')
REDUCE = '@media (prefers-reduced-motion:reduce){*{animation:none!important}}'

def svg(w, h, body, title, defs='', css=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{title}"><title>{title}</title>'
            f'<style>{CSS}{css}{REDUCE}</style>'
            f'{"<defs>" + defs + "</defs>" if defs else ""}{body}</svg>')

def dl(s):
    """inline animation-delay"""
    return f' style="animation-delay:{f1(s)}s"' if s else ''

def t(text, font, size, x, y, fill, anchor='start', kind='text', cls=None, delay=0):
    """cls='dr' draws the outline in (hairline stroke, hidden at rest), cls='u' slides it up."""
    d, w = P(text, font, size, x, y, anchor=anchor)
    bx = B(text, font, size, x, y, anchor=anchor)
    BOXES.append((text, kind, *bx))
    extra = ''
    if cls == 'dr':
        extra = f' class="dr" pathLength="1" stroke="{fill}" stroke-width="{f1(max(1.2, size / 110))}" stroke-opacity="0"'
    elif cls:
        extra = f' class="{cls}"'
    return f'<path d="{d}" fill="{fill}"{extra}{dl(delay)}/>'

def blinks(name, on, e=1.2):
    """@keyframes for opacity that is 1 inside the given [a, b] percent intervals, 0 elsewhere,
    with short crossfades of e percent at each edge."""
    pts = {}
    for a, b in on:
        if a <= 0: pts[0] = 1
        else: pts[a] = 0; pts[a + e] = 1
        if b >= 100: pts[100] = 1
        else: pts[b] = 1; pts[b + e] = 0
    pts.setdefault(0, 0); pts.setdefault(100, 0)
    return '@keyframes %s{%s}' % (name, ''.join(f'{f1(k)}%{{opacity:{v}}}' for k, v in sorted(pts.items())))

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
    b = [t('Abdulla', SERIF, 200, 40, 210, c['ink'], cls='dr')]
    _, w = P('Abdulla', SERIF, 200, 40, 210)
    # the one red detail: a full stop after the Latin name
    # (a full stop, so it sits just after the name and is left out of the spacing check)
    # motion: it lands once both names are drawn, then blinks softly now and then, like a cursor
    b.append(f'<circle class="pop dot" cx="{f1(40 + w + 20)}" cy="197" r="13" fill="{c["red"]}"/>')
    b.append(t('عەبدوڵڵا', KU, 124, 1160, 210, c['ink'], anchor='end', cls='dr', delay=.5))
    b.append(t('Medical physics student building Kurdish-first software.', SERIF_I, 52, 42, 322, c['mute'], cls='u', delay=1.5))
    css = ('@keyframes blink{0%,86%,100%{opacity:1}90%,94%{opacity:0}}'
           '.dot{animation:pop .6s 2s cubic-bezier(.3,1.5,.5,1) both,blink 7s 4s step-end infinite}')
    return svg(Wd, H, ''.join(b), 'Abdulla Aziz Hameed, عەبدوڵڵا. Medical physics student building Kurdish-first software.', css=css)

# ------------------------------------------------------------------ SECTION WORD
def section(th, en, ku):
    c = THEMES[th]; Wd, H = 1200, 200
    _, ew = P(en, SERIF, 150, 0, 0)
    b = [t(en, SERIF, 150, 36, 150, c['ink'], cls='dr'), t(ku, KU, 76, 36 + ew + 34, 150, c['red'], cls='u', delay=.9)]
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
    motion = [('dr', .2), ('u', 1.0), ('u', 1.25)]   # title draws in, then the two lines rise
    for k, ((s, f, z, col), bb, h) in enumerate(zip(items, bbs, hs)):
        out.append(t(s, f, z, TX, y - bb[1], col, cls=motion[k][0], delay=motion[k][1]))
        y += h + (gaps[k] if k < 2 else 0)
    return out

def plate_reelcart(c):
    """A film reel and one cash-on-delivery ticket."""
    b = []
    cx, cy, R = 170, 205, 118
    holes = ''.join(f'<circle cx="{f1(cx + 66*math.cos(math.radians(a)))}" cy="{f1(cy + 66*math.sin(math.radians(a)))}" r="27" fill="{c["page"]}"/>'
                    for a in range(-90, 270, 72))
    # motion: the reel rolls in, then turns once every 24 s (CSS, so reduced motion stops it)
    b.append(f'<g class="pop"><g class="reel">'
             f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{c["ink"]}"/>{holes}'
             f'<circle cx="{cx}" cy="{cy}" r="13" fill="{c["page"]}"/></g></g>')
    fig(cx - R, cy - R, cx + R, cy + R)
    x, y, tw, thh = 318, 230, 96, 150
    teeth = 6; s = tw / teeth
    d = f'M{x} {y}h{tw}v{thh}' + ''.join(f'l{f1(-s/2)} 9l{f1(-s/2)} -9' for _ in range(teeth)) + 'Z'
    # motion: the ticket rises in after the reel, then every 8 s gives a small hop, an order coming in
    b.append('<g class="u" style="animation-delay:.5s"><g class="hop">')
    b.append(f'<path d="{d}" fill="{c["red"]}"/>'
             f'<path d="M{x+16} {y+30}h{tw-32}M{x+16} {y+54}h{tw-50}" stroke="{c["page"]}" stroke-width="7" stroke-linecap="round"/>')
    bx = x + 16; bars = ''
    for k, wd in enumerate([4, 2, 6, 2, 3, 2, 7, 2, 3, 2, 5, 2, 4]):
        if k % 2 == 0: bars += f'M{bx} {y+thh-56}h{wd}v36h{-wd}Z'
        bx += wd + 2
    b.append(f'<path d="{bars}" fill="{c["page"]}"/></g></g>')
    fig(x, y, x + tw, y + thh + 9)
    b += words(c, 'Reelcart', 'بازارگە', 'Reels in, cash orders out.')
    css = ('@keyframes spin{to{transform:rotate(360deg)}}'
           '@keyframes hop{0%,88%,100%{transform:none}92%{transform:translateY(-10px)}96%{transform:translateY(1px)}}'
           f'.reel{{transform-box:view-box;transform-origin:{cx}px {cy}px;animation:spin 24s linear infinite}}'
           '.hop{animation:hop 8s 3s ease-in-out infinite}')
    return b, 'Reelcart, بازارگە. Store builder for Instagram, TikTok and WhatsApp sellers.', '', css

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
    # motion: soft tissue develops first, then the bones, like a film coming up;
    # after that a thin red scan line sweeps down the hand every 8 s and is gone between sweeps
    b.append(f'<g mask="url(#fm)"><g class="dev">{"".join(fl)}</g><g class="dev" style="animation-delay:.5s">'
             f'<g stroke="{c["ink"]}" stroke-linecap="round" fill="none">{"".join(cort)}</g>'
             f'<g stroke="url(#bone)" stroke-linecap="round" fill="none">{"".join(med)}</g></g></g>')
    b.append(f'<rect class="scan" x="{FX0 + 30}" y="{FY0 + 4}" width="{FS - 60}" height="3" rx="1.5" fill="{c["red"]}" opacity="0"/>')
    fig(FX0, FY0, FX0 + FS, FY0 + FS)
    b += words(c, 'Medical Physics', 'فیزیای پزیشکی', 'Radiology, taught in Sorani.')
    css = ('@keyframes dev{from{opacity:0}to{opacity:1}}'
           '@keyframes scan{0%{opacity:0;transform:none}4%{opacity:.85}44%{opacity:.85}'
           f'50%{{opacity:0;transform:translateY({FS - 50}px)}}100%{{opacity:0;transform:translateY({FS - 50}px)}}}}'
           '.dev{animation:dev 1.4s ease-out both}'
           '.scan{animation:scan 8s 2.2s ease-in-out infinite}')
    return b, 'Medical Physics, فیزیای پزیشکی. Radiology and medical imaging, taught in Sorani.', defs, css

def plate_kai(c):
    """One row of discs spelling کوردی (Kurdish), read right to left."""
    letters = ['ک', 'و', 'ر', 'د', 'ی']          # reading order, placed right to left
    r, gap = 36, 5; cy = FY0 + FS / 2
    # motion: the discs rise in one by one, right to left (reading order). Then every 12 s the red
    # fill walks ک و ر د ی and back to ک, where it rests (the static design) most of the time.
    # Each disc carries both states, outlined and red, and the loop crossfades between them.
    walk = [[(0, 40), (90, 100)], [(40, 48), (84, 90)], [(48, 56), (78, 84)], [(56, 64), (72, 78)], [(64, 72)]]
    b = []; css = ''
    for i, g in enumerate(letters):
        cx = FX0 + FS - r - i * (2 * r + gap)
        bb = B(g, KU, 48, 0, 0)
        d, _ = P(g, KU, 48, cx - (bb[0] + bb[2]) / 2, cy - (bb[1] + bb[3]) / 2)
        b.append(f'<g class="u"{dl(.1 + i * .14)}>')
        # outlined state (hidden at rest for the first disc)
        b.append(f'<g class="o{i}"{" opacity=\"0\"" if i == 0 else ""}>'
                 f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{r-1.5}" fill="none" stroke="{c["ink"]}" stroke-width="3"/>'
                 f'<path d="{d}" fill="{c["ink"]}"/></g>')
        # red state (shown at rest only on the first disc)
        b.append(f'<g class="k{i}"{"" if i == 0 else " opacity=\"0\""}>'
                 f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{r}" fill="{c["red"]}"/>'
                 f'<path d="{d}" fill="{c["page"]}"/></g></g>')
        off = [(0, 0)]; prev = 0
        for a, z in walk[i]:
            if a > prev: off.append((prev, a))
            prev = z
        if prev < 100: off.append((prev, 100))
        css += blinks(f'k{i}', walk[i]) + blinks(f'o{i}', [iv for iv in off if iv[1] > iv[0]])
        css += f'.k{i}{{animation:k{i} 12s 2.6s linear infinite}}.o{i}{{animation:o{i} 12s 2.6s linear infinite}}'
        fig(cx - r, cy - r, cx + r, cy + r)
    b += words(c, 'Kurdistan AI', 'کوردستان ئەی ئای', 'An AI journal written in Sorani.')
    return b, 'Kurdistan AI. An AI journal written in Kurdish Sorani.', '', css

def plate_iman(c):
    """A small khatam rosette: an eight-point star inside an eight-point star, in a ring."""
    cx, cy = FX0 + FS / 2, FY0 + FS / 2
    def star(Ro, Ri, rot=0):
        return [((Ro if k % 2 == 0 else Ri) * math.cos(math.radians(rot + k * 22.5 - 90)) + cx,
                 (Ro if k % 2 == 0 else Ri) * math.sin(math.radians(rot + k * 22.5 - 90)) + cy) for k in range(16)]
    # motion: the ring and both stars are traced in, the red star lands in the middle; then every
    # 12 s the two stars turn 45 degrees in opposite directions, which brings each back onto itself
    b = [f'<circle class="tr" pathLength="1" cx="{f1(cx)}" cy="{f1(cy)}" r="150" fill="none" stroke="{c["ink"]}" stroke-width="4"/>',
         f'<path class="tr s1" pathLength="1" d="{poly_d(star(132, 96, 22.5))}" fill="none" stroke="{c["ink"]}" stroke-width="4" stroke-linejoin="miter"/>',
         f'<path class="tr s2" pathLength="1" d="{poly_d(star(132, 96))}" fill="none" stroke="{c["ink"]}" stroke-width="4" stroke-linejoin="miter"/>',
         f'<path class="pop" style="animation-delay:1.5s" d="{poly_d(star(70, 38, 0))}" fill="{c["red"]}"/>']
    fig(cx - 152, cy - 152, cx + 152, cy + 152)
    b += words(c, 'Iman', 'ئیمان', 'A Kurdish Islamic community.')
    # the dash is dropped on the last frame so the closing corner keeps its mitre
    css = ('@keyframes tr{0%{stroke-dasharray:1 1;stroke-dashoffset:1}99%{stroke-dasharray:1 1;stroke-dashoffset:0}100%{stroke-dasharray:none;stroke-dashoffset:0}}'
           '@keyframes cw{0%,72%{transform:none}100%{transform:rotate(45deg)}}'
           '@keyframes ccw{0%,72%{transform:none}100%{transform:rotate(-45deg)}}'
           f'.tr{{transform-box:view-box;transform-origin:{f1(cx)}px {f1(cy)}px;animation:tr 1.6s ease-in-out both}}'
           '.s1{animation:tr 1.6s .2s ease-in-out both,cw 12s 3s ease-in-out infinite}'
           '.s2{animation:tr 1.6s .4s ease-in-out both,ccw 12s 3s ease-in-out infinite}')
    return b, 'Iman, ئیمان. A Kurdish Islamic community platform.', '', css

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
    b, label = r[0], r[1]; defs = r[2] if len(r) > 2 else ''; css = r[3] if len(r) > 3 else ''
    s = svg(PW, PH, ''.join(b), label, defs, css); check(k, PW, PH); return s

def write(name, s):
    with open(os.path.join(OUT, name), 'w') as f: f.write(s)

if __name__ == '__main__':
    for th in THEMES:
        s = hero(th); check('hero', 1200, 380); write(f'hero-{th}.svg', s)
        for en, ku, n in (('Work', 'کار', 'work'), ('More', 'زیاتر', 'more'), ('Contact', 'پەیوەندی', 'contact')):
            s = section(th, en, ku); check(n, 1200, 200); write(f'sec-{n}-{th}.svg', s)
        for k in PLATES: write(f'plate-{k}-{th}.svg', plate(th, k))
    print('ok')

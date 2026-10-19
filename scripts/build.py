#!/usr/bin/env python3
"""Builds every SVG in assets/ for the Abdulla090 profile README.
All type is converted to outlines (HarfBuzz-shaped), so nothing depends on fonts
installed on the viewer's machine. Run: python3 scripts/build.py assets
Fonts (OFL, not committed; put them in ./fonts next to scripts/):
  InstrumentSerif-Regular/Italic.ttf, IBMPlexMono-Regular/Medium.ttf  (github.com/google/fonts)
  NotoNaskhArabic-Bold.ttf = NotoNaskhArabic[wght].ttf, instanced at wght 700 (github.com/google/fonts)
Needs: pip install uharfbuzz fonttools"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from tp import path as P, width as W

OUT = sys.argv[1] if len(sys.argv) > 1 else 'assets'
os.makedirs(OUT, exist_ok=True)

SERIF, SERIF_I = 'InstrumentSerif-Regular.ttf', 'InstrumentSerif-Italic.ttf'
MONO, MONO_M = 'IBMPlexMono-Regular.ttf', 'IBMPlexMono-Medium.ttf'
NASKH = 'NotoNaskhArabic-Bold.ttf'

THEMES = {
    # 'blue' is the accent slot (signal red in both themes); 'line' is illustration ink.
    'light': dict(field='#F3F5F8', ink='#0A1020', blue='#D0263A', mute='#5A6476',
                  hair='#CDD3DD', hair2='#E3E7EE', line='#A9B1BE', knock='#F3F5F8', page='#FFFFFF',
                  beam=.07),
    'dark':  dict(field='#0D1117', ink='#E6EDF3', blue='#F2484E', mute='#C9D1D9',
                  hair='#3D444D', hair2='#262C36', line='#C9D1D9', knock='#0D1117', page='#0D1117',
                  beam=.16),
}

def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>')

def t(text, font, size, x, y, fill, anchor='start', track=0, wght=None, extra=''):
    d, w = P(text, font, size, x, y, anchor=anchor, wght=wght, tracking=track)
    return f'<path d="{d}" fill="{fill}"{extra}/>'

def mono(text, size, x, y, fill, anchor='start', track=None, medium=False, upper=True):
    return t(text.upper() if upper else text, MONO_M if medium else MONO, size, x, y, fill, anchor,
             track=size * 0.12 if track is None else track)

def ticks(x0, x1, y, step, fill, major=5, h=8, hm=16):
    out = []
    i = 0; x = x0
    while x <= x1 + 0.01:
        hh = hm if i % major == 0 else h
        out.append(f'M{x:.1f} {y}v{-hh}')
        x += step; i += 1
    return f'<path d="{" ".join(out)}" stroke="{fill}" stroke-width="1" fill="none"/>'

def regmark(x, y, c, r=9):
    return (f'<g stroke="{c}" stroke-width="1" fill="none"><circle cx="{x}" cy="{y}" r="{r}"/>'
            f'<path d="M{x-r-6} {y}h{2*r+12}M{x} {y-r-6}v{2*r+12}"/></g>')

SPL = 'calcMode="spline" keySplines="0.55 0 0.2 1;0 0 1 1"'

# ------------------------------------------------------------------ HERO
def hero(th):
    c = THEMES[th]; Wd, H = 1200, 660
    b = [f'<rect width="{Wd}" height="{H}" fill="{c["field"]}"/>']
    # baseline grid
    b.append('<g stroke="%s" stroke-width="1">' % c['hair2'] + ''.join(
        f'<path d="M48 {y}H1152"/>' for y in (330, 500)) + '</g>')
    b.append(f'<rect x="24.5" y="24.5" width="{Wd-49}" height="{H-49}" fill="none" stroke="{c["hair"]}"/>')
    for x, y in ((24, 24), (Wd - 24, 24), (24, H - 24), (Wd - 24, H - 24)):
        b.append(regmark(x, y, c['hair']))
    # header line
    b.append(mono('Abdulla Aziz Hameed', 19, 60, 76, c['ink'], medium=True))
    b.append(mono('Erbil · Kurdistan', 19, 1140, 76, c['mute'], anchor='end'))
    b.append(f'<path d="M60 92H1140" stroke="{c["hair"]}"/>')

    latin, _ = P('Abdulla', SERIF, 268, 52, 330)
    kurd, kw = P('عەبدوڵڵا', NASKH, 176, 1148, 505, anchor='end', wght=700)
    names_base = f'<path d="{latin}" fill="{c["ink"]}"/><path d="{kurd}" fill="{c["blue"]}"/>'
    b.append(names_base)
    # small captions attached to the names

    # the scan: a beam sweeps across and shows the names in negative
    anim = (f'<animate attributeName="x" values="-150;1210;1210" keyTimes="0;0.72;1" dur="9s" '
            f'repeatCount="indefinite" {SPL}/>')
    animT = (f'<animateTransform attributeName="transform" type="translate" values="-150 0;1210 0;1210 0" '
             f'keyTimes="0;0.72;1" dur="9s" repeatCount="indefinite" {SPL}/>')
    b.append(f'<defs><clipPath id="beam"><rect x="-150" y="96" width="132" height="470">{anim}</rect></clipPath>'
             f'<pattern id="scan" width="6" height="4" patternUnits="userSpaceOnUse">'
             f'<rect width="6" height="1.2" fill="{c["knock"]}" opacity=".18"/></pattern></defs>')
    b.append(f'<g clip-path="url(#beam)"><rect y="96" width="{Wd}" height="470" fill="{c["blue"]}"/>'
             f'<path d="{latin}" fill="{c["knock"]}"/><path d="{kurd}" fill="{c["knock"]}"/>'
             f'<rect y="96" width="{Wd}" height="470" fill="url(#scan)"/></g>')
    b.append(f'<g>{animT}<path d="M150 96V566" stroke="{c["blue"]}" stroke-width="2.5"/>'
             f'{mono("scan", 15, 158, 116, c["blue"], medium=True)}</g>')

    # tagline + three facts
    b.append(t('Medical physics student building', SERIF_I, 40, 60, 585, c['ink']))
    b.append(t('Kurdish-first software.', SERIF_I, 40, 60, 622, c['ink']))
    cols = [('01  Physics', 'Salahaddin University'),
            ('02  Language', 'Kurdish · Arabic · English'),
            ('03  Product', 'Founder, Kurdistan AI')]
    # right block, stacked to stay legible when scaled down
    yy = 568
    for k, v in cols:
        b.append(mono(k.split('  ')[1], 17, 690, yy, c['blue'], medium=True))
        b.append(mono(v, 17, 1140, yy, c['ink'], anchor='end'))
        yy += 27
    b.append(ticks(60, 1140, H - 25, 12, c['hair'], major=10, h=5, hm=11))
    return svg(Wd, H, ''.join(b), 'Abdulla Aziz Hameed. Medical physics student building Kurdish-first software.')

# ------------------------------------------------------------------ SECTION HEADER
def section(th, num, en, ku):
    c = THEMES[th]; Wd, H = 1200, 120
    b = [mono(f'§ {num}', 18, 0, 78, c['blue'], medium=True),
         t(en, SERIF, 64, 96, 84, c['ink']),
         t(ku, NASKH, 46, 1200, 82, c['blue'], anchor='end', wght=700),
         f'<path d="M0 108.5H1200" stroke="{c["hair"]}"/>',
         ticks(0, 1200, 108, 24, c['hair'], major=5, h=0, hm=8)]
    return svg(Wd, H, ''.join(b), f'{num} {en}')

# ------------------------------------------------------------------ PLATES
def plate_frame(c, num, cat, name, ku, line, tags):
    b = [f'<path d="M0 0.5H1200" stroke="{c["hair"]}"/>',
         mono(num, 22, 0, 48, c['blue'], medium=True),
         mono(cat, 20, 66, 48, c['mute'])]
    d, nw = P(name, SERIF, 96, -4, 160)
    b.append(f'<path d="{d}" fill="{c["ink"]}"/>')
    if ku:
        b.append(t(ku, NASKH, 60, nw + 30, 158, c['blue'], wght=700))
    b.append(f'<path d="M0 196.5H600" stroke="{c["hair2"]}"/>')
    # wrap the one-liner to the text column so it can be set larger
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
        b.append(f'<rect x="{x+0.75}" y="{ty+0.75}" width="{tw+24}" height="36" fill="none" stroke="{c["line"]}" stroke-width="1.5"/>')
        b.append(mono(tg, 17, x + 12, ty + 25, c['ink'], track=1.6))
        x += tw + 34
    return b

def diag_reelcart(c):
    b = []
    srcs = [('TikTok', 110), ('Instagram', 180), ('WhatsApp', 250)]
    px, py, pw, ph = 925, 70, 118, 226
    for i, (n, y) in enumerate(srcs):
        b.append(mono(n, 18, 762, y + 6, c['ink'], anchor='end'))
        d = f'M776 {y} C850 {y}, 860 {py+ph/2}, {px} {py+ph/2}'
        b.append(f'<path id="rc{i}" d="{d}" fill="none" stroke="{c["line"]}" stroke-width="2.2"/>')
        b.append(f'<circle cx="776" cy="{y}" r="5" fill="{c["ink"]}"/>')
        b.append(f'<circle r="6" fill="{c["blue"]}"><animateMotion dur="3.6s" begin="{i*1.2}s" repeatCount="indefinite" '
                 f'keyPoints="0;1;1" keyTimes="0;0.55;1" calcMode="linear"><mpath href="#rc{i}"/></animateMotion></circle>')
    # phone storefront
    b.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16" fill="none" stroke="{c["ink"]}" stroke-width="2.8"/>')
    b.append(f'<path d="M{px+44} {py+12}h30" stroke="{c["ink"]}" stroke-width="3" stroke-linecap="round"/>')
    b.append(f'<rect x="{px+14}" y="{py+28}" width="{pw-28}" height="26" fill="{c["blue"]}" opacity=".9"/>')
    for r in range(3):
        for col in range(2):
            x = px + pw - 14 - (col + 1) * 42 - col * 6   # laid out right-to-left
            y = py + 64 + r * 44
            b.append(f'<rect x="{x}" y="{y}" width="42" height="36" fill="none" stroke="{c["line"]}" stroke-width="2.2"/>')
            b.append(f'<path d="M{x+42-6} {y+30}h-18" stroke="{c["mute"]}" stroke-width="3"/>')
    b.append(f'<rect x="{px+14}" y="{py+ph-34}" width="{pw-28}" height="20" rx="10" fill="{c["ink"]}"/>')
    # order slip
    ox = 1078
    b.append(f'<path id="rco" d="M{px+pw} {py+ph-24} H{ox}" fill="none" stroke="{c["line"]}" stroke-width="2.2"/>')
    b.append(f'<circle r="6" fill="{c["blue"]}"><animateMotion dur="3.6s" begin="0.6s" repeatCount="indefinite" '
             f'keyPoints="0;0;1;1" keyTimes="0;0.55;0.8;1" calcMode="linear"><mpath href="#rco"/></animateMotion></circle>')
    b.append(f'<path d="M{ox} 196h82v110l-10.25 -8l-10.25 8l-10.25 -8l-10.25 8l-10.25 -8l-10.25 8l-10.25 -8l-10.25 8z" '
             f'fill="none" stroke="{c["ink"]}" stroke-width="2.6"/>')
    for i, w in enumerate((56, 40, 50)):
        b.append(f'<path d="M{ox+12} {222+i*16}h{w}" stroke="{c["line"]}" stroke-width="3"/>')
    b.append(mono('order', 17, ox + 41, 184, c['blue'], anchor='middle', medium=True))
    return b

def diag_medphys(c):
    b = []
    sx, sy = 740, 182; dx = 1130
    # fan beam
    b.append(f'<path d="M{sx+28} {sy} L{dx} 70 L{dx} 294 Z" fill="{c["blue"]}" opacity="{c["beam"]}"/>')
    b.append(f'<path d="M{sx+28} {sy} L{dx} 70 M{sx+28} {sy} L{dx} 294" stroke="{c["line"]}" stroke-width="2"/>')
    # photons
    for i, y2 in enumerate((96, 140, 182, 224, 268)):
        b.append(f'<path d="M{sx+30} {sy} L{dx} {y2}" stroke="{c["blue"]}" stroke-width="2.8" '
                 f'stroke-dasharray="6 34" fill="none"><animate attributeName="stroke-dashoffset" '
                 f'values="0;-40" dur="{0.9 + i*0.13:.2f}s" repeatCount="indefinite"/></path>')
    # tube
    b.append(f'<rect x="{sx-30}" y="{sy-22}" width="58" height="44" rx="6" fill="{c["field"]}" stroke="{c["ink"]}" stroke-width="2.8"/>')
    b.append(f'<circle cx="{sx-6}" cy="{sy}" r="7" fill="none" stroke="{c["ink"]}" stroke-width="2.6"/>')
    b.append(f'<path d="M{sx+6} {sy-10}l14 10l-14 10" fill="none" stroke="{c["blue"]}" stroke-width="2.8"/>')
    # patient cross-section
    b.append(f'<ellipse cx="935" cy="182" rx="58" ry="84" fill="{c["field"]}" stroke="{c["ink"]}" stroke-width="2.6"/>')
    b.append(f'<ellipse cx="935" cy="182" rx="42" ry="66" fill="none" stroke="{c["line"]}" stroke-width="2" stroke-dasharray="4 5"/>')
    b.append(f'<circle cx="928" cy="140" r="14" fill="{c["ink"]}" opacity=".85"/>')
    b.append(f'<circle cx="942" cy="222" r="17" fill="{c["ink"]}" opacity=".85"/>')
    # detector + attenuation profile
    b.append(f'<rect x="{dx}" y="62" width="10" height="240" fill="{c["ink"]}"/>')
    prof = []
    for k in range(0, 241, 4):
        y = 62 + k
        a = 0.0
        a += 26 * math.exp(-((y - 130) / 14) ** 2)
        a += 30 * math.exp(-((y - 232) / 16) ** 2)
        a += 9 * math.exp(-((y - 182) / 70) ** 2)
        prof.append(f'{dx+50-a:.1f} {y}')
    b.append(f'<path d="M{dx+50} 62V302" stroke="{c["line"]}" stroke-width="2"/>')
    b.append(f'<path d="M{" L".join(prof)}" fill="none" stroke="{c["blue"]}" stroke-width="3.2"/>')
    b.append(mono('source', 17, sx - 30, 234, c['mute']))
    b.append(mono('tissue', 17, 935, 296, c['mute'], anchor='middle'))
    b.append(mono('I(x)', 18, dx + 50, 50, c['blue'], anchor='end', medium=True, upper=False))
    return b

def diag_kai(c):
    b = []
    x0, y0, w, h = 760, 54, 400, 262
    b.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" stroke="{c["ink"]}" stroke-width="2.6"/>')
    b.append(t('Kurdistan AI', SERIF, 34, x0 + 20, y0 + 44, c['ink']))
    b.append(t('کوردستان', NASKH, 30, x0 + w - 20, y0 + 44, c['blue'], anchor='end', wght=700))
    b.append(f'<path d="M{x0+20} {y0+60}H{x0+w-20}M{x0+20} {y0+64}H{x0+w-20}" stroke="{c["ink"]}" stroke-width="2"/>')
    # two RTL columns of text lines, right-aligned
    colw = (w - 60) / 2
    lens = [[1, .92, .97, .7, 1, .88, .95, .6], [1, .95, .8, 1, .9, .97, .5]]
    for ci in range(2):
        right = x0 + w - 20 - ci * (colw + 20)
        for li, L in enumerate(lens[ci]):
            y = y0 + 88 + li * 21
            if ci == 0 and li == 0:
                b.append(f'<rect x="{right-colw}" y="{y-7}" width="{colw}" height="12" fill="{c["blue"]}" opacity=".9"/>')
                continue
            b.append(f'<path d="M{right} {y}h{-colw*L:.1f}" stroke="{c["line"]}" stroke-width="6"/>')
    # typing line: grows leftwards (RTL) with a caret
    right = x0 + w - 20 - (colw + 20); y = y0 + 88 + 7 * 21
    b.append(f'<rect x="{right}" y="{y-3}" width="0" height="6" fill="{c["mute"]}">'
             f'<animate attributeName="width" values="0;{colw*.85:.1f};{colw*.85:.1f};0" keyTimes="0;.6;.9;1" dur="5s" repeatCount="indefinite"/>'
             f'<animate attributeName="x" values="{right};{right-colw*.85:.1f};{right-colw*.85:.1f};{right}" keyTimes="0;.6;.9;1" dur="5s" repeatCount="indefinite"/></rect>')
    b.append(f'<rect x="{right-2}" y="{y-9}" width="2" height="18" fill="{c["blue"]}">'
             f'<animate attributeName="x" values="{right-2};{right-colw*.85-4:.1f};{right-colw*.85-4:.1f};{right-2}" keyTimes="0;.6;.9;1" dur="5s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="1;0;1" dur="0.9s" repeatCount="indefinite"/></rect>')
    return b

def star(cx, cy, r):
    pts = []
    for k in range(16):
        a = math.pi / 8 * k - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.70
        pts.append(f'{cx + rr*math.cos(a):.1f} {cy + rr*math.sin(a):.1f}')
    return 'M' + ' L'.join(pts) + 'Z'

def diag_iman(c):
    b = []
    # khatam lattice: eight-point stars on a square grid
    s = 74
    xs = [800 + i * s for i in range(5)]; ys = [72 + j * s for j in range(4)]
    cl = '<clipPath id="ik"><rect x="760" y="52" width="400" height="262"/></clipPath>'
    g = []
    for x in xs:
        for y in ys:
            g.append(f'<rect x="{x-24}" y="{y-24}" width="48" height="48" fill="none"/>')
            g.append(f'<rect x="{x-24}" y="{y-24}" width="48" height="48" transform="rotate(45 {x} {y})" fill="none"/>')
    b.append(f'<defs>{cl}</defs><g clip-path="url(#ik)" stroke="{c["line"]}" stroke-width="2.2">{"".join(g)}</g>')
    b.append(f'<rect x="760.5" y="52.5" width="400" height="262" fill="none" stroke="{c["ink"]}" stroke-width="2.6"/>')
    cx, cy = xs[2], ys[1] + s / 2
    b.append(f'<g><animateTransform attributeName="transform" type="rotate" values="0 {cx} {cy};45 {cx} {cy};45 {cx} {cy}" '
             f'keyTimes="0;.5;1" dur="8s" repeatCount="indefinite" calcMode="spline" keySplines="0.6 0 0.2 1;0 0 1 1"/>'
             f'<path d="{star(cx, cy, 70)}" fill="{c["blue"]}"/>'
             f'<path d="{star(cx, cy, 48)}" fill="none" stroke="{c["knock_p"]}" stroke-width="2.6"/></g>')
    return b

PLATES = {
    'reelcart': dict(num='01', cat='Commerce · live', name='Reelcart', ku='بازارگە',
                     line='Store builder for Instagram, TikTok and WhatsApp sellers',
                     tags=['Next.js 16', 'Postgres / Drizzle', '4 languages · RTL'], diag=diag_reelcart),
    'medicalphysics': dict(num='02', cat='Education · live', name='Medical Physics', ku=None,
                     line='Radiology and medical imaging, taught in Sorani',
                     tags=['React', 'Three.js', 'Convex', 'DICOM'], diag=diag_medphys),
    'kurdistanai': dict(num='03', cat='Publication · live', name='Kurdistan AI', ku=None,
                     line='An AI journal written in Kurdish Sorani',
                     tags=['Founder', 'Sorani', 'kurdistanai.app'], diag=diag_kai),
    'imanikurd': dict(num='04', cat='Community · live', name='Iman', ku='ئیمان',
                     line='A Kurdish Islamic community platform',
                     tags=['TypeScript', 'MIT licence', 'Sorani'], diag=diag_iman),
}

def plate(th, key):
    c = dict(THEMES[th]); c['knock_p'] = c['page']
    p = PLATES[key]
    b = plate_frame(c, p['num'], p['cat'], p['name'], p['ku'], p['line'], p['tags'])
    dx = -50 if key == 'medicalphysics' else 0
    b.append(f'<g transform="translate({955+dx} 185) scale(1.12) translate(-955 -185)">')
    b += p['diag'](c)
    b.append('</g>')
    return svg(1200, 360, ''.join(b), f'{p["num"]} {p["name"]}. {p["line"]}.')

# ------------------------------------------------------------------ COLOPHON
def colophon(th):
    c = THEMES[th]; Wd, H = 1200, 110
    b = [f'<path d="M0 0.5H1200" stroke="{c["hair"]}"/>',
         ticks(0, 1200, 12, 24, c['hair'], major=5, h=0, hm=8),
         mono('Colophon', 17, 0, 54, c['blue'], medium=True),
         mono('Instrument Serif · IBM Plex Mono · Noto Naskh Arabic', 17, 170, 54, c['mute']),
         mono('Hand-built SVG.  Erbil, Kurdistan Region, 2026.', 17, 170, 86, c['mute']),
         t('عەبدوڵڵا', NASKH, 40, 1200, 80, c['ink'], anchor='end', wght=700)]
    return svg(Wd, H, ''.join(b), 'Colophon')

def write(name, s):
    with open(os.path.join(OUT, name), 'w') as f: f.write(s)

for th in THEMES:
    write(f'hero-{th}.svg', hero(th))
    write(f'sec-now-{th}.svg', section(th, '01', 'Now', 'ئێستا'))
    write(f'sec-work-{th}.svg', section(th, '02', 'Work', 'کار'))
    write(f'sec-index-{th}.svg', section(th, '03', 'Index', 'پێڕست'))
    write(f'sec-contact-{th}.svg', section(th, '04', 'Contact', 'پەیوەندی'))
    write(f'colophon-{th}.svg', colophon(th))
    for k in PLATES:
        write(f'plate-{k}-{th}.svg', plate(th, k))
print('ok', sorted(os.listdir(OUT)))

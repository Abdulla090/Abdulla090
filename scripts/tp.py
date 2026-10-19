"""Text -> SVG path, shaped with HarfBuzz (correct Arabic-script joining / RTL)."""
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.varLib import instancer
import io, functools, os

FD = os.environ.get('FONT_DIR', os.path.join(os.path.dirname(__file__), '..', 'fonts'))

@functools.lru_cache(None)
def load(name, wght=None):
    path = os.path.join(FD, name)
    tt = TTFont(path)
    if wght is not None and 'fvar' in tt:
        tt = instancer.instantiateVariableFont(tt, {'wght': wght})
    buf = io.BytesIO(); tt.save(buf); data = buf.getvalue()
    tt = TTFont(io.BytesIO(data))
    face = hb.Face(data); font = hb.Font(face)
    return tt, font, tt['head'].unitsPerEm

def shape(text, fname, wght=None, features=None, direction=None):
    tt, font, upem = load(fname, wght)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    if direction: buf.direction = direction
    hb.shape(font, buf, features or {"kern": True, "liga": True})
    return tt, upem, buf.glyph_infos, buf.glyph_positions

def width(text, fname, size, wght=None, tracking=0):
    tt, upem, infos, pos = shape(text, fname, wght)
    s = size / upem
    return sum(p.x_advance for p in pos) * s + tracking * max(len(infos) - 1, 0)

def path(text, fname, size, x, y, anchor='start', wght=None, tracking=0):
    """Return (d, width). y is the baseline. tracking in px between glyphs."""
    tt, upem, infos, pos = shape(text, fname, wght)
    gs = tt.getGlyphSet(); order = tt.getGlyphOrder()
    s = size / upem
    w = sum(p.x_advance for p in pos) * s + tracking * max(len(infos) - 1, 0)
    if anchor == 'middle': x -= w / 2
    elif anchor == 'end': x -= w
    pen = SVGPathPen(gs, ntos=lambda v: ('%.1f' % v).rstrip('0').rstrip('.'))
    cx = 0.0
    for i, (info, p) in enumerate(zip(infos, pos)):
        g = order[info.codepoint]
        ox = x + (cx + p.x_offset) * s
        oy = y - p.y_offset * s
        tp = TransformPen(pen, (s, 0, 0, -s, ox, oy))
        gs[g].draw(tp)
        cx += p.x_advance + tracking / s
    return pen.getCommands(), w

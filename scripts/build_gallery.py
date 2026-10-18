"""Rebuild the original editorial project tiles and tiny motion index.

Run: py scripts/build_gallery.py
Dependencies: Pillow (for GIF only), otherwise Python standard library.
"""
from pathlib import Path
from html import escape

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'assets'/'projects'
OUT.mkdir(parents=True,exist_ok=True)

# The typography itself is the visual: no illustrations, fake UI, or stock art.
ENTRIES=[
 ('bazarga','01 / INDEPENDENT PRODUCT','REELCART','بازارگە','SOCIAL COMMERCE / KURDISTAN','blue'),
 ('medicalphysics','02 / LEARNING EXPERIENCE','MEDICAL','PHYSICS','INTERACTIVE RADIOGRAPHY SIMULATOR','black'),
 ('imanikurd','03 / COMMUNITY TOOL','IMANI','KURD','KURDISH LANGUAGE / COMMUNITY','cream'),
 ('kurdlingoo','04 / LANGUAGE LEARNING','PHINGO','.','AI × LANGUAGE × PLAY','black'),
 ('zheer-voice','05 / LANGUAGE TECHNOLOGY','ZHEER','VOICE','KURDISH SORANI / VOICE & TEXT','cream'),
 ('3DCellForge','06 / EXPERIMENTAL 3D','CELL','FORGE','BIOLOGY / INTERACTIVE WEBGL','blue'),
 ('aiacademic','07 / EDUCATION','AI','ACADEMIC','TOOLS FOR BETTER STUDYING','black'),
 ('BMX_Racer','08 / GAME DEVELOPMENT','DESCENT','.','PROCEDURAL DOWNHILL BMX','cream'),
]

def layout(name, idx, first, second, detail, variant):
    dark = variant=='black'
    blue = variant=='blue'
    bg='#20201F' if dark else '#2842E7' if blue else '#F3F1EA'
    ink='#F5F3ED' if dark or blue else '#1C1C1B'
    subtle='#B1B2AE' if dark else '#C6D0FF' if blue else '#696864'
    rule='#535551' if dark else '#7689F9' if blue else '#CAC6BD'
    accent='#AFC4FF' if dark else '#F4F1EA' if blue else '#2842E7'
    w=670;h=307
    mainSize=78 if len(first)<=8 else 65 if len(first)<=11 else 54
    secondSize=86 if len(second)<=8 else 70 if len(second)<=11 else 55
    if second=='.':
      firstSize=105 if len(first)<7 else 84
      large=f'<text x="34" y="188" class="display" fill="{ink}" font-size="{firstSize}" letter-spacing="-5">{escape(first)}</text><rect x="37" y="204" width="96" height="7" fill="{accent}"/>'
    else:
      large=f'<text x="34" y="158" class="display" fill="{ink}" font-size="{mainSize}" letter-spacing="-3">{escape(first)}</text><text x="34" y="236" class="display" fill="{accent if blue else ink}" font-size="{secondSize}" letter-spacing="-3">{escape(second)}</text>'
    if name=='imanikurd':
      large=f'<text x="34" y="157" class="display" fill="{ink}" font-size="90" letter-spacing="-3">IMANI</text><text x="34" y="235" class="display" fill="{accent}" font-size="102" letter-spacing="-3">KURD</text>'
    if name=='3DCellForge':
      large=f'<text x="34" y="154" class="display" fill="{ink}" font-size="106" letter-spacing="-5">CELL</text><text x="34" y="235" class="display" fill="{ink}" font-size="106" letter-spacing="-5">FORGE</text>'
    doc=f'''<svg xmlns="http://www.w3.org/2000/svg" width="670" height="307" viewBox="0 0 670 307" role="img" aria-labelledby="title desc">
<title id="title">{escape(first+' '+second)} — GitHub portfolio project</title><desc id="desc">Editorial typography project tile, {escape(detail)}.</desc>
<style>.display{{font-family:Arial,'Helvetica Neue',Helvetica,sans-serif;font-weight:900}}.micro{{font-family:'Courier New',monospace;font-size:12px;letter-spacing:1.4px}} @media(prefers-reduced-motion:no-preference){{.accent{{animation:shift 9s ease-in-out infinite}}@keyframes shift{{0%,100%{{opacity:1}}50%{{opacity:.48}}}}}}</style>
<rect width="670" height="307" fill="{bg}"/>
<path d="M34 63H635 M34 258H635" stroke="{rule}" stroke-width="1" />
<text x="35" y="39" class="micro" fill="{ink}">{escape(idx.upper())}</text>
<text x="634" y="39" text-anchor="end" class="micro" fill="{subtle}">AA / WORKS 2026</text>
{large}
<text x="36" y="286" class="micro" fill="{ink}">{escape(detail)}</text>
<g class="accent" fill="none" stroke="{accent}" stroke-width="3"><path d="M599 279h35v-35"/><path d="M611 267l23-23"/></g>
</svg>'''
    return doc

for e in ENTRIES:
    slug,*rest=e
    (OUT/(slug+'.svg')).write_text(layout(slug,*rest),encoding='utf-8')

def motion():
    from PIL import Image,ImageFont,ImageDraw
    W,H=1200,118
    serif='C:/Windows/Fonts/segoeuib.ttf'
    mono='C:/Windows/Fonts/consola.ttf'
    font=ImageFont.truetype(serif,38)
    small=ImageFont.truetype(mono,17)
    micro=ImageFont.truetype(mono,14)
    frames=[]
    names=['THINK','DESIGN','BUILD','SHIP']
    for i in range(40):
      im=Image.new('RGB',(W,H),(244,242,236))
      d=ImageDraw.Draw(im)
      d.line((20,10,1180,10),fill=(28,28,28),width=2)
      d.line((20,108,1180,108),fill=(28,28,28),width=2)
      d.text((30,30),'AA.',font=font,fill=(29,29,28))
      d.line((132,26,132,93),fill=(190,185,176),width=1)
      d.text((159,24),'ALWAYS',font=micro,fill=(80,80,76))
      d.text((158,46),'IN PROGRESS',font=small,fill=(30,30,30))
      x0=443
      for j,word in enumerate(names):
        x=x0+j*170
        active = j==(i//10)
        d.text((x,43),word,font=small,fill=(40,62,225) if active else (76,75,70))
        d.line((x,77,x+136,77),fill=(40,62,225) if active else (205,201,193),width=4 if active else 1)
      d.text((1050,18),'26 / 26',font=micro,fill=(29,29,28))
      d.line((1103,97,1124,76),fill=(40,62,225),width=3)
      d.line((1110,76,1124,76),fill=(40,62,225),width=3)
      d.line((1124,76,1124,90),fill=(40,62,225),width=3)
      frames.append(im)
    dest=ROOT/'assets'/'build-loop.gif'
    frames[0].save(dest,format='GIF',save_all=True,append_images=frames[1:],duration=100,loop=0,optimize=True)
    print('Saved '+str(dest)+' ('+str(dest.stat().st_size//1024)+' KiB)')

if __name__=='__main__':motion()

"""Manga page components: blackletter headings, tapered ink, hatching and screentones.

No remote resources, scripts, embedded fonts, gradients or blur filters in the
resulting SVGs. Heading paths are complete compositions. Body text remains text
for arbitrary repository names and descriptions; plain-text links supplement the
image cards in README. Day counts and levels are never altered for decoration.
"""
from __future__ import annotations
import hashlib
import html
import json
import math
import random
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from . import data

ROOT=Path(__file__).resolve().parents[2]
THEMES={
 'light':dict(paper='#ffffff',ink='#101010',secondary='#444444',faint='#bcbcbc',tone='#eeeeee',deep='#181818'),
 'dark':dict(paper='#fafafa',ink='#101010',secondary='#444444',faint='#b4b4b4',tone='#eeeeee',deep='#101010')}

def esc(text): return html.escape(str(text if text is not None else ''),quote=True)
def n(value): return f'{float(value):.3f}'.rstrip('0').rstrip('.') or '0'
def place(x,y,art,scale=1,rotate=0):
    return f'<g transform="translate({n(x)} {n(y)}) rotate({n(rotate)}) scale({n(scale)})">{art}</g>'

# Line weights are set for how GitHub actually shows each image: the README
# column is about 830 CSS px wide on desktop and about 358 on a phone, so a
# 960-unit drawing is shown at ~0.86 and a 480-unit one at ~0.75. Every stroke
# asks for a weight on screen, and `k` is the drawing's cumulative scale there
# (display scale x any place() scale), so nested flowers keep the same nibs.
SHOWN_WIDTH={960:830,480:358}
NIB={'contour':1.6,'inner':1.1,'detail':.85}

def shown(doc):
    """Design units -> CSS px when the README displays this image."""
    return SHOWN_WIDTH.get(doc.width,830)/doc.width

def nib(k,tier,size=1):
    """Stroke width (design units) that renders at the tier's weight at scale k.

    `size` (0.6-1) lightens the nib for drawings only a few dozen pixels
    across, where full-weight contours would close up into solid black.
    """
    return NIB[tier]/k*size

def taper(extent,full):
    """Nib factor for a drawing `extent` px across on screen: full weight from `full` px up."""
    return min(1,max(.6,extent/full))

# Screentone in screen px: (pitch, dot radius), tilted 45 degrees like printed tone.
TONES={'dense-dots':(3.4,.95),'dots':(6.2,.6),'fine-dots':(4.2,.72),'pale-dots':(4.6,.75)}
HATCH=(4.4,.8)

def tone(doc,name,k,ink=None):
    """A screentone pattern sized for scale k, defined once per document."""
    made=doc.__dict__.setdefault('_tones',set())
    pid=f'{name}-{round(k*1000)}'+(f'-{ink[1:].lower()}' if ink else '')
    if pid not in made:
        made.add(pid);i=ink or doc.pal['ink']
        if name.endswith('hatch'):
            pitch,width=HATCH;angle=-32 if name=='edge-hatch' else 32
            doc.defs.append(f'<pattern id="{pid}" width="{n(pitch/k)}" height="{n(pitch/k)}" patternUnits="userSpaceOnUse" '
                            f'patternTransform="rotate({angle})"><path d="M0 0V{n(pitch/k)}" stroke="{i}" stroke-width="{n(width/k)}"/></pattern>')
        else:
            pitch,r=TONES[name];c=pitch/2/k
            doc.defs.append(f'<pattern id="{pid}" width="{n(pitch/k)}" height="{n(pitch/k)}" patternUnits="userSpaceOnUse" '
                            f'patternTransform="rotate(45)"><circle cx="{n(c)}" cy="{n(c)}" r="{n(r/k)}" fill="{i}"/></pattern>')
    return f'url(#{pid})'

class Doc:
    def __init__(self,width,height,title='',desc='',theme='light'):
        self.width,self.height,self.title,self.desc=width,height,title,desc
        self.pal=THEMES[theme];self.theme=theme;self.parts=[];self.defs=[];self.serial=0
        # Screentones are added by tone() at the scale each drawing is shown.
    def add(self,s): self.parts.append(s)
    def uid(self,prefix='shape'):
        self.serial+=1;return f'{prefix}-{self.serial}'
    def render(self,animated=True):
        # Intentionally quiet: the video is the only continuously moving visual.
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{esc(self.title)}</title><desc id="desc">{esc(self.desc)}</desc>'
            '<style>text{font-kerning:normal} @media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>'
            f'<defs>{"".join(self.defs)}</defs><g data-edition="ink-v2" stroke-linecap="round" stroke-linejoin="round">'+''.join(self.parts)+'</g></svg>')

def text(doc,label,x,y,size=16,face='sans',weight=400,fill=None,anchor='start',spacing=0,italic=False):
    family={'sans':'Arial, Helvetica, sans-serif','serif':'Georgia, Times New Roman, serif','cjk':'Noto Serif CJK JP, Yu Mincho, Songti SC, serif','mono':'Menlo, Consolas, monospace'}[face]
    return (f'<text x="{n(x)}" y="{n(y)}" font-family="{family}" font-size="{n(size)}" font-weight="{weight}" '
            f'fill="{fill or doc.pal["ink"]}" text-anchor="{anchor}" letter-spacing="{n(spacing)}"'
            +(f' font-style="italic"' if italic else '')+f'>{esc(label)}</text>')

@lru_cache(maxsize=1)
def lettering():
    return json.loads(Path(__file__).with_name('manga_lettering.json').read_text(encoding='utf-8'))

def title(doc,label,x,y,size=48,max_width=None,fill=None):
    composition=lettering().get(label)
    if not composition:
        return text(doc,label,x,y,min(size, max_width / max(1,len(label)*.63)) if max_width else size,'serif',weight=600,fill=fill)
    scale=size/composition['units']
    if max_width:scale=min(scale,max_width/composition['advance'])
    return (f'<g role="img" aria-label="{esc(label)}" transform="translate({n(x)} {n(y)}) scale({n(scale)} {n(-scale)})" fill="{fill or doc.pal["ink"]}">'
            f'<path d="{composition["path"]}"/></g>')

def text_width(s,size):
    """Conservative layout estimate; long labels also have full accessible alternatives."""
    total=0
    for c in str(s):
        if unicodedata.east_asian_width(c) in ('W','F'): factor=1
        elif c in 'ilI.,:;!\'| ':factor=.29
        elif c in 'MW@#%&':factor=.88
        elif c.isupper():factor=.71
        else:factor=.56
        total+=factor*size
    return total

def fit(s,size,width):
    s=' '.join(str(s or '').split())
    if text_width(s,size)<=width:return s
    while s and text_width(s+'…',size)>width:s=s[:-1]
    return s.rstrip()+'…'

def wrap(s,size,width,lines=2):
    s=' '.join(str(s or '').split());out=[]
    while s and len(out)<lines:
        if text_width(s,size)<=width:out.append(s);break
        i=1
        while i<len(s) and text_width(s[:i+1],size)<=width:i+=1
        # Prefer whitespace, but support long slugs and unspaced CJK.
        cut=s.rfind(' ',0,i+1)
        if cut<i*.55:cut=i
        if len(out)==lines-1:out.append(fit(s,size,width));break
        out.append(s[:cut].strip());s=s[cut:].lstrip()
    return out

def line(doc,x1,y1,x2,y2,width=1,ink=None):
    return f'<path d="M{n(x1)} {n(y1)}L{n(x2)} {n(y2)}" fill="none" stroke="{ink or doc.pal["ink"]}" stroke-width="{n(width)}"/>'

def panel(doc):
    """A sheet of black ink on white paper in both display themes."""
    w,h=doc.width,doc.height;p=doc.pal;k=shown(doc)
    doc.add(f'<rect width="{w}" height="{h}" fill="{p["paper"]}"/>')
    doc.add(f'<path d="M12 10H{w-13}L{w-10} {h-13}H11Z" fill="none" stroke="{p["ink"]}" stroke-width="{n(nib(k,"contour"))}"/>')
    doc.add(f'<path d="M18 16H{w-20}M18 16V{h-21}M{w-20} 22V{h-21}H23" fill="none" stroke="{p["ink"]}" stroke-width="{n(nib(k,"detail"))}"/>')
    # Unequal nib weight, rather than a blurred or extruded card shadow.
    doc.add(f'<path d="M11 9H{min(103,w-30)}V13H11ZM{w-13} {h-98}L{w-9} {h-13}H{w-13}Z" fill="{p["ink"]}"/>')

def petal_leaf(doc,length=34,width=10,black=False,k=1):
    """A leaf whose vein count follows its size on screen: small leaves stay clean."""
    p=doc.pal;i=p['ink'];a=p['paper'];shown_len=length*k;m=taper(shown_len,30)
    shape=f'M0 0C{-width*1.1} {-length*.29} {-width*.93} {-length*.63} 3 {-length}C{width*1.11} {-length*.68} {width} {-length*.28} 0 0Z'
    out=f'<path d="{shape}" fill="{i if black else a}" stroke="{i}" stroke-width="{n(nib(k,"contour" if shown_len>=18 else "inner",m))}"/>'
    vein=a if black else i
    if shown_len>=12:
        out+=f'<path d="M0-1Q4 {-length*.63} 3 {-length*.94}" fill="none" stroke="{vein}" stroke-width="{n(nib(k,"detail"))}"/>'
    pairs=6 if shown_len>=44 else 4 if shown_len>=30 else 2 if shown_len>=18 else 0
    for j in range(pairs):
        y=-length*(.21+j*.6/max(1,pairs-1)) if pairs>1 else -length*.5
        for side in [-1,1]:
            out+=f'<path d="M2 {n(y)}Q{n(side*width*.39)} {n(y-length*.09)} {n(side*width*.65)} {n(y-length*.16)}" fill="none" stroke="{vein}" stroke-width="{n(nib(k,"detail"))}"/>'
    if not black:
        out+=f'<path d="M0 0Q{-width*.5} {-length*.29} {-width*.35} {-length*.49}Q1 {-length*.27} 0 0Z" fill="{i}"/>'
    return out

def blossom(doc,radius=46,seed=1,kind='rose',k=1):
    """Layered nib-drawn petals, hard ink folds and screentone, never lighting.

    Detail follows the flower's size on screen: a large head gets every fold
    and striation, a small one keeps only its silhouette, ink crescents and
    tone, so it reads as a flower instead of a grey smudge.
    """
    rng=random.Random(seed);p=doc.pal;out=[];shown_r=radius*k;m=taper(shown_r,22)
    rows=[(5,1,0)] if kind=='sakura' else [(8,1,0),(7,.71,.27),(5,.44,-.19)]
    rows=rows[:1 if shown_r<10 else 2 if shown_r<16 else 3]
    lines=0 if shown_r<14 else 3 if shown_r<24 else 5 if shown_r<34 else 7
    for row,(num,scale,phase) in enumerate(rows):
        for j_petal in range(num):
            a=360*j_petal/num+phase*180/math.pi+rng.uniform(-7,7)
            r=radius*scale*rng.uniform(.88,1.08);w=r*(.51 if row==0 else .56)
            shape=(f'M-1 {n(-r*.12)}C{n(-w*.75)} {n(-r*.19)} {n(-w*1.26)} {n(-r*.61)} {n(-w*.88)} {n(-r*.84)}'
                   f'C{n(-w*.58)} {n(-r*1.06)} {n(-w*.14)} {n(-r*1.08)} {n(w*.05)} {n(-r*.94)}'
                   f'C{n(w*.45)} {n(-r*1.16)} {n(w*1.16)} {n(-r*.95)} {n(w*1.03)} {n(-r*.67)}'
                   f'C{n(w*.96)} {n(-r*.36)} {n(w*.32)} {n(-r*.18)} -1 {n(-r*.12)}Z')
            shade=(f'M-1 {n(-r*.12)}Q{n(-w*.98)} {n(-r*.52)} {n(-w*.72)} {n(-r*.85)}'
                   f'Q{n(-w*.20)} {n(-r*.58)} -1 {n(-r*.12)}Z')
            segment=f'<path d="{shape}" fill="{p["paper"]}" stroke="{p["ink"]}" stroke-width="{n(nib(k,"contour" if row==0 else "inner",m))}"/>'
            if shown_r>=10:
                segment+=f'<path d="{shade}" fill="{tone(doc,"fine-dots",k)}"/>'
            # Tapered black crescent follows the hidden petal edge.
            segment+=(f'<path d="M-1 {n(-r*.12)}Q{n(-w*.87)} {n(-r*.45)} {n(-w*.81)} {n(-r*.77)}'
                      f'Q{n(-w*.54)} {n(-r*.44)} {n(-w*.19)} {n(-r*.37)}L-1 {n(-r*.12)}Z" fill="{p["ink"]}"/>')
            for j in range(lines):
                t=(j+.5)/lines*7-.5
                xx=(-.33+t*.12)*w;end=-r*(.42+.12*math.sin(t*.8+row)+rng.random()*.08)
                segment+=(f'<path d="M{n(xx*.19)} {n(-r*.24)}Q{n(xx*.78)} {n(-r*.37)} {n(xx)} {n(end)}" '
                          f'fill="none" stroke="{p["ink"]}" stroke-width="{n(nib(k,"detail"))}"/>')
            if shown_r>=14:
                segment+=f'<path d="M{n(-w*.61)} {n(-r*.85)}Q{n(-w*.3)} {n(-r*.97)} {n(w*.04)} {n(-r*.86)}" fill="none" stroke="{p["ink"]}" stroke-width="{n(nib(k,"detail"))}"/>'
            out.append(f'<g transform="rotate({n(a)})">{segment}</g>')
    rr=radius*.18
    out.append(f'<path d="M{n(-rr)} 2C{n(-rr)} {n(-rr)} {n(rr)} {n(-rr)} {n(rr)} 0C{n(rr)} {n(rr)} {n(-rr*.7)} {n(rr)} {n(-rr*.6)} 0Q0 {n(-rr*.7)} {n(rr*.5)} 0Q0 {n(rr*.4)} 0 0" fill="{p["paper"]}" stroke="{p["ink"]}" stroke-width="{n(nib(k,"inner",m))}"/>')
    return ''.join(out)

def sprig(doc,variant=0,k=1):
    p=doc.pal;out=[]
    stems=['M-118 73C-48 84 32 24 62-56','M-21 58C25 52 75 57 98 22','M-73 73C-36 47-55 15-69-3','M30 13C4-6 6-47-12-68']
    for d in stems:
        out.append(f'<path d="{d}" fill="none" stroke="{p["ink"]}" stroke-width="{n(nib(k,"contour",taper(240*k,170)))}"/>')
    for x,y,l,w,a,black in [(-91,75,37,9,-62,1),(-59,65,45,12,43,0),(-38,64,32,8,70,1),(-44,26,34,9,-47,0),(18,36,42,10,-56,1),(52,-20,36,10,64,0),(59,54,34,9,129,1),(70,44,31,8,65,0),(7,-26,32,9,-38,1),(92,29,27,8,70,1)]:
        out.append(place(x,y,petal_leaf(doc,l,w,bool(black),k),rotate=a))
    out.append(place(-68,-6,blossom(doc,29,21+variant,'sakura',k),rotate=-27))
    out.append(place(66,-42,blossom(doc,35,13+variant,k=k),rotate=13))
    out.append(place(14,12,blossom(doc,51,4+variant,k=k),rotate=-14))
    out.append(place(99,17,blossom(doc,24,31+variant,'sakura',k),rotate=21))
    return ''.join(out)

def sparkle(doc,x,y,r=5):
    return f'<path d="M{n(x-r)} {n(y)}Q{n(x)} {n(y)} {n(x)} {n(y-r*1.8)}Q{n(x)} {n(y)} {n(x+r)} {n(y)}Q{n(x)} {n(y)} {n(x)} {n(y+r*1.8)}Q{n(x)} {n(y)} {n(x-r)} {n(y)}Z" fill="{doc.pal["ink"]}"/>'

def header(theme,section,index,mobile=False):
    w,h=(480,150) if mobile else (960,176);p=THEMES[theme]
    doc=Doc(w,h,section['title'].title(),section.get('subtitle',''),theme);k=shown(doc)
    doc.add(f'<rect width="{w}" height="{h}" fill="{p["paper"]}"/>')
    # A narrow black panel and white diamond numbering pair with the hair-like ink masses.
    doc.add(f'<path d="M16 21H{90 if not mobile else 60}V{120 if not mobile else 108}H16Z" fill="{p["ink"]}"/>')
    center=53 if not mobile else 38
    doc.add(text(doc,section['number'],center,70 if not mobile else 64,31 if not mobile else 23,'serif',fill=p['paper'],anchor='middle',italic=True))
    doc.add(text(doc,'CH.',center,94 if not mobile else 85,9,'sans',fill=p['paper'],anchor='middle',spacing=2))
    x=114 if not mobile else 77
    doc.add(text(doc,'INK & PETALS / A MANGA JOURNAL' if not mobile else 'INK & PETALS',x,33,10 if not mobile else 9,spacing=2))
    doc.add(title(doc,section['title'].title(),x,100 if not mobile else 88,75 if not mobile else 47,max_width=520 if not mobile else 286))
    doc.add(text(doc,section.get('title_ja',''),x,134 if not mobile else 115,18 if not mobile else 15,'cjk',spacing=4))
    if not mobile:
        doc.add(text(doc,section.get('subtitle','').lower(),x+122,134,14,'serif',italic=True,fill=p['secondary']))
        doc.add(f'<path d="M685 14H944V150H721Z" fill="{tone(doc,"dots",k)}"/>')
        doc.add(place(814,93,sprig(doc,index,k*.91),scale=.91))
    else:
        doc.add(f'<path d="M365 17H470V129H389Z" fill="{tone(doc,"dots",k)}"/>')
        doc.add(place(427,70,sprig(doc,index,k*.4),scale=.4))
    doc.add(line(doc,16,h-17,w-16,h-17,nib(k,"contour")));doc.add(line(doc,16,h-13,w-16,h-13,nib(k,"detail")))
    return doc

def small_flower(doc,level,k=1):
    p=doc.pal;thin=n(nib(k,"detail"))
    if level==0:return f'<circle r="1.75" fill="none" stroke="{p["faint"]}" stroke-width="{thin}"/>'
    r=[0,3.1,4,5.1,6.1][level];parts=[]
    for i in range(5):
        fill=p['paper'] if level==1 else (tone(doc,"fine-dots",k) if level==2 else p['ink'])
        parts.append(f'<ellipse cx="0" cy="{n(-r*.56)}" rx="{n(r*.43)}" ry="{n(r*.64)}" transform="rotate({i*72})" fill="{fill}" stroke="{p["ink"]}" stroke-width="{thin}"/>')
    parts.append(f'<circle r="{n(r*.23)}" fill="{p["ink"] if level<3 else p["paper"]}"/>')
    if level==4:parts.append(f'<circle r=".7" fill="{p["ink"]}"/>')
    return ''.join(parts)

def calendar_card(theme,snap,mobile=False):
    days=data.days_from(snap);cols=data.week_columns(days);p=THEMES[theme]
    chunk_size=26 if mobile else max(1,len(cols))
    chunks=[cols[i:i+chunk_size] for i in range(0,len(cols),chunk_size)] or [[]]
    # A normal year takes three strips only when it has 53+ weeks: use 27 to keep two bands.
    if mobile:
        chunk_size=math.ceil(len(cols)/2) if cols else 1
        chunks=[cols[i:i+chunk_size] for i in range(0,len(cols),chunk_size)] or [[]]
    w=480 if mobile else 960;h=624 if mobile else 428
    doc=Doc(w,h,'Bloom calendar',f'{snap["calendar"]["total"]} contributions; one mark for every date. GitHub levels are represented by increasing ink coverage, not by a new score.',theme)
    panel(doc);k=shown(doc)
    tx=27 if mobile else 38
    doc.add(title(doc,'Bloom Calendar',tx,57,42 if mobile else 46,max_width=w-110))
    doc.add(text(doc,'花暦',w-37,50,17,'cjk',anchor='end',spacing=3))
    doc.add(line(doc,tx,75,w-38,75,nib(k,"inner")))
    longest,current=data.streaks(days);best=max(days,key=lambda d:d.count) if days else None
    items=[(f'{snap["calendar"]["total"]:,}','CONTRIBUTIONS'),(str(longest),'LONGEST / DAYS'),(str(current),'CURRENT / DAYS'),(best.date.strftime('%m.%d') if best and best.count else '—','BEST DAY')]
    for i,(v,caption) in enumerate(items):
        x=(29+(i%2)*218) if mobile else 39+i*228
        y=(120+(i//2)*72) if mobile else 136
        doc.add(text(doc,v,x,y,37 if mobile else 44,'serif',italic=True))
        doc.add(text(doc,caption,x,y+23,11 if mobile else 12,spacing=1,fill=p['secondary']))
        if not mobile and i:doc.add(line(doc,x-23,100,x-23,159,nib(k,"detail"),ink=p['faint']))
    start_y=275 if mobile else 224
    sx=14.65 if mobile else min(16.1,850/max(1,len(cols)-1));sy=16.5 if mobile else 17
    x0=50 if mobile else 63
    for band,group in enumerate(chunks):
        y0=start_y+band*161
        for row,label in [(1,'M'),(3,'W'),(5,'F')]:doc.add(text(doc,label,x0-19,y0+row*sy+4,10,fill=p['secondary']))
        last_month_x=-100
        for c,column in enumerate(group):
            for row,day in enumerate(column):
                if day is None:continue
                x=x0+c*sx;y=y0+row*sy
                if day.date.day==1 or (c==0 and row==next((j for j,a in enumerate(column) if a),0)):
                    if x-last_month_x>29:
                        doc.add(text(doc,day.date.strftime('%b').upper(),x-3,y0-19,9 if mobile else 10,fill=p['secondary']));last_month_x=x
                mark=small_flower(doc,min(4,max(0,int(day.level))),k)
                doc.add(f'<g data-date="{day.date.isoformat()}" data-count="{day.count}" data-level="{day.level}" transform="translate({n(x)} {n(y)})"><title>{day.date.isoformat()}: {day.count} contributions</title>{mark}</g>')
        if mobile and band<len(chunks)-1:doc.add(line(doc,29,y0+125,w-36,y0+125,nib(k,"detail"),ink=p['faint']))
    legend_y=555 if mobile else 363
    doc.add(text(doc,'LESS',tx,legend_y+3,10,spacing=1,fill=p['secondary']))
    for level in range(5):doc.add(place(tx+60+level*20,legend_y,small_flower(doc,level,k)))
    doc.add(text(doc,'MORE',tx+169,legend_y+3,10,spacing=1,fill=p['secondary']))
    rng=f'{days[0].date.isoformat()} — {days[-1].date.isoformat()}' if days else 'No contribution data'
    doc.add(text(doc,rng,tx,583 if mobile else 397,11,fill=p['secondary']))
    if not mobile:
        doc.add(text(doc,'ONE DAY, ONE FLOWER.',w-39,369,12,anchor='end',spacing=2))
        doc.add(text(doc,'一日一輪',w-39,398,16,'cjk',anchor='end',spacing=6))
    return doc

def bouquet_card(theme,snap,mobile=False):
    w=480 if mobile else 960;h=807 if mobile else 574;p=THEMES[theme]
    vals=sorted([(str(k),max(0,int(v))) for k,v in snap.get('languages',{}).items()],key=lambda z:(-z[1],z[0]))
    vals=[v for v in vals if v[1]];total=sum(v for _,v in vals)
    if len(vals)>6:vals=vals[:5]+[('Other',sum(v for _,v in vals[5:]))]
    doc=Doc(w,h,'Language bouquet','Language shares by code bytes in public, non-fork repositories. '+'; '.join(f'{k}: {v} bytes' for k,v in vals),theme)
    panel(doc);k=shown(doc)
    doc.add(title(doc,'Language Bouquet',29 if mobile else 38,68,46 if mobile else 56,max_width=419 if mobile else 665))
    if not mobile:doc.add(text(doc,'言語の花束',w-42,58,19,'cjk',anchor='end',spacing=3))
    doc.add(line(doc,30,86,w-34,86,nib(k,"inner")))
    if mobile:
        doc.add(f'<path d="M28 104H451V342H28Z" fill="{tone(doc,"dots",k)}"/>')
        doc.add(f'<path d="M160 97H370L315 345H128Z" fill="{p["paper"]}"/>')
        doc.add(place(130,68,bouquet_art(doc,k*.655),scale=.655))
        doc.add(text(doc,'INK',44,151,22,'serif',italic=True))
        doc.add(text(doc,'& PETALS',44,173,11,spacing=1))
        doc.add(text(doc,f'{len(vals):02d}',422,295,37,'serif',italic=True,anchor='end'))
        doc.add(text(doc,'LANGUAGES',425,316,8,anchor='end',spacing=.6))
        x,right,y,gap=46,435,388,59
    else:
        doc.add(f'<path d="M29 104H327V531H29Z" fill="{tone(doc,"dots",k)}"/>')
        doc.add(f'<path d="M127 97H266L287 535H74Z" fill="{p["paper"]}"/>')
        doc.add(place(32,103,bouquet_art(doc,k*.91),scale=.91))
        doc.add(text(doc,'gathered in ink',175,529,22,'serif',italic=True,anchor='middle'))
        doc.add(line(doc,344,112,344,523,nib(k,"detail")))
        x,right,y,gap=387,912,145,64
    patterns=[p['ink'],tone(doc,"hatch",k),tone(doc,"dense-dots",k),tone(doc,"dots",k),tone(doc,"fine-dots",k),p['ink']]
    for j,(name,value) in enumerate(vals):
        share=value/total if total else 0
        doc.add(place(x-18,y-6,small_flower(doc,4 if j==0 else 1,k*.8),scale=.8))
        doc.add(text(doc,fit(name,19 if mobile else 22,right-x-86),x,y,19 if mobile else 22,weight=600))
        doc.add(text(doc,f'{share*100:.1f}%',right,y+1,26 if mobile else 29,'serif',italic=True,anchor='end'))
        bw=right-x;by=y+15
        doc.add(f'<rect x="{x}" y="{n(by)}" width="{bw}" height="9" fill="{p["paper"]}" stroke="{p["ink"]}" stroke-width="{n(nib(k,"inner"))}"/>')
        doc.add(f'<rect data-language="{esc(name)}" data-bytes="{value}" data-share="{n(share)}" x="{x}" y="{n(by)}" width="{n(bw*share)}" height="9" fill="{patterns[j%6]}"/>')
        y+=gap
    if not vals:doc.add(text(doc,'No public code yet',x,y+30,21,'serif',italic=True))
    doc.add(text(doc,'PUBLIC / NON-FORK REPOSITORIES / BY CODE BYTES',30 if mobile else 387,h-31,9.5 if mobile else 11,spacing=.4))
    return doc

def notes_card(theme,snap,notes,tz_name,mobile=False):
    w=480 if mobile else 960;h=657 if mobile else 603;p=THEMES[theme]
    doc=Doc(w,h,'Garden notes','Recent public activity. '+('; '.join(f'{e["local"].isoformat()} {e["text"]} / {e["repo"]}' for e in notes) or 'No events in the last 30 days.'),theme)
    panel(doc);k=shown(doc)
    doc.add(title(doc,'Garden Notes',30 if mobile else 38,68,47 if mobile else 56,max_width=w-139))
    doc.add(text(doc,'花便り',w-38,60,18,'cjk',anchor='end',spacing=2))
    doc.add(line(doc,30,86,w-34,86,nib(k,"inner")))
    x=116 if mobile else 192;bx=x-12;y=128;step=97 if mobile else 86
    for j,note in enumerate(notes[:5]):
        stamp=note['local'].strftime('%m.%d');clock=note['local'].strftime('%H:%M')
        doc.add(text(doc,stamp,32 if mobile else 44,y+10,19 if mobile else 25,'serif',italic=True))
        doc.add(text(doc,clock,33 if mobile else 46,y+33,11 if mobile else 13))
        # Pen-drawn stem connects ink flowers in the gutter outside the caption boxes.
        cx=88 if mobile else 144
        if j<len(notes[:5])-1:
            doc.add(f'<path d="M{cx} {y+10}Q{cx+7} {y+43} {cx} {y+step-9}" fill="none" stroke="{p["ink"]}" stroke-width="{n(nib(k,"inner"))}"/>')
            doc.add(place(cx+1,y+48,petal_leaf(doc,25,6,j%2==0,k),rotate=50 if j%2 else -47))
        doc.add(place(cx,y,blossom(doc,10 if mobile else 13,j+290,'sakura',k)))
        top=y-17;bottom=y+57 if mobile else y+52;right=w-35
        d=f'M{bx} {top}H{right}V{bottom}H{bx}V{y+14}L{bx-8} {y+7}L{bx} {y+4}Z'
        doc.add(f'<path d="{d}" fill="{p["paper"]}" stroke="{p["ink"]}" stroke-width="{n(nib(k,"contour" if j==0 else "inner"))}"/>')
        doc.add(f'<path d="M{right-34} {top+1}H{right-1}V{top+31}Z" fill="{tone(doc,"fine-dots",k)}"/>')
        doc.add(text(doc,fit(note['text'],17 if mobile else 21,right-x-26),x+2,y+7,17 if mobile else 21,weight=600))
        name=note['repo'];prefix=snap.get('user','')+'/'
        if name.startswith(prefix):name=name[len(prefix):]
        doc.add(text(doc,fit(name,13 if mobile else 16,right-x-23),x+2,y+32,13 if mobile else 16,'serif'))
        y+=step
    if not notes:
        doc.add(place(w/2,245,blossom(doc,62,311,k=k)))
        doc.add(text(doc,'The garden is resting.',w/2,358,27,'serif',italic=True,anchor='middle'))
    doc.add(text(doc,f'LAST 30 DAYS / {tz_name.upper()}',32 if mobile else 42,h-31,10 if mobile else 11,spacing=.8))
    return doc

def little_architecture(doc,k=1):
    p=doc.pal;i=p['ink'];a=p['paper'];out=[]
    # Original tiny ink vignette; no image or model from the independent site is modified.
    out.append(f'<rect x="0" y="0" width="290" height="215" fill="{tone(doc,"dots",k)}"/>')
    out.append(f'<circle cx="211" cy="39" r="24" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"inner"))}"/>')
    out.append(f'<path d="M21 190L133 118L271 171L158 211Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"contour"))}"/>')
    out.append(f'<path d="M61 141L117 110L174 143L117 176Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"contour"))}"/>')
    out.append(f'<path d="M61 141V172L117 203V176Z" fill="{tone(doc,"hatch",k)}" stroke="{i}" stroke-width="{n(nib(k,"contour"))}"/>')
    out.append(f'<path d="M117 176L174 143V174L117 203Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"contour"))}"/>')
    out.append(f'<path d="M94 119V56L129 35L164 55V120L129 141Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"contour"))}"/>')
    out.append(f'<path d="M94 56L129 76V141L94 120Z" fill="{tone(doc,"hatch",k)}" stroke="{i}" stroke-width="{n(nib(k,"inner"))}"/>')
    out.append(f'<path d="M94 56L129 35L164 55L129 76Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"inner"))}"/>')
    out.append(f'<path d="M137 125V93C137 78 155 68 155 84V115Z" fill="{i}"/>')
    out.append(f'<path d="M115 47V24L129 9L145 23V47L129 56Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"contour"))}"/>')
    out.append(f'<path d="M115 24L129 9L145 23L129 32Z" fill="{i}"/>')
    # Readable stair treads instead of extra decorative towers.
    for j in range(9):
        xx=172+j*5;yy=136+j*4
        out.append(f'<path d="M{xx} {yy}l22-13v5l-22 13Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"detail"))}"/>')
    out.append(sparkle(doc,45,55,5));out.append(sparkle(doc,243,114,4))
    return ''.join(out)

def book_vignette(doc,k=1):
    p=doc.pal;i=p['ink'];a=p['paper']
    s=f'<rect width="290" height="215" fill="{tone(doc,"dots",k)}"/>'
    s+=f'<path d="M29 165Q80 123 143 158Q200 120 260 160L251 187Q196 154 143 183Q88 155 33 190Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"contour"))}"/>'
    s+=f'<path d="M36 150Q83 111 143 154Q195 112 253 147L246 176Q190 144 143 176Q86 145 36 180Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"inner"))}"/>'
    s+=line(doc,143,155,143,177,nib(k,"inner"))
    for y in [141,147,154,161]:s+=f'<path d="M53 {y}Q94 {y-18} 127 {y+9}M160 {y+9}Q194 {y-18} 236 {y}" fill="none" stroke="{i}" stroke-width="{n(nib(k,"detail"))}"/>'
    s+=place(138,89,sprig(doc,27,k*.58),scale=.58,rotate=12)
    for x,y in [(46,57),(241,68)]:s+=sparkle(doc,x,y,5)
    return s

def repo_card(theme,repo,index,mobile=False):
    w=480 if mobile else 960;h=347 if mobile else 264;p=THEMES[theme]
    name=str(repo.get('name','Repository'));desc=str(repo.get('description') or 'No description provided.');lang=repo.get('language') or '—'
    aliases={'kelvint0714-arch.github.io':'A Quiet Valley','ML-practice':'Machine Learning'}
    label=aliases.get(name,'Repository')
    stamp=(repo.get('pushed_at') or '—')[:10];stars=repo.get('stargazers_count') or 0
    flags=' / '.join(x for x in ['PUBLIC','FORK' if repo.get('fork') else '', 'ARCHIVED' if repo.get('archived') else ''] if x)
    doc=Doc(w,h,name,f'{desc} Language: {lang}. {stars} stars. Updated {stamp}. {flags}.',theme)
    panel(doc);k=shown(doc)
    x=27 if mobile else 35
    doc.add(text(doc,f'{index+1:02d} / {flags}',x,35,10 if mobile else 12,spacing=1.7,fill=p['secondary']))
    doc.add(title(doc,label,x,94 if mobile else 109,55 if mobile else 62,max_width=420 if mobile else 582))
    doc.add(text(doc,fit(name,14 if mobile else 17,421 if mobile else 595),x,126 if mobile else 144,14 if mobile else 17,'mono',fill=p['secondary']))
    # Preserve original descriptions verbatim in accessible text; wrap in the drawing.
    for j,row in enumerate(wrap(desc,17 if mobile else 18,420 if mobile else 585,3 if mobile else 2)):
        doc.add(text(doc,row,x,165+j*23 if mobile else 176+j*23,17 if mobile else 18,'serif'))
    y=259 if mobile else 221
    doc.add(line(doc,x,y-13,439 if mobile else 616,y-13,nib(k,"detail"),ink=p['faint']))
    doc.add(text(doc,lang,x,y+9,13 if mobile else 14,weight=600))
    doc.add(text(doc,f'☆ {stars}',242 if mobile else 285,y+9,14))
    doc.add(text(doc,stamp,439 if mobile else 616,y+9,11 if mobile else 12,anchor='end',fill=p['secondary']))
    if mobile:
        doc.add(text(doc,'OPEN REPOSITORY',x,315,11,spacing=1.4))
        doc.add(line(doc,388,310,438,310,nib(k,"inner")));doc.add(f'<path d="M431 304L438 310L431 316" fill="none" stroke="{p["ink"]}" stroke-width="{n(nib(k,"inner"))}"/>')
    else:
        drawing=little_architecture(doc,k) if name.endswith('.github.io') else book_vignette(doc,k)
        doc.add(place(643,19,drawing,scale=1))
        doc.add(f'<path d="M639 17L640 241" stroke="{p["ink"]}" stroke-width="{n(nib(k,"contour"))}"/>')
        doc.add(f'<rect x="824" y="210" width="103" height="25" fill="{p["paper"]}" stroke="{p["ink"]}" stroke-width="{n(nib(k,"inner"))}"/>')
        doc.add(text(doc,'OPEN  →',875,227,11,anchor='middle',spacing=1.1))
    return doc

def repo_slug(repo):
    name=str(repo.get('name','repo'))
    slug=re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')[:70] or 'repo'
    return f'{slug}-{hashlib.sha256(name.encode()).hexdigest()[:7]}'

def picture(base,alt,width='100%',href=None):
    """Real HTML link wraps each image: SVG-image hyperlinks are not relied upon."""
    s=(f'<picture>\n'
       f'  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="{esc(base)}-dark-mobile.svg" />\n'
       f'  <source media="(max-width: 600px)" srcset="{esc(base)}-light-mobile.svg" />\n'
       f'  <source media="(prefers-color-scheme: dark)" srcset="{esc(base)}-dark.svg" />\n'
       f'  <img src="{esc(base)}-light.svg" width="{width}" alt="{esc(alt)}" />\n</picture>')
    return f'<a href="{esc(href)}">\n{s}\n</a>' if href else s


def bouquet_art(doc,k=1):
    """An original flower arrangement, drawn as solid ink, contours and dots."""
    p=doc.pal;i=p['ink'];a=p['paper'];out=[]
    stems=['M171 351C137 278 92 176 62 135','M172 351C207 266 223 178 198 83','M171 352C216 280 271 218 276 179','M171 353C120 312 85 282 52 253','M171 355C200 315 255 310 259 274','M170 355C153 278 126 228 126 204']
    for d in stems:
        out.append(f'<path d="{d}" fill="none" stroke="{i}" stroke-width="{n(nib(k,"contour")*1.25)}"/>')
    for x,y,l,w,angle,black in [(169,330,70,15,-60,1),(183,317,83,21,59,1),(141,280,61,14,-52,0),(199,254,57,17,54,1),(224,221,48,12,57,0),(115,239,56,16,-76,1),(83,188,49,12,-42,1),(212,150,62,17,47,1),(152,308,44,11,30,0),(226,316,45,13,50,1),(95,291,54,12,-67,1)]:
        out.append(place(x,y,petal_leaf(doc,l,w,bool(black),k),rotate=angle))
    for x,y,r,seed,kind,angle in [(62,135,39,151,'rose',-15),(276,179,33,143,'sakura',20),(52,253,24,16,'sakura',-12),(259,274,30,125,'sakura',-16),(198,83,60,72,'rose',16),(126,204,42,192,'rose',-5)]:
        out.append(place(x,y,blossom(doc,r,seed,kind,k),rotate=angle))
    # A flowing black ribbon echoes the avatar's large ink masses and white hair highlights.
    out.append(f'<path d="M170 350C142 320 85 317 92 343C97 368 145 364 170 350Z" fill="{i}" stroke="{i}" stroke-width="{n(nib(k,"inner"))}"/>')
    out.append(f'<path d="M176 350C205 319 246 324 233 348C221 373 195 365 176 350Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"contour"))}"/>')
    out.append(f'<path d="M176 350C207 333 224 334 230 340C207 341 193 354 179 356Z" fill="{tone(doc,"fine-dots",k)}"/>')
    out.append(f'<path d="M168 353C162 380 148 391 135 413L151 407L162 414C163 393 186 368 178 354Z" fill="{i}"/>')
    out.append(f'<path d="M174 354C202 371 214 389 232 399L213 398L208 408C202 385 180 380 170 358Z" fill="{a}" stroke="{i}" stroke-width="{n(nib(k,"contour"))}"/>')
    out.append(f'<path d="M102 340Q131 332 163 350M103 345Q131 342 161 353M165 367Q156 392 146 401" fill="none" stroke="{a}" stroke-width="{n(nib(k,"detail"))}"/>')
    out.append(f'<path d="M185 362Q202 381 217 391" fill="none" stroke="{i}" stroke-width="{n(nib(k,"detail"))}"/>')
    out.append(f'<path d="M162 343Q174 339 182 348L179 360Q168 364 161 353Z" fill="{i}"/><path d="M168 347Q173 344 177 349" fill="none" stroke="{a}" stroke-width="{n(nib(k,"detail"))}"/>')
    return '<g data-ink-art="bouquet">'+''.join(out)+'</g>'


def footer(theme,mobile=False):
    w=480 if mobile else 960;h=108;p=THEMES[theme]
    doc=Doc(w,h,'One day, one flower.','一日一輪 / An original monochrome manga-style profile.',theme)
    doc.add(f'<rect width="{w}" height="{h}" fill="{p["paper"]}"/>')
    k=shown(doc)
    doc.add(line(doc,28,18,w-28,18,nib(k,"contour")))
    doc.add(place(54 if mobile else 255,64,blossom(doc,15,557,'sakura',k)))
    doc.add(text(doc,'one day, one flower.',w/2,63,26 if mobile else 29,'serif',italic=True,anchor='middle'))
    doc.add(text(doc,'一日一輪',w/2,88,13,'cjk',anchor='middle',spacing=5))
    doc.add(text(doc,'FIN',w-29,45,9,'serif',italic=True,anchor='end'))
    return doc

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
 'light':dict(paper='#ffffff',ink='#181818',secondary='#555555',faint='#bcbcbc',tone='#eeeeee',deep='#181818'),
 'dark':dict(paper='#171717',ink='#f1f1f1',secondary='#b9b9b9',faint='#555555',tone='#282828',deep='#080808')}

def esc(text): return html.escape(str(text if text is not None else ''),quote=True)
def n(value): return f'{float(value):.3f}'.rstrip('0').rstrip('.') or '0'
def place(x,y,art,scale=1,rotate=0):
    return f'<g transform="translate({n(x)} {n(y)}) rotate({n(rotate)}) scale({n(scale)})">{art}</g>'

class Doc:
    def __init__(self,width,height,title='',desc='',theme='light'):
        self.width,self.height,self.title,self.desc=width,height,title,desc
        self.pal=THEMES[theme];self.theme=theme;self.parts=[];self.defs=[];self.serial=0
        p=self.pal
        self.defs.extend([
          f'<pattern id="dots" width="6" height="6" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".65" fill="{p["ink"]}"/></pattern>',
          f'<pattern id="fine-dots" width="4" height="4" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".52" fill="{p["ink"]}"/></pattern>',
          f'<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(32)"><path d="M0 0V6" stroke="{p["ink"]}" stroke-width=".8"/></pattern>'
        ])
    def add(self,s): self.parts.append(s)
    def uid(self,prefix='shape'):
        self.serial+=1;return f'{prefix}-{self.serial}'
    def render(self,animated=True):
        # Intentionally quiet: the video is the only continuously moving visual.
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{esc(self.title)}</title><desc id="desc">{esc(self.desc)}</desc>'
            '<style>text{font-kerning:normal} @media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>'
            f'<defs>{"".join(self.defs)}</defs><g stroke-linecap="round" stroke-linejoin="round">'+''.join(self.parts)+'</g></svg>')

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
    w,h=doc.width,doc.height;p=doc.pal
    # Double ink rule with a small offset hatch: a printed panel, not a 3-D card.
    doc.add(f'<path d="M8 11H{w-5}V{h-7}H8Z" fill="url(#hatch)"/>')
    doc.add(f'<path d="M3 4H{w-11}V{h-14}H3Z" fill="{p["paper"]}" stroke="{p["ink"]}" stroke-width="1.55"/>')
    doc.add(f'<path d="M10 11H{w-18}V{h-21}H10Z" fill="none" stroke="{p["ink"]}" stroke-width=".42"/>')

def petal_leaf(doc,length=34,width=10,black=False):
    p=doc.pal
    shape=f'M0 0C{-width*.7} {-length*.32} {-width} {-length*.68} 2 {-length}C{width*1.18} {-length*.7} {width*.87} {-length*.21} 0 0Z'
    out=f'<path d="{shape}" fill="{p["ink"] if black else p["paper"]}" stroke="{p["ink"]}" stroke-width="1.1"/>'
    ink=p['paper'] if black else p['ink']
    out+=f'<path d="M0 0Q4 {-length*.57} 2 {-length*.95}" stroke="{ink}" stroke-width=".64" fill="none"/>'
    for i in range(1,5):
        y=-length*(.14+i*.13)
        for side in (-1,1):
            out+=f'<path d="M2 {n(y)}Q{n(side*width*.4)} {n(y-length*.035)} {n(side*width*.68)} {n(y-length*.1)}" stroke="{ink}" stroke-width=".4" fill="none"/>'
    return out

def blossom(doc,radius=46,seed=1,kind='rose'):
    """Original layered ink petals with tapered folds and curved radial hatching."""
    rng=random.Random(seed);p=doc.pal;out=[]
    if kind=='sakura':
        rows=[(5,1,0)]
    else: rows=[(8,1,.0),(6,.73,.28),(5,.48,-.12)]
    for row,(num,scale,phase) in enumerate(rows):
        for i in range(num):
            a=360*i/num+phase*180/math.pi+rng.uniform(-5,5)
            r=radius*scale*rng.uniform(.9,1.07);w=r*(.46 if row==0 else .53)
            shape=(f'M-2 {n(-r*.12)}C{n(-w*.62)} {n(-r*.18)} {n(-w*1.25)} {n(-r*.55)} {n(-w*.91)} {n(-r*.84)}'
                   f'C{n(-w*.71)} {n(-r*1.07)} {n(-w*.22)} {n(-r*1.05)} {n(w*.035)} {n(-r*.94)}'
                   f'C{n(w*.48)} {n(-r*1.14)} {n(w*1.17)} {n(-r*.96)} {n(w*1.09)} {n(-r*.7)}'
                   f'C{n(w*1.04)} {n(-r*.42)} {n(w*.55)} {n(-r*.1)} -2 {n(-r*.12)}Z')
            fill=p['paper']
            segment=f'<path d="{shape}" fill="{fill}" stroke="{p["ink"]}" stroke-width="{n(1.05 if row else 1.3)}"/>'
            # Small screentone crescent inside the petal, never a blurred drop shadow.
            shade=f'M0 {n(-r*.13)}Q{n(-w*.85)} {n(-r*.51)} {n(-w*.6)} {n(-r*.88)}Q{n(-w*.25)} {n(-r*.6)} 0 {n(-r*.13)}Z'
            segment+=f'<path d="{shade}" fill="url(#fine-dots)"/>'
            for k in range(5):
                xx=(-.5+k*.23)*w
                yy=-r*(.52+.15*math.sin(k*.6+row))
                segment+=f'<path d="M{n(xx*.19)} {n(-r*.22)}Q{n(xx*.85)} {n(-r*.43)} {n(xx)} {n(yy)}" fill="none" stroke="{p["ink"]}" stroke-width="{n(.37+.08*(k%2))}"/>'
            segment+=f'<path d="M{n(-w*.69)} {n(-r*.84)}Q{n(-w*.3)} {n(-r*.99)} {n(w*.05)} {n(-r*.85)}" fill="none" stroke="{p["ink"]}" stroke-width=".8"/>'
            # Wedge establishes line-weight at the overlapping base.
            segment+=f'<path d="M-2 {n(-r*.12)}Q{n(-w*.32)} {n(-r*.2)} {n(-w*.45)} {n(-r*.4)}Q{n(-w*.25)} {n(-r*.26)} -2 {n(-r*.12)}Z" fill="{p["ink"]}"/>'
            out.append(f'<g transform="rotate({n(a)})">{segment}</g>')
    # Irregular central folds.
    rr=radius*.2
    out.append(f'<path d="M{n(-rr)} 2C{n(-rr)} {n(-rr)} {n(rr)} {n(-rr)} {n(rr)} 0C{n(rr)} {n(rr)} {n(-rr*.7)} {n(rr)} {n(-rr*.6)} 0Q0 {n(-rr*.6)} {n(rr*.5)} 0Q0 {n(rr*.4)} 0 0" fill="{p["paper"]}" stroke="{p["ink"]}" stroke-width="1.1"/>')
    return ''.join(out)

def sprig(doc,variant=0):
    p=doc.pal;out=[]
    stems=['M-118 73C-48 84 32 24 62-56','M-21 58C25 52 75 57 98 22','M-73 73C-36 47-55 15-69-3','M30 13C4-6 6-47-12-68']
    for d in stems:
        out.append(f'<path d="{d}" fill="none" stroke="{p["ink"]}" stroke-width="1.7"/>')
    for x,y,l,w,a,black in [(-91,75,37,9,-62,1),(-59,65,45,12,43,0),(-38,64,32,8,70,1),(-44,26,34,9,-47,0),(18,36,42,10,-56,1),(52,-20,36,10,64,0),(59,54,34,9,129,1),(70,44,31,8,65,0),(7,-26,32,9,-38,1),(92,29,27,8,70,1)]:
        out.append(place(x,y,petal_leaf(doc,l,w,bool(black)),rotate=a))
    out.append(place(-68,-6,blossom(doc,29,21+variant,'sakura'),rotate=-27))
    out.append(place(66,-42,blossom(doc,35,13+variant),rotate=13))
    out.append(place(14,12,blossom(doc,51,4+variant),rotate=-14))
    out.append(place(99,17,blossom(doc,24,31+variant,'sakura'),rotate=21))
    return ''.join(out)

def sparkle(doc,x,y,r=5):
    return f'<path d="M{n(x-r)} {n(y)}Q{n(x)} {n(y)} {n(x)} {n(y-r*1.8)}Q{n(x)} {n(y)} {n(x+r)} {n(y)}Q{n(x)} {n(y)} {n(x)} {n(y+r*1.8)}Q{n(x)} {n(y)} {n(x-r)} {n(y)}Z" fill="{doc.pal["ink"]}"/>'

def header(theme,section,index,mobile=False):
    w,h=(480,150) if mobile else (960,176);p=THEMES[theme]
    doc=Doc(w,h,section['title'].title(),section.get('subtitle',''),theme)
    doc.add(f'<rect width="{w}" height="{h}" fill="{p["paper"]}"/>')
    # A narrow black panel and white diamond numbering pair with the hair-like ink masses.
    doc.add(f'<path d="M16 21H{90 if not mobile else 60}V{120 if not mobile else 108}H16Z" fill="{p["ink"]}"/>')
    center=53 if not mobile else 38
    doc.add(text(doc,section['number'],center,70 if not mobile else 64,31 if not mobile else 23,'serif',fill=p['paper'],anchor='middle',italic=True))
    doc.add(text(doc,'CH.',center,94 if not mobile else 85,9,'sans',fill=p['paper'],anchor='middle',spacing=2))
    x=114 if not mobile else 77
    doc.add(text(doc,'THE GARDEN / IN BLACK & WHITE' if not mobile else 'INK / PETALS',x,33,10 if not mobile else 9,spacing=2))
    doc.add(title(doc,section['title'].title(),x,100 if not mobile else 88,75 if not mobile else 47,max_width=520 if not mobile else 286))
    doc.add(text(doc,section.get('title_ja',''),x,134 if not mobile else 115,18 if not mobile else 15,'cjk',spacing=4))
    if not mobile:
        doc.add(text(doc,section.get('subtitle','').lower(),x+122,134,14,'serif',italic=True,fill=p['secondary']))
        doc.add(f'<path d="M685 14H944V150H721Z" fill="url(#dots)"/>')
        doc.add(place(814,93,sprig(doc,index),scale=.91))
    else:
        doc.add(f'<path d="M365 17H470V129H389Z" fill="url(#dots)"/>')
        doc.add(place(427,70,sprig(doc,index),scale=.4))
    doc.add(line(doc,16,h-17,w-16,h-17,1.3));doc.add(line(doc,16,h-13,w-16,h-13,.4))
    return doc

def small_flower(doc,level):
    p=doc.pal
    if level==0:return f'<circle r="1.75" fill="none" stroke="{p["faint"]}" stroke-width=".85"/>'
    r=[0,3.1,4,5.1,6.1][level];parts=[]
    for i in range(5):
        fill=p['paper'] if level==1 else ('url(#fine-dots)' if level==2 else p['ink'])
        parts.append(f'<ellipse cx="0" cy="{n(-r*.56)}" rx="{n(r*.43)}" ry="{n(r*.64)}" transform="rotate({i*72})" fill="{fill}" stroke="{p["ink"]}" stroke-width=".7"/>')
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
    panel(doc)
    tx=27 if mobile else 38
    doc.add(title(doc,'Bloom Calendar',tx,57,42 if mobile else 46,max_width=w-110))
    doc.add(text(doc,'花暦',w-37,50,17,'cjk',anchor='end',spacing=3))
    doc.add(line(doc,tx,75,w-38,75,1))
    longest,current=data.streaks(days);best=max(days,key=lambda d:d.count) if days else None
    items=[(f'{snap["calendar"]["total"]:,}','CONTRIBUTIONS'),(str(longest),'LONGEST / DAYS'),(str(current),'CURRENT / DAYS'),(best.date.strftime('%m.%d') if best and best.count else '—','BEST DAY')]
    for i,(v,k) in enumerate(items):
        x=(29+(i%2)*218) if mobile else 39+i*228
        y=(120+(i//2)*72) if mobile else 136
        doc.add(text(doc,v,x,y,37 if mobile else 44,'serif',italic=True))
        doc.add(text(doc,k,x,y+23,11 if mobile else 12,spacing=1,fill=p['secondary']))
        if not mobile and i:doc.add(line(doc,x-23,100,x-23,159,.6,ink=p['faint']))
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
                mark=small_flower(doc,min(4,max(0,int(day.level))))
                doc.add(f'<g data-date="{day.date.isoformat()}" data-count="{day.count}" data-level="{day.level}" transform="translate({n(x)} {n(y)})"><title>{day.date.isoformat()}: {day.count} contributions</title>{mark}</g>')
        if mobile and band<len(chunks)-1:doc.add(line(doc,29,y0+125,w-36,y0+125,.5,ink=p['faint']))
    legend_y=555 if mobile else 363
    doc.add(text(doc,'LESS',tx,legend_y+3,10,spacing=1,fill=p['secondary']))
    for level in range(5):doc.add(place(tx+60+level*20,legend_y,small_flower(doc,level)))
    doc.add(text(doc,'MORE',tx+169,legend_y+3,10,spacing=1,fill=p['secondary']))
    rng=f'{days[0].date.isoformat()} — {days[-1].date.isoformat()}' if days else 'No contribution data'
    doc.add(text(doc,rng,tx,583 if mobile else 397,11,fill=p['secondary']))
    if not mobile:
        doc.add(text(doc,'ONE DAY, ONE FLOWER.',w-39,369,12,anchor='end',spacing=2))
        doc.add(text(doc,'一日一輪',w-39,398,16,'cjk',anchor='end',spacing=6))
    return doc

def bouquet_card(theme,snap,mobile=False):
    w=480 if mobile else 960;h=498 if mobile else 365;p=THEMES[theme]
    values=sorted([(str(k),max(0,int(v))) for k,v in snap.get('languages',{}).items()],key=lambda x:(-x[1],x[0]))
    values=[x for x in values if x[1]>0];total=sum(v for _,v in values)
    if len(values)>6:values=values[:5]+[('Other',sum(v for _,v in values[5:]))]
    doc=Doc(w,h,'Language bouquet','Language shares by code bytes in public, non-fork repositories. '+ '; '.join(f'{k}: {v} bytes' for k,v in values),theme)
    panel(doc)
    doc.add(title(doc,'Language Bouquet',28 if mobile else 38,58,41 if mobile else 46,max_width=w-55 if mobile else 450))
    if not mobile:doc.add(text(doc,'言語の花束',w-40,51,16,'cjk',anchor='end',spacing=3))
    doc.add(line(doc,30,76,w-39,76,1))
    if not mobile:
        doc.add(f'<path d="M27 91H317V329H27Z" fill="url(#dots)"/>')
        # The diagonal white cut-out and bow frame one ink bouquet.
        doc.add(f'<path d="M64 87H280L243 338H107Z" fill="{p["paper"]}"/>')
        doc.add(place(177,180,sprig(doc,12),scale=1.03,rotate=-8))
        doc.add(f'<path d="M85 248Q137 315 221 284M131 258Q175 317 233 264" fill="none" stroke="{p["ink"]}" stroke-width="1.3"/>')
        doc.add(f'<path d="M160 281Q120 259 131 292Q158 300 175 284Q216 263 215 294Q196 306 175 284M168 290L148 326M177 291L200 322" fill="{p["paper"]}" stroke="{p["ink"]}" stroke-width="1.2"/>')
    x=31 if mobile else 355;right=w-42;y=136 if mobile else 116;gap=50 if mobile else 36.5
    if mobile:doc.add(text(doc,'CODE, GATHERED INTO A BOUQUET.',x,103,10,spacing=1.2,fill=p['secondary']))
    pattern_names=[p['ink'],'url(#hatch)','url(#dots)',p['secondary'],'url(#fine-dots)',p['faint']]
    for i,(name,value) in enumerate(values):
        share=value/total if total else 0
        doc.add(text(doc,fit(name,17 if mobile else 18,right-x-88),x,y,17 if mobile else 18,weight=600))
        doc.add(text(doc,f'{share*100:.1f}%',right,y+1,21,'serif',italic=True,anchor='end'))
        bar_y=y+12;bar_w=right-x
        doc.add(f'<rect x="{x}" y="{n(bar_y)}" width="{bar_w}" height="6" fill="{p["tone"]}" stroke="{p["faint"]}" stroke-width=".3"/>')
        doc.add(f'<rect data-language="{esc(name)}" data-bytes="{value}" data-share="{n(share)}" x="{x}" y="{n(bar_y)}" width="{n(bar_w*share)}" height="6" fill="{pattern_names[i%len(pattern_names)]}"/>')
        y+=gap
    if not values:doc.add(text(doc,'No public code yet',x,y+30,21,'serif',italic=True))
    doc.add(text(doc,'PUBLIC, NON-FORK REPOSITORIES / BY CODE BYTES',x,h-30,9.5 if mobile else 11,fill=p['secondary'],spacing=.5))
    return doc

def notes_card(theme,snap,notes,tz_name,mobile=False):
    w=480 if mobile else 960;h=465 if mobile else 388;p=THEMES[theme]
    doc=Doc(w,h,'Garden notes','Recent public activity. '+('; '.join(f'{e["local"].isoformat()} {e["text"]} / {e["repo"]}' for e in notes) or 'No events in the last 30 days.'),theme)
    panel(doc);doc.add(title(doc,'Garden Notes',29 if mobile else 38,58,43 if mobile else 46,max_width=w-95))
    doc.add(text(doc,'花便り',w-39,50,16,'cjk',anchor='end',spacing=2))
    doc.add(line(doc,30,76,w-39,76,1))
    y=111;step=64 if mobile else 48
    x=108 if mobile else 155
    for i,note in enumerate(notes[:5]):
        stamp=note['local'].strftime('%m.%d');clock=note['local'].strftime('%H:%M')
        doc.add(text(doc,stamp,31 if mobile else 40,y,16,'serif',italic=True))
        doc.add(text(doc,clock,32 if mobile else 41,y+17,10,fill=p['secondary']))
        doc.add(place(x-16,y-4,small_flower(doc,3 if i==0 else 1)))
        if i<len(notes)-1:doc.add(line(doc,x-16,y+7,x-16,y+step-14,.65,ink=p['faint']))
        doc.add(text(doc,fit(note['text'],16 if mobile else 18,w-x-40),x,y,16 if mobile else 18,weight=600))
        name=note['repo'];prefix=snap.get('user','')+'/'
        if name.startswith(prefix):name=name[len(prefix):]
        doc.add(text(doc,fit(name,12 if mobile else 14,w-x-40),x,y+23 if mobile else y+21,12 if mobile else 14,fill=p['secondary']))
        doc.add(line(doc,x,y+34,w-40,y+34,.4,ink=p['faint']))
        y+=step
    if not notes:
        doc.add(place(w/2,188,blossom(doc,39,33)))
        doc.add(text(doc,'The garden is resting.',w/2,267,22,'serif',italic=True,anchor='middle'))
    doc.add(text(doc,f'LAST 30 DAYS / {tz_name.upper()}',31 if mobile else 40,h-30,10,fill=p['secondary'],spacing=1))
    return doc

def little_architecture(doc):
    p=doc.pal;i=p['ink'];a=p['paper'];out=[]
    # Original tiny ink vignette; no image or model from the independent site is modified.
    out.append(f'<rect x="0" y="0" width="290" height="215" fill="url(#dots)"/>')
    out.append(f'<circle cx="211" cy="39" r="24" fill="{a}" stroke="{i}" stroke-width="1.2"/>')
    out.append(f'<path d="M21 190L133 118L271 171L158 211Z" fill="{a}" stroke="{i}" stroke-width="1.3"/>')
    out.append(f'<path d="M61 141L117 110L174 143L117 176Z" fill="{a}" stroke="{i}" stroke-width="1.5"/>')
    out.append(f'<path d="M61 141V172L117 203V176Z" fill="url(#hatch)" stroke="{i}" stroke-width="1.3"/>')
    out.append(f'<path d="M117 176L174 143V174L117 203Z" fill="{a}" stroke="{i}" stroke-width="1.3"/>')
    out.append(f'<path d="M94 119V56L129 35L164 55V120L129 141Z" fill="{a}" stroke="{i}" stroke-width="1.6"/>')
    out.append(f'<path d="M94 56L129 76V141L94 120Z" fill="url(#hatch)" stroke="{i}" stroke-width="1.1"/>')
    out.append(f'<path d="M94 56L129 35L164 55L129 76Z" fill="{a}" stroke="{i}" stroke-width="1.1"/>')
    out.append(f'<path d="M137 125V93C137 78 155 68 155 84V115Z" fill="{i}"/>')
    out.append(f'<path d="M115 47V24L129 9L145 23V47L129 56Z" fill="{a}" stroke="{i}" stroke-width="1.3"/>')
    out.append(f'<path d="M115 24L129 9L145 23L129 32Z" fill="{i}"/>')
    # Readable stair treads instead of extra decorative towers.
    for j in range(9):
        xx=172+j*5;yy=136+j*4
        out.append(f'<path d="M{xx} {yy}l22-13v5l-22 13Z" fill="{a}" stroke="{i}" stroke-width=".9"/>')
    out.append(sparkle(doc,45,55,5));out.append(sparkle(doc,243,114,4))
    return ''.join(out)

def book_vignette(doc):
    p=doc.pal;i=p['ink'];a=p['paper']
    s=f'<rect width="290" height="215" fill="url(#dots)"/>'
    s+=f'<path d="M29 165Q80 123 143 158Q200 120 260 160L251 187Q196 154 143 183Q88 155 33 190Z" fill="{a}" stroke="{i}" stroke-width="1.6"/>'
    s+=f'<path d="M36 150Q83 111 143 154Q195 112 253 147L246 176Q190 144 143 176Q86 145 36 180Z" fill="{a}" stroke="{i}" stroke-width="1.1"/>'
    s+=line(doc,143,155,143,177,1.2)
    for y in [141,147,154,161]:s+=f'<path d="M53 {y}Q94 {y-18} 127 {y+9}M160 {y+9}Q194 {y-18} 236 {y}" fill="none" stroke="{i}" stroke-width=".6"/>'
    s+=place(138,89,sprig(doc,27),scale=.58,rotate=12)
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
    panel(doc)
    x=27 if mobile else 35
    doc.add(text(doc,f'{index+1:02d} / {flags}',x,35,10 if mobile else 12,spacing=1.7,fill=p['secondary']))
    doc.add(title(doc,label,x,94 if mobile else 109,55 if mobile else 62,max_width=420 if mobile else 582))
    doc.add(text(doc,fit(name,14 if mobile else 17,421 if mobile else 595),x,126 if mobile else 144,14 if mobile else 17,'mono',fill=p['secondary']))
    # Preserve original descriptions verbatim in accessible text; wrap in the drawing.
    for j,row in enumerate(wrap(desc,17 if mobile else 18,420 if mobile else 585,3 if mobile else 2)):
        doc.add(text(doc,row,x,165+j*23 if mobile else 176+j*23,17 if mobile else 18,'serif'))
    y=259 if mobile else 221
    doc.add(line(doc,x,y-13,439 if mobile else 616,y-13,.55,ink=p['faint']))
    doc.add(text(doc,lang,x,y+9,13 if mobile else 14,weight=600))
    doc.add(text(doc,f'☆ {stars}',242 if mobile else 285,y+9,14))
    doc.add(text(doc,stamp,439 if mobile else 616,y+9,11 if mobile else 12,anchor='end',fill=p['secondary']))
    if mobile:
        doc.add(text(doc,'OPEN REPOSITORY',x,315,11,spacing=1.4))
        doc.add(line(doc,388,310,438,310,1.2));doc.add(f'<path d="M431 304L438 310L431 316" fill="none" stroke="{p["ink"]}" stroke-width="1.2"/>')
    else:
        drawing=little_architecture(doc) if name.endswith('.github.io') else book_vignette(doc)
        doc.add(place(643,19,drawing,scale=1))
        doc.add(f'<path d="M639 17L640 241" stroke="{p["ink"]}" stroke-width="1.3"/>')
        doc.add(f'<rect x="824" y="210" width="103" height="25" fill="{p["paper"]}" stroke="{p["ink"]}" stroke-width=".85"/>')
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

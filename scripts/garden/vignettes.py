"""Small ink scenes for the repository cards, one per repository.

Each scene is an original drawing in the 290 x 215 box on the right of a
desktop card (and a band at the top of a phone card). Line weights come from
manga.nib and tones from manga.tone, so scenes match the rest of the profile at
whatever size they are shown. Scenes leave the lower-right corner quiet, where
the desktop card puts its OPEN button.

Repositories are matched to scenes by words in their name and description and
by language; no two repositories share a scene until every scene is in use.
"""
from __future__ import annotations

import hashlib
import math
import re

from . import manga

n = manga.n
W, H = 290, 215


class Pen:
    """Shorthand for one scene: ink, paper and nibs at the scene's scale."""
    def __init__(self, doc, k):
        self.doc, self.k = doc, k
        self.ink, self.paper = doc.pal['ink'], doc.pal['paper']

    def w(self, tier, m=1.0):
        return n(manga.nib(self.k, tier, m))

    def shape(self, d, fill=None, tier='contour', m=1.0):
        return f'<path d="{d}" fill="{fill or self.paper}" stroke="{self.ink}" stroke-width="{self.w(tier, m)}"/>'

    def line(self, d, tier='detail', ink=None, m=1.0):
        return f'<path d="{d}" fill="none" stroke="{ink or self.ink}" stroke-width="{self.w(tier, m)}"/>'

    def solid(self, d, fill=None):
        return f'<path d="{d}" fill="{fill or self.ink}"/>'

    def tone(self, name):
        return manga.tone(self.doc, name, self.k)

    def bloom(self, x, y, r, seed, kind='sakura', rotate=0):
        return manga.place(x, y, manga.blossom(self.doc, r, seed, kind, self.k), rotate=rotate)

    def leaf(self, x, y, length, width, black, rotate):
        return manga.place(x, y, manga.petal_leaf(self.doc, length, width, black, self.k), rotate=rotate)

    def sparkle(self, x, y, r=5):
        return manga.sparkle(self.doc, x, y, r)

    def petal(self, x, y, size, rotate, black=False):
        """A falling sakura petal: notched tip and a centre crease."""
        size = max(size, 11 / self.k)
        d = (f'M0 0C{n(size*.62)} {n(-size*.18)} {n(size*.66)} {n(-size*.78)} {n(size*.24)} {n(-size)}'
             f'L0 {n(-size*.8)}L{n(-size*.24)} {n(-size)}C{n(-size*.66)} {n(-size*.78)} {n(-size*.62)} {n(-size*.18)} 0 0Z')
        art = self.shape(d, self.ink if black else None, 'inner')
        art += self.line(f'M0 {n(-size*.12)}Q{n(size*.08)} {n(-size*.45)} 0 {n(-size*.72)}', 'detail', self.paper if black else None)
        return manga.place(x, y, art, rotate=rotate)


def ellipse_d(cx, cy, rx, ry):
    return (f'M{n(cx-rx)} {n(cy)}A{n(rx)} {n(ry)} 0 1 0 {n(cx+rx)} {n(cy)}'
            f'A{n(rx)} {n(ry)} 0 1 0 {n(cx-rx)} {n(cy)}Z')


def gear_d(cx, cy, r, teeth, depth=.17):
    pts = []
    for i in range(teeth):
        base = 2 * math.pi * i / teeth
        for frac, rr in ((0, 1-depth), (.16, 1-depth), (.3, 1), (.6, 1), (.74, 1-depth)):
            a = base + frac * 2 * math.pi / teeth
            pts.append(f'{n(cx + r*rr*math.cos(a))} {n(cy + r*rr*math.sin(a))}')
    return 'M' + 'L'.join(pts) + 'Z'


# -- scenes -----------------------------------------------------------------

def valley(p: Pen) -> str:
    """A quiet valley: a tower and stair under an event horizon."""
    i, a, out = p.ink, p.paper, []
    # Hills behind the plateau, the far one in pale tone.
    # Hills run well past the frame; the card clips the scene to whatever window it shows.
    out.append(f'<path d="M-200 128Q-110 100 -40 122Q0 134 48 112Q90 100 98 120Q140 132 176 112Q226 88 290 110Q350 128 400 104Q450 92 500 116V230H-200Z" fill="{p.tone("fine-dots")}"/>')
    out.append(p.shape('M-200 148Q-120 126 -50 146Q-10 156 30 140Q70 128 118 142Q170 156 214 134Q252 118 290 128Q340 140 390 124Q440 112 500 132V230H-200Z', a, 'inner'))
    # The event horizon: a ring band behind the disc, the disc, then the band's near half in front.
    out.append('<g transform="translate(212 50) rotate(-13)">')
    out.append(f'<path d="{ellipse_d(0, 0, 47, 11)}{ellipse_d(0, 0, 30, 6)}" fill="{a}" fill-rule="evenodd" stroke="{i}" stroke-width="{p.w("inner")}"/>')
    out.append(p.line(ellipse_d(0, 0, 40, 9)) + p.line(ellipse_d(0, 0, 35, 7.4)))
    out.append(f'<circle r="21.5" fill="none" stroke="{i}" stroke-width="{p.w("detail")}"/>')
    # The far side of the disc, lensed up and over the top of the hole.
    out.append(f'<path d="M-27 2A27 27 0 0 1 27 2L22 2A22 22 0 0 0 -22 2Z" fill="{a}" stroke="{i}" stroke-width="{p.w("inner")}"/>')
    out.append(p.line('M-24.5 2A24.5 24.5 0 0 1 24.5 2'))
    out.append(f'<circle r="18" fill="{i}"/>')
    near = 'M-47 0A47 11 0 0 0 47 0L30 0A30 6 0 0 1 -30 0Z'
    out.append(p.shape(near, a, 'inner'))
    out.append(p.line('M-40 0A40 9 0 0 0 40 0M-35 0A35 7.4 0 0 0 35 0'))
    out.append('</g>')
    # The plateau, tower and stair.
    out.append(p.shape('M21 190L133 118L271 171L158 211Z'))
    out.append(p.shape('M61 141L117 110L174 143L117 176Z'))
    out.append(p.shape('M61 141V172L117 203V176Z', p.tone('hatch')))
    out.append(p.shape('M117 176L174 143V174L117 203Z'))
    out.append(p.shape('M94 119V56L129 35L164 55V120L129 141Z'))
    out.append(p.shape('M94 56L129 76V141L94 120Z', p.tone('hatch'), 'inner'))
    out.append(p.shape('M94 56L129 35L164 55L129 76Z', None, 'inner'))
    out.append(p.solid('M137 125V93C137 78 155 68 155 84V115Z'))
    out.append(p.line('M143 98V112', 'detail', a))
    out.append(p.shape('M115 47V24L129 9L145 23V47L129 56Z'))
    out.append(p.solid('M115 24L129 9L145 23L129 32Z'))
    for j in range(9):
        xx, yy = 172 + j*5, 136 + j*4
        out.append(p.shape(f'M{xx} {yy}l22-13v5l-22 13Z', None, 'detail'))
    # Flowers and grass at the foot of the tower.
    for x, y in ((40, 186), (70, 171), (196, 186)):
        out.append(p.line(f'M{x} {y}q-2-7 1-12M{x+4} {y}q1-8 6-10M{x-4} {y+1}q-3-5-7-6', 'inner'))
    out.append(p.bloom(52, 176, 8, 71, rotate=12))
    out.append(p.bloom(84, 186, 6.5, 72, rotate=-20))
    out.append(p.bloom(210, 176, 7.5, 73, rotate=30))
    out.append(p.sparkle(34, 44, 5) + p.sparkle(150, 22, 3.5) + p.sparkle(268, 98, 4))
    for x, y in ((62, 30), (100, 70), (172, 18), (282, 26)):
        out.append(f'<circle cx="{x}" cy="{y}" r="{n(1.1/p.k)}" fill="{i}"/>')
    return ''.join(out)


def notebook(p: Pen) -> str:
    """A lab notebook: a loss curve growing leaves, and a little network of flowers."""
    i, a, out = p.ink, p.paper, []
    # A pencil resting behind the book.
    out.append('<g transform="translate(26 70) rotate(-12)">')
    out.append(p.shape('M0 1Q-5 1-5 5.5Q-5 10 0 10Z', i, 'inner'))
    out.append(p.shape('M0 0H9V11H0Z', p.tone('hatch'), 'inner'))
    out.append(p.shape('M9 0H62V11H9Z', None, 'inner'))
    out.append(p.line('M9 3.7H62M9 7.3H62'))
    out.append(p.shape('M62 0L78 5.5L62 11Z', None, 'inner'))
    out.append(p.solid('M73.5 4L78 5.5L73.5 7Z'))
    out.append('</g>')
    # Page stacks, then the two pages.
    out.append(p.shape('M24 200Q82 186 143 202Q204 186 268 200L266 192Q205 179 143 195Q82 179 26 192Z', p.tone('hatch'), 'inner'))
    out.append(p.shape('M28 108Q84 92 143 110V195Q82 179 26 192Z'))
    out.append(p.shape('M143 110Q202 92 260 106L266 192Q205 179 143 195Z'))
    out.append(p.line('M143 110V195', 'inner'))
    out.append(p.line('M128 110Q136 112 143 116V192Q137 188 128 186', 'detail'))
    # Left page: axes, ticks and a descending curve that has grown leaves.
    out.append(p.line('M46 122V176H130', 'inner'))
    for t in range(4):
        out.append(p.line(f'M43 {130+t*12}H46M{58+t*20} 176V179'))
    out.append(p.line('M50 128C62 152 76 162 96 167S120 170 128 170', 'inner'))
    out.append(p.leaf(63, 148, 13, 4, True, -40))
    out.append(p.leaf(86, 163, 12, 4, False, 70))
    out.append(p.leaf(111, 168, 11, 3.5, True, -60))
    out.append(p.bloom(128, 168, 6, 81, rotate=10))
    # Right page: a 3-3-2 network whose nodes are flowers.
    layers = [(166, (126, 150, 174)), (204, (122, 146, 170)), (240, (134, 160))]
    for (x0, ys0), (x1, ys1) in zip(layers, layers[1:]):
        for y0 in ys0:
            for y1 in ys1:
                out.append(p.line(f'M{x0} {y0}L{x1} {y1}', 'detail'))
    for li, (x, ys) in enumerate(layers):
        for yi, y in enumerate(ys):
            out.append(p.bloom(x, y, 7.5 if li == 2 else 6.5, 90 + li*5 + yi, 'sakura' if (li+yi) % 2 else 'rose', rotate=li*20+yi*9))
    # A sprig rising from the spine.
    out.append(manga.place(150, 66, manga.sprig(p.doc, 41, p.k*.4), scale=.4, rotate=-6))
    out.append(p.sparkle(30, 40, 5) + p.sparkle(262, 52, 4))
    return ''.join(out)


def clockwork(p: Pen) -> str:
    """An open pocket watch with its gears showing and a rose growing from the arbor."""
    i, a, out = p.ink, p.paper, []
    # The lid, hinged open behind the case.
    out.append('<g transform="translate(70 64) rotate(-28)">')
    out.append(p.shape(ellipse_d(0, 0, 50, 40), p.tone('fine-dots')))
    out.append(p.shape(ellipse_d(0, 0, 43, 34), None, 'inner'))
    for r in (14, 22, 30):
        out.append(p.line(ellipse_d(0, 0, r, r*.78)))
    out.append('</g>')
    # The chain, link by link, out to the right.
    for j in range(15):
        t = j / 14
        x = 128 + 140*t
        y = 54 + 120*t*t - 34*math.sin(t*math.pi)
        out.append(manga.place(x, y, p.shape(ellipse_d(0, 0, 5.4, 3), None, 'inner'), rotate=(60 if j % 2 else -20) + 40*t))
    # Case, bezel and the exposed movement.
    out.append(p.shape(ellipse_d(120, 136, 64, 62)))
    out.append(f'<path d="{ellipse_d(120, 136, 64, 62)}{ellipse_d(118, 133, 56, 54)}" fill="{p.tone("hatch")}" fill-rule="evenodd"/>')
    out.append(p.shape(ellipse_d(118, 133, 56, 54), None, 'inner'))
    out.append(p.shape(gear_d(100, 124, 27, 15), None, 'inner'))
    out.append(p.shape(ellipse_d(100, 124, 17, 17), p.tone('fine-dots'), 'detail'))
    for s in range(4):
        ang = s * math.pi / 2 + .3
        out.append(p.solid(f'M{n(100+5*math.cos(ang-.35))} {n(124+5*math.sin(ang-.35))}'
                           f'L{n(100+15*math.cos(ang-.2))} {n(124+15*math.sin(ang-.2))}'
                           f'L{n(100+15*math.cos(ang+.2))} {n(124+15*math.sin(ang+.2))}'
                           f'L{n(100+5*math.cos(ang+.35))} {n(124+5*math.sin(ang+.35))}Z'))
    out.append(p.shape(gear_d(141, 152, 19, 11), None, 'inner'))
    out.append(f'<circle cx="141" cy="152" r="5" fill="{i}"/>')
    out.append(p.shape(gear_d(138, 104, 12, 8), None, 'inner'))
    out.append(f'<circle cx="138" cy="104" r="3" fill="{i}"/>')
    out.append(p.shape(gear_d(98, 166, 10, 8), p.tone('fine-dots'), 'detail'))
    # Crown and bow at twelve o'clock.
    out.append(p.shape('M112 66H128V75H112Z', p.tone('hatch'), 'inner'))
    out.append(p.shape(ellipse_d(120, 58, 9, 8), 'none', 'inner'))
    # The rose rising out of the movement.
    out.append(p.line('M101 124C116 104 132 88 160 60', 'contour'))
    out.append(p.leaf(122, 100, 22, 7, True, 40))
    out.append(p.leaf(140, 80, 18, 6, False, -50))
    out.append(p.bloom(162, 52, 21, 101, 'rose', rotate=8))
    out.append(p.sparkle(232, 40, 5) + p.sparkle(26, 170, 4))
    return ''.join(out)


def teacup(p: Pen) -> str:
    """A teacup whose steam drifts up into cherry blossom."""
    i, a, out = p.ink, p.paper, []
    # Saucer, then a spoon resting on it.
    out.append(p.shape(ellipse_d(140, 184, 96, 21)))
    out.append(p.line(ellipse_d(140, 182, 62, 13), 'inner'))
    out.append(p.line('M93 177L130 170', 'contour'))
    out.append(p.shape(ellipse_d(80, 179, 14, 7), None, 'inner'))
    out.append(p.line('M70 180Q80 184 90 179', 'detail'))
    # The cup body with shade on the side away from the light.
    out.append(p.shape('M82 126C84 162 106 184 140 184C174 184 196 162 198 126Z'))
    out.append(f'<path d="M172 130C186 132 196 129 198 126C196 158 182 178 158 183C176 166 179 146 172 130Z" fill="{p.tone("hatch")}"/>')
    out.append(p.shape('M196 136C226 130 230 168 190 166', 'none', 'contour'))
    out.append(p.line('M195 144C214 141 214 160 193 158', 'inner'))
    # Rim and tea, with one petal afloat.
    out.append(p.shape(ellipse_d(140, 126, 58, 14)))
    out.append(p.solid(ellipse_d(140, 129, 50, 10)))
    out.append(p.line('M108 128Q126 123 150 124', 'detail', a))
    out.append(p.petal(156, 132, 9, 70))
    # Steam: three curls, the middle one opening into blossom.
    out.append(p.line('M122 108C114 94 130 86 122 72C116 62 124 56 120 50', 'inner'))
    out.append(p.line('M142 106C134 90 152 80 144 64', 'inner'))
    out.append(p.line('M160 108C168 96 156 88 164 76C168 70 164 66 166 62', 'inner'))
    # The scent becomes blossom a little above the steam.
    out.append(p.bloom(150, 34, 14, 111, rotate=10))
    out.append(p.bloom(184, 46, 9, 112, rotate=-25))
    out.append(p.bloom(116, 28, 8, 113, rotate=40))
    out.append(p.petal(212, 74, 12, 120) + p.petal(88, 52, 11, -40) + p.petal(238, 112, 11, 160, True))
    out.append(p.sparkle(34, 60, 5) + p.sparkle(250, 30, 4))
    return ''.join(out)


def lantern(p: Pen) -> str:
    """A paper lantern under a cherry branch, its light drawn as short ink rays."""
    i, a, out = p.ink, p.paper, []
    # Branch from the upper left with a few blossoms.
    out.append(p.line('M0 26C40 30 70 18 104 8M40 30C52 40 54 52 50 60', 'contour'))
    out.append(p.bloom(28, 22, 10, 121, rotate=10))
    out.append(p.bloom(70, 18, 8, 122, rotate=-30))
    out.append(p.bloom(50, 60, 7, 123, rotate=20))
    out.append(p.leaf(92, 12, 15, 5, True, 70))
    # Rays of light around the body.
    for j in range(14):
        ang = j * 2 * math.pi / 14 + .1
        x0, y0 = 145 + 70*math.cos(ang), 96 + 64*math.sin(ang)
        x1, y1 = 145 + 82*math.cos(ang), 96 + 75*math.sin(ang)
        if y1 < 200 and not (x1 > 175 and y1 > 180):
            out.append(p.line(f'M{n(x0)} {n(y0)}L{n(x1)} {n(y1)}', 'detail'))
    # Cord, caps, body and ribs.
    out.append(p.line('M145 0V30', 'inner'))
    out.append(p.shape('M100 44C72 70 72 124 100 150H190C218 124 218 70 190 44Z'))
    out.append(f'<path d="M176 46H190C218 70 218 124 190 150H176C200 124 200 70 176 46Z" fill="{p.tone("hatch")}"/>')
    for y in range(58, 144, 13):
        bulge = 1 - abs(y - 97) / 60
        out.append(p.line(f'M{n(100 - 22*bulge)} {y}Q145 {n(y + 6*bulge)} {n(190 + 22*bulge)} {y}', 'detail'))
    out.append(p.shape('M122 30H168V44H122Z', i, 'inner'))
    out.append(p.shape('M122 150H168V162H122Z', i, 'inner'))
    out.append(manga.text(p.doc, '花', 145, 108, 30, 'cjk', anchor='middle'))
    # Tassel.
    out.append(p.line('M145 162V176', 'inner'))
    out.append(p.shape('M139 176H151L154 200H136Z', p.tone('hatch'), 'inner'))
    for x in (138, 142, 146, 150, 153):
        out.append(p.line(f'M{x} 200V{206 if x % 4 else 204}'))
    out.append(p.petal(236, 120, 8, 140) + p.petal(60, 140, 7, -30, True) + p.petal(250, 60, 7, 60))
    out.append(p.sparkle(262, 26, 5) + p.sparkle(34, 182, 4))
    return ''.join(out)


def crane(p: Pen) -> str:
    """An origami crane over a sea of curling ink waves."""
    i, a, out = p.ink, p.paper, []
    # Waves, back to front: each a crest with a curl and a few foam lines.
    for x0, y0, s in ((-10, 168, 1.0), (96, 176, .9), (190, 166, 1.05)):
        out.append(manga.place(x0, y0, wave(p, s)))
    # The crane: wings, body, neck and tail as folded facets.
    # Far wing first, then the body diamond, neck, tail and near wing.
    out.append(p.shape('M152 100L228 18L196 112Z'))
    out.append(p.shape('M152 100L228 18L176 104Z', p.tone('fine-dots'), 'inner'))
    out.append(p.shape('M104 120L150 96L198 118L150 146Z'))
    out.append(p.shape('M150 96L198 118L150 146Z', p.tone('hatch'), 'inner'))
    out.append(p.line('M150 96V146', 'inner'))
    out.append(p.shape('M112 118L62 54L70 52L124 112Z'))
    out.append(p.shape('M62 54L44 66L66 58Z', i, 'inner'))
    out.append(p.shape('M186 114L258 76L262 82L194 120Z'))
    out.append(p.shape('M150 104L84 22L106 110Z'))
    out.append(p.shape('M84 22L96 74L106 110Z', p.tone('hatch'), 'inner'))
    out.append(p.line('M150 104L96 74', 'detail'))
    # Petals on the wind.
    out.append(p.petal(40, 118, 12, 40) + p.petal(262, 128, 11, -60, True) + p.petal(30, 60, 11, 120))
    out.append(p.bloom(222, 150, 7, 131, rotate=15))
    out.append(p.sparkle(256, 24, 5) + p.sparkle(30, 30, 4))
    return ''.join(out)


def wave(p: Pen, s: float) -> str:
    d = (f'M0 {n(40*s)}C{n(20*s)} {n(10*s)} {n(56*s)} {n(-14*s)} {n(84*s)} {n(-2*s)}'
         f'C{n(100*s)} {n(6*s)} {n(98*s)} {n(24*s)} {n(84*s)} {n(22*s)}'
         f'C{n(74*s)} {n(20*s)} {n(76*s)} {n(10*s)} {n(84*s)} {n(10*s)}'
         f'C{n(70*s)} {n(0)} {n(44*s)} {n(16*s)} {n(40*s)} {n(40*s)}Z')
    out = p.shape(d, p.paper, 'inner')
    out += p.solid(f'M{n(40*s)} {n(40*s)}C{n(46*s)} {n(22*s)} {n(66*s)} {n(10*s)} {n(84*s)} {n(10*s)}'
                   f'C{n(64*s)} {n(14*s)} {n(52*s)} {n(26*s)} {n(52*s)} {n(40*s)}Z')
    for j in range(3):
        out += p.line(f'M{n((8+j*9)*s)} {n((38-j*4)*s)}C{n((24+j*8)*s)} {n((18-j*3)*s)} {n((48+j*6)*s)} {n((2-j*2)*s)} {n((70+j*3)*s)} {n((-2-j)*s)}')
    return out


def terminal(p: Pen) -> str:
    """A little terminal with a vine growing out of its prompt."""
    i, a, out = p.ink, p.paper, []
    # Keyboard slab in front, keys as a ruled grid.
    out.append(p.shape('M40 186L196 186L214 204L22 204Z'))
    for j in range(1, 4):
        y = 186 + j*4.5
        out.append(p.line(f'M{n(40 - j*4.5)} {n(y)}L{n(196 + j*4.5)} {n(y)}'))
    for j in range(1, 12):
        x = 40 + j*13
        out.append(p.line(f'M{x} 186L{n(x - 18*(x-118)/156 - 2)} 204'))
    # Monitor: side face, front, screen and stand.
    out.append(p.shape('M200 50L228 38V132L200 146Z', p.tone('hatch')))
    out.append(p.shape('M68 50L200 50L228 38L96 38Z', None, 'inner'))
    out.append(p.shape('M114 146H154L164 166H104Z', p.tone('fine-dots'), 'inner'))
    out.append(p.shape('M68 50H200V146H68Z'))
    out.append(p.shape('M80 62H188V132H80Z', i, 'inner'))
    out.append(manga.text(p.doc, '> grow_', 90, 84, 13, 'mono', fill=a))
    out.append(manga.text(p.doc, '  bloom ok', 90, 102, 11, 'mono', fill=a))
    out.append(f'<rect x="90" y="110" width="8" height="12" fill="{a}"/>')
    # The vine climbs out over the top edge.
    out.append(p.line('M170 96C186 84 182 64 196 50C214 32 236 34 248 20', 'contour'))
    out.append(p.leaf(184, 74, 16, 5, True, 30))
    out.append(p.leaf(210, 40, 14, 5, False, -40))
    out.append(p.leaf(236, 32, 13, 4, True, 60))
    out.append(p.bloom(252, 18, 12, 141, rotate=12))
    out.append(p.bloom(200, 46, 7, 142, rotate=-20))
    out.append(p.sparkle(36, 40, 5) + p.sparkle(262, 80, 4) + p.petal(254, 120, 7, 130))
    return ''.join(out)


def seedling(p: Pen) -> str:
    """A potted seedling with a paper tag, watered from the side."""
    i, a, out = p.ink, p.paper, []
    # Watering can tilted in from the upper left, drops falling.
    out.append('<g transform="translate(62 62) rotate(16)">')
    out.append(p.line('M-22 -16C-22 -36 18 -36 18 -16', 'contour'))
    out.append(p.shape('M-30 -16H22L18 26H-26Z'))
    out.append(f'<path d="M6 -16H22L18 26H4Z" fill="{p.tone("hatch")}"/>')
    out.append(p.line('M-30 -8H22', 'inner'))
    out.append(p.shape('M18 14L58 -14L62 -9L22 20Z', None, 'inner'))
    out.append(p.shape('M56 -20L68 -12L62 0L52 -8Z', None, 'inner'))
    out.append(p.line('M58 -14l3 3M60 -9l3 3M55 -9l3 3', 'detail'))
    out.append(p.line('M-30 -2C-46 -4 -46 18 -28 16', 'contour'))
    out.append('</g>')
    for x, y in ((122, 70), (130, 82), (120, 92), (134, 102), (126, 112)):
        out.append(p.shape(f'M{x} {y}c2.5 4 3 8 0 8s-2.5-4 0-8Z', i, 'detail'))
    # Pot: rim, body with a shaded flank, soil.
    out.append(p.shape('M114 142H184L176 200H122Z'))
    out.append(f'<path d="M164 142H184L176 200H162Z" fill="{p.tone("hatch")}"/>')
    out.append(p.shape('M108 126H190V142H108Z'))
    out.append(p.solid(ellipse_d(149, 127, 38, 5)))
    # The seedling and its tag.
    out.append(p.line('M149 126C149 110 146 96 152 84', 'contour'))
    out.append(p.leaf(151, 100, 26, 9, True, -62))
    out.append(p.leaf(150, 94, 22, 8, False, 58))
    out.append(p.bloom(153, 80, 9, 151, rotate=10))
    out.append(p.line('M176 126L198 92', 'inner'))
    out.append(p.shape('M190 86L224 70L232 86L198 102Z'))
    out.append(manga.text(p.doc, 'NEW', 210, 91, 10, 'sans', weight=600, anchor='middle'))
    out.append(p.petal(238, 150, 8, 150) + p.petal(80, 170, 7, -50, True))
    out.append(p.sparkle(250, 40, 5) + p.sparkle(40, 150, 4))
    return ''.join(out)


SCENES = {
    'valley': valley, 'notebook': notebook, 'clockwork': clockwork, 'teacup': teacup,
    'lantern': lantern, 'crane': crane, 'terminal': terminal, 'seedling': seedling,
}

# scene: (words in name/description, languages)
TOPICS = {
    'valley': ({'homepage', 'website', 'site', 'portfolio', 'personal', 'github', 'io', 'pages', 'landing'},
               {'TypeScript', 'JavaScript', 'HTML', 'CSS', 'Vue', 'Svelte', 'Astro', 'SCSS'}),
    'notebook': ({'ml', 'machine', 'learning', 'data', 'model', 'models', 'neural', 'ai', 'notebook', 'analysis',
                  'research', 'dataset', 'training', 'deep', 'active', 'science', 'materials'},
                 {'Jupyter Notebook', 'Python', 'R', 'Julia', 'MATLAB'}),
    'clockwork': ({'engine', 'system', 'systems', 'kernel', 'compiler', 'runtime', 'embedded', 'performance',
                   'simulator', 'driver'},
                  {'C', 'C++', 'Rust', 'Go', 'Zig', 'Assembly', 'Verilog', 'CUDA'}),
    'teacup': ({'notes', 'note', 'docs', 'doc', 'documentation', 'blog', 'writing', 'journal', 'diary', 'book',
                'reading', 'awesome', 'list', 'resume', 'cv'},
               {'Markdown', 'TeX', 'MDX', 'reStructuredText'}),
    'lantern': ({'app', 'ui', 'ios', 'android', 'mobile', 'desktop', 'gui', 'game', 'widget', 'extension',
                 'player', 'client'},
                {'Swift', 'Kotlin', 'Dart', 'C#', 'Java', 'Objective-C', 'GDScript'}),
    'crane': ({'algorithm', 'algorithms', 'leetcode', 'contest', 'solution', 'solutions', 'practice', 'puzzle',
               'math', 'acm', 'icpc', 'oj', 'exercise', 'exercises', 'course', 'homework', 'lab'}, set()),
    'terminal': ({'cli', 'tool', 'tools', 'script', 'scripts', 'dotfiles', 'config', 'bot', 'automation',
                  'action', 'workflow', 'shell', 'utils'},
                 {'Shell', 'PowerShell', 'Lua', 'Perl', 'Makefile', 'Dockerfile', 'Nix', 'Vim Script'}),
    'seedling': (set(), set()),
}


def words(repo: dict) -> set[str]:
    text = f"{repo.get('name') or ''} {repo.get('description') or ''} {' '.join(repo.get('topics') or [])}"
    return {w for w in re.split(r'[^a-z0-9]+', text.lower()) if w}


def ranked(repo: dict) -> list[str]:
    """Scenes best suited to a repository first; a stable hash breaks ties."""
    found, lang = words(repo), repo.get('language')
    salt = hashlib.sha256(str(repo.get('name', '')).encode()).digest()
    def score(item):
        index, scene = item
        keys, langs = TOPICS[scene]
        return (-(2 * len(found & keys) + (1 if lang in langs else 0)), salt[index % len(salt)] ^ index)
    return [scene for _, scene in sorted(enumerate(SCENES), key=score)]


def assign(repos: list[dict]) -> dict[str, str]:
    """One scene per repository, in list order, without repeats until all are used."""
    chosen: dict[str, str] = {}
    used: set[str] = set()
    for repo in repos:
        options = ranked(repo)
        pick = next((s for s in options if s not in used), options[0])
        chosen[str(repo.get('name'))] = pick
        used.add(pick)
        if len(used) == len(SCENES):
            used.clear()
    return chosen


def draw(doc, scene: str, k: float, window=(0, 0, W, H)) -> str:
    """The scene's ink at scale k (its CSS px per design unit on screen),
    clipped to `window` (x0, y0, x1, y1) in the scene's own units."""
    cid = f'scene-clip-{len(doc.defs)}'
    x0, y0, x1, y1 = window
    doc.defs.append(f'<clipPath id="{cid}"><rect x="{n(x0)}" y="{n(y0)}" width="{n(x1-x0)}" height="{n(y1-y0)}"/></clipPath>')
    return f'<g data-vignette="{scene}" clip-path="url(#{cid})">{SCENES[scene](Pen(doc, k))}</g>'

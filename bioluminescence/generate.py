"""Generate the Bioluminescence T3 Code theme.

The deep abyss, darker than Deep Sea, where every creature makes its own light.
Glowing animals take turns drifting behind the chat area, one or two on screen
at a time, over three shuffled rounds. Glows are faked with stacked translucent
shapes and opacity pulses (no SVG filters), so the always-running animation
stays cheap. See ../common/themekit.py for how the background is built.

    python3 generate.py

The output is deterministic (fixed seeds).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from themekit import (Actor, blink, build_css, build_svg, dot_pattern, dotted, gallery_svg, parade, pulse,  # noqa: E402
                      specks, wave, write_theme)

OUT = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(5)

ABYSS = "#05080d"
C1, C2, C3, W = "#3ff0e0", "#2bc4c4", "#8ffcff", "#e8ffff"  # aqua, teal, pale cyan, white-cyan core
V, E, V2 = "#7a6cff", "#3f8cff", "#a99bff"  # violet, electric blue, lilac
DIM2 = "#1b7a82"  # unlit body tissue

defs = (dot_pattern("g", 5, 1.6, [C2, C1, C2, C3, C2, C1, C2, W, C1])
        + dot_pattern("s", 4, 1.3, [C2, DIM2, C2, C1, DIM2, C2, C2, C3, DIM2])
        + dot_pattern("v", 5, 1.6, [V, E, V, V2, V, E, V, C3, E]))


def halo(r, color=C1, op=.1, cx=0, cy=0):
    """Fake glow: two soft translucent discs."""
    return (f"<circle cx='{cx:g}' cy='{cy:g}' r='{r:g}' fill='{color}' opacity='{op:g}'/>"
            f"<circle cx='{cx:g}' cy='{cy:g}' r='{r * .55:g}' fill='{color}' opacity='{op * 1.8:g}'/>")


def light(cx, cy, r, dur, begin=0, color=C3):
    """A bright core with a halo that breathes."""
    return (f"<g>{blink('1;.25;1', dur, begin=-begin if begin else None)}{halo(r * 3.2, color, .14, cx, cy)}"
            f"<circle cx='{cx:g}' cy='{cy:g}' r='{r:g}' fill='{W}'/></g>")


# ---------- Bodies: drawn facing +x, head near the origin ----------

# Jellyfish swarm: two jelly variants with different pulse rates, bobbing out of step.
ja, jb = "M0,3C3,15-3,28 0,42", "M0,3C-3,15 3,28 0,42"
defs += f"<path id='jt' d='{ja}'>{wave(ja, jb, 1.8)}</path>"
for jid, dur in (("j1", 2.5),):
    defs += (f"<g id='{jid}'><ellipse cy='-4' rx='24' ry='22' fill='{C1}' opacity='.07'/>"
             f"<g {dotted(C1, 2, 4)}><use href='#jt' x='-8'/><use href='#jt'/><use href='#jt' x='8'/></g>"
             f"<g>{pulse('1 1;1.15 .8;1 1', dur)}<path d='M-14,0C-15,-19 15,-19 14,0C9,3 4,1 0,3C-4,1-9,3-14,0Z' fill='url(#g)'/></g>"
             f"<circle cy='-8' r='3' fill='{W}'>{blink('1;.3;1', dur)}</circle></g>")
jellies = ""
for i, (x, y, s) in enumerate([(0, 0, 1.3), (-58, 46, .9), (52, 64, 1), (-30, -70, .75), (40, -50, .65)]):
    jellies += (f"<g transform='translate({x},{y}) scale({s:g})'><use href='#j1'>"
                f"<animateTransform attributeName='transform' type='translate' dur='{rng.uniform(2.5, 4):.1f}s' "
                f"repeatCount='indefinite' values='0 0;{rng.randint(-3, 3)} -6;0 0'/></use></g>")


# Siphonophore: a long colonial string. A travelling wave bends it, a soft wide
# stroke glows around it, and pulses of light run down its segments.
def sip(ph):
    return "M" + "L".join(f"{-x},{14 * min(1, x / 80) * math.sin(x / 45 + ph):.0f}" for x in range(0, 421, 28))


sv = ";".join(sip(k * math.pi / 2) for k in (0, 1, 2, 3, 0))
defs += f"<path id='sp' d='{sip(0)}'><animate attributeName='d' dur='3s' repeatCount='indefinite' values='{sv}'/></path>"
siphonophore = (f"<use href='#sp' fill='none' stroke='{C1}' stroke-width='14' stroke-linecap='round' opacity='.1'/>"
                f"<use href='#sp' {dotted(C3, 2.5, 7)}/>"
                f"<use href='#sp' {dotted(C1, 6, 21)}><animate attributeName='stroke-dashoffset' values='0;42' dur='1.4s' "
                f"repeatCount='indefinite'/></use>"
                + light(4, 0, 4, 2.4, color=C1))

# Comb jelly: a translucent oval whose comb rows shimmer through colors and ripple.
rows = ""
for i, cy in enumerate((-26, -12, 12, 26)):
    rows += (f"<path d='M38,0C20,{cy}-20,{cy}-38,0' {dotted(C1, 3, 5)}>"
             f"<animate attributeName='stroke' dur='1.6s' begin='-{i * .4:g}s' repeatCount='indefinite' values='{C1};{V};{C3};{E};{C1}'/>"
             "</path>")
ca, cb = "M-36,4C-70,10-100,30-140,26", "M-36,4C-70,-4-100,40-140,40"
comb = (halo(52, C2, .06)
        + f"<ellipse rx='38' ry='24' fill='{C2}' opacity='.12' stroke='{C2}' stroke-opacity='.35' stroke-width='1.5'/>"
        + rows
        + f"<path d='{ca}' {dotted(C2, 2, 5)} opacity='.7'>{wave(ca, cb, 3.4)}</path>"
        + light(36, 0, 2.5, 1.6))

# Glowing squid: dotted arms, a lit mantle and photophores that flicker.
sa, sb = "M-36,0C-80,-10-110,10-160,0", "M-36,0C-80,10-110,-10-160,0"
defs += f"<path id='st' d='{sa}'>{wave(sa, sb, 1.7)}</path>"
squid = (f"<ellipse cx='10' rx='72' ry='30' fill='{C1}' opacity='.05'/>"
         f"<g {dotted(C2, 2.6, 5)}>" + "".join(f"<use href='#st' y='{y}'/>" for y in (-9, -3, 3, 9)) + "</g>"
         "<path d='M64,0C50,-8 30,-16-40,-14L-40,14C30,16 50,8 64,0ZM64,0L40,-28L32,-8ZM64,0L40,28L32,8Z' fill='url(#g)'/>"
         + "".join(f"<g fill='{W}'>{blink('1;.2;1', 1.3, begin=b)}"
                   + "".join(f"<circle cx='{x}' cy='{y}' r='2.4'/>" for x, y in pts) + "</g>"
                   for b, pts in ((None, ((40, 0), (-6, -9), (-6, 9))), (-.65, ((18, -7), (18, 7), (-28, 0))))))

# Lanternfish school: small dim fish with blinking belly lights.
for lid, dur in (("l1", 1.9),):
    defs += (f"<g id='{lid}'><ellipse rx='12' ry='5' fill='url(#s)'/><path d='M-10,0L-19,-5L-19,5Z' fill='url(#s)'/>"
             f"<g fill='{W}'>{blink('1;.15;1', dur)}<circle cx='6' cy='3' r='1.6'/><circle cy='3.5' r='1.6'/>"
             f"<circle cx='-6' cy='3' r='1.6'/></g><circle cx='9' cy='-1' r='2.2' fill='{C3}'/></g>")
school = ""
for i in range(9):
    x = rng.uniform(-110, 110)
    y = rng.uniform(-45, 45) + x * .15
    school += (f"<use href='#l1' x='{x:.0f}' y='{y:.0f}'><animateTransform attributeName='transform' type='translate' "
               f"dur='{rng.uniform(1.6, 2.6):.1f}s' repeatCount='indefinite' values='0 0;3 {rng.uniform(2, 5):.0f};0 0'/></use>")

# Vampire squid: a dome mantle with ear-like fins, trailing a webbed cloak whose
# arm spokes end in blue lights; the cloak opens and closes as it swims.
TIPS = ((-70, -55), (-116, -40), (-128, 0), (-116, 40), (-70, 55))
tips = (f"<g>{blink('1;.3;1', 2.6)}"
        + "".join(f"<circle cx='{x}' cy='{y}' r='8' fill='{E}' opacity='.35'/><circle cx='{x}' cy='{y}' r='2.8' fill='{W}'/>"
                  for x, y in TIPS)
        + "</g>")
spokes = "".join(f"M-4,{k * 4 - 8}L{x},{y}" for k, (x, y) in enumerate(TIPS))
vampire = (f"<g>{pulse('1 1;1 .68;1 1', 2.6)}"
           "<path d='M-4,-16C-25,-40-50,-52-70,-55Q-90,-40-116,-40Q-112,-18-128,0Q-112,18-116,40Q-90,40-70,55"
           "C-50,52-25,40-4,16Z' fill='url(#v)' opacity='.75'/>"
           f"<path d='{spokes}' {dotted(V2, 2, 6)}/>{tips}</g>"
           "<path d='M30,-18C34,-38 16,-42 10,-22ZM30,18C34,38 16,42 10,22Z' fill='url(#v)'/>"
           "<path d='M48,0C48,-22 20,-24-6,-16L-6,16C20,24 48,22 48,0Z' fill='url(#v)'/>"
           + "".join(f"<circle cx='14' cy='{y}' r='5' fill='{E}'/><circle cx='15' cy='{y}' r='2.2' fill='{W}'/>" for y in (-11, 11)))

# Dragonfish: a dark, slender hunter with a row of flank lights and a glowing chin lure.
ba, bb = "M24,9C30,40 10,70 24,96", "M24,9C18,40 38,70 24,96"
dragonfish = ("<path d='M44,2C40,-6 20,-12-20,-11L-150,-6L-170,-22L-166,0L-170,22L-150,6L-20,11C10,12 30,10 44,2Z' fill='url(#s)'/>"
              f"<circle cx='30' cy='-3' r='3' fill='{C3}'/>"
              f"<g fill='{C1}'>{blink('.95;.3;.95', 2.4)}"
              + "".join(f"<circle cx='{x}' cy='7' r='1.7'/>" for x in range(-10, -145, -13)) + "</g>"
              f"<path d='{ba}' {dotted(C2, 2, 5)}>{wave(ba, bb, 2.6)}</path>"
              + light(24, 96, 3.6, 1.3))

# Sea fireflies (ostracods): little clusters that flash one after another, leaving a fading trail.
fireflies = ""
for k, (cx, cy) in enumerate(((0, 0), (-60, 18), (-120, -8))):
    dots = "".join(f"<circle cx='{cx + rng.randint(-12, 12)}' cy='{cy + rng.randint(-10, 10)}' r='{rng.choice((1.6, 2, 2.4)):g}'/>"
                   for _ in range(5))
    fireflies += (f"<g fill='{C3}' opacity='0'>{blink('0;1;.45;0;0', 2.6, begin=k * .8)}"
                  f"<circle cx='{cx}' cy='{cy}' r='20' fill='{C1}' opacity='.12'/>{dots}</g>")

# ---------- Cast ----------
cast = [
    Actor("jellyfish swarm", jellies, 1.3, 28, "M1100,1250C1000,900 1200,500 1050,-350", rotate=False),
    Actor("siphonophore", siphonophore, 1.3, 30, "M-800,520C200,440 1000,600 2450,500"),
    Actor("comb jelly", comb, 1.4, 24, "M300,1250C500,900 800,600 1000,-300", lanes=((-150, 450), (0, 0))),
    Actor("glowing squid", squid, 1.3, 16, "M2200,200C1500,300 900,600-600,800"),
    Actor("lanternfish", school, 1.5, 22, "M2300,700C1300,640 600,760-700,680", flip=True, lanes=((0, 0), (-250, 80))),
    Actor("vampire squid", vampire, 1.3, 24, "M-400,150C300,300 900,500 2100,900"),
    Actor("dragonfish", dragonfish, 1.4, 24, "M2400,380C1400,330 700,450-800,400", flip=True, lanes=((0, 0), (-120, 220))),
    Actor("sea fireflies", fireflies, 1.2, 26, "M-300,300C300,380 900,220 1900,320", rotate=False, lanes=((0, 0), (-100, 450))),
]

creatures, loop, schedule = parade(cast, rounds=3, seed=3)
snow = specks(16, C2, seed=9, radii=(1, 1.3, 1.6), opacities=(.12, .2, .3), twinkle_every=5, drift=(-14, 18), drift_dur=80)
svg = build_svg(defs, snow, creatures)

DARK = {"bg": ABYSS, "glow": "rgba(43,196,196,.05)", "veil": "#05080d00", "veil_chat": "#05080dbb"}
css = build_css(svg, DARK)

gallery = gallery_svg(defs, cast, ABYSS, fit={"siphonophore": (.75, 120, False)})
write_theme(OUT, "bioluminescence", "Bioluminescence", svg, css, accent="#2bc4c4",
            dark_chrome={"canvas": ABYSS, "sidebar": "#04060a", "chrome": "#04060a", "toolbar": "#04060a"},
            schedule=schedule, loop=loop, gallery=gallery)

"""Generate the Arctic T3 Code theme.

Dot-matrix polar animals take turns crossing behind the chat area, one or two
on screen at a time, while snow falls. Three rounds, each in a shuffled order
and with every animal on a different lane, make up one loop. See
../common/themekit.py for how the background is built.

    python3 generate.py

The output is deterministic (fixed seeds).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from themekit import (Actor, build_css, build_svg, dot_pattern, gallery_svg, parade, pulse, specks,  # noqa: E402
                      spin, write_theme)

OUT = os.path.dirname(os.path.abspath(__file__))

# Navy for dark markings, ice blues for bodies, near-white for snowy fur and feathers.
# Mid-tone blues so the same SVG reads on both the dark and the light background.
N1, N2 = "#2c5684", "#3a6a9c"
I1, I2, I3, W = "#5b9bd5", "#7fb3e3", "#a9cdef", "#e6f3ff"

defs = (dot_pattern("d", 5, 1.75, [I1, I2, I1, I3, I1, I2, I1, W, I2])     # ice blue body
        + dot_pattern("n", 5, 1.75, [N1, N2, N1, N2, I1, N1, N1, N2, I1])  # dark markings
        + dot_pattern("w", 5, 1.75, [I3, W, I3, W, I2, W, I3, W, I3]))     # snowy white


def dots(color, width=3, gap=5):
    return f"fill='none' stroke='{color}' stroke-linecap='round' stroke-dasharray='0 {gap}' stroke-width='{width}'"


def face_left(body):
    """Mirror a +x-facing body for upright (rotate=False) walkers heading left."""
    return f"<g transform='scale(-1,1)'>{body}</g>"


def flapping_wing(d, x, y, dur, fill="url(#w)"):
    """A wing hinged at (x, y) that beats by squashing vertically through zero."""
    return (f"<g transform='translate({x},{y})'><g>{pulse('1 1;1 -.55;1 1', dur)}"
            f"<path d='{d}' fill='{fill}'/></g></g>")


# ---------- Bodies: drawn facing +x, head near the origin ----------

orca = ("<path d='M0,0C-6,-18-40,-30-90,-30L-112,-92L-130,-28C-180,-24-230,-14-260,-4L-300,-34L-290,0L-300,34L-260,4"
        "C-220,14-160,26-100,28L-118,58L-80,28C-40,26-8,16 0,0Z' fill='url(#n)'/>"
        "<ellipse cx='-42' cy='-10' rx='16' ry='6' fill='url(#w)'/>"
        "<path d='M-20,12C-60,22-120,24-170,14C-120,16-60,12-20,4Z' fill='url(#w)'/>")

narwhal = ("<path d='M0,0C-10,-20-60,-26-120,-20C-160,-14-190,-6-210,-2L-240,-24L-232,0L-240,24L-210,2"
           "C-180,10-130,20-80,20C-40,20-10,12 0,0Z' fill='url(#d)'/>"
           f"<path d='M-2,-4L118,-12' {dots(W, 3, 6)}/>"
           "<path d='M-60,14L-84,34L-72,12Z' fill='url(#d)'>" + spin("0 -62 14;16 -62 14;0 -62 14", 2.4) + "</path>")

beluga = ("<path d='M0,4C0,-20-20,-34-50,-32C-90,-36-150,-28-200,-12L-200,12C-150,26-90,30-40,26C-14,24 0,18 0,4Z' fill='url(#w)'/>"
          "<path d='M-196,-10L-232,-34L-222,0L-232,34L-196,10Z' fill='url(#w)'>"
          + spin("0 -200 0;-12 -200 0;12 -200 0;0 -200 0", 2.6) + "</path>"
          "<path d='M-56,18L-80,40L-70,16Z' fill='url(#w)'/>")

defs += ("<g id='pg'>" + spin("-7 0 30;7 0 30;-7 0 30", .55)
         + "<ellipse rx='15' ry='30' fill='url(#n)'/><ellipse cx='5' cy='4' rx='9' ry='22' fill='url(#w)'/>"
         "<circle cx='3' cy='-28' r='11' fill='url(#n)'/><path d='M12,-31L25,-27L12,-24Z' fill='url(#d)'/>"
         "<path d='M-6,28L8,32M2,28L16,32' " + dots(I1, 3, 5) + "/></g>")
penguins = ("<use href='#pg'/><use href='#pg' x='-52' y='4'/>"
            "<g transform='translate(-102,10) scale(.8)'><use href='#pg'/></g>")

# Birds are drawn seen from below, wings spread; flapping squashes the wingspan.
defs += "<path id='ow' d='M14,-10C6,-46-14,-96-44,-118C-58,-92-62,-52-50,-12Z'/><path id='tw' d='M6,-4C-2,-34-6,-76 4,-118C-18,-86-30,-44-26,-4Z'/>"
owl = ("<g fill='url(#w)'><g>" + pulse("1 1;1 .3;1 1", 1.1) + "<use href='#ow'/><use href='#ow' transform='scale(1,-1)'/></g>"
       "<ellipse cx='-12' rx='42' ry='19'/><circle cx='28' r='17'/><path d='M-48,-11L-76,-16L-76,16L-48,11Z'/></g>"
       "<path d='M44,-3L52,0L44,3Z' fill='url(#n)'/>")

tern = ("<g fill='url(#w)'><g>" + pulse("1 1;1 .25;1 1", .55) + "<use href='#tw'/><use href='#tw' transform='scale(1,-1)'/></g>"
        "<ellipse cx='-6' rx='34' ry='7'/><circle cx='26' r='8'/><path d='M-32,-4L-74,-22L-54,0L-74,22L-32,4Z'/></g>"
        "<circle cx='26' r='5' fill='url(#n)'/><path d='M33,-2L46,0L33,2Z' fill='url(#d)'/>")

defs += ("<g id='lg'><path d='M0,-4L3,24' " + dots(W, 3.4, 5) + ">"
         + spin("0 0 -4;24 0 -4;0 0 -4;-24 0 -4;0 0 -4", .6) + "</path></g>")
fox = ("<use href='#lg' x='6'/><use href='#lg' x='-74'/>"
       "<path d='M-92,-20C-122,-30-152,-20-168,-2C-150,4-120,-2-96,-8Z' fill='url(#w)'/>"
       "<path d='M56,-18L40,-26L36,-42L28,-30L20,-40L16,-28C0,-30-40,-32-80,-28C-96,-26-100,-12-92,-2"
       "C-60,2-20,2 4,-2L30,-10Z' fill='url(#w)'/><circle cx='56' cy='-18' r='2.5' fill='" + N1 + "'/>")

seal = ("<path d='M0,0C-4,-14-24,-22-50,-22C-90,-22-130,-14-160,-6L-188,-22L-180,0L-188,22L-160,6"
        "C-130,14-90,20-50,20C-24,20-4,14 0,0Z' fill='url(#d)'/>"
        "<path d='M-48,14L-70,36L-58,14Z' fill='url(#d)'>" + spin("0 -50 14;20 -50 14;0 -50 14", 1.6) + "</path>"
        "<ellipse cx='-90' cy='-10' rx='28' ry='7' fill='url(#n)'/>"
        f"<path d='M-4,2L14,-2M-4,6L14,8' {dots(W, 2, 4)}/>")

walrus = ("<path d='M-138,0L66,0L50,18L-120,20Z' fill='url(#w)' opacity='.55'/>"  # ice floe, kept faint so the walrus reads first
          "<g>" + pulse("1 1;1.03 .96;1 1", 3.2)
          + "<path d='M40,-18C44,-40 22,-54 0,-52C-40,-50-90,-36-112,-6L-120,0L40,0Z' fill='url(#d)'/></g>"
          "<circle cx='30' cy='-34' r='3' fill='" + N1 + "'/>"
          f"<path d='M34,-14L38,14M24,-14L26,14' {dots(W, 3.4, 5)}/>")

bear = ("<g>" + pulse("1 1;1 1.04;1 1", .8)
        + "<path d='M84,-36C88,-40 88,-46 82,-48L64,-52C56,-56 46,-56 38,-50C20,-60-20,-64-60,-58C-90,-54-110,-40-112,-20"
        "L-108,0L-92,0L-88,-16L-70,-14L-66,0L-50,0L-50,-14C-20,-12 0,-14 16,-18L18,0L34,0L36,-20L44,0L60,0L54,-26"
        "C64,-30 74,-32 84,-36Z' fill='url(#w)'/><circle cx='50' cy='-54' r='6' fill='url(#w)'/>"
        "<circle cx='84' cy='-44' r='3' fill='" + N1 + "'/></g>")

hare = ("<g>" + "<animateTransform attributeName='transform' type='translate' dur='.7s' repeatCount='indefinite' "
        "values='0 0;0 -46;0 0' keyTimes='0;.45;1' calcMode='spline' keySplines='.2 .7 .4 1;.6 0 .8 .3'/>"
        "<path d='M30,-26C30,-40 18,-44 8,-40C-10,-44-40,-40-56,-24C-66,-12-60,0-46,0L10,0C24,0 30,-10 30,-26Z' fill='url(#w)'/>"
        "<path d='M14,-40C4,-70 0,-80 6,-84C14,-74 20,-60 20,-42ZM22,-40C20,-66 24,-78 30,-80C34,-68 30,-52 26,-38Z' fill='url(#w)'/>"
        "<circle cx='-58' cy='-18' r='9' fill='url(#w)'/></g>")

puffin = (flapping_wing("M0,0C-10,-30-34,-44-56,-40C-40,-30-28,-16-22,0Z", -10, -4, .3, "url(#n)")
          + "<ellipse cx='-20' cy='0' rx='34' ry='17' fill='url(#n)'/><ellipse cx='-12' cy='6' rx='22' ry='9' fill='url(#w)'/>"
          "<circle cx='8' cy='-8' r='14' fill='url(#w)'/><path d='M20,-18L42,-6L20,4Z' fill='url(#d)'/>"
          "<circle cx='10' cy='-12' r='3' fill='" + N1 + "'/>")

# ---------- Snow: one tile of flakes, scrolled down in three layers for depth ----------
defs += specks(56, I3, seed=5, radii=(1.4, 1.8, 2.4), opacities=(.35, .5, .7), twinkle_every=0,
               drift=None).replace("<g ", "<g id='sn' ", 1)


def snow_layer(dur, dx, scale, opacity, sway):
    return (f"<g opacity='{opacity}'><g><animateTransform attributeName='transform' type='translate' dur='{sway}s' "
            f"repeatCount='indefinite' values='0 0;24 0;0 0'/>"
            f"<g transform='translate({dx},0) scale({scale})'><g><animateTransform attributeName='transform' type='translate' "
            f"dur='{dur}s' repeatCount='indefinite' values='0 0;0 1000'/><use href='#sn'/><use href='#sn' y='-1000'/></g></g></g></g>")


snow = snow_layer(60, 0, 1, .9, 9) + snow_layer(95, 530, .7, .55, 13)

# ---------- Cast ----------
# Paths start and end well off-screen. lanes = ((dx range), (dy range)) shifts
# the path on each pass. Ground animals walk along the bottom with tight lanes.
H = "M-{s},{y}C300,{a} 1000,{b} 2300,{c}"
R = "M2300,{y}C1300,{a} 600,{b} -{e},{c}"
ground = ((0, 0), (-15, 10))
cast = [
    Actor("orca", orca, 1.4, 18, H.format(s=800, y=560, a=500, b=620, c=540)),
    Actor("narwhal", narwhal, 1.4, 22, R.format(y=430, a=470, b=380, c=440, e=500), flip=True),
    Actor("beluga", beluga, 1.4, 22, H.format(s=600, y=500, a=560, b=450, c=520), opacity=.85),
    Actor("penguins", penguins, 1.8, 26, "M-350,800L1900,800", rotate=False, lanes=ground),
    Actor("snowy owl", owl, 1.3, 16, H.format(s=400, y=280, a=220, b=330, c=240), lanes=((0, 0), (-80, 160))),
    Actor("arctic fox", face_left(fox), 1.6, 20, "M1900,812L-450,812", rotate=False, lanes=ground),
    Actor("harp seal", seal, 1.4, 18, "M2200,300C1500,420 900,700-500,760", flip=True),
    Actor("walrus", walrus, 1.3, 30, "M-350,800C200,790 600,812 1000,798S1600,790 1950,804", rotate=False, lanes=ground),
    Actor("polar bear", bear, 1.4, 26, "M-350,820L1950,820", rotate=False, lanes=ground),
    Actor("arctic tern", tern, 1.3, 11, R.format(y=330, a=260, b=380, c=300, e=300), lanes=((0, 0), (-120, 140))),
    Actor("snow hare", face_left(hare), 1.3, 16, "M1900,826L-300,826", rotate=False, lanes=ground),
    Actor("puffin", puffin, 1.7, 13, H.format(s=300, y=360, a=300, b=420, c=340), lanes=((0, 0), (-120, 160))),
]

animals, loop, schedule = parade(cast, rounds=3, seed=23)
svg = build_svg(defs, snow, animals)

DARK = {"bg": "#0c1117", "glow": "rgba(111,168,220,.08)", "veil": "#0c111700", "veil_chat": "#0c111799"}
LIGHT = {"bg": "#eef4f8", "glow": "rgba(91,155,213,.14)", "veil": "#eef4f826", "veil_chat": "#eef4f8b8"}
css = build_css(svg, DARK, LIGHT)

gallery = gallery_svg(defs, cast, DARK["bg"], fit={"orca": (.8, 60, False)})
write_theme(OUT, "arctic", "Arctic", svg, css, accent="#5b9bd5",
            dark_chrome={"canvas": DARK["bg"], "sidebar": "#090d12", "chrome": "#090d12", "toolbar": "#090d12"},
            light_chrome={"canvas": LIGHT["bg"], "sidebar": "#e2eaf1", "chrome": "#e2eaf1", "toolbar": "#e2eaf1"},
            schedule=schedule, loop=loop, gallery=gallery)

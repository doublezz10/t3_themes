"""Generate the Deep Space T3 Code theme.

Dot-matrix space objects take turns drifting behind the chat area, one or two
on screen at a time, over a twinkling starfield. Three rounds, each in a
shuffled order and with every object on a different lane, make up one loop.
See ../common/themekit.py for how the background is built.

    python3 generate.py

The output is deterministic (fixed seeds). Dark mode only.
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from themekit import (Actor, blink, build_css, build_svg, dot_pattern, dotted, gallery_svg, parade, specks,  # noqa: E402
                      spin, wave, write_theme)

OUT = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(5)
BG = "#0b0a14"
V1, V2, V3, C, W = "#5b4fd6", "#7b6cf0", "#9d8cff", "#5ad1e6", "#e6e9ff"

# 'd' is the violet body texture, 'c' the cyan accent texture.
defs = (dot_pattern("d", 5, 1.75, [V1, V2, V1, V3, V1, V2, V1, W, V2])
        + dot_pattern("c", 4, 1.45, [C, V3, C, W, C, V2, C, V3, C]))

# ---------- Bodies: drawn facing +x, head near the origin ----------

# Comet: a bright head with three dotted tail streaks that shimmer.
comet = (f"<path d='M-12,-4L-250,-24' {dotted(V3, 3, 6)}>{blink('1;.4;1', 1.3)}</path>"
         f"<path d='M-12,0L-290,0' {dotted(C, 3.4, 6)}>{blink('.5;1;.5', 1.1)}</path>"
         f"<path d='M-12,4L-240,22' {dotted(V2, 3, 6)}>{blink('1;.5;1', 1.7)}</path>"
         "<circle r='17' fill='url(#c)'/>")

# Ringed planet: back half of the ring, planet, then the front half on top.
planet = ("<g transform='rotate(-16)'>"
          f"<path d='M-100,0A100,24 0 0 1 100,0' {dotted(C, 3, 7)}/>"
          "<circle r='56' fill='url(#d)'/>"
          f"<path d='M100,0A100,24 0 0 1-100,0' {dotted(C, 3.4, 7)}/></g>")

# Satellite: a body, two solar panels, a blinking beacon; it rocks gently.
satellite = ("<g>" + spin("-10;10;-10", 7)
             + "<rect x='-72' y='-13' width='52' height='26' fill='url(#d)'/>"
             "<rect x='20' y='-13' width='52' height='26' fill='url(#d)'/>"
             f"<path d='M-20,0L20,0M0,-16L0,-44' {dotted(V3, 3, 5)}/>"
             "<rect x='-15' y='-16' width='30' height='32' fill='url(#c)'/>"
             f"<circle cy='-46' r='4' fill='{W}'>{blink('1;.1;1', 1.4)}</circle></g>")

# Astronaut: tumbles slowly end over end.
astronaut = ("<g>" + spin("0;360", 18)
             + "<rect x='-30' y='-26' width='14' height='40' rx='4' fill='url(#d)'/>"  # backpack
             "<path d='M-18,-24L18,-24L20,18L-20,18Z' fill='url(#d)'/>"  # torso
             "<path d='M18,-20L42,-6L38,2L16,-8ZM-16,-18L-34,4L-27,10L-12,-4Z' fill='url(#d)'/>"  # arms
             "<path d='M-18,16L-24,56L-12,56L-4,18ZM4,18L14,56L26,54L18,16Z' fill='url(#d)'/>"  # legs
             "<circle cy='-44' r='21' fill='url(#c)'/>"  # helmet
             f"<ellipse cx='6' cy='-44' rx='12' ry='9' fill='{BG}' opacity='.75'/></g>")  # visor

# Rocket: nose forward, window, fins, flickering exhaust.
ex = [("M-52,0L-118,0", "M-52,0L-150,0", C, 4), ("M-52,-8L-100,-12", "M-52,-8L-124,-16", V3, 3),
      ("M-52,8L-100,12", "M-52,8L-124,16", V3, 3)]
rocket = ("".join(f"<path d='{a}' {dotted(col, w, 6)}>{wave(a, b, .35)}</path>" for a, b, col, w in ex)
          + "<path d='M62,0C42,-17 0,-19-52,-16L-52,16C0,19 42,17 62,0Z' fill='url(#d)'/>"
          "<path d='M-26,-16L-60,-44L-50,-16ZM-26,16L-60,44L-50,16Z' fill='url(#c)'/>"
          f"<circle cx='16' r='8' fill='{BG}'/><circle cx='16' r='5' fill='{C}'/>")

# UFO: saucer and dome, rim lights chasing, a faint beam that flickers on and off.
ufo_lights = "".join(f"<circle cx='{x}' cy='4' r='4' fill='{W}'>{blink('1;.15;1', 1.2, begin=-i * .24)}</circle>"
                     for i, x in enumerate((-48, -24, 0, 24, 48)))
ufo = ("<g><animateTransform attributeName='transform' type='translate' dur='3s' repeatCount='indefinite' values='0 0;0 -9;0 0'/>"
       f"<path d='M-18,18L-58,130M0,18L0,136M18,18L58,130' {dotted(C, 3, 8)} opacity='0'>{blink('0;0;.7;0', 5)}</path>"
       "<path d='M-30,-6C-30,-42 30,-42 30,-6Z' fill='url(#c)'/>"
       "<ellipse rx='74' ry='17' fill='url(#d)'/>" + ufo_lights + "</g>")

# Asteroid cluster: three lumpy rocks, each spinning on its own axis.
defs += "<path id='ast' d='M30,-10L18,-28L-8,-31L-28,-14L-26,12L-8,29L20,23Z' fill='url(#d)'/>"
asteroids = "".join(f"<g transform='translate({x},{y}) scale({s})'><g>{spin(v, d)}<use href='#ast'/></g></g>"
                    for x, y, s, v, d in ((0, 0, 1.3, "0;360", 14), (-80, -40, .7, "360;0", 9), (-70, 45, .55, "0;360", 11)))

# Space station: a slowly turning dotted ring with spokes, a hub, and solar arms.
station = ("<rect x='-150' y='-10' width='70' height='20' fill='url(#d)'/><rect x='80' y='-10' width='70' height='20' fill='url(#d)'/>"
           f"<path d='M-80,0L-54,0M54,0L80,0' {dotted(V3, 3, 5)}/>"
           "<g>" + spin("0;360", 40)
           + f"<circle r='52' {dotted(C, 4, 8)}/><path d='M-52,0L52,0M0,-52L0,52' {dotted(V3, 3, 6)}/></g>"
           "<circle r='15' fill='url(#c)'/>")

# Moon: dotted disc with dark craters.
moon = ("<circle r='46' fill='url(#d)'/>"
        + "".join(f"<circle cx='{x}' cy='{y}' r='{r}' fill='{BG}' opacity='.85'/>"
                  for x, y, r in ((-14, -16, 13), (19, 7, 10), (-8, 24, 7), (22, -22, 6))))

# Space whale: Deep Sea's humpback, with a few cyan sparkles in its wake.
space_whale = ("<path d='M0,0C-10,-35-110,-55-250,-42C-350,-32-420,-14-470,-4L-470,4C-400,24-300,44-180,46C-90,46-20,30 0,0Z' fill='url(#d)'/>"
               "<path d='M-130,36C-150,76-196,116-246,124C-210,94-186,64-166,38Z' fill='url(#d)'>" + spin("0 -150 36;14 -150 36;0 -150 36", 4) + "</path>"
               "<path d='M-462,-4L-524,-48L-504,0L-524,48L-462,4Z' fill='url(#d)'>" + spin("0 -470 0;-14 -470 0;14 -470 0;0 -470 0", 4) + "</path>"
               + "".join(f"<circle cx='{x}' cy='{y}' r='3' fill='{C}'>{blink('1;0;1', d, begin=-b)}</circle>"
                         for x, y, d, b in ((-560, -20, 1.6, 0), (-600, 14, 2.1, .7), (-650, -6, 1.8, 1.2), (-700, 22, 2.4, .4))))

# ---------- Cast ----------
# Paths start and end well off-screen; lanes shift each pass (defaults: +-170
# across horizontal paths, +-320 across vertical ones).
cast = [
    Actor("comet", comet, 1.2, 10, "M-500,120C300,260 1000,520 2200,860", lanes=((0, 0), (-60, 120))),
    Actor("ringed planet", planet, 1.2, 40, "M2300,330C1500,290 700,380-400,320", rotate=False, opacity=.85),
    Actor("satellite", satellite, 1.3, 20, "M-300,800C400,640 1100,420 1950,180", rotate=False),
    Actor("astronaut", astronaut, 1.3, 26, "M1900,880C1300,700 800,560-300,380", rotate=False),
    Actor("rocket", rocket, 1.3, 12, "M-400,900C300,720 900,420 2100,-200"),
    Actor("ufo", ufo, 1.2, 22, "M2300,300C1700,200 1300,450 800,300S100,200-700,320", rotate=False, lanes=((0, 0), (-60, 260))),
    Actor("asteroids", asteroids, 1.2, 26, "M1950,120C1300,320 700,560-350,820", rotate=False, opacity=.85),
    Actor("space station", station, 1.1, 34, "M-500,620C300,660 1000,580 2100,640", rotate=False, opacity=.85),
    Actor("moon", moon, 1.3, 30, "M300,1200C380,800 560,400 520,-200", rotate=False, opacity=.85, lanes=((-150, 650), (0, 0))),
    Actor("space whale", space_whale, 1.1, 38, "M2300,470C1300,430 600,520-1100,460", flip=True, opacity=.75),
]

objects, loop, schedule = parade(cast, rounds=3, seed=17)
stars = specks(44, W, seed=3, radii=(1.5, 2, 2.6), opacities=(.3, .45, .6, .8), twinkle_every=3, twinkle=(3, 7),
               drift=(-14, -6), drift_dur=90)
cyan_stars = specks(10, C, seed=9, radii=(1.8, 2.6), opacities=(.4, .6), twinkle_every=2, drift=None)
svg = build_svg(defs, stars, cyan_stars, objects)

DARK = {"bg": BG, "glow": "rgba(123,108,240,.10)", "veil": "#0b0a1400", "veil_chat": "#0b0a1480"}
DARK.update(accent="#7b6cf0", sidebar="#08070f")
css = build_css(svg, DARK)

gallery = gallery_svg(defs, cast, BG, fit={"space whale": (.55, 120, False)})
write_theme(OUT, "deep-space", "Deep Space", svg, css, accent="#7b6cf0",
            dark_chrome={"canvas": BG, "sidebar": "#08070f", "chrome": "#08070f", "toolbar": "#08070f"},
            schedule=schedule, loop=loop, gallery=gallery)

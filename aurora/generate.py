"""Generate the Aurora T3 Code theme.

Curtains of northern lights ripple over a dotted mountain-and-pine horizon under a
twinkling starfield. Each curtain is a row of dotted vertical rays whose base line
and height undulate through three phases, shading from bright green at the lower
edge to violet at the top. Segments of each curtain brighten and fade on their own
slow cycles, so the sky keeps changing. Now and then a shooting star, a satellite
or a flock of birds crosses, spaced well apart. See ../common/themekit.py.

    python3 generate.py

The output is deterministic. Dark mode only.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from themekit import Actor, blink, build_css, build_svg, dot_pattern, parade, specks, write_theme  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(5)

BG = "#070b12"
GREEN_HI, GREEN, GREEN_LO = "#8ff5d2", "#3fe0b0", "#2fc79a"
BLUE, VIOLET = "#5a7cf0", "#7b6cf0"
STAR = "#cfe0ff"
SPINE = "keySplines='.45 0 .55 1;.45 0 .55 1;.45 0 .55 1' calcMode='spline'"

defs = (dot_pattern("m", 6, 1.7, ["#1a2840", "#22324d", "#1a2840", "#2a3d5c", "#1a2840", "#22324d", "#1a2840", "#33496b", "#22324d"])
)


# ---------- Curtains ----------
# Each curtain is a ribbon whose lower edge ripples and whose ragged top fades out,
# tapering to points at both ends, filled with a bright-green-to-violet gradient.
# Two masks shape the whole sky: slowly drifting vertical ray streaks modulate the
# brightness, and a fixed grid of dots gives the dot-matrix look.

def ribbon_phase(x0, x1, step, base, amp, height, phase, k):
    xs = list(range(x0, x1 + 1, step))
    low = [base + amp * math.sin(x / 210 + phase + k) + amp * .45 * math.sin(x / 95 - phase * .7 + k) for x in xs]
    env = [math.sin(math.pi * i / (len(xs) - 1)) ** .6 for i in range(len(xs))]  # taper to points at both ends
    up = [y - e * height * (.5 + .5 * (.5 + .5 * math.sin(x / 130 + phase * 1.3 + k)) + .16 * math.sin(x / 37 + phase * 2 + k))
          for x, y, e in zip(xs, low, env)]
    pts = list(zip(xs, low)) + list(zip(xs, up))[::-1]
    return "M" + "L".join(f"{x},{y:.0f}" for x, y in pts) + "Z"


def curtain(cid, x0, x1, base, amp, height, dur, fade, seed):
    top, bottom = base - height * .95, base + amp
    grad = (f"<linearGradient id='g{cid}' gradientUnits='userSpaceOnUse' x1='0' y1='{bottom:.0f}' x2='0' y2='{top:.0f}'>"
            f"<stop offset='0' stop-color='{GREEN_HI}'/><stop offset='.1' stop-color='{GREEN}'/>"
            f"<stop offset='.35' stop-color='{GREEN_LO}' stop-opacity='.7'/><stop offset='.6' stop-color='{BLUE}' stop-opacity='.4'/>"
            f"<stop offset='.85' stop-color='{VIOLET}' stop-opacity='.12'/><stop offset='1' stop-color='{VIOLET}' stop-opacity='0'/></linearGradient>")
    phases = [ribbon_phase(x0, x1, 48, base, amp, height, p * 2 * math.pi / 3, seed) for p in (0, 1, 2, 0)]
    shape = (f"<path id='r{cid}' d='{phases[0]}'><animate attributeName='d' dur='{dur}s' repeatCount='indefinite' {SPINE} "
             f"values='{';'.join(phases)}'/></path>")
    fdur, fvals = fade
    # 'screen' blending: overlapping curtains add light instead of the upper,
    # semi-transparent violet of one curtain darkening the green of another.
    body = f"<use href='#r{cid}' fill='url(#g{cid})' style='mix-blend-mode:screen'>{blink(fvals, fdur, begin=-rng.randint(0, fdur))}</use>"
    return grad + shape, body


ray_stops = ""
for off, a in [(0, .55), (.06, 1), (.1, .55), (.22, .6), (.27, 1), (.31, .65), (.36, .95), (.42, .55), (.55, .6), (.6, .95),
               (.64, .55), (.74, .65), (.79, 1), (.85, .55), (1, .55)]:
    ray_stops += f"<stop offset='{off:g}' stop-color='#fff' stop-opacity='{a:g}'/>"
defs += (f"<linearGradient id='ray' gradientUnits='userSpaceOnUse' x1='0' x2='340' spreadMethod='repeat'>{ray_stops}"
         "<animateTransform attributeName='gradientTransform' type='translate' values='0;340' dur='70s' repeatCount='indefinite'/>"
         "</linearGradient>")
defs += dot_pattern("w", 6, 2.1, ["#fff", "#ccc", "#eee", "#aaa", "#fff", "#ddd", "#eee", "#bbb", "#fff"])
for mid, fill in (("dm", "w"), ("rm", "ray")):
    defs += f"<mask id='{mid}' maskUnits='userSpaceOnUse' x='0' y='0' width='1600' height='1000'><rect width='1600' height='1000' fill='url(#{fill})'/></mask>"

d1, c1 = curtain("a", -60, 1340, 500, 44, 300, 46, (61, ".55;1;.7;.95;.55"), 1)
d2, c2 = curtain("b", 560, 1700, 395, 36, 230, 58, (79, ".2;.7;.35;.8;.2"), 2)
d3, c3 = curtain("c", 200, 1300, 615, 26, 150, 38, (53, ".2;.55;.1;.5;.2"), 3)
defs += d1 + d2 + d3
# Fainter, higher curtain first so the bright main one sits in front.
sky = f"<g mask='url(#dm)'><g mask='url(#rm)'><g opacity='.8'>{c2}</g>{c3}{c1}</g></g>"
haze = ("<linearGradient id='hz' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#2fc79a' stop-opacity='0'/>"
        "<stop offset='1' stop-color='#2fc79a' stop-opacity='.12'/></linearGradient>")
defs += haze
glow = "<rect y='560' width='1600' height='320' fill='url(#hz)'/>"

# ---------- Horizon: far ridge, then near forested ridge ----------

def ridge(points):
    return "M-20,1000" + "".join(f"L{x},{y}" for x, y in points) + "L1620,1000Z"


far = []
x = -20
while x < 1640:
    far.append((x, rng.randint(735, 805)))
    x += rng.randint(70, 140)
near_pts, trees = [], ""
x = -20
while x < 1640:
    y = rng.randint(845, 875)
    near_pts.append((x, y))
    x += rng.randint(60, 110)


def near_y(x):
    for (xa, ya), (xb, yb) in zip(near_pts, near_pts[1:]):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) / (xb - xa)
    return 860


x = -10
while x < 1620:
    h = rng.randint(28, 62)
    w = h * .32
    y = near_y(x) + 6
    trees += f"M{x - w:.0f},{y:.0f}L{x:.0f},{y - h:.0f}L{x + w:.0f},{y:.0f}Z"
    x += rng.randint(20, 58)

defs += f"<path id='fr' d='{ridge(far)}'/><path id='nr' d='{ridge(near_pts)}{trees}'/>"
horizon = ("<use href='#fr' fill='#080d16'/><use href='#fr' fill='url(#m)' opacity='.7'/>"
           "<use href='#nr' fill='#020407'/><use href='#nr' fill='url(#m)' opacity='.3'/>")

# ---------- Occasional events ----------

streak = (f"<linearGradient id='ss' x1='1' y1='0' x2='0' y2='0'><stop offset='0' stop-color='#ffffff'/>"
          f"<stop offset='1' stop-color='{STAR}' stop-opacity='0'/></linearGradient>")
defs += streak
shooting_star = ("<path d='M0,0L-170,0' stroke='url(#ss)' stroke-width='2.4' stroke-linecap='round' stroke-dasharray='0 5'/>"
                 "<circle r='3' fill='#ffffff'/>")
satellite = f"<circle r='2.4' fill='{STAR}'>{blink('1;.35;1', 2.8)}</circle>"

fa, fb = "M-7,-4L0,0L7,-4", "M-7,3L0,0L7,3"
defs += (f"<path id='bd' d='{fa}' fill='none' stroke='#9fb4d8' stroke-width='1.8' stroke-linecap='round'>"
         f"<animate attributeName='d' dur='.9s' repeatCount='indefinite' values='{fa};{fb};{fa}'/></path>")
flock = "".join(f"<use href='#bd' x='{dx}' y='{dy}'/>" for dx, dy in
                [(0, 0), (-18, -9), (-18, 9), (-36, -17), (-36, 18), (-55, -25), (-54, 27)])

events = [
    Actor("shooting star", shooting_star, 1, 2.6, "M250,-120L1950,520", lanes=((-250, 250), (0, 140))),
    Actor("shooting star 2", shooting_star, .8, 2.2, "M1400,-120L-300,440", lanes=((-200, 200), (0, 120))),
    Actor("satellite", satellite, 1, 46, "M-60,120L1660,300", rotate=False, lanes=((0, 0), (-40, 160))),
    Actor("birds", flock, 1.2, 34, "M1750,330C1200,300 600,380-150,320", flip=True, opacity=.7, lanes=((0, 0), (-90, 90))),
]
# Negative overlap leaves quiet sky between events.
moving, loop, schedule = parade(events, rounds=3, overlap=-22, seed=4)

stars = specks(32, STAR, seed=9, radii=(1, 1.3, 1.7), opacities=(.25, .4, .6, .8), twinkle_every=3,
               twinkle=(3, 8), drift=(-8, -3), drift_dur=90, h=760)

svg = build_svg(defs, stars, moving, sky, glow, horizon)

DARK = {"bg": BG, "glow": "rgba(63,224,176,.05)", "veil": "#070b1200", "veil_chat": "#070b12a8"}
css = build_css(svg, DARK)
write_theme(OUT, "aurora", "Aurora", svg, css, accent="#2fc79a",
            dark_chrome={"canvas": BG, "sidebar": "#05080d", "chrome": "#05080d", "toolbar": "#05080d"},
            schedule=schedule, loop=loop)

"""Generate the Aurora T3 Code theme.

Curtains of northern lights ripple over snow-capped mountain ranges and a pine
forest under a twinkling starfield. Each curtain is a dotted ribbon shading from
bright green at the lower edge to violet at the top. Its shape drifts through five
random phases at uneven tempos, and its brightness follows its own irregular
cycle (all prime-length, so the sky as a whole almost never repeats). A rare
fourth curtain flares up now and then, and the snowcaps catch its light. Shooting
stars, a fireball, a satellite and flocks of birds cross at uneven intervals, the
birds on a different curving route every time. See ../common/themekit.py.

    python3 generate.py

The output is deterministic. Dark mode only.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
import critters  # noqa: E402
from themekit import Actor, blink, build_css, build_svg, dot_pattern, parade, specks, write_theme  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(5)

BG = "#070b12"
GREEN_HI, GREEN, GREEN_LO = "#8ff5d2", "#3fe0b0", "#2fc79a"
BLUE, VIOLET = "#5a7cf0", "#7b6cf0"
STAR = "#cfe0ff"

defs = (dot_pattern("m", 6, 1.7, ["#1a2840", "#22324d", "#1a2840", "#2a3d5c", "#1a2840", "#22324d", "#1a2840", "#33496b", "#22324d"])
)


# ---------- Curtains ----------
# Each curtain is a ribbon whose lower edge ripples and whose ragged top fades out,
# tapering to points at both ends, filled with a bright-green-to-violet gradient.
# Two masks shape the whole sky: slowly drifting vertical ray streaks modulate the
# brightness, and a fixed grid of dots gives the dot-matrix look.

def irregular(n, rng):
    """n+1 keyTimes from 0 to 1 with uneven spacing."""
    cuts = sorted(rng.uniform(.08, .92) for _ in range(n - 1))
    return "0;" + ";".join(f"{c:.2f}" for c in cuts) + ";1"


def ribbon_phase(x0, x1, step, base, amp, height, phase, k):
    xs = list(range(x0, x1 + 1, step))
    low = [base + amp * math.sin(x / 210 + phase + k) + amp * .45 * math.sin(x / 95 - phase * .7 + k) for x in xs]
    env = [math.sin(math.pi * i / (len(xs) - 1)) ** .6 for i in range(len(xs))]  # taper to points at both ends
    up = [y - e * height * (.5 + .5 * (.5 + .5 * math.sin(x / 130 + phase * 1.3 + k)) + .16 * math.sin(x / 61 + phase * 2 + k))
          for x, y, e in zip(xs, low, env)]
    pts = [(x, round(y)) for x, y in list(zip(xs, low)) + list(zip(xs, up))[::-1]]
    # Relative line-tos (every phase has the same commands, so they still animate):
    # about 40% shorter than absolute coordinates.
    d = f"M{pts[0][0]},{pts[0][1]}l"
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        d += f"{xb - xa},{yb - ya} "
    return d.rstrip().replace(" -", "-").replace(",-", "-") + "z"


def curtain(cid, x0, x1, base, amp, height, dur, fade, seed):
    crng = random.Random(seed)
    ph = [crng.uniform(0, 2 * math.pi) for _ in range(4)]
    phases = [ribbon_phase(x0, x1, 72, base, amp, height, p, seed) for p in ph + ph[:1]]
    shape = (f"<path id='r{cid}' d='{phases[0]}'><animate attributeName='d' dur='{dur}s' repeatCount='indefinite' "
             f"calcMode='spline' keySplines='{';'.join(['.45 0 .55 1'] * 4)}' keyTimes='{irregular(4, crng)}' "
             f"values='{';'.join(phases)}'/></path>")
    fdur, fvals = fade
    if isinstance(fvals, tuple):  # (lo, hi, n): n random brightness levels at uneven times
        lo, hi, n = fvals
        lv = [f"{crng.uniform(lo, hi):.2f}" for _ in range(n)]
        fvals = ";".join(lv + lv[:1])
        fade_kt = irregular(n, crng)
    else:
        fade_kt = None
    # 'screen' blending: overlapping curtains add light instead of the upper,
    # semi-transparent violet of one curtain darkening the green of another.
    anim = blink(fvals, fdur, begin=-rng.randint(0, fdur))
    if fade_kt:
        anim = anim.replace("values=", f"keyTimes='{fade_kt}' values=")
    body = f"<use href='#r{cid}' fill='url(#g)' style='mix-blend-mode:screen'>{anim}</use>"
    return shape, body, anim


# One gradient for every curtain, stretched over each one's own bounding box:
# bright green along the lower edge, through blue, fading out in violet at the top.
defs += ("<linearGradient id='g' x1='0' y1='1' x2='0' y2='0'>"
         f"<stop offset='0' stop-color='{GREEN_HI}'/><stop offset='.08' stop-color='{GREEN}'/>"
         f"<stop offset='.25' stop-color='{GREEN_LO}' stop-opacity='.6'/><stop offset='.45' stop-color='{BLUE}' stop-opacity='.25'/>"
         f"<stop offset='.65' stop-color='{VIOLET}' stop-opacity='.08'/><stop offset='.8' stop-color='{VIOLET}' stop-opacity='0'/></linearGradient>")
ray_stops = ""
for off, a in [(0, .55), (.06, 1), (.1, .55), (.22, .6), (.27, 1), (.31, .65), (.36, .95), (.42, .55), (.55, .6), (.6, .95),
               (.64, .55), (.74, .65), (.79, 1), (.85, .55), (1, .55)]:
    g = round(255 * a)  # a mask reads brightness, so a grey stop does what white-at-opacity did
    ray_stops += f"<stop offset='{off:g}' stop-color='#{g:02x}{g:02x}{g:02x}'/>"
defs += (f"<linearGradient id='ray' gradientUnits='userSpaceOnUse' x1='0' x2='340' spreadMethod='repeat'>{ray_stops}"
         "<animateTransform attributeName='gradientTransform' type='translate' values='0;70;95;230;340' keyTimes='0;.3;.45;.7;1' dur='83s' repeatCount='indefinite'/>"
         "</linearGradient>")
defs += dot_pattern("w", 6, 2.1, ["#fff", "#ccc", "#eee", "#aaa", "#fff", "#ddd", "#eee", "#bbb", "#fff"])
for mid, fill in (("dm", "w"), ("rm", "ray")):
    defs += f"<mask id='{mid}'><rect width='1600' height='1000' fill='url(#{fill})'/></mask>"

# Durations are primes, so the curtains drift in and out of step and the sky
# as a whole repeats only after hours.
d1, c1, _ = curtain("a", -60, 1340, 500, 44, 300, 47, (61, (.5, 1, 6)), 1)
d2, c2, _ = curtain("b", 560, 1700, 390, 36, 230, 59, (79, (.15, .8, 6)), 2)
d3, c3, _ = curtain("c", 200, 1300, 610, 26, 150, 41, (53, (.1, .6, 5)), 3)
# The flare: mostly hidden, it surges up for a few seconds on an odd cycle.
d4, c4, flare = curtain("d", 380, 1500, 430, 50, 330, 31, (157, "0;0;.95;.5;.8;0;0"), 4)
c4 = c4.replace("values='0;0", "keyTimes='0;.55;.6;.66;.7;.78;1' values='0;0")
flare = flare.replace("values='0;0", "keyTimes='0;.55;.6;.66;.7;.78;1' values='0;0")
defs += d1 + d2 + d3 + d4
# Fainter, higher curtain first so the bright main one sits in front.
# A faint diffuse glow behind the curtains, so the sky between them isn't pitch black.
defs += (f"<radialGradient id='dg'><stop offset='0' stop-color='{GREEN}' stop-opacity='.12'/>"
         f"<stop offset='.6' stop-color='{GREEN_LO}' stop-opacity='.05'/><stop offset='1' stop-color='{BLUE}' stop-opacity='0'/></radialGradient>")
diffuse = f"<ellipse cx='820' cy='470' rx='1000' ry='260' fill='url(#dg)'>{blink('.7;1;.8;1;.7', 67)}</ellipse>"
sky = f"<g mask='url(#dm)'>{diffuse}<g mask='url(#rm)'><g opacity='.8'>{c2}</g>{c3}{c1}{c4}</g></g>"
haze = ("<linearGradient id='hz' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#2fc79a' stop-opacity='0'/>"
        "<stop offset='1' stop-color='#2fc79a' stop-opacity='.12'/></linearGradient>")
defs += haze
glow = "<rect y='540' width='1600' height='300' fill='url(#hz)'/>"

# ---------- Horizon: snow-capped far range, darker near range, pine forest ----------

def range_(peak_y, drop, spacing, rough, x_start):
    """An irregular mountain ridge: peaks of uneven height and spacing, valleys
    of uneven depth, and two jittered kinks on every slope.
    Returns (outline points, list of (left slope, right slope) for snowcaps)."""
    peaks = []
    x = x_start
    while x < 1700:
        peaks.append((x, rng.randint(*peak_y)))
        x += rng.randint(*spacing)
    pts, sides = [], []
    valleys = []
    for (xa, ya), (xb, yb) in zip(peaks, peaks[1:]):
        f = rng.uniform(.3, .7)
        valleys.append((xa + (xb - xa) * f, max(ya, yb) + rng.randint(*drop)))
    valleys = [(peaks[0][0] - 200, peaks[0][1] + drop[1])] + valleys + [(peaks[-1][0] + 200, peaks[-1][1] + drop[1])]

    def slope(p, v):  # from peak p down to valley v, with two kinks
        out = [p]
        for t in (rng.uniform(.25, .4), rng.uniform(.55, .75)):
            y = p[1] + (v[1] - p[1]) * t + rng.randint(-rough, rough)
            x = p[0] + (v[0] - p[0]) * t + rng.randint(-rough, rough) // 2
            out.append((x, max(y, out[-1][1] + .45 * abs(x - out[-1][0]))))  # steep enough: no flat-topped mesas
        return out + [(v[0], max(v[1], out[-1][1] + 10))]

    for i, p in enumerate(peaks):
        left, right = slope(p, valleys[i]), slope(p, valleys[i + 1])
        pts += left[::-1][:-1] + right[:-1]
        sides.append((left, right))
    pts.append(valleys[-1])
    return pts, sides


def outline(pts):
    return "M-60,1000" + "".join(f"L{x:.0f},{y:.0f}" for x, y in pts) + "L1660,1000Z"


def caps(sides, depth):
    """A jagged snowcap on each peak, `depth` px down its slopes."""
    def cut(side, ycut):  # walk down a slope until y reaches ycut
        out = [side[0]]
        for a, b in zip(side, side[1:]):
            if b[1] >= ycut:
                t = (ycut - a[1]) / (b[1] - a[1])
                return out + [(a[0] + (b[0] - a[0]) * t, ycut)]
            out.append(b)
        return out
    d = ""
    for left, right in sides:
        px, py = left[0]
        dd = depth * rng.uniform(.7, 1.3)
        r, l = cut(right, py + dd), cut(left, py + dd * rng.uniform(.75, 1.1))
        teeth = ""
        for i in range(1, 4):  # ragged lower edge, right to left
            t = i / 4
            x = r[-1][0] + (l[-1][0] - r[-1][0]) * t
            y = r[-1][1] + (l[-1][1] - r[-1][1]) * t + (dd * .35 if i % 2 else -dd * .1) * rng.uniform(.5, 1.2)
            teeth += f"L{x:.0f},{y:.0f}"
        d += ("M" + "L".join(f"{x:.0f},{y:.0f}" for x, y in r) + teeth
              + "".join(f"L{x:.0f},{y:.0f}" for x, y in l[::-1][:-1]) + "Z")
    return d


far_pts, far_peaks = range_((545, 650), (70, 150), (230, 430), 30, -120)
mid_pts, mid_peaks = range_((680, 750), (50, 90), (260, 480), 20, -40)
near_pts = []
x = -20
while x < 1640:
    near_pts.append((x, rng.randint(858, 900)))
    x += rng.randint(60, 110)


def near_y(x):
    for (xa, ya), (xb, yb) in zip(near_pts, near_pts[1:]):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) / (xb - xa)
    return 870


trees = ""
x = -10
while x < 1620:
    h = rng.randint(26, 56)
    w = h * .3
    y = near_y(x) + 6
    trees += f"M{x - w:.0f},{y:.0f}l{w:.0f}-{h}l{w:.0f},{h}z"
    x += rng.randint(26, 72)

defs += dot_pattern("sn", 6, 1.9, ["#a9bddb", "#7f93b5", "#c4d4ec", "#7f93b5", "#a9bddb", "#93a7c8", "#c4d4ec", "#93a7c8", "#e2ecfa"])
defs += (f"<path id='fr' d='{outline(far_pts)}'/><path id='fc' d='{caps(far_peaks, 42)}'/>"
         f"<path id='mr' d='{outline(mid_pts)}'/>"
         f"<path id='nr' d='{outline(near_pts)}{trees}'/>")
# Snow lit by the sky: a faint green that brightens with the main curtain and the flare.
horizon = ("<use href='#fr' fill='#0b1220'/><use href='#fr' fill='url(#m)' opacity='.5'/>"
           "<use href='#fc' fill='url(#sn)' opacity='.5'/>"
           f"<use href='#fc' fill='{GREEN}' opacity='0'>{flare.replace('.95', '.14').replace('.8;', '.1;').replace('.5;', '.07;')}</use>"
           "<use href='#mr' fill='#060a12'/><use href='#mr' fill='url(#m)' opacity='.28'/>"
           "<use href='#nr' fill='#020407'/><use href='#nr' fill='url(#m)' opacity='.22'/>")

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

fireball = ("<path d='M0,0L-260,0' stroke='url(#fb)' stroke-width='4' stroke-linecap='round' stroke-dasharray='0 6'/>"
            f"<circle r='4.5' fill='{GREEN_HI}'/>")
defs += (f"<linearGradient id='fb' x1='1' y1='0' x2='0' y2='0'><stop offset='0' stop-color='{GREEN_HI}'/>"
         f"<stop offset='1' stop-color='{GREEN}' stop-opacity='0'/></linearGradient>")
few = "".join(f"<use href='#bd' x='{dx}' y='{dy}'/>" for dx, dy in [(0, 0), (-20, -8), (-38, 6)])

events = [
    Actor("shooting star", shooting_star, 1, 2.6, "M250,-120L1950,520", lanes=((-250, 250), (0, 140)), wander=0),
    Actor("shooting star 2", shooting_star, .8, 2.2, "M1400,-120L-300,440", lanes=((-200, 200), (0, 120)), wander=0),
    Actor("fireball", fireball, 1, 4.5, "M-300,60L1900,420", lanes=((0, 0), (-60, 120)), wander=0),
    Actor("satellite", satellite, 1, 46, "M-60,120L1660,300", rotate=False, lanes=((0, 0), (-40, 160)), wander=0),
    Actor("birds", flock, 1.2, 34, "M1750,330C1200,300 600,380-150,320", flip=True, opacity=.7, lanes=((0, 0), (-90, 90))),
    Actor("three birds", few, 1.1, 26, "M-150,260C500,300 1100,220 1750,280", opacity=.65, lanes=((0, 0), (-80, 120))),
]
# Negative overlap leaves quiet sky between events; jitter makes those gaps uneven.
moving, loop, schedule = parade(events, rounds=3, overlap=-18, jitter=34, seed=4)

stars = specks(26, STAR, seed=9, radii=(1, 1.3, 1.7), opacities=(.25, .4, .6, .8), twinkle_every=3,
               twinkle=(3, 8), drift=(-8, -3), drift_dur=90, h=760)

svg = build_svg(defs, stars, moving, sky, glow, horizon)

DARK = {"bg": BG, "glow": "rgba(63,224,176,.05)", "veil": "#070b1200", "veil_chat": "#070b1228"}
DARK.update(accent="#2fc79a", sidebar="#05080d", sheen=[GREEN_LO, GREEN, BLUE, VIOLET])
css = build_css(svg, DARK, critter=critters.FOX)
# Calm version: the same scene with nothing crossing it
calm = build_svg(defs, stars, sky, glow, horizon)
calm_css = build_css(calm, DARK, critter=critters.FOX)
write_theme(OUT, "aurora", "Aurora", svg, css, accent="#2fc79a",
            dark_chrome={"canvas": BG, "sidebar": "#05080d", "chrome": "#05080d", "toolbar": "#05080d"},
            schedule=schedule, loop=loop,
            calm=(calm, calm_css))

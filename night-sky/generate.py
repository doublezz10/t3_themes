"""Generate the Night Sky T3 Code theme.

A calm, clear night: a slowly turning starfield with a faint Milky Way,
constellations that take turns drawing themselves line by line (one or two at a
time, in a different part of the sky each time), plus occasional shooting stars,
a blinking satellite and a slow comet. See ../common/themekit.py for how the
background is built.

    python3 generate.py

The output is deterministic (fixed seeds).
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from themekit import blink, build_css, build_svg, gallery_svg, shift_path, specks, write_theme  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(5)

BG = "#0a0d18"
W, C, P, V = "#e8f0ff", "#8fe3ff", "#9db8ff", "#c9b8ff"  # white, cyan, pale blue, pale violet
LINE = "#8fb8ff"


def kt(t, loop):
    return f"{t / loop:.4f}"


# ---------------------------------------------------------------------------
# Constellations: stars (x, y) and the strokes that connect them (index lists)
# ---------------------------------------------------------------------------
CONSTELLATIONS = {
    "big dipper": ([(0, 0), (55, -18), (100, -22), (145, -15), (155, 30), (225, 40), (230, -12)],
                   [[0, 1, 2, 3, 4, 5, 6, 3]]),
    "cassiopeia": ([(0, 0), (40, 45), (85, 15), (125, 55), (165, 5)], [[0, 1, 2, 3, 4]]),
    "orion": ([(0, 0), (95, 12), (50, -30), (30, 92), (52, 86), (75, 80), (25, 170), (110, 160)],
              [[0, 2, 1], [0, 3, 4, 5, 1], [3, 6], [5, 7]]),
    "cygnus": ([(0, 0), (60, 55), (140, 125), (15, 110), (110, 10), (-15, 150), (150, -25)],
               [[0, 1, 2], [5, 3, 1, 4, 6]]),
    "lyra": ([(0, 0), (22, 18), (40, 22), (34, 60), (16, 56)], [[0, 1, 2, 3, 4, 1]]),
    "leo": ([(0, 110), (8, 72), (22, 45), (40, 20), (68, 18), (80, 40), (140, 40), (205, 80), (138, 82)],
            [[5, 4, 3, 2, 1, 0, 8, 7, 6, 2]]),
    "scorpius": ([(0, 0), (6, -35), (10, 32), (45, 5), (70, 20), (85, 50), (90, 85), (100, 115), (125, 135),
                  (155, 135), (172, 115), (160, 95)],
                 [[1, 0, 2], [0, 3, 4, 5, 6, 7, 8, 9, 10, 11]]),
}
SIZE = {"lyra": 2.6, "cassiopeia": 1.9}  # small ones drawn bigger; others fit ~320 wide


def centered(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return [(round(x - cx), round(y - cy)) for x, y in pts], (max(xs) - min(xs), max(ys) - min(ys))


def constellation_body(name, animated=None):
    """Stars plus connecting lines. animated: (loop, passes) adds the draw-in animation."""
    pts, strokes = CONSTELLATIONS[name]
    pts, _ = centered(pts)
    d = "".join("M" + "L".join(f"{pts[i][0]},{pts[i][1]}" for i in s) for s in strokes)
    anim = ""
    if animated:
        loop, passes = animated
        # Lines: hidden (offset 1) until 2 s in, draw over 7 s, hold, reset while invisible.
        kts, vals = ["0"], ["1"]
        for s, e in passes:
            kts += [kt(s, loop), kt(s + 2, loop), kt(s + 9, loop), kt(e, loop)]
            vals += ["1", "1", "0", "0"]
        kts.append("1")
        vals.append("1")
        anim = (f"<animate attributeName='stroke-dashoffset' dur='{loop:g}s' repeatCount='indefinite' "
                f"keyTimes='{';'.join(kts)}' values='{';'.join(vals)}'/>")
        lines = (f"<path d='{d}' pathLength='1' stroke-dasharray='1' fill='none' stroke='{LINE}' "
                 f"stroke-width='1.3' stroke-linecap='round' opacity='.55'>{anim}</path>")
    else:
        lines = f"<path d='{d}' fill='none' stroke='{LINE}' stroke-width='1.3' stroke-linecap='round' opacity='.55'/>"
    stars = "".join(f"<use href='#s' x='{x}' y='{y}'/>" for x, y in pts)
    return lines + stars


# ---------------------------------------------------------------------------
# Schedule: constellations take turns, 3 shuffled rounds, at most two visible
# ---------------------------------------------------------------------------
NAMES = list(CONSTELLATIONS)
SHOW, STEP = 26, 15  # each one is visible ~26 s; the next starts 15 s later
ROUNDS = 3
SPOTS = [(420, 280), (1180, 270), (800, 230), (430, 620), (1190, 630), (640, 440), (980, 420)]

order, last = [], None
for _ in range(ROUNDS):
    r = NAMES[:]
    rng.shuffle(r)
    if r[0] == last:
        r[0], r[1] = r[1], r[0]
    order += r
    last = r[-1]

t, passes, prev_spot = .5, [], None
for name in order:
    spot = rng.choice([s for s in SPOTS if s != prev_spot])
    passes.append((name, t, t + SHOW, spot))
    prev_spot = spot
    t += STEP
LOOP = round(passes[-1][2] + 1, 1)


def scale_for(name):
    _, (w, h) = centered(CONSTELLATIONS[name][0])
    return SIZE.get(name, min(1.6, 320 / max(w, h)))


sky_figures = ""
for name in NAMES:
    mine = [(s, e, spot) for n, s, e, spot in passes if n == name]
    k_op, v_op = ["0"], ["0"]
    for s, e, _ in mine:
        k_op += [kt(s, loop=LOOP), kt(s + 3, LOOP), kt(e - 4, LOOP), kt(e, LOOP)]
        v_op += ["0", "1", "1", "0"]
    k_op.append("1")
    v_op.append("0")
    # Move to the next spot while invisible (discrete jumps at the end of each pass).
    k_tr = ["0"] + [kt(e, LOOP) for s, e, _ in mine[:-1]]
    v_tr = [f"{x} {y}" for _, _, (x, y) in mine]
    body = constellation_body(name, (LOOP, [(s, e) for s, e, _ in mine]))
    sky_figures += (f"<g opacity='0'><animate attributeName='opacity' dur='{LOOP:g}s' repeatCount='indefinite' "
                    f"keyTimes='{';'.join(k_op)}' values='{';'.join(v_op)}'/>"
                    f"<animateTransform attributeName='transform' type='translate' calcMode='discrete' dur='{LOOP:g}s' "
                    f"repeatCount='indefinite' keyTimes='{';'.join(k_tr)}' values='{';'.join(v_tr)}'/>"
                    f"<g transform='scale({scale_for(name):.2g})'>{body}</g></g>")


# ---------------------------------------------------------------------------
# Things that move: shooting stars, a satellite, a comet
# ---------------------------------------------------------------------------
def travel(body, base, starts, dur, offsets, fade=(0, 0), rotate=True, opacity=1):
    """Cross `base` (shifted by offsets[k]) during [starts[k], starts[k]+dur]; hidden otherwise."""
    n = len(starts)
    sub = "".join(shift_path(base, dx, dy) for dx, dy in offsets)
    k_m, v_m, k_o, v_o = ["0"], ["0"], ["0"], ["0"]
    for k, s in enumerate(starts):
        e = s + dur
        k_m += [kt(s, LOOP), kt(e, LOOP)]
        v_m += [f"{k / n:.4g}", f"{(k + 1) / n:.4g}"]
        k_o += [kt(s, LOOP), kt(s + fade[0], LOOP), kt(e - fade[1], LOOP), kt(e, LOOP)]
        v_o += ["0", "1", "1", "0"]
    k_m.append("1")
    v_m.append("1")
    k_o.append("1")
    v_o.append("0")
    rot = " rotate='auto'" if rotate else ""
    return (f"<g opacity='0'><animate attributeName='opacity' dur='{LOOP:g}s' repeatCount='indefinite' "
            f"keyTimes='{';'.join(k_o)}' values='{';'.join(v_o)}'/>"
            f"<animateMotion dur='{LOOP:g}s' repeatCount='indefinite' calcMode='linear' keyPoints='{';'.join(v_m)}' "
            f"keyTimes='{';'.join(k_m)}'{rot} path='{sub}'/><g opacity='{opacity:g}'>{body}</g></g>")


METEOR = (f"<path d='M-170,0L0,0' stroke='url(#mt)' stroke-width='2.4' stroke-linecap='round' stroke-dasharray='0 6' fill='none'/>"
          f"<circle r='2.6' fill='{W}'/><circle r='6' fill='{C}' opacity='.25'/>")
SATELLITE = f"<circle r='1.8' fill='{W}'>{blink('1;.15;1', 1.6)}</circle>"
COMET = (f"<g stroke='url(#ct)' stroke-linecap='round' stroke-dasharray='0 7' fill='none' stroke-width='2.6'>"
         "<path d='M-6,0L-260,0'/><path d='M-6,-3L-220,-20'/><path d='M-6,3L-230,18'/></g>"
         f"<circle r='14' fill='{C}' opacity='.1'/><circle r='8' fill='{C}' opacity='.25'/><circle r='3.6' fill='{W}'/>")

# Shooting stars: every 18-40 s, alternating two directions, at random spots in the upper sky.
meteor_times, t = [], 9.0
while t < LOOP - 4:
    meteor_times.append(round(t, 1))
    t += rng.uniform(18, 40)
m_right = meteor_times[0::2]
m_left = meteor_times[1::2]
movers = travel(METEOR, "M0,0L460,230", m_right, 1.3, [(rng.randint(150, 1000), rng.randint(60, 380)) for _ in m_right],
                fade=(.15, .45))
movers += travel(METEOR, "M0,0L-460,230", m_left, 1.3, [(rng.randint(600, 1450), rng.randint(60, 380)) for _ in m_left],
                 fade=(.15, .45))
# Satellite: two slow crossings per loop.
sat_times = [round(LOOP * .18, 1), round(LOOP * .66, 1)]
movers += travel(SATELLITE, "M-60,0L1660,140", sat_times, 75, [(0, rng.randint(120, 600)) for _ in sat_times],
                 fade=(0, 0), rotate=False, opacity=.9)
# Comet: one slow pass per loop, right to left across the upper sky.
comet_time = round(LOOP * .42, 1)
movers += travel(COMET, "M1950,110L-450,430", [comet_time], 60, [(0, rng.randint(0, 120))], fade=(0, 0), opacity=.9)

# ---------------------------------------------------------------------------
# The sky itself: Milky Way glow, two tiled layers of faint stars, brighter twinklers
# ---------------------------------------------------------------------------


def star_tile(pid, w, h, n, seed):
    r = random.Random(seed)
    s = f"<pattern id='{pid}' width='{w}' height='{h}' patternUnits='userSpaceOnUse'>"
    for _ in range(n):
        s += (f"<circle cx='{r.randint(0, w)}' cy='{r.randint(0, h)}' r='{r.choice((.7, .9, 1.1, 1.3)):g}' "
              f"fill='{r.choice((W, P, P, C, V))}' opacity='{r.choice((.25, .35, .45, .6)):g}'/>")
    return s + "</pattern>"


defs = (star_tile("p1", 331, 277, 22, 1) + star_tile("p2", 523, 419, 20, 2)
        + f"<radialGradient id='mw'><stop offset='0' stop-color='{V}' stop-opacity='.10'/>"
        f"<stop offset='1' stop-color='{V}' stop-opacity='0'/></radialGradient>"
        f"<linearGradient id='mt' gradientUnits='userSpaceOnUse' x1='-170' x2='0'><stop offset='0' stop-color='{C}' stop-opacity='0'/>"
        f"<stop offset='1' stop-color='{W}'/></linearGradient>"
        f"<linearGradient id='ct' gradientUnits='userSpaceOnUse' x1='-260' x2='0'><stop offset='0' stop-color='{C}' stop-opacity='0'/>"
        f"<stop offset='1' stop-color='{C}' stop-opacity='.9'/></linearGradient>"
        f"<g id='s'><circle r='6' fill='{C}' opacity='.16'/><circle r='2.4' fill='{W}'/></g>")

sky = ("<g><animateTransform attributeName='transform' type='translate' dur='240s' repeatCount='indefinite' values='0 0;-30 -10;0 0'/>"
       "<ellipse cx='800' cy='500' rx='1100' ry='170' fill='url(#mw)' transform='rotate(-24 800 500)'/>"
       "<rect x='-60' y='-40' width='1720' height='1080' fill='url(#p1)'/>"
       "<rect x='-60' y='-40' width='1720' height='1080' fill='url(#p2)'/>"
       + specks(14, W, seed=3, radii=(1.3, 1.7, 2.1), opacities=(.55, .7, .9), twinkle_every=2, twinkle=(3, 8), drift=None)
       + specks(10, C, seed=4, radii=(1.2, 1.5), opacities=(.45, .6, .8), twinkle_every=2, twinkle=(4, 9), drift=None)
       + specks(6, V, seed=6, radii=(1.2, 1.5), opacities=(.45, .6), twinkle_every=3, twinkle=(5, 9), drift=None)
       + "</g>")

svg = build_svg(defs, sky, sky_figures, movers)
DARK = {"bg": BG, "glow": "rgba(110,130,255,.06)", "veil": "#0a0d1800", "veil_chat": "#0a0d1880"}
css = build_css(svg, DARK)


class Figure:  # minimal stand-in for Actor in the gallery
    def __init__(self, name, body):
        self.name, self.body = name, body


figures = [Figure(n, f"<g transform='scale({scale_for(n) * .75:.2g})'>{constellation_body(n)}</g>") for n in NAMES]
figures += [Figure("shooting star", METEOR), Figure("comet", f"<g transform='scale(.8)'>{COMET}</g>"),
            Figure("satellite", f"<g transform='scale(2.5)'>{SATELLITE}</g>")]
fit = {f.name: (1, -48, False) for f in figures}
fit["shooting star"] = (1, 40, False)
fit["comet"] = (1, 50, False)
gallery = gallery_svg(defs, figures, BG, cols=5, cell_w=360, cell_h=300, fit=fit)

schedule = [{"name": n, "start": round(s, 2), "end": round(e, 2)} for n, s, e, _ in passes]
notes = {"shooting_stars": meteor_times, "satellite": sat_times, "comet": comet_time}
write_theme(OUT, "night-sky", "Night Sky", svg, css, accent="#7aa8ff",
            dark_chrome={"canvas": BG, "sidebar": "#080a12", "chrome": "#080a12", "toolbar": "#080a12"},
            schedule=schedule, loop=LOOP, gallery=gallery, notes=notes)

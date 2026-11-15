"""Generate the Night Rain T3 Code theme.

Calm rain behind the chat area: three layers of dotted rain falling at a slight
angle (far = faint and slow, near = brighter and faster), ripples spreading on
the ground, a few drops sliding down the glass, and a very faint flash of
distant lightning about once a minute. Now and then something drifts past in
the rain: a paper boat, a gull, a lost umbrella, a falling leaf. Long stretches
of plain rain sit between them. See ../common/themekit.py for how the
background is built.

    python3 generate.py

The output is deterministic (fixed seeds).
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))
from themekit import (Actor, VIEW_H, VIEW_W, build_css, build_svg, dot_pattern, dotted,  # noqa: E402
                      gallery_svg, parade, spin, wave, write_theme)

OUT = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(5)
FAR, MID, NEAR, PALE = "#4f6b8a", "#6489b0", "#86aad0", "#b9d4ee"

defs = dot_pattern("d", 5, 1.7, [MID, NEAR, MID, PALE, MID, NEAR, MID, PALE, NEAR])

# ---------- Rain ----------
# Each layer is one path of short slanted streaks covering a 1600x1000 tile,
# drawn twice (the second copy one tile higher). The pair slides down exactly
# one tile per cycle, so the loop is seamless.
SLANT = -0.16  # horizontal drift per unit of fall (streaks lean left as they fall)


def rain_layer(pid, n, length, color, width, gap, opacity, dur):
    d = ""
    for _ in range(n):
        x, y = rng.randint(-120, VIEW_W + 260), rng.randint(0, VIEW_H - 1)
        d += f"M{x},{y}l{SLANT * length:.0f},{length}"
    dx = round(SLANT * VIEW_H)
    tile = f"<path id='{pid}' d='{d}'/>"
    layer = (f"<g {dotted(color, width, gap)} opacity='{opacity:g}'>"
             f"<animateTransform attributeName='transform' type='translate' dur='{dur:g}s' repeatCount='indefinite' "
             f"values='0 0;{dx} {VIEW_H}'/><use href='#{pid}'/><use href='#{pid}' x='{-dx}' y='{-VIEW_H}'/></g>")
    return tile, layer


rain_defs, rain = "", ""
for args in (("rf", 90, 22, FAR, 2, 5, .55, 4.6),     # far: faint, small, slow
             ("rm", 58, 34, MID, 2.4, 6, .7, 3.2),    # middle
             ("rn", 32, 52, NEAR, 3, 7, .85, 2.3)):   # near: brighter, longer, faster
    t, l = rain_layer(*args)
    rain_defs += t
    rain += l
defs += rain_defs

# ---------- Ground: haze and ripples ----------
defs += ("<linearGradient id='hz' x1='0' y1='0' x2='0' y2='1'><stop offset='.55' stop-color='#7fa3c8' stop-opacity='0'/>"
         "<stop offset='1' stop-color='#7fa3c8' stop-opacity='.09'/></linearGradient>")
haze = f"<rect width='{VIEW_W}' height='{VIEW_H}' fill='url(#hz)'/>"

ripples = ""
for i in range(14):
    x, y = rng.randint(80, VIEW_W - 80), rng.randint(760, 960)
    size = (y - 700) / 260
    rx, ry = 34 * size + 14, 7 * size + 3
    dur = rng.choice([3.1, 3.7, 4.3, 5.3, 6.1, 6.7])
    begin = f"-{rng.uniform(0, dur):.1f}s"
    common = f"dur='{dur:g}s' begin='{begin}' repeatCount='indefinite' keyTimes='0;.5;1'"
    ripples += (f"<ellipse cx='{x}' cy='{y}'>"
                f"<animate attributeName='rx' {common} values='1;{rx:.0f};{rx * 1.15:.0f}'/>"
                f"<animate attributeName='ry' {common} values='1;{ry:.0f};{ry * 1.15:.0f}'/>"
                f"<animate attributeName='opacity' {common} values='1;.25;0'/></ellipse>")
ripples = f"<g {dotted(NEAR, 2.6, 5)}>{ripples}</g>"

# ---------- Drops sliding down the glass ----------
glass = ""
for i, (x, dur, begin) in enumerate(((210, 26, 0), (1390, 31, -11), (760, 37, -23), (1180, 29, -6))):
    w1, w2, w3 = (rng.randint(-14, 14) for _ in range(3))
    glass += (f"<g><animateTransform attributeName='transform' type='translate' dur='{dur}s' begin='{begin}s' "
              f"repeatCount='indefinite' keyTimes='0;.3;.55;.8;1' "
              f"values='{x} -160;{x + w1} 180;{x + w2} 420;{x + w3} 760;{x + w3} 1200'/>"
              f"<path d='M0,-8L0,-90' {dotted(PALE, 2, 6)} opacity='.5'/>"
              f"<circle r='4.5' fill='{PALE}' opacity='.8'/></g>")

# ---------- Distant lightning: a faint double flicker about once a minute ----------
lightning = (f"<rect width='{VIEW_W}' height='{VIEW_H}' fill='#9fb8d6' opacity='0'>"
             "<animate attributeName='opacity' dur='61s' begin='-20s' repeatCount='indefinite' "
             "keyTimes='0;.62;.623;.628;.633;.638;.648;1' values='0;0;.09;.02;.06;.01;0;0'/></rect>")

# ---------- Passers-by: drawn facing +x ----------
boat = ("<g>" + spin("-5 0 10;5 0 10;-5 0 10", 3.4)
        + "<path d='M-44,0L44,0L30,18L-30,18ZM-8,0L6,-40L26,0Z' fill='url(#d)'/></g>")

wa, wb = "M-36,-4Q-18,-24 0,0Q18,-24 36,-4", "M-36,12Q-18,10 0,0Q18,10 36,12"
gull = (f"<path d='{wa}' {dotted(NEAR, 3.4, 5)}>{wave(wa, wb, .9)}</path>"
        "<ellipse cx='2' rx='9' ry='5' fill='url(#d)'/>")

umbrella = ("<g>" + spin("-12 0 30;12 0 30;-12 0 30", 5)
            + "<path d='M-52,0C-52,-36 52,-36 52,0C44,-7 35,-7 26,0C18,-7 8,-7 0,0C-8,-7-18,-7-26,0C-35,-7-44,-7-52,0Z' fill='url(#d)'/>"
            f"<path d='M0,-30L0,42C0,52 12,52 12,44' {dotted(PALE, 3, 5)}/></g>")

leaf = ("<g>" + spin("-35 0 0;35 0 0;-35 0 0", 3)
        + "<path d='M0,-16C16,-9 16,9 0,16C-16,9-16,-9 0,-16Z' fill='url(#d)'/>"
        f"<path d='M0,16L0,26' {dotted(NEAR, 2.4, 4)}/></g>")

cast = [
    Actor("paper boat", boat, 1.3, 34, "M-200,880C400,868 1000,894 1820,876", rotate=False, lanes=((0, 0), (-30, 25))),
    Actor("gull", gull, 1.2, 15, "M-150,230C300,170 900,270 1760,190", rotate=False, opacity=.8, lanes=((0, 0), (-60, 160))),
    Actor("umbrella", umbrella, 1.3, 30, "M1820,160C1300,320 800,260-220,620", rotate=False, opacity=.85),
    Actor("leaf", leaf, 1.8, 22, "M420,-120C700,180 220,420 560,700S360,900 640,1150", rotate=False, opacity=.85,
          lanes=((-260, 700), (0, 0))),
]
# A negative overlap leaves a quiet gap of plain rain between passers-by.
passers, loop, schedule = parade(cast, rounds=3, overlap=-14, seed=3)
# The flash fires 62% into its 61 s cycle, which starts 20 s early: first at about 17.8 s.
schedule.append({"name": "lightning", "start": 17.8, "end": 19.5})

svg = build_svg(defs, haze, rain, ripples, passers, glass, lightning)

DARK = {"bg": "#0b0f14", "glow": "rgba(127,163,200,.06)", "veil": "#0b0f1400", "veil_chat": "#0b0f1499"}
LIGHT = {"bg": "#e6ecf2", "glow": "rgba(79,107,138,.10)", "veil": "#e6ecf21a", "veil_chat": "#e6ecf2b8"}
css = build_css(svg, DARK, LIGHT)

gallery = gallery_svg(defs, cast, DARK["bg"], cols=4, fit={a.name: (a.scale * 1.4, -40, False) for a in cast})
write_theme(OUT, "night-rain", "Night Rain", svg, css, accent="#5b8cc4",
            dark_chrome={"canvas": DARK["bg"], "sidebar": "#080b0f", "chrome": "#080b0f", "toolbar": "#080b0f"},
            light_chrome={"canvas": LIGHT["bg"], "sidebar": "#dae2ea", "chrome": "#dae2ea", "toolbar": "#dae2ea"},
            schedule=schedule, loop=loop, gallery=gallery)

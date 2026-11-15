"""Shared toolkit for animated T3 Code themes.

T3 themes are CSS only: no JavaScript, no external files, at most 20,000
characters. Every theme in this repo therefore draws its background as one
animated SVG (SMIL), embedded in the CSS as a data: URL on the chat area.

A theme's generate.py builds its SVG pieces with these helpers and calls
write_theme(), which validates everything and writes:

    background.svg, theme.css, theme.json, preview/gallery.svg, preview/timeline.json

The main building block is parade(): a set of creatures (or comets, rain
clouds, ...) that take turns crossing the screen, one or two at a time. It
plays several rounds, each in a freshly shuffled order, and every pass uses a
different lane, so the loop takes a long time to repeat and stays hard to
predict.
"""
import json
import os
import random
import re
import xml.dom.minidom

CSS_LIMIT = 20000
VIEW_W, VIEW_H = 1600, 1000

# ---------------------------------------------------------------------------
# Small SVG helpers
# ---------------------------------------------------------------------------


def dot_pattern(pid, step, r, colors):
    """A 3x3 tile of dots; fill any path with url(#pid) to draw it in dots.

    colors: nine colors, row by row. Mix a few bright ones in for sparkle.
    """
    assert len(colors) == 9
    s = f"<pattern id='{pid}' width='{step * 3:g}' height='{step * 3:g}' patternUnits='userSpaceOnUse'>"
    for i, c in enumerate(colors):
        s += f"<circle cx='{i % 3 * step + step / 2:g}' cy='{i // 3 * step + step / 2:g}' r='{r:g}' fill='{c}'/>"
    return s + "</pattern>"


def dotted(color, width=3, gap=5):
    """Attributes for a dotted stroke (round dots spaced `gap` apart)."""
    return (f"fill='none' stroke='{color}' stroke-linecap='round' "
            f"stroke-dasharray='0 {gap:g}' stroke-width='{width:g}'")


def wave(a, b, dur):
    """Animate a path's d between shapes a and b and back. Both need the same commands.

    Note: the halfway frame is the average of a and b. If they are mirror images
    the shape goes flat for a moment; use several phases (see Deep Sea's eel)
    when that matters.
    """
    return f"<animate attributeName='d' dur='{dur:g}s' repeatCount='indefinite' values='{a};{b};{a}'/>"


def spin(values, dur):
    """animateTransform rotate, e.g. spin('0 10 0;-20 10 0;0 10 0', 2)."""
    return f"<animateTransform attributeName='transform' type='rotate' dur='{dur:g}s' repeatCount='indefinite' values='{values}'/>"


def pulse(values, dur):
    """animateTransform scale, e.g. pulse('1 1;1.1 .9;1 1', 2)."""
    return f"<animateTransform attributeName='transform' type='scale' dur='{dur:g}s' repeatCount='indefinite' values='{values}'/>"


def blink(values, dur, attr="opacity", begin=None):
    b = f" begin='{begin:g}s'" if begin is not None else ""
    return f"<animate attributeName='{attr}' dur='{dur:g}s'{b} repeatCount='indefinite' values='{values}'/>"


_TOKEN = re.compile(r"[A-Za-z]|-?\d*\.?\d+(?:e-?\d+)?")


def shift_path(d, dx, dy):
    """Translate a path that uses only absolute M/L/C/S/Q/T commands (x,y pairs)."""
    out, nums = [], []

    def flush():
        for i in range(0, len(nums), 2):
            out.append(f"{nums[i] + dx:g},{nums[i + 1] + dy:g}")
        nums.clear()

    for tok in _TOKEN.findall(d):
        if tok.isalpha():
            assert tok in "MLCSQTZ", f"shift_path only handles absolute M/L/C/S/Q/T/Z, got {tok}"
            flush()
            out.append(tok)
        else:
            nums.append(float(tok))
    flush()
    s = ""
    for part in out:  # join, adding a space only between two coordinate pairs
        s += (" " if s and not s[-1].isalpha() and not part.isalpha() else "") + part
    return s


def _endpoints(d):
    nums = [float(t) for t in _TOKEN.findall(d) if not t.isalpha()]
    return (nums[0], nums[1]), (nums[-2], nums[-1])


# ---------------------------------------------------------------------------
# Parade: things that take turns crossing the screen
# ---------------------------------------------------------------------------


class Actor:
    """Something that crosses the screen once per round.

    body      SVG drawn facing +x, with its head near the origin.
    scale     size multiplier.
    dur       seconds it takes to cross its path.
    path      motion path (absolute M/L/C/S only). Start and end it far enough
              off-screen that the whole body is hidden while it waits; viewBox
              is 1600x1000 and wide windows show all of x, tall ones all of y.
    rotate    turn to face along the path (False keeps it upright).
    flip      mirror vertically, for side-view bodies that travel right to left
              with rotate=True (otherwise they swim upside down).
    opacity   overall opacity.
    lanes     ((dx_lo, dx_hi), (dy_lo, dy_hi)) random offset applied to the path
              on each pass. Default: +-170 across a horizontal path, +-320
              across a vertical one. Use ((0, 0), (0, 0)) for a fixed route.
    """

    def __init__(self, name, body, scale, dur, path, rotate=True, flip=False, opacity=.9, lanes=None):
        self.name, self.body, self.scale, self.dur, self.path = name, body, scale, dur, path
        self.rotate, self.flip, self.opacity = rotate, flip, opacity
        if lanes is None:
            (x0, y0), (x1, y1) = _endpoints(path)
            lanes = ((0, 0), (-170, 170)) if abs(x1 - x0) >= abs(y1 - y0) else ((-320, 320), (0, 0))
        self.lanes = lanes


def parade(actors, rounds=3, overlap=4, seed=1, lead=.5, tail=1):
    """Schedule actors to take turns, `rounds` times, each round shuffled.

    The next actor starts `overlap` seconds before the current one finishes,
    so at most two are on screen. Returns (svg, loop_seconds, schedule) where
    schedule is a list of {name, start, end}.
    """
    rng = random.Random(seed)
    order, prev_last = [], None
    for _ in range(rounds):
        r = actors[:]
        rng.shuffle(r)
        if prev_last is not None and r[0] is prev_last and len(r) > 1:
            r[0], r[1] = r[1], r[0]  # never the same actor twice in a row
        order += r
        prev_last = r[-1]

    t, slots = lead, []
    for a in order:
        slots.append((a, t, t + a.dur))
        t += a.dur - overlap
    loop = round(slots[-1][2] + tail, 1)

    svg = ""
    for a in actors:
        mine = [(s, e) for b, s, e in slots if b is a]
        n = len(mine)
        subpaths = []
        for _ in range(n):
            (dxl, dxh), (dyl, dyh) = a.lanes
            subpaths.append(shift_path(a.path, round(rng.uniform(dxl, dxh)), round(rng.uniform(dyl, dyh))))
        # Each pass is a translated copy, so every subpath has the same length and
        # pass k covers keyPoints k/n..(k+1)/n. Move-tos jump without adding length.
        kt, kp = ["0"], ["0"]
        for k, (s, e) in enumerate(mine):
            kt += [f"{s / loop:.4f}", f"{e / loop:.4f}"]
            kp += [f"{k / n:.4g}", f"{(k + 1) / n:.4g}"]
        kt.append("1")
        kp.append("1")
        rot = " rotate='auto'" if a.rotate else ""
        inner = f"scale({a.scale:g},{-a.scale:g})" if a.flip else f"scale({a.scale:g})"
        svg += (f"<g opacity='{a.opacity:g}'><animateMotion dur='{loop:g}s' repeatCount='indefinite' calcMode='linear' "
                f"keyPoints='{';'.join(kp)}' keyTimes='{';'.join(kt)}'{rot} path='{''.join(subpaths)}'/>"
                f"<g transform='{inner}'>{a.body}</g></g>")
    schedule = [{"name": a.name, "start": round(s, 2), "end": round(e, 2)} for a, s, e in slots]
    return svg, loop, schedule


def specks(n, color, seed=7, radii=(1.3, 1.6, 2), opacities=(.25, .35, .5, .65), twinkle_every=4,
           twinkle=(4, 9), drift=(-20, -12), drift_dur=60, w=VIEW_W, h=VIEW_H):
    """Scattered background dots (plankton, stars, dust). Every `twinkle_every`-th one fades in and out."""
    rng = random.Random(seed)
    s = ""
    for i in range(n):
        x, y, o = rng.randint(0, w), rng.randint(0, h), rng.choice(opacities)
        s += f"<circle cx='{x}' cy='{y}' r='{rng.choice(radii):g}' opacity='{o:g}'"
        if twinkle_every and i % twinkle_every == 0:
            s += f">{blink(f'{o:g};.05;{o:g}', rng.randint(*twinkle))}</circle>"
        else:
            s += "/>"
    anim = ""
    if drift:
        anim = (f"<animateTransform attributeName='transform' type='translate' dur='{drift_dur}s' "
                f"repeatCount='indefinite' values='0 0;{drift[0]} {drift[1]};0 0'/>")
    return f"<g fill='{color}'>{anim}{s}</g>"


# ---------------------------------------------------------------------------
# Assembling and writing a theme
# ---------------------------------------------------------------------------

CHAT = '[data-workspace-area="conversation"]'
HAS_MSG = ':has([data-timeline-row-kind])'


def build_svg(defs, *layers):
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {VIEW_W} {VIEW_H}' preserveAspectRatio='xMidYMid slice'>"
           f"<defs>{defs}</defs>{''.join(layers)}</svg>")
    assert '"' not in svg, "use single quotes inside the SVG"
    xml.dom.minidom.parseString(svg)  # one XML error silently blanks the whole background
    return svg


def data_url(svg):
    return "data:image/svg+xml," + svg.replace("%", "%25").replace("#", "%23").replace("<", "%3C").replace(">", "%3E")


def build_css(svg, dark, light=None):
    """Theme CSS for the chat-area background.

    dark / light: dicts with
        bg         water/sky color behind everything
        glow       color of a soft glow at the top (or None)
        veil       color laid over the animation everywhere (alpha hex; '#xxxxxx00' for none)
        veil_chat  stronger veil once a thread has messages, so text stays readable
    Without `light`, the background only applies in dark mode.
    """
    def vars_(p):
        glow = p.get("glow") or "#0000"
        return f"--bg:{p['bg']};--glow:{glow};--veil:{p['veil']}"

    A = CHAT if light else f".dark {CHAT}"
    css = (f'{A}{{--sea:url("{data_url(svg)}");{vars_(dark)};'
           'background:linear-gradient(var(--veil),var(--veil)),radial-gradient(ellipse at 50% 0%,var(--glow),transparent 60%),'
           'var(--sea) center/cover no-repeat,var(--bg)!important}'
           f'{A}{HAS_MSG}{{--veil:{dark["veil_chat"]}}}')
    if light:
        L = f":root:not(.dark) {CHAT}"
        css += f'{L}{{{vars_(light)}}}{L}{HAS_MSG}{{--veil:{light["veil_chat"]}}}'
    css += (f'{A} .messages-timeline-scroll,{A} [data-chat-composer-form]{{background:transparent!important}}'
            f'@media (prefers-reduced-motion:reduce){{{A}{{background:var(--bg)!important}}}}')
    return css


def gallery_svg(defs, actors, bg, cols=4, cell_w=400, cell_h=260, fit=None):
    """Static sheet of every actor, for checking shapes. fit: {name: (scale, dx, flip)} overrides."""
    fit = fit or {}
    rows = (len(actors) + cols - 1) // cols
    cells = ""
    for i, a in enumerate(actors):
        x, y = cell_w * (i % cols) + cell_w * .62, cell_h * (i // cols) + cell_h * .5
        k, dx, fl = fit.get(a.name, (1, 0, False))
        sy = -k if fl else k
        cells += (f"<g transform='translate({x + dx:g},{y:g}) scale({k:g},{sy:g})'>{a.body}</g>"
                  f"<text x='{x - cell_w * .55:g}' y='{y + cell_h * .42:g}' fill='#888' font-size='18' font-family='sans-serif'>{a.name}</text>")
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {cols * cell_w} {rows * cell_h}' "
            f"style='background:{bg}'><defs>{defs}</defs>{cells}</svg>")


def write_theme(out_dir, theme_id, name, svg, css, accent, dark_chrome, light_chrome=None,
                schedule=None, loop=None, gallery=None, notes=None):
    """Validate and write everything a theme folder needs.

    dark_chrome / light_chrome: T3 color roles, e.g. {"canvas": ..., "sidebar": ...}.
    The dark dict must include "canvas".
    """
    assert len(css) <= CSS_LIMIT, f"theme css is {len(css)} chars; T3 allows {CSS_LIMIT}"
    os.makedirs(os.path.join(out_dir, "preview"), exist_ok=True)

    def w(path, text):
        with open(os.path.join(out_dir, path), "w") as fh:
            fh.write(text)

    w("background.svg", svg)
    w("theme.css", css)
    chrome = dict(dark_chrome)
    theme = {"version": 1, "name": name, "appearance": "dark", "canvas": chrome.pop("canvas"), "accent": accent,
             "colors": chrome}
    if light_chrome:
        theme["variants"] = {"light": light_chrome}
    theme["css"] = css
    w("theme.json", json.dumps(theme, indent=2) + "\n")
    if gallery:
        w("preview/gallery.svg", gallery)
    timeline = {"id": theme_id, "loop_seconds": loop, "has_light": bool(light_chrome), "schedule": schedule or []}
    if notes:
        timeline["notes"] = notes
    w("preview/timeline.json", json.dumps(timeline, indent=1) + "\n")
    print(f"{name}: css {len(css)}/{CSS_LIMIT} chars"
          + (f", loop {loop:g}s ({loop / 60:.1f} min), {len(schedule)} passes" if loop else ""))
    return theme

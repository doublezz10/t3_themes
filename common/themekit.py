"""Shared toolkit for animated T3 Code themes.

T3 themes are CSS only: no JavaScript, no external files, at most 20,000
characters. Every theme in this repo therefore draws its background as one
animated SVG (SMIL), embedded in the CSS as a data: URL on the chat area.

A theme's generate.py builds its SVG pieces with these helpers and calls
write_theme(), which validates everything and writes:

    background.svg, theme.css, theme.json, preview/gallery.svg, preview/timeline.json

The main building block is parade(): a set of creatures (or comets, rain
clouds, ...) that take turns crossing the screen, one or two at a time. It
plays several rounds, each in a freshly shuffled order, and every pass takes
its own route: a different lane, bent into its own random swoops, dips and
S-curves. The loop takes a long time to repeat and stays hard to predict.
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
    b = f" begin='{round(begin, 1):g}s'" if begin is not None else ""
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
    wander    how far (px) each pass may bend away from `path`, sideways to the
              direction of travel. Every pass gets its own random swoops, dips,
              S-bends and climbs, so no two crossings look alike. 0 keeps the
              path's shape (walkers on the ground, shooting stars).
    """

    def __init__(self, name, body, scale, dur, path, rotate=True, flip=False, opacity=.9, lanes=None, wander=150):
        self.name, self.body, self.scale, self.dur, self.path = name, body, scale, dur, path
        self.rotate, self.flip, self.opacity, self.wander = rotate, flip, opacity, wander
        if lanes is None:
            (x0, y0), (x1, y1) = _endpoints(path)
            lanes = ((0, 0), (-170, 170)) if abs(x1 - x0) >= abs(y1 - y0) else ((-320, 320), (0, 0))
        self.lanes = lanes


def _cubics(d):
    """Parse an absolute M/L/C/S path (one subpath) into [p0, [(c1, c2, p), ...]]."""
    toks = _TOKEN.findall(d)
    cmd, nums, segs, start = None, [], [], None

    def pt(i):
        return (nums[i], nums[i + 1])

    def emit():
        nonlocal start
        if cmd is None:
            return
        if cmd == "M":
            start = pt(0)
            for i in range(2, len(nums), 2):  # implicit line-tos
                seg_line(pt(i))
        elif cmd == "L":
            for i in range(0, len(nums), 2):
                seg_line(pt(i))
        elif cmd == "C":
            for i in range(0, len(nums), 6):
                segs.append((pt(i), pt(i + 2), pt(i + 4)))
        elif cmd == "S":
            for i in range(0, len(nums), 4):
                last = segs[-1] if segs else None
                cur = last[2] if last else start
                c1 = (2 * cur[0] - last[1][0], 2 * cur[1] - last[1][1]) if last else cur
                segs.append((c1, pt(i), pt(i + 2)))
        else:
            raise AssertionError(f"wander paths support absolute M/L/C/S only, got {cmd}")

    def seg_line(p):
        a = segs[-1][2] if segs else start
        segs.append(((a[0] + (p[0] - a[0]) / 3, a[1] + (p[1] - a[1]) / 3),
                     (a[0] + 2 * (p[0] - a[0]) / 3, a[1] + 2 * (p[1] - a[1]) / 3), p))

    for tok in toks:
        if tok.isalpha():
            emit()
            cmd, nums = tok, []
        else:
            nums.append(float(tok))
    emit()
    return start, segs


def _split(p0, seg, t=.5):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p0, *seg
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)  # noqa: E731
    a, b, c = lerp((x0, y0), (x1, y1)), lerp((x1, y1), (x2, y2)), lerp((x2, y2), (x3, y3))
    ab, bc = lerp(a, b), lerp(b, c)
    m = lerp(ab, bc)
    return (a, ab, m), (bc, c, (x3, y3))


def _length(p0, segs):
    total, a = 0.0, p0
    for c1, c2, p in segs:
        prev = a
        for i in range(1, 33):
            t = i / 32
            u = 1 - t
            q = (u ** 3 * a[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p[0],
                 u ** 3 * a[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p[1])
            total += ((q[0] - prev[0]) ** 2 + (q[1] - prev[1]) ** 2) ** .5
            prev = q
        a = p
    return total


def _fmt(p):
    return f"{round(p[0])},{round(p[1])}"


def _write(p0, segs):
    d = "M" + _fmt(p0)
    prev_c2, prev_p = None, p0
    for c1, c2, p in segs:
        smooth = prev_c2 and abs(2 * prev_p[0] - prev_c2[0] - c1[0]) < 1.5 and abs(2 * prev_p[1] - prev_c2[1] - c1[1]) < 1.5
        d += (f"S{_fmt(c2)} {_fmt(p)}" if smooth else f"C{_fmt(c1)} {_fmt(c2)} {_fmt(p)}").replace(" -", "-")
        prev_c2, prev_p = c2, p
    return d


def wander_path(d, amount, rng):
    """A random variation of path d: bends of up to `amount` px sideways to the
    direction of travel (y for mostly-horizontal paths, x for vertical ones).
    Endpoints keep their off-screen coordinate, so actors still park hidden.
    Returns (new_d, length)."""
    p0, segs = _cubics(d)
    if amount and len(segs) == 1:
        segs = list(_split(p0, segs[0]))
    if not amount:
        return d, _length(p0, segs)
    end = segs[-1][2]
    ax = 1 if abs(end[0] - p0[0]) >= abs(end[1] - p0[1]) else 0  # axis to bend along: 1 = y
    lo, hi = (90, VIEW_H - 90) if ax else (90, VIEW_W - 90)

    def nudge(p, dv):
        q = list(p)
        if lo <= p[ax] <= hi:  # leave deliberately off-screen points alone
            q[ax] = min(hi, max(lo, p[ax] + dv))
        return tuple(q)

    style = rng.random()
    if style < .2:  # gentle: mostly the designed route
        amount *= .35
    out, a = [], p0
    shared = rng.uniform(-1, 1)  # a common bias makes arcs/dips; independent parts make S-bends
    for i, (c1, c2, p) in enumerate(segs):
        last = i == len(segs) - 1
        dp = rng.uniform(-.6, .6) * amount if last else (shared * .6 + rng.uniform(-.7, .7)) * amount
        if i == 0:
            d1 = (shared * .5 + rng.uniform(-.8, .8)) * amount
        else:  # keep the joint smooth: mirror the previous outgoing control
            pc2, pp = out[-1][1], out[-1][2]
            out_c1 = (2 * pp[0] - pc2[0], 2 * pp[1] - pc2[1])
            d1 = None
        d2 = (shared * .5 + rng.uniform(-.8, .8)) * amount
        n1 = nudge(c1, d1) if d1 is not None else out_c1
        n2 = nudge(c2, d2)
        np_ = nudge(p, dp) if not last else tuple(
            (p[k] + (dp if k == ax else 0)) for k in (0, 1))
        out.append((n1, n2, np_))
        a = p
    return _write(p0, out), _length(p0, out)


def parade(actors, rounds=3, overlap=4, seed=1, lead=.5, tail=1, jitter=0):
    """Schedule actors to take turns, `rounds` times, each round shuffled.

    The next actor starts `overlap` seconds before the current one finishes,
    so at most two are on screen. `jitter` adds a random 0..jitter seconds to
    each gap, so the rhythm is uneven too. Every pass also gets its own lane and
    (unless the actor's wander is 0) its own curved route. Returns
    (svg, loop_seconds, schedule) where schedule is a list of {name, start, end}.
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
        t += a.dur - overlap + (rng.uniform(0, jitter) if jitter else 0)
    loop = round(slots[-1][2] + tail, 1)

    svg = ""
    for a in actors:
        mine = [(s, e) for b, s, e in slots if b is a]
        n = len(mine)
        subpaths, lengths = [], []
        for _ in range(n):
            (dxl, dxh), (dyl, dyh) = a.lanes
            base = shift_path(a.path, round(rng.uniform(dxl, dxh)), round(rng.uniform(dyl, dyh)))
            d, ln = wander_path(base, a.wander, rng)
            subpaths.append(d)
            lengths.append(ln)
        # Move-tos jump between passes without adding length, so pass k covers the
        # keyPoints span of its own share of the total length.
        total, acc = sum(lengths), 0.0
        kt, kp = ["0"], ["0"]
        for k, (s, e) in enumerate(mine):
            kt += [f"{s / loop:.4f}".rstrip("0").rstrip("."), f"{e / loop:.4f}".rstrip("0").rstrip(".")]
            kp += [f"{acc / total:.4g}", f"{(acc + lengths[k]) / total:.4g}" if k < n - 1 else "1"]
            acc += lengths[k]
        kt.append("1")
        kp.append("1")
        rot = " rotate='auto'" if a.rotate else ""
        inner = f"scale({a.scale:g},{-a.scale:g})" if a.flip else f"scale({a.scale:g})"
        body = a.body if inner == "scale(1)" else f"<g transform='{inner}'>{a.body}</g>"
        op = f" opacity='{a.opacity:g}'" if a.opacity != 1 else ""
        svg += (f"<g{op}><animateMotion dur='{loop:g}s' repeatCount='indefinite' calcMode='linear' "
                f"keyPoints='{';'.join(kp)}' keyTimes='{';'.join(kt)}'{rot} path='{''.join(subpaths)}'/>"
                f"{body}</g>")
    schedule = [{"name": a.name, "start": round(s, 2), "end": round(e, 2)} for a, s, e in slots]
    return svg, loop, schedule


def specks(n, color, seed=7, radii=(1.3, 1.6, 2), opacities=(.25, .35, .5, .65), twinkle_every=4,
           twinkle=(4, 9), drift=(-20, -12), drift_dur=60, w=VIEW_W, h=VIEW_H, groups=3):
    """Scattered background dots (plankton, stars, dust). Every `twinkle_every`-th one
    fades in and out. Twinkling dots share `groups` animations (each group on its own
    period and phase) rather than one each, which saves a lot of characters."""
    rng = random.Random(seed)
    steady, tw = "", [""] * groups
    for i in range(n):
        x, y, o = rng.randint(0, w), rng.randint(0, h), rng.choice(opacities)
        dot = f"<circle cx='{x}' cy='{y}' r='{rng.choice(radii):g}' opacity='{o:g}'/>"
        if twinkle_every and i % twinkle_every == 0:
            tw[(i // twinkle_every) % groups] += dot
        else:
            steady += dot
    for k in range(groups):
        if tw[k]:
            dur = rng.randint(*twinkle)
            steady += f"<g>{blink('1;.1;1', dur, begin=-rng.uniform(0, dur))}{tw[k]}</g>"
    anim = ""
    if drift:
        anim = (f"<animateTransform attributeName='transform' type='translate' dur='{drift_dur}s' "
                f"repeatCount='indefinite' values='0 0;{drift[0]} {drift[1]};0 0'/>")
    return f"<g fill='{color}'>{anim}{steady}</g>"


# ---------------------------------------------------------------------------
# Assembling and writing a theme
# ---------------------------------------------------------------------------

CHAT = '[data-workspace-area="conversation"]'
HAS_MSG = ':has([data-timeline-row-kind])'
WRAP = '[data-slot="sidebar-wrapper"]'

_LEAD0 = re.compile(r"(?<=[='; ,(:-])0\.(\d)")


def build_svg(defs, *layers):
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {VIEW_W} {VIEW_H}' preserveAspectRatio='xMidYMid slice'>"
           f"<defs>{defs}</defs>{''.join(layers)}</svg>")
    svg = _LEAD0.sub(r".\1", svg)  # 0.35 -> .35 everywhere
    assert '"' not in svg, "use single quotes inside the SVG"
    xml.dom.minidom.parseString(svg)  # one XML error silently blanks the whole background
    return svg


def data_url(svg):
    # Only % and # must be escaped (plus the quote style, which the SVG never uses).
    # Raw < and > are fine in every current browser and save ~6 characters per tag.
    return "data:image/svg+xml," + svg.replace("%", "%25").replace("#", "%23")


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------


def _rgb(c):
    c = c.lstrip("#")
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)]


def mix(a, b, t):
    """Blend hex colors: t=0 gives a, t=1 gives b."""
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(_rgb(a), _rgb(b)))


def _lum(c):
    r, g, b = (v / 255 for v in _rgb(c))
    return .2126 * r + .7152 * g + .0722 * b


def palette(canvas, accent, sidebar, dark=True):
    """A full set of T3 color roles tinted to match the scene, so message bubbles,
    menus, code blocks, inputs and the terminal all belong to the theme.
    Roles cost nothing against the 20,000-character CSS limit."""
    ink = "#ffffff" if dark else "#0b1220"
    lift = (lambda t: mix(canvas, mix("#ffffff", accent, .25), t)) if dark else (lambda t: mix(canvas, "#ffffff", t * 4))
    on_accent = "#06101a" if _lum(accent) > .45 else "#ffffff"
    tint = lambda t: mix(canvas, accent, t)  # noqa: E731
    muted_text = mix(mix(ink, accent, .12), canvas, .38)
    return {
        "canvas": canvas, "chrome": sidebar, "toolbar": sidebar, "sidebar": sidebar,
        "sidebarBorder": mix(sidebar, accent, .1 if dark else .14),
        "border": mix(lift(.07), accent, .06) if dark else mix(canvas, ink, .1),
        "accent": accent, "accentForeground": on_accent, "focus": accent,
        "surface": lift(.035), "surfaceRaised": lift(.06), "surfaceOverlay": lift(.045),
        "input": mix(lift(.08), accent, .1) if dark else mix(canvas, ink, .14),
        "messageSurface": tint(.18 if dark else .12),
        "messageAction": accent, "messageActionForeground": on_accent,
        "messageActionHover": mix(accent, "#ffffff" if dark else "#000000", .15),
        "accentSurface": tint(.14 if dark else .1), "accentSurfaceForeground": mix(accent, ink, .45),
        "update": accent, "updateForeground": mix(accent, ink, .4), "updateSurface": tint(.12),
        "muted": tint(.1), "secondary": tint(.08), "secondaryForeground": mix(ink, accent, .06),
        "mutedForeground": muted_text, "secondaryLabel": muted_text, "sidebarMutedForeground": muted_text,
        "sidebarControlSurface": sidebar,
        "sidebarRowHover": mix(sidebar, accent, .1), "sidebarRowActive": mix(sidebar, accent, .16),
        "sidebarRowSelected": mix(sidebar, accent, .2),
        "codeBackground": mix(canvas, "#000000", .3) if dark else mix(canvas, "#ffffff", .6),
        "terminalBackground": mix(canvas, "#000000", .25) if dark else mix(canvas, "#ffffff", .5),
        "terminalCursor": mix(accent, ink, .35), "terminalSelection": tint(.3),
        "searchMatchBackground": tint(.35), "searchMatchActiveBackground": accent,
        "searchMatchActiveForeground": on_accent,
    }


def _alpha(c, a):
    return c + f"{round(a * 255):02x}"


# ---------------------------------------------------------------------------
# Theme CSS
# ---------------------------------------------------------------------------


def build_css(svg, dark, light=None):
    """Theme CSS. The animated scene fills the whole window, behind a see-through
    sidebar, and the chat area adds a veil once a thread has messages.

    dark / light: dicts with
        bg         scene color behind everything
        glow       soft glow at the top (or None)
        veil       color over the chat area on the empty new-thread page (alpha hex)
        veil_chat  stronger veil once a thread has messages, so text stays readable
        accent     theme accent (tints bubbles, the current thread, menus)
        sidebar    sidebar color; drawn at ~64% (78% in light mode) so the scene shows through
    Without `light`, everything applies in dark mode only.

    The whole-window layout relies on T3's sidebar wrapper markup (the approach
    Nyx uses: github.com/Deepusleepy/t3-nyx-theme). If a T3 update renames it, the
    scene falls back to filling the chat area alone, as before.
    """
    P = "" if light else ".dark "
    R = ":root" if light else ".dark"
    ac = dark["accent"]
    t = lambda a: _alpha(ac, a)  # noqa: E731  accent at alpha a

    def vars_(p, lm=False):
        bg = p["bg"]
        return (f"--bg:{bg};--glow:{p.get('glow') or '#0000'};--veil:{p['veil']};--vc:{p['veil_chat']};"
                f"--sb:{_alpha(p['sidebar'], .78 if lm else .64)};--hd:{_alpha(bg, .8)};--sc:{_alpha(bg, .75 if lm else .7)};"
                f"--bu:{_alpha(mix(bg, ac, .12 if lm else .16), .8)};--po:{_alpha(mix(bg, '#ffffff' if lm else ac, .6 if lm else .07), .94)}")

    W = "[data-slot=sidebar-wrapper]"
    C = "[data-workspace-area=conversation]"
    H = ":has([data-timeline-row-kind])"
    hw = f"{R}:has({W}) "
    css = (
        f'{R}{{--sea:url("{data_url(svg)}");{vars_(dark)};'
        f'--sn:radial-gradient(ellipse at 50% 0%,var(--glow),#0000 60%),var(--sea) center/cover no-repeat,var(--bg);'
        f'--sh:inset 0 -14px 22px -16px {t(.6)},inset 0 1px 0 #ffffff0d}}'
        + (f":root:not(.dark){{{vars_(light, True)}}}" if light else "")
        # whole-window scene behind the sidebar wrapper, with the layers above it cleared
        + f'{P}{W}{{isolation:isolate;background:var(--bg)}}'
        f'{P}{W}::before{{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background:var(--sn);will-change:transform}}'
        f'{hw}:is([data-slot=sidebar-inset],[data-slot=sidebar-inset]>div,[data-chat-canvas],[data-timeline-loading],'
        f'.messages-timeline-scroll,[data-chat-composer-form]){{background:#0000!important}}'
        f'{P}[data-slot=sidebar-inner]{{background:var(--sb)!important}}'
        f'{hw}[data-chat-header]{{background:var(--hd)!important}}'
        # chat area: the scene itself if there's no wrapper, else just the veil
        f'{P}{C}{{background:linear-gradient(var(--veil),var(--veil)),var(--sn)!important}}'
        f'{hw}{C}{{background:var(--veil)!important}}'
        f'{P}{C}{H}{{--veil:var(--vc)}}'
        f'{P}{C} :is(.messages-timeline-scroll,[data-chat-composer-form]){{background:#0000!important}}'
        # new-thread page: a soft dark pool behind the composer and its heading
        f'{P}{C}:not({H}) [data-slot=composer-host]{{box-shadow:0 -60px 150px 70px var(--sc)}}'
        # small touches in the accent color
        f'{P}[data-user-message-bubble]{{background:linear-gradient(90deg,{t(.26)},{t(.06)}),var(--bu)!important;box-shadow:var(--sh)!important}}'
        f'{P}[data-thread-item] [aria-current=page]{{background:linear-gradient(90deg,{t(.32)},{t(.08)} 60%,#0000)!important;box-shadow:var(--sh)!important}}'
        f'{P}:is([data-slot=popover-popup],[data-slot=menu-popup]){{background:linear-gradient(160deg,{t(.14)},#0000 45%),var(--po)!important;border-color:{t(.18)}!important}}'
        f'@media (prefers-reduced-motion:reduce){{{R}{{--sea:none!important}}}}'
    )
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

    dark_chrome / light_chrome: at least {"canvas": ..., "sidebar": ...}. The rest of
    T3's color roles are derived from these and the accent (see palette()); any role
    given here overrides the derived one.
    """
    assert len(css) <= CSS_LIMIT, f"theme css is {len(css)} chars; T3 allows {CSS_LIMIT}"
    os.makedirs(os.path.join(out_dir, "preview"), exist_ok=True)

    def w(path, text):
        with open(os.path.join(out_dir, path), "w") as fh:
            fh.write(text)

    w("background.svg", svg)
    w("theme.css", css)
    chrome = palette(dark_chrome["canvas"], accent, dark_chrome["sidebar"])
    chrome.update(dark_chrome)
    canvas = chrome.pop("canvas")
    chrome.pop("accent")
    theme = {"version": 1, "name": name, "appearance": "dark", "canvas": canvas, "accent": accent, "colors": chrome}
    if light_chrome:
        lc = palette(light_chrome["canvas"], light_chrome.get("accent", accent), light_chrome["sidebar"], dark=False)
        lc.update(light_chrome)
        theme["variants"] = {"light": lc}
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

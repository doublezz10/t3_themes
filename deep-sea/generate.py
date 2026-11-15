"""Generate the Deep Sea T3 Code theme.

A parade of dot-matrix sea animals swims behind the chat area, one or two on
screen at a time. The background is an animated SVG (SMIL) embedded in the
theme CSS as a data: URL, because T3 themes cannot load external files.

    python3 generate.py

writes background.svg, theme.css, theme.json and preview/gallery.svg next to
this script. The output is deterministic (fixed random seed).
"""
import json
import math
import os
import random
import xml.dom.minidom

random.seed(7)
OUT = os.path.dirname(os.path.abspath(__file__))
B, M, L, W = "#2f5fe0", "#4a7bf0", "#8fb0ff", "#dfe8ff"
OVERLAP = 4  # seconds the next animal overlaps the previous one


def pat(pid, step, r, cols):
    s = f"<pattern id='{pid}' width='{step*3}' height='{step*3}' patternUnits='userSpaceOnUse'>"
    for i in range(9):
        s += f"<circle cx='{i%3*step+step/2:g}' cy='{i//3*step+step/2:g}' r='{r}' fill='{cols[i]}'/>"
    return s + "</pattern>"


def wave(a, b, dur):  # animate a path's d between two shapes
    return f"<animate attributeName='d' dur='{dur}s' repeatCount='indefinite' values='{a};{b};{a}'/>"


def spin(vals, dur):
    return f"<animateTransform attributeName='transform' type='rotate' dur='{dur}s' repeatCount='indefinite' values='{vals}'/>"


def pulse(vals, dur):
    return f"<animateTransform attributeName='transform' type='scale' dur='{dur}s' repeatCount='indefinite' values='{vals}'/>"


DOT = f"fill='none' stroke='{M}' stroke-linecap='round' stroke-dasharray='0 5'"

defs = (pat("d", 5, 1.75, [B, M, B, L, B, M, B, W, M])
        + pat("f", 4, 1.45, [M, B, L, B, W, B, M, B, L]))

# ---------- bodies (facing +x, head near origin) ----------
ta, tb = "M-185,0C-215,-1-245,-8-290,-14", "M-185,0C-215,2-245,10-290,16"
shark = ("<path d='M0,0C-8,-9-30,-13-55,-14L-70,-14L-118,-58L-104,-13L-150,-8L-185,-4L-185,4L-150,8"
         "L-112,11L-132,44L-84,14L-55,14C-30,13-8,9,0,0Z' fill='url(#d)'/>"
         f"<path d='{ta}' {DOT} stroke-width='3.4'>{wave(ta, tb, 1.6)}</path>")

ray = ("<g transform='rotate(90)'><g>" + pulse("1 1;.62 1;1 1", 3.2)
       + "<path d='M0,-70C14,-50 40,-20 78,4C40,18 14,30 0,46C-14,30-40,18-78,4C-40,-20-14,-50 0,-70Z' fill='url(#d)'/></g>"
       f"<path d='M0,46L0,140' {DOT} stroke-width='3.4'/></g>")

defs += "<g id='fi'><ellipse rx='10' ry='4.5' fill='url(#f)'/><path d='M-9,0L-16,-4L-16,4Z' fill='url(#f)'/></g>"
school = ""
for i in range(14):
    x = random.uniform(-110, 110)
    y = random.uniform(-45, 45) + x * .18
    school += (f"<use href='#fi' x='{x:.0f}' y='{y:.0f}'><animateTransform attributeName='transform' type='translate' "
               f"dur='{random.uniform(1.6, 2.6):.1f}s' repeatCount='indefinite' values='0 0;3 {random.uniform(2, 5):.0f};0 0'/></use>")

ja, jb = "M0,6C8,40-8,80 0,120", "M0,6C-8,40 8,80 0,120"
defs += f"<path id='jt' d='{ja}'>{wave(ja, jb, 2.4)}</path>"
jelly = ("<g>" + pulse("1 1;1.12 .82;1 1", 2.4)
         + "<path d='M-40,0C-42,-52 42,-52 40,0C28,6 14,2 0,6C-14,2-28,6-40,0Z' fill='url(#d)'/></g>"
         f"<g {DOT} stroke-width='3'>" + "".join(f"<use href='#jt' x='{x}'/>" for x in (-28, -14, 0, 14, 28)) + "</g>")

defs += ("<g id='tf'><path d='M18,-28C30,-72 0,-92-24,-82C-2,-62 4,-46 2,-28Z' fill='url(#d)'>" + spin("0 10 -28;-28 10 -28;0 10 -28", 2.6)
         + "</path><path d='M-36,-20L-64,-36L-52,-10Z' fill='url(#d)'/></g>")
turtle = ("<use href='#tf'/><use href='#tf' transform='scale(1,-1)'/>"
          "<ellipse rx='46' ry='36' fill='url(#d)'/><ellipse cx='58' rx='15' ry='11' fill='url(#d)'/>"
          "<path d='M-44,-5L-62,0L-44,5Z' fill='url(#d)'/>")

sword = ("<path d='M70,0L0,-3C-20,-14-60,-18-100,-14L-82,-52L-130,-12L-170,-5L-200,-36L-190,0L-200,36L-170,5"
         "L-120,12L-92,24L-80,12C-50,16-20,12 0,3Z' fill='url(#d)'/>")

defs += f"<path id='ot' d='M-36,0C-80,-12-110,12-170,0'>{wave('M-36,0C-80,-12-110,12-170,0', 'M-36,0C-80,12-110,-12-170,0', 1.8)}</path>"
octo = (f"<g {DOT} stroke-width='3.4'>" + "".join(f"<use href='#ot' y='{y}'/>" for y in (-24, -12, 0, 12, 24)) + "</g>"
        "<g>" + pulse("1 1;.9 1.12;1 1", 1.8) + "<path d='M44,0C44,-42-20,-46-40,-24L-40,24C-20,46 44,42 44,0Z' fill='url(#d)'/></g>")

whale = ("<path d='M0,0C-10,-35-110,-55-250,-42C-350,-32-420,-14-470,-4L-470,4C-400,24-300,44-180,46C-90,46-20,30 0,0Z' fill='url(#d)'/>"
         "<path d='M-130,36C-150,76-196,116-246,124C-210,94-186,64-166,38Z' fill='url(#d)'>" + spin("0 -150 36;14 -150 36;0 -150 36", 4) + "</path>"
         "<path d='M-462,-4L-524,-48L-504,0L-524,48L-462,4Z' fill='url(#d)'>" + spin("0 -470 0;-14 -470 0;14 -470 0;0 -470 0", 4) + "</path>")

seahorse = ("<path d='M0,-60C15,-62 22,-55 20,-48L46,-44L46,-37L18,-36C22,-20 8,-8 10,10C12,30 18,45 8,60"
            "C0,72-18,70-18,58C-18,50-8,50-8,56C-6,48 2,40-2,25C-6,10-18,0-16,-20C-14,-40-12,-58 0,-60Z' fill='url(#d)'/>"
            "<path d='M-14,-10L-30,-4L-28,14L-10,8Z' fill='url(#d)'>" + spin("0 -12 0;-18 -12 0;0 -12 0", .6) + "</path>")

def eelp(ph):
    return "M" + "L".join(f"{-x},{18 * min(1, x / 120) * math.sin(x / 38 + ph):.0f}" for x in range(0, 361, 24))
ev = ";".join(eelp(k * math.pi / 2) for k in (0, 1, 2, 3, 0))
defs += f"<path id='el' d='{eelp(0)}'><animate attributeName='d' dur='2s' repeatCount='indefinite' values='{ev}'/></path>"
eel = (f"<g fill='none' stroke='{M}' stroke-linecap='round' stroke-dasharray='0 8' stroke-width='5'><use href='#el' y='-4'/><use href='#el' y='4'/></g>"
       "<ellipse cx='4' rx='18' ry='10' fill='url(#d)'/>")

dolphin = ("<path d='M40,2L18,-2C0,-16-50,-22-100,-16C-104,-30-110,-44-122,-50C-122,-36-126,-24-128,-14C-160,-10-190,-4-210,0L-240,-22L-230,2L-240,24L-210,4"
           "C-170,12-120,20-80,18L-96,40L-66,18C-30,16 10,10 18,6Z' fill='url(#d)'/>")

puffer = ("<path d='M-28,0L-50,-16L-50,16Z' fill='url(#d)'/><g>" + pulse("1;1.22;1.22;1", 5)
          + f"<circle r='30' fill='url(#d)'/><circle r='37' fill='none' stroke='{M}' stroke-linecap='round' stroke-width='3' stroke-dasharray='0 9'/></g>")

defs += f"<g id='cl'><path d='M30,-14L54,-30M28,-4L58,-12M26,6L56,10' {DOT} stroke-width='3'>" + spin("0 26 0;8 26 0;0 26 0", .5) + "</path>" \
        "<circle cx='40' cy='-40' r='13' fill='url(#d)'/></g>"
crab = ("<use href='#cl'/><use href='#cl' transform='scale(-1,1)'/><ellipse rx='36' ry='25' fill='url(#d)'/>")


angler = ("<path d='M30,-6C30,-40-20,-48-50,-30C-70,-18-80,-8-96,-4L-118,-24L-110,0L-118,24L-96,4C-80,10-60,26-30,32C0,36 24,22 30,10L14,4Z' fill='url(#d)'/>"
          f"<path d='M-6,-40C8,-82 40,-82 48,-58' {DOT} stroke-width='3'/>"
          f"<circle cx='48' cy='-52' r='6' fill='{W}'><animate attributeName='opacity' values='1;.25;1' dur='2.2s' repeatCount='indefinite'/></circle>")

squid = (f"<g {DOT} stroke-width='3'>" + "".join(f"<use href='#ot' y='{y}'/>" for y in (-10, -3, 4, 11)) + "</g>"
         "<path d='M64,0C50,-8 30,-16-40,-14L-40,14C30,16 50,8 64,0ZM64,0L40,-28L32,-8ZM64,0L40,28L32,8Z' fill='url(#d)'/>")

ha, hb = "M-140,0C-160,-2-180,-8-210,-12", "M-140,0C-160,2-180,8-210,12"
hammer = ("<path d='M4,-38L28,-38L28,38L4,38L0,8L-60,10L-130,4L-140,0L-130,-4L-60,-10L0,-8Z"
          "M-24,-9L-58,-42L-52,-9ZM-24,9L-58,42L-52,9Z' fill='url(#d)'/>"
          f"<path d='{ha}' {DOT} stroke-width='3.4'>{wave(ha, hb, 1.4)}</path>")

# ---------- parade: (name, body, scale, duration, path, rotate, flip, opacity) ----------
H = "M-700,{y}C300,{a} 1000,{b} 2300,{c}"
R = "M2300,{y}C1300,{a} 600,{b} -{e},{c}"
parade = [
    ("shark", shark, 1.6, 18, H.format(y=640, a=560, b=700, c=600), 1, 0, .9),
    ("jelly", jelly, 1.5, 26, "M1150,1250C1050,900 1250,500 1100,-300", 0, 0, .85),
    ("school", f"<g>{school}</g>", 1.5, 22, R.format(y=760, a=700, b=820, c=700, e=700), 1, 0, .85),
    ("turtle", turtle, 1.4, 22, "M-250,900C400,700 900,500 1850,150", 1, 0, .9),
    ("swordfish", sword, 1.4, 12, H.format(y=380, a=420, b=330, c=400), 1, 0, .9),
    ("octopus", octo, 1.3, 18, "M500,1300C600,900 900,600 1300,-300", 1, 0, .85),
    ("whale", whale, 1.1, 38, R.format(y=470, a=430, b=520, c=460, e=1000), 1, 1, .7),
    ("seahorse", seahorse, 1.7, 24, "M-150,520C250,420 450,640 800,520S1400,420 1750,560", 0, 0, .9),
    ("ray", ray, 1.6, 20, "M300,1250C380,900 520,500 420,-300", 1, 0, .85),
    ("anglerfish", angler, 1.5, 22, H.format(y=300, a=360, b=260, c=320), 1, 0, .9),
    ("eel", eel, 1.3, 23, R.format(y=780, a=740, b=820, c=760, e=700), 1, 0, .85),
    ("dolphin", dolphin, 1.5, 15, "M-450,760C300,330 1100,330 2300,700", 1, 0, .9),
    ("hammerhead", hammer, 1.5, 18, "M-500,250C300,350 1000,650 2200,800", 1, 0, .9),
    ("puffer", puffer, 1.5, 25, R.format(y=330, a=280, b=400, c=320, e=700), 1, 1, .9),
    ("squid", squid, 1.4, 18, "M2100,180C1400,260 900,520-500,720", 1, 0, .85),
    ("crab", crab, 1.3, 22, "M1800,820C1200,800 600,840-200,820", 0, 0, .85),
]

starts, t = [], .5
for p in parade:
    starts.append(t)
    t += p[3] - OVERLAP
T = round(starts[-1] + parade[-1][3] + 1, 1)

ROT = " rotate='auto'"
animals = ""
for (name, body, sc, dur, path, rot, flip, op), st in zip(parade, starts):
    a, b = st / T, (st + dur) / T
    inner = f"scale({sc},{-sc})" if flip else f"scale({sc})"
    animals += (f"<g opacity='{op}'><animateMotion dur='{T}s' repeatCount='indefinite' calcMode='linear' "
                f"keyPoints='0;0;1;1' keyTimes='0;{a:.4f};{b:.4f};1'{ROT if rot else ''} path='{path}'/>"
                f"<g transform='{inner}'>{body}</g></g>")

plank = ""
for i in range(30):
    x, y, o = random.randint(0, 1600), random.randint(0, 1000), random.choice([.25, .35, .5, .65])
    plank += f"<circle cx='{x}' cy='{y}' r='{random.choice([1.3, 1.6, 2])}' opacity='{o}'"
    plank += (f"><animate attributeName='opacity' values='{o};.05;{o}' dur='{random.randint(4, 9)}s' repeatCount='indefinite'/></circle>"
              if i % 4 == 0 else "/>")
plank = (f"<g fill='{M}'><animateTransform attributeName='transform' type='translate' dur='60s' repeatCount='indefinite' "
         f"values='0 0;-20 -12;0 0'/>{plank}</g>")

svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 1000' preserveAspectRatio='xMidYMid slice'>"
       f"<defs>{defs}</defs>{plank}{animals}</svg>")
xml.dom.minidom.parseString(svg)  # an XML error would silently blank the whole background
open(os.path.join(OUT, "background.svg"), "w").write(svg)

enc = svg.replace("%", "%25").replace("#", "%23").replace("<", "%3C").replace(">", "%3E")
# Colors per appearance. The same background SVG serves both; only the water color,
# the glow and the veil that softens the animals change. "veil" applies everywhere,
# "veil_chat" once a thread has messages, so the animals don't fight the text.
DARK = {"bg": "#0d1016", "glow": "rgba(47,95,224,.07)", "veil": "#0d101600", "veil_chat": "#0d101699"}
LIGHT = {"bg": "#eef4fa", "glow": "rgba(47,95,224,.12)", "veil": "#eef4fa40", "veil_chat": "#eef4fac0"}

A = '[data-workspace-area="conversation"]'
L = f':root:not(.dark) {A}'  # light appearance
HAS_MSG = ':has([data-timeline-row-kind])'
css = (f'{A}{{--sea:url("data:image/svg+xml,{enc}");--bg:{DARK["bg"]};--glow:{DARK["glow"]};--veil:{DARK["veil"]};'
       'background:linear-gradient(var(--veil),var(--veil)),radial-gradient(ellipse at 50% 0%,var(--glow),transparent 60%),'
       'var(--sea) center/cover no-repeat,var(--bg)!important}'
       f'{A}{HAS_MSG}{{--veil:{DARK["veil_chat"]}}}'
       f'{L}{{--bg:{LIGHT["bg"]};--glow:{LIGHT["glow"]};--veil:{LIGHT["veil"]}}}'
       f'{L}{HAS_MSG}{{--veil:{LIGHT["veil_chat"]}}}'
       f'{A} .messages-timeline-scroll,{A} [data-chat-composer-form]{{background:transparent!important}}'
       f'@media (prefers-reduced-motion:reduce){{{A}{{background:var(--bg)!important}}}}')
assert len(css) <= 20000, f"theme css is {len(css)} chars; T3 allows 20,000"
open(os.path.join(OUT, "theme.css"), "w").write(css)

# The object T3's theme tool takes (t3_theme_set, themeId "deep-sea").
# Dark is the primary appearance; variants.light restyles the chrome for light mode.
theme = {"version": 1, "name": "Deep Sea", "appearance": "dark", "canvas": DARK["bg"], "accent": "#3b6cf6",
         "colors": {"sidebar": "#0a0b0d", "chrome": "#0a0b0d", "toolbar": "#0a0b0d"},
         "variants": {"light": {"canvas": LIGHT["bg"], "sidebar": "#e3eaf3", "chrome": "#e3eaf3", "toolbar": "#e3eaf3"}},
         "css": css}
with open(os.path.join(OUT, "theme.json"), "w") as fh:
    json.dump(theme, fh, indent=2)
    fh.write("\n")
print(f"{len(parade)} animals, {T}s loop, css {len(css)}/20000 chars")

# Static gallery of every animal, for checking shapes
cells = ""
for i, (name, body, sc, *_r) in enumerate(parade):
    x, y = 260 + (i % 4) * 400, 160 + (i // 4) * 260
    fl = ",-1" if name in ("whale",) else ""
    k = .55 if name == "whale" else 1
    cells += f"<g transform='translate({x + (120 if name=='whale' else 0)},{y}) scale({k}{fl and ','+str(-k)})'>{body}</g><text x='{x-200}' y='{y+110}' fill='#888' font-size='18'>{name}</text>"
gal = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 1300' style='background:#0d1016'><defs>{defs}</defs>{cells}</svg>"
open(os.path.join(OUT, "preview", "gallery.svg"), "w").write(gal)

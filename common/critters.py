"""Typing companions: a small dot-matrix critter that sits on the composer's top
edge, sleeps while the composer isn't focused, wakes when you click in, and
moves along above the end of your text as you type.

The trick (from the Koi Pond and Biscuit skins on t3skins.dev): the critter is
the ::after of the composer's last paragraph, absolutely positioned with
left:auto. An absolute box with no left keeps its "static" horizontal
position, which is just after the last character typed. The editor itself is
a scroller, so it's made position:static and its parent becomes the
containing block; otherwise the scroller would clip the critter.

Each critter is drawn as rows of characters, one dot per character, in the
same dotted style as the scenes. Blinks, a glow or a bob are CSS animations
inside the SVG, so the SVG's own prefers-reduced-motion rule can stop them.
"""
import xml.dom.minidom

from themekit import _alpha, data_url

DOT = 3  # px between dots; the sprite is drawn at 1 SVG unit = 1 CSS px


class Critter:
    def __init__(self, name, art, colors, eyes="E", eye_under="W", sleep_art=None, anim=None, body_anim="",
                 extra_awake="", extra_css="", glow=None, lift=0):
        """art: rows of characters; '.' is empty, every other character is a key into colors.
        eyes: characters that blink (and close when asleep); eye_under: the color drawn under them.
        sleep_art: a different pose for sleeping; default is the awake pose with eyes closed.
        anim: {character: css animation} for parts that move while awake (a glowing tail tip...).
        body_anim: css animation for the whole critter while awake (a bob, a sway).
        extra_awake: raw SVG drawn on top while awake (drips, bubbles).
        lift: px to raise (+) or lower (-) the critter relative to the composer edge."""
        self.name, self.art, self.colors, self.eyes, self.eye_under = name, art, colors, eyes, eye_under
        self.sleep_art, self.anim, self.body_anim = sleep_art, anim or {}, body_anim
        self.extra_awake, self.extra_css, self.glow, self.lift = extra_awake, extra_css, glow, lift

    def _rows(self, art):
        return [r for r in art.strip("\n").split("\n")]

    def size(self):
        rows = self._rows(self.art)
        return max(len(r) for r in rows) * DOT, len(rows) * DOT

    def svg(self, asleep):
        rows = self._rows(self.sleep_art if (asleep and self.sleep_art) else self.art)
        w, h = self.size()
        groups = {}  # (color, css class) -> path data
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch == ".":
                    continue
                pos = f"M{x * DOT + DOT / 2:g} {y * DOT + DOT / 2:g}h0"
                if ch in self.eyes:
                    groups.setdefault((self.colors[self.eye_under], ""), []).append(pos)
                    if asleep:
                        continue
                    groups.setdefault((self.colors[ch], "e"), []).append(pos)
                else:
                    cls = "" if asleep or ch not in self.anim else "a" + ch
                    groups.setdefault((self.colors[ch], cls), []).append(pos)
        paths = "".join("<path" + (f" class='{c}'" if c else "") + f" stroke='{col}' d='{''.join(d)}'/>"
                        for (col, c), d in groups.items())
        style = ("@keyframes b{0%,93%,100%{opacity:1}95%{opacity:0}}.e{animation:b 4.7s infinite}"
                 "@keyframes z{0%{opacity:0;transform:translate(0,4px)}30%{opacity:.85}100%{opacity:0;transform:translate(5px,-9px)}}"
                 ".z{animation:z 3.2s infinite;font:bold 8px monospace}.z2{animation-delay:-1.6s}")
        used = set()
        if not asleep:
            for ch, a in self.anim.items():
                style += f".a{ch}{{animation:{a}}}"
                used.add(a.split()[0])
            if self.body_anim:
                style += f".bd{{animation:{self.body_anim};transform-box:fill-box;transform-origin:50% 100%}}"
                used.add(self.body_anim.split()[0])
            style += self.extra_css
        style += "".join(KEYFRAMES[k] for k in sorted(used))
        style += "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        zz = ""
        if asleep:
            zc = self.glow or "#ffffff"
            zz = (f"<text class='z' x='{w - 7}' y='{9}' fill='{zc}'>z</text>"
                  f"<text class='z z2' x='{w - 7}' y='{9}' fill='{zc}'>z</text>")
        # the box is padded 10px on top for the floating z's
        out = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 -10 {w} {h + 10}'><style>{style}</style>"
                f"<g class='bd' fill='none' stroke-width='2.6' stroke-linecap='round'>{paths}"
                f"{'' if asleep else self.extra_awake}</g>{zz}</svg>")
        xml.dom.minidom.parseString(out)  # one XML error blanks the sprite
        return out

    @staticmethod
    def _url(svg):
        # a raw "</style>" would end the <style> element the theme CSS sits in, so escape its "<"
        return data_url(svg).replace("</style>", "%3C/style>")

    def css(self, P):
        """CSS for the theme. P is the selector prefix ('.dark ' for dark-only themes)."""
        w, h = self.size()
        h += 10
        glow = f"filter:drop-shadow(0 0 5px {_alpha(self.glow, .45)});" if self.glow else ""
        return (f"{P}[data-slot=composer-host] :has(>.composer-tiptap){{position:relative!important}}"
                f"{P}[data-slot=composer-host] .composer-tiptap{{position:static!important}}"
                f'{P}.composer-tiptap>p:last-child::after{{content:"";position:absolute;top:{-(h + 11 + self.lift)}px;'
                f'margin-left:-3px;width:{w}px;height:{h}px;pointer-events:none;z-index:40;{glow}'
                f'background:url("{self._url(self.svg(True))}") 0 0/100% 100% no-repeat}}'
                f'{P}.composer-tiptap:focus>p:last-child::after{{background-image:url("{self._url(self.svg(False))}")}}')


# ---------------------------------------------------------------------------
# The cast, one per theme
# ---------------------------------------------------------------------------

FOX = Critter("arctic fox", """
...........W...W.
..........WW..WW.
..........WWWWWW.
..........WWEWWWW
...........WWWWWN
.....WWWWWWWWWW..
....WWWWWWWWWWW..
GW..WWWWWWWWWS...
GWW.WWWWWWWWWS...
.WWWWWWWWWWWWS...
..WWWWSWW.SWW....
...SS..SS..SS....
""", {"W": "#e2ecfa", "S": "#93a7c8", "E": "#07101a", "N": "#07101a", "G": "#8ff5d2"},
    sleep_art="""
.................
.................
.................
.................
...........W.W...
..........WWWWW..
.....WWWWWWWWWWW.
...WWWWWWWWWWSWWN
..GWWWWWWWWWWWWW.
..GGWWWWWWWWWWW..
...GGGWWWWWWWW...
....SSSSSSSSS....
""", anim={"G": "g 3.1s ease-in-out infinite alternate"}, glow="#8ff5d2")

PENGUIN = Critter("penguin", """
....KKKK.....
...KKKKKK....
...KKKWEKK...
...KKKWWKKO..
..KKKWWWWK...
..KKWWWWWWK..
.KKKWWWWWWKK.
.KKKWWWWWWKK.
..KKWWWWWWK..
..KKWWWWWWK..
...KWWWWWK...
...OO...OO...
""", {"K": "#4a6488", "W": "#e8f2fb", "E": "#0a0f16", "O": "#f2a65a"},
    body_anim="w 2.4s ease-in-out infinite alternate", glow="#8cc4ee")

FISH = Critter("fish", """
.................
.......BBBB......
.....BBBBBBBB....
.T..BBBBBBBWEB...
.TTBBBBBBBBBBBB..
.TTTBBBBBBBBBBBB.
.TTBBBLLLLLLLBB..
.T..BBBLLLLLBB...
.....BBBBBBBB....
.......BBBB......
""", {"B": "#4a7bf0", "L": "#b6cbff", "T": "#2f5fe0", "W": "#dfe8ff", "E": "#06101a"},
    anim={"T": "t 1.1s ease-in-out infinite alternate"},
    extra_awake=("<circle class='bb' cx='50' cy='6' r='1.6' stroke='#b6cbff' stroke-width='.8'/>"
                 "<circle class='bb b2' cx='48' cy='8' r='1.1' stroke='#b6cbff' stroke-width='.8'/>"),
    extra_css=("@keyframes u{0%{opacity:0;transform:translateY(4px)}20%{opacity:.9}100%{opacity:0;transform:translateY(-12px)}}"
               ".bb{animation:u 2.6s ease-out infinite}.b2{animation-delay:-1.3s}"),
    glow="#4a7bf0")

JELLY = Critter("jellyfish", """
.....CCCCC.....
...CCCCCCCCC...
..CCLCCCCCLCC..
..CCCECCCECCC..
..CCCCCCCCCCC..
..C.C.C.C.C.C..
..t.t.t.t.t.t..
...t.t.t.t.t...
..t.t.t.t.t.t..
...t...t...t...
""", {"C": "#2bc4c4", "L": "#b8fff4", "t": "#1fa3b8", "E": "#03161a"}, eye_under="C",
    anim={"t": "t 1.6s ease-in-out infinite alternate", "C": "p 2.8s ease-in-out infinite alternate"},
    glow="#5ef0e0")

DUCK = Critter("duck in a rain hat", """
....HHHHH........
...HHHHHHH.......
..HHHHHHHHH......
....YYYYEY.......
....YYYYYYOO.....
....YYYYYYOO.....
.....YYYY........
..YYYYYYYYY......
.YYYYYYYYYYY.....
.YYYYYYYYYYY.....
..YYYYYYYYY......
....OO..OO.......
""", {"H": "#5b8cc4", "Y": "#f2d36b", "O": "#f0a050", "E": "#0b0f14"}, eye_under="Y",
    extra_awake="<circle class='dr' cx='4.5' cy='9' r='1.2' fill='#b9d4ee' stroke='none'/>",
    extra_css=("@keyframes d{0%,40%{opacity:0;transform:translateY(0)}50%{opacity:.9}100%{opacity:0;transform:translateY(16px)}}"
               ".dr{animation:d 3.7s ease-in infinite}"),
    glow="#86aad0")

OWL = Critter("owl", """
..B.........B..
..BB.......BB..
..BBBBBBBBBBB..
.BBWWWBBBWWWBB.
.BBWEWBOBWEWBB.
.BBWWWBOBWWWBB.
.BBBBBBBBBBBBB.
.BBLBLBLBLBLBB.
.BBBLBLBLBLBBB.
..BBBBBBBBBBB..
...BBBBBBBBB...
....YY...YY....
""", {"B": "#6f78a8", "W": "#e8f0ff", "E": "#ffd27a", "O": "#c9a46a", "L": "#9db8ff", "Y": "#c9a46a"},
    glow="#9db8ff")

ASTRONAUT = Critter("astronaut", """
....WWWWW....
...WWWWWWW...
..WWVVVVVWW..
..WWVVVVGWW..
..WWVVVVVWW..
...WWWWWWW...
..PWWWWWWWP..
.WW.WWWWW.WW.
.W..WWRWW..W.
....WWWWW....
....WW.WW....
....WW.WW....
""", {"W": "#e6e4f5", "V": "#2a2560", "G": "#b4a8ff", "P": "#7b6cf0", "R": "#f07b8a"}, eyes="G", eye_under="V",
    body_anim="f 3.4s ease-in-out infinite alternate", glow="#b4a8ff")

# keyframes the anims above refer to; each critter's SVG carries only what it uses
KEYFRAMES = {
    "g": "@keyframes g{from{opacity:.35}to{opacity:1}}",
    "w": "@keyframes w{from{transform:rotate(-4deg)}to{transform:rotate(4deg)}}",
    "t": "@keyframes t{from{transform:translateY(0)}to{transform:translateY(1.5px)}}",
    "p": "@keyframes p{from{opacity:.7}to{opacity:1}}",
    "f": "@keyframes f{from{transform:translateY(0)}to{transform:translateY(-3px)}}",
}

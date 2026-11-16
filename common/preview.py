"""Render preview screenshots and GIFs for a theme, through its real theme.css.

    python3 common/preview.py deep-sea                 # stills, GIFs and gallery
    python3 common/preview.py deep-sea --only stills
    python3 common/preview.py deep-sea --clip whale:106:12 --clip intro:2:14

Each frame is a fresh headless Chrome page: a T3-style window mockup whose chat
area carries the theme's CSS. Chrome's --virtual-time-budget fast-forwards the
SVG animation to the exact moment, so frames are deterministic. Needs Google
Chrome and ffmpeg. Set T3_PREVIEW_WORKERS to limit parallel Chrome processes (default 8).

Outputs go to <theme>/preview/:
  home.png, conversation.png            (+ -light versions if the theme has light mode)
  home.gif, conversation.gif            (+ home-light.gif)
  gallery.png                           (from gallery.svg)
  any --clip name:start:seconds         -> name.gif
"""
import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FPS = 7
WIN = (1280, 800)

PALETTES = {
    "dark": dict(page="#3a6ea5", side="#c9cbd1", act="#1a1c21", mut="#6b6f78", txt="#d6d8de", hdr="#e4e6ea",
                 bub="#1c1f27", bubb="#262a33", code="#12151b", codeb="#20232b", codet="#c8d3ff", inl="#1a1d24",
                 box="rgba(22,24,30,.92)", boxb="#262932", line="#1a1d23", border="#16181d"),
    "light": dict(page="#9cc3e6", side="#2c3442", act="#d3dce8", mut="#7a8496", txt="#1f2633", hdr="#141a24",
                  bub="#ffffff", bubb="#d3dbe6", code="#f7f9fc", codeb="#d6dee9", codet="#25407f", inl="#e1e8f2",
                  box="rgba(255,255,255,.92)", boxb="#d3dbe6", line="#d7dfe9", border="#d7dfe9"),
}

def _row(role, inner):
    # mirrors T3's markup: one [data-timeline-root] lane per timeline row
    return (f"<div data-timeline-root><div data-timeline-row-kind=message data-message-role={role}>{inner}</div></div>")


MESSAGES = "".join((
    _row("user", "<div class=row><div class=ub data-user-message-bubble>Can you add a jitter plot of the per-mouse firing rates "
                 "to Fig. 3b, matching the existing palette?</div></div>"),
    _row("assistant", """<div class="as chat-markdown"><p>Done. I added a strip plot of per-mouse means on top of the bars in <code>fig3.py</code>, using the same two-tone palette, and ran the figure checker.</p>
<div class=chat-markdown-codeblock><pre>ax.scatter(x + jitter, rates, s=9, color=PALETTE["key"],
           alpha=.8, linewidths=0, zorder=3)
pubfig.finalize_figure(fig, "fig3b.pdf")</pre></div>
<p>The checker passed with no warnings. Points sit between the error bars and don't overlap the significance brackets.</p></div>"""),
    _row("user", "<div class=row><div class=ub data-user-message-bubble>Nice, can you make the dots a bit bigger?</div></div>"),
    _row("assistant", "<div class='as chat-markdown'><p>Bumped the marker size from 9 to 14 and re-exported. Updated figure is at "
                      "<code>figures/fig3b.pdf</code>.</p></div>"),
))


def mock_html(css, theme, mode, view):
    c = dict(PALETTES[mode])
    roles = theme.get("colors", {}) if mode == "dark" else theme.get("variants", {}).get("light", {})
    c["win"] = roles.get("sidebar", "#0a0b0d" if mode == "dark" else "#e3eaf3")
    # use the theme's own color roles where the mockup has a matching surface
    for key, role in (("code", "codeBackground"), ("bub", "messageSurface"), ("act", "sidebarRowSelected"),
                      ("inl", "muted"), ("boxb", "border"), ("codeb", "border")):
        if role in roles:
            c[key] = roles[role]
    if "surfaceOverlay" in roles:
        c["box"] = roles["surfaceOverlay"] + "eb"
    conv = view == "conversation"
    # mirrors T3's editor markup so the typing companion lands where it would in the app:
    # the conversation view has a focused draft (critter awake), the home view an empty one (asleep)
    draft = "<p>Make the dots a bit bigger</p>" if view == "conversation" else "<p><br></p>"
    ph = "" if view == "conversation" else "<div class=ph>Ask anything, / for commands, @ for context</div>"
    composer = ("<form data-chat-composer-form><div class=box data-slot=composer-host><div class=ed><div>"
                f"<div class=composer-tiptap contenteditable {'autofocus' if view == 'conversation' else ''}>{draft}</div></div>{ph}</div>"
                "<button type=button class='send bg-message-action'>&#8593;</button></div></form>")
    body = (f"<div class=hdr data-chat-header>Fig 3b jitter plot</div><div class=feed>{MESSAGES}</div><div class='comp bot'>{composer}</div>" if conv else
            f"<div class=comp>{composer}<div class=bar><span>Full access</span><span>project</span><span>main</span><b>Opus 5.5</b></div></div>")
    threads = ('<div data-thread-item><div class="th a" aria-current=page>Fig 3b jitter plot</div></div><div class=th>Theme ideas</div>' if conv
               else '<div class=th>Theme ideas</div><div class=th>Fig 3b jitter plot</div>')
    return f"""<!doctype html><html class="{'dark' if mode == 'dark' else ''}"><head><meta charset=utf-8><style>
*{{box-sizing:border-box}}body{{margin:0;background:{c['page']};font:13px -apple-system,BlinkMacSystemFont,sans-serif;color:{c['txt']}}}
.win{{position:absolute;inset:14px;border-radius:12px;overflow:hidden;background:{c['win']};display:flex;box-shadow:0 10px 40px rgba(0,0,0,.35);transform:translateZ(0)}}
.side{{width:220px;padding:12px 8px;display:flex;flex-direction:column;gap:2px;color:{c['side']}}}
.dots span{{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:6px}}
.it{{padding:7px 10px;border-radius:7px}} .it.a,.th.a{{background:{c['act']}}} .lbl{{color:{c['mut']};font-size:11px;padding:16px 10px 6px}} .th{{padding:7px 10px;border-radius:7px}}
[data-workspace-area]{{position:relative;flex:1;margin:40px 8px 8px 0;border-radius:10px;overflow:hidden;border:1px solid {c['border']}}}
.hdr{{height:44px;border-bottom:1px solid {c['line']};padding:13px 18px;color:{c['hdr']};font-weight:500}}
.feed{{max-width:680px;margin:0 auto;padding:22px 20px;font-size:14px;line-height:1.6}}
.row{{display:flex;justify-content:flex-end;margin:6px 0 18px}} .ub{{background:{c['bub']};border:1px solid {c['bubb']};border-radius:14px;padding:9px 14px;max-width:75%;color:{c['hdr']}}}
.as{{margin-bottom:4px}} [data-timeline-root]{{margin-bottom:10px}} .as p{{margin:0 0 10px}} .chat-markdown-codeblock{{margin:0 0 10px;border-radius:10px}} code{{font:12.5px ui-monospace,Menlo,monospace;background:{c['inl']};padding:1px 5px;border-radius:5px;color:{c['codet']}}}
pre{{font:12.5px/1.5 ui-monospace,Menlo,monospace;background:{c['code']};border:1px solid {c['codeb']};border-radius:10px;padding:12px 14px;margin:0;color:{c['codet']}}}
.comp{{position:absolute;left:50%;top:44%;transform:translateX(-50%);width:520px}} .comp.bot{{top:auto;bottom:18px;width:640px}}
.send{{position:absolute;right:10px;bottom:8px;width:26px;height:26px;border-radius:50%;border:0;background:{c['mut']};color:#fff;font-size:14px}}
.ed{{position:relative}} .ph{{position:absolute;inset:0;pointer-events:none}} .composer-tiptap{{position:relative;outline:none;color:{c['hdr']};caret-color:transparent}} .composer-tiptap p{{margin:0}}
.box{{position:relative;background:{c['box']};border:1px solid {c['boxb']};border-radius:12px;padding:12px 14px 36px;color:{c['mut']}}}
.bar{{margin:0 10px;background:{c['box']};border:1px solid {c['boxb']};border-top:0;border-radius:0 0 10px 10px;padding:7px 12px;color:{c['mut']};font-size:12px;display:flex;gap:16px}} .bar b{{margin-left:auto;font-weight:500}}
{css}</style></head><body><div class=win data-slot=sidebar-wrapper>
<div class=side data-slot=sidebar-inner><div class=dots style="padding:2px 6px 14px"><span style=background:#ff5f57></span><span style=background:#febc2e></span><span style=background:#28c840></span></div>
<div class="it{'' if conv else ' a'}">New thread</div><div class=it>Pull requests</div><div class=it>Usage</div><div class=lbl>Threads</div>{threads}</div>
<div data-workspace-area=conversation>{body}</div></div></body></html>"""


class Renderer:
    def __init__(self, workers=None):
        workers = workers or int(os.environ.get("T3_PREVIEW_WORKERS", "8"))
        self.tmp = tempfile.mkdtemp(prefix="t3preview-")
        self.profiles = queue.Queue()
        for i in range(workers):
            self.profiles.put(os.path.join(self.tmp, f"profile{i}"))
        self.workers = workers

    def shot(self, html_path, out_png, t, size=WIN):
        for _ in range(3):
            prof = self.profiles.get()
            try:
                subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={prof}",
                                f"--window-size={size[0]},{size[1]}", f"--virtual-time-budget={int(t * 1000)}",
                                f"--screenshot={out_png}", "file://" + html_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            except subprocess.TimeoutExpired:
                pass
            finally:
                self.profiles.put(prof)
            if os.path.exists(out_png) and os.path.getsize(out_png) > 0:
                return
        raise RuntimeError(f"Chrome failed to render {out_png}")

    def clip(self, html_path, out_gif, start, seconds, width=720):
        frames = os.path.join(self.tmp, os.path.basename(out_gif) + "-frames")
        os.makedirs(frames, exist_ok=True)
        n = int(seconds * FPS)
        with ThreadPoolExecutor(self.workers) as ex:
            list(ex.map(lambda i: self.shot(html_path, os.path.join(frames, f"f{i:04d}.png"), start + i / FPS), range(n)))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(frames, "f%04d.png"),
                        "-vf", f"scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=none",
                        out_gif], check=True)
        shutil.rmtree(frames)

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("theme_dir")
    ap.add_argument("--only", choices=["stills", "gifs", "gallery"], action="append")
    ap.add_argument("--still", type=float, help="time (s) for the stills; default: middle of the first pass")
    ap.add_argument("--clip", action="append", default=[], help="name:start:seconds, home view, dark mode")
    args = ap.parse_args()

    tdir = os.path.abspath(args.theme_dir)
    pdir = os.path.join(tdir, "preview")
    css = open(os.path.join(tdir, "theme.css")).read()
    theme = json.load(open(os.path.join(tdir, "theme.json")))
    tl = json.load(open(os.path.join(pdir, "timeline.json")))
    sched = tl["schedule"]
    modes = ["dark", "light"] if tl.get("has_light") else ["dark"]
    want = set(args.only or ["stills", "gifs", "gallery"])

    r = Renderer()
    try:
        pages = {}
        for mode in modes:
            for view in ("home", "conversation"):
                p = os.path.join(r.tmp, f"{mode}-{view}.html")
                with open(p, "w") as fh:
                    fh.write(mock_html(css, theme, mode, view))
                pages[mode, view] = p

        first = sched[0] if sched else {"start": 0, "end": 12}
        t_still = args.still if args.still is not None else (first["start"] + first["end"]) / 2
        jobs = []
        if "stills" in want:
            for mode in modes:
                sfx = "" if mode == "dark" else "-light"
                for view in ("home", "conversation"):
                    jobs.append(("shot", pages[mode, view], os.path.join(pdir, f"{view}{sfx}.png"), t_still))
        if "gifs" in want:
            # home: the first actor leaving as the second arrives
            hand = sched[1]["start"] if len(sched) > 1 else first["start"] + 6
            jobs.append(("clip", pages["dark", "home"], os.path.join(pdir, "home.gif"), max(0, hand - 8), 15))
            jobs.append(("clip", pages["dark", "conversation"], os.path.join(pdir, "conversation.gif"), max(0, t_still - 7), 14))
            if "light" in modes:
                jobs.append(("clip", pages["light", "home"], os.path.join(pdir, "home-light.gif"), max(0, t_still - 7), 14))
        for spec in args.clip:
            name, start, secs = spec.split(":")
            jobs.append(("clip", pages["dark", "home"], os.path.join(pdir, f"{name}.gif"), float(start), float(secs)))

        for kind, page, out, *rest in jobs:
            if kind == "shot":
                r.shot(page, out, rest[0])
            else:
                r.clip(page, out, rest[0], rest[1])
            print("wrote", os.path.relpath(out, tdir))

        gsvg = os.path.join(pdir, "gallery.svg")
        if "gallery" in want and os.path.exists(gsvg):
            import re
            vb = re.search(r"viewBox='0 0 (\d+) (\d+)'", open(gsvg).read())
            w, h = int(vb.group(1)), int(vb.group(2))
            tmp_png = os.path.join(r.tmp, "gallery.png")
            r.shot(gsvg, tmp_png, 1.3, size=(w, h))
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp_png, "-vf", "scale=1200:-1",
                            os.path.join(pdir, "gallery.png")], check=True)
            print("wrote preview/gallery.png")
    finally:
        r.close()


if __name__ == "__main__":
    sys.exit(main())

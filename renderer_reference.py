"""Render "Things You Wouldn't Google" slideshow #1 at TikTok size (1080x1920).

Every text block is kept inside TikTok's safe zone (clear of the top tabs,
right-side action buttons and bottom caption/music bar), auto-shrinks if it
would overflow, and is checked for overlaps before the PNG is saved.
"""
import base64, json, pathlib, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
W, H = 1080, 1920
# TikTok UI-safe zone (px at 1080x1920)
SAFE = dict(top=260, bottom=H - 500, left=84, right=W - 168)

SLIDES = [
    dict(kind="title", bg="title", kicker="be honest…",
         title="5 things you'd never Google", emoji="🫣"),
    dict(kind="q", bg="q1", n=1,
         q="Is it normal that one boob is bigger than the other?",
         a="Completely. Most people's breasts are a little uneven, and for some it's a full cup size or more. Hormones, weight changes and getting older all play a part. Bodies are siblings, not twins. The one thing to watch for is a sudden change in size, shape or feel. That's worth getting checked."),
    dict(kind="q", bg="q2", n=2,
         q="Why do I have to poop right after coffee?",
         a="Coffee sets off something called the gastrocolic reflex, basically a wake-up call for your colon. It can kick in within minutes, and even decaf can do it, so it's not only the caffeine. Mornings are already when your gut is most active, so the timing stacks up. You're not weird, you're just efficient."),
    dict(kind="q", bg="q3", n=3,
         q="Is it normal to still miss my ex a year later?",
         a="Yes, and it's way more common than people admit. Your brain spent months or years wiring that person into your routines, your songs and your inside jokes, and that doesn't unwire on a schedule. Missing someone doesn't mean you should go back. It means they mattered. Both can be true."),
    dict(kind="q", bg="q4", n=4,
         q="Why do I always wake up at 3am?",
         a="Usually stress. Your body's alert hormones naturally start rising in the early hours, and sleep gets lighter in the second half of the night. A busy mind catches that wave and suddenly you're wide awake. A dark, cool room and not checking the clock really help. If it happens most nights, it's worth mentioning to a doctor."),
    dict(kind="q", bg="q5", n=5,
         q="Can you get pregnant on your period?",
         a="Yes. It's less likely, but it can happen, especially if you have a short cycle. Sperm can survive up to five days, so sex near the end of your period can line up with an early ovulation. Some bleeding that looks like a period isn't one, either. If you're not trying for a baby, use protection all month."),
    dict(kind="end", bg="end", title="Which one did you secretly need?", emoji="👀",
         sub="comment the number. no one's judging"),
]

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#1a1410}
body{font-family:'Inter',sans-serif;color:#fff;-webkit-font-smoothing:antialiased;
  font-feature-settings:'ss01','cv11'}
.bg{position:absolute;inset:0;background-size:cover;background-position:center;
  filter:saturate(.82) contrast(.96) brightness(.92)}
.tint{position:absolute;inset:0;
  background:
    radial-gradient(120% 75% at 50% 45%, rgba(40,24,12,.10) 0%, rgba(20,12,6,.62) 100%),
    linear-gradient(180deg, rgba(36,22,12,.38) 0%, rgba(30,18,10,.30) 45%, rgba(18,11,6,.58) 100%)}
.warm{position:absolute;inset:0;background:#ff9a4a;mix-blend-mode:soft-light;opacity:.16}
.grain{position:absolute;inset:-50%;opacity:.13;mix-blend-mode:overlay}
.stage{position:absolute;left:SAFE_Lpx;top:SAFE_Tpx;width:SAFE_Wpx;height:SAFE_Hpx;
  display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:GAPpx}
.t{text-shadow:0 2px 18px rgba(0,0,0,.45),0 1px 3px rgba(0,0,0,.35);overflow-wrap:break-word}
.emoji{font-family:'Noto Color Emoji';text-shadow:none}
.kicker{font-weight:600;font-size:46px;letter-spacing:.01em;opacity:.92;font-style:italic}
.title{font-weight:900;letter-spacing:-.025em;line-height:1.02}
.chip{display:inline-flex;align-items:center;gap:12px;font-weight:700;font-size:34px;
  padding:12px 26px;border-radius:999px;background:rgba(255,246,236,.92);color:#2a1a10;
  text-shadow:none;box-shadow:0 6px 24px rgba(0,0,0,.18)}
.q{font-weight:800;letter-spacing:-.02em;line-height:1.1}
.card{width:100%}
.a{font-weight:600;line-height:1.36;color:#fff8f0;letter-spacing:-.003em;
  text-shadow:0 0 2px rgba(0,0,0,.55),0 2px 6px rgba(0,0,0,.55),0 4px 28px rgba(0,0,0,.6)}
.sub{font-weight:500;font-size:44px;opacity:.9}
"""

GRAIN = ("<svg class='grain' xmlns='http://www.w3.org/2000/svg' width='2160' height='3840'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/>"
         "<feColorMatrix type='saturate' values='0'/></filter><rect width='100%' height='100%' filter='url(#n)'/></svg>")


def body_for(s):
    if s["kind"] == "title":
        return (f"<div class='t kicker' data-fit>{s['kicker']}</div>"
                f"<div class='t title' data-fit data-size='132'>{s['title']} <span class='emoji'>{s['emoji']}</span></div>")
    if s["kind"] == "end":
        return (f"<div class='t title' data-fit data-size='112'>{s['title']} <span class='emoji'>{s['emoji']}</span></div>"
                f"<div class='t sub' data-fit>{s['sub']}</div>")
    return (f"<div class='t chip' data-fit>{s['n']} of 5</div>"
            f"<div class='t q' data-fit data-size='72'>{s['q']}</div>"
            f"<div class='card' data-fit><div class='a' data-size='44'>{s['a']}</div></div>")


def html_for(s):
    img = base64.b64encode((ROOT / "bg" / f"{s['bg']}.jpg").read_bytes()).decode()
    css = (CSS.replace("SAFE_L", str(SAFE["left"])).replace("SAFE_T", str(SAFE["top"]))
              .replace("SAFE_W", str(SAFE["right"] - SAFE["left"]))
              .replace("SAFE_H", str(SAFE["bottom"] - SAFE["top"]))
              .replace("GAP", "44" if s["kind"] == "q" else "36"))
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>"
            f"<div class='bg' style=\"background-image:url('data:image/jpeg;base64,{img}')\"></div>"
            f"<div class='warm'></div><div class='tint'></div>{GRAIN}"
            f"<div class='stage'>{body_for(s)}</div></body></html>")


# Sets font sizes, shrinks until the stack fits, then reports geometry.
FIT_JS = """(safe) => {
  const stage = document.querySelector('.stage');
  const sized = [...document.querySelectorAll('[data-size]')];
  sized.forEach(e => e.style.fontSize = e.dataset.size + 'px');
  let scale = 1;
  const tooTall = () => [...stage.children].reduce((h,c)=>h+c.getBoundingClientRect().height,0)
                        + parseFloat(getComputedStyle(stage).gap)*(stage.children.length-1) > stage.clientHeight;
  while (tooTall() && scale > 0.6) {
    scale -= 0.02;
    sized.forEach(e => e.style.fontSize = (e.dataset.size*scale) + 'px');
  }
  const boxes = [...document.querySelectorAll('[data-fit]')].map(e => {
    const r = e.getBoundingClientRect();
    return {cls: e.className, x0:r.left, y0:r.top, x1:r.right, y1:r.bottom,
            overflowX: e.scrollWidth > e.clientWidth + 1};
  });
  return {scale, boxes};
}"""


def check(name, geo):
    problems = []
    b = geo["boxes"]
    for box in b:
        if (box["x0"] < SAFE["left"] - 0.5 or box["x1"] > SAFE["right"] + 0.5 or
                box["y0"] < SAFE["top"] - 0.5 or box["y1"] > SAFE["bottom"] + 0.5):
            problems.append(f"{box['cls']} outside safe zone {box}")
        if box["overflowX"]:
            problems.append(f"{box['cls']} overflows horizontally")
    for i in range(len(b)):
        for j in range(i + 1, len(b)):
            p, q = b[i], b[j]
            if p["x0"] < q["x1"] and q["x0"] < p["x1"] and p["y0"] < q["y1"] and q["y0"] < p["y1"]:
                problems.append(f"overlap: {p['cls']} / {q['cls']}")
    return problems


def main():
    report, failed = [], False
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        page = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for i, s in enumerate(SLIDES, 1):
            page.set_content(html_for(s), wait_until="load")
            page.evaluate("document.fonts.ready")
            geo = page.evaluate(FIT_JS, SAFE)
            probs = check(i, geo)
            failed |= bool(probs)
            out = OUT / f"slide_{i:02d}.png"
            page.screenshot(path=str(out), full_page=False)
            report.append({"slide": i, "scale": round(geo["scale"], 2), "problems": probs})
        br.close()
    print(json.dumps(report, indent=1))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

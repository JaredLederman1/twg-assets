"""Render "Things You Wouldn't Google" slideshows to TikTok-size JPGs (1080x1920).

Usage: python3 pipeline/render.py SPEC.json OUT_DIR
SPEC.json: {"slides": [ {kind:title|q|end, bg:"backgrounds/x.jpg", ...}, ... ]}
  title: kicker, title, emoji        q: n, q, a        end: title, emoji, sub
Text stays inside TikTok's UI safe zone, auto-shrinks to fit, and every slide is
checked for overlap/overflow. Exits 1 (and writes nothing for that slide) on any problem.
"""
import base64, io, json, pathlib, sys
from PIL import Image
from playwright.sync_api import sync_playwright

W, H = 1080, 1920
SAFE = dict(top=260, bottom=H - 500, left=84, right=W - 168)
REPO = pathlib.Path(__file__).resolve().parent.parent

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#1a1410}
body{font-family:'Inter',sans-serif;color:#fff;-webkit-font-smoothing:antialiased;font-feature-settings:'ss01','cv11'}
.bg{position:absolute;inset:0;background-size:cover;background-position:center;filter:saturate(.82) contrast(.96) brightness(.92)}
.tint{position:absolute;inset:0;background:
 radial-gradient(120% 75% at 50% 45%, rgba(40,24,12,.10) 0%, rgba(20,12,6,.62) 100%),
 linear-gradient(180deg, rgba(36,22,12,.38) 0%, rgba(30,18,10,.30) 45%, rgba(18,11,6,.58) 100%)}
.warm{position:absolute;inset:0;background:#ff9a4a;mix-blend-mode:soft-light;opacity:.16}
.grain{position:absolute;inset:-50%;opacity:.13;mix-blend-mode:overlay}
.stage{position:absolute;left:SAFE_Lpx;top:SAFE_Tpx;width:SAFE_Wpx;height:SAFE_Hpx;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:GAPpx}
.t{text-shadow:0 2px 18px rgba(0,0,0,.45),0 1px 3px rgba(0,0,0,.35);overflow-wrap:break-word}
.emoji{font-family:'Noto Color Emoji';text-shadow:none}
.kicker{font-weight:600;font-size:46px;letter-spacing:.01em;opacity:.92;font-style:italic}
.title{font-weight:900;letter-spacing:-.025em;line-height:1.02}
.chip{display:inline-flex;align-items:center;gap:12px;font-weight:700;font-size:34px;padding:12px 26px;border-radius:999px;background:rgba(255,246,236,.92);color:#2a1a10;text-shadow:none;box-shadow:0 6px 24px rgba(0,0,0,.18)}
.q{font-weight:800;letter-spacing:-.02em;line-height:1.1}
.card{width:100%}
.a{font-weight:600;line-height:1.36;color:#fff8f0;letter-spacing:-.003em;text-shadow:0 0 2px rgba(0,0,0,.55),0 2px 6px rgba(0,0,0,.55),0 4px 28px rgba(0,0,0,.6)}
.sub{font-weight:500;font-size:44px;opacity:.9}
"""
GRAIN = ("<svg class='grain' xmlns='http://www.w3.org/2000/svg' width='2160' height='3840'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/>"
         "<feColorMatrix type='saturate' values='0'/></filter><rect width='100%' height='100%' filter='url(#n)'/></svg>")


def esc(x):
    return x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bg_b64(path):
    p = pathlib.Path(path)
    if not p.is_absolute():
        p = REPO / p
    im = Image.open(p).convert("RGB")
    # cover-crop to 9:16 and upscale to 1080x1920
    r = W / H
    w, h = im.size
    if w / h > r:
        nw = int(h * r); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / r); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    im = im.resize((W, H), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=92)
    return base64.b64encode(buf.getvalue()).decode()


def body_for(s, total):
    if s["kind"] == "title":
        return (f"<div class='t kicker' data-fit>{esc(s.get('kicker',''))}</div>"
                f"<div class='t title' data-fit data-size='132'>{esc(s['title'])} <span class='emoji'>{s.get('emoji','')}</span></div>")
    if s["kind"] == "end":
        return (f"<div class='t title' data-fit data-size='112'>{esc(s['title'])} <span class='emoji'>{s.get('emoji','')}</span></div>"
                f"<div class='t sub' data-fit>{esc(s.get('sub',''))}</div>")
    return (f"<div class='t chip' data-fit>{s['n']} of {total}</div>"
            f"<div class='t q' data-fit data-size='72'>{esc(s['q'])}</div>"
            f"<div class='card' data-fit><div class='a' data-size='44'>{esc(s['a'])}</div></div>")


def html_for(s, total):
    css = (CSS.replace("SAFE_L", str(SAFE["left"])).replace("SAFE_T", str(SAFE["top"]))
              .replace("SAFE_W", str(SAFE["right"] - SAFE["left"])).replace("SAFE_H", str(SAFE["bottom"] - SAFE["top"]))
              .replace("GAP", "44" if s["kind"] == "q" else "36"))
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>"
            f"<div class='bg' style=\"background-image:url('data:image/jpeg;base64,{bg_b64(s['bg'])}')\"></div>"
            f"<div class='warm'></div><div class='tint'></div>{GRAIN}<div class='stage'>{body_for(s, total)}</div></body></html>")


FIT_JS = """() => {
  const stage = document.querySelector('.stage');
  const sized = [...document.querySelectorAll('[data-size]')];
  sized.forEach(e => e.style.fontSize = e.dataset.size + 'px');
  let scale = 1;
  const tooTall = () => [...stage.children].reduce((h,c)=>h+c.getBoundingClientRect().height,0)
     + parseFloat(getComputedStyle(stage).gap)*(stage.children.length-1) > stage.clientHeight;
  while (tooTall() && scale > 0.6) { scale -= 0.02; sized.forEach(e => e.style.fontSize = (e.dataset.size*scale)+'px'); }
  const boxes = [...document.querySelectorAll('[data-fit]')].map(e => { const r = e.getBoundingClientRect();
    return {cls:e.className, x0:r.left, y0:r.top, x1:r.right, y1:r.bottom, overflowX: e.scrollWidth > e.clientWidth + 1}; });
  return {scale, boxes};
}"""


def check(geo):
    probs, b = [], geo["boxes"]
    for x in b:
        if x["x0"] < SAFE["left"]-.5 or x["x1"] > SAFE["right"]+.5 or x["y0"] < SAFE["top"]-.5 or x["y1"] > SAFE["bottom"]+.5:
            probs.append(f"{x['cls']} outside safe zone")
        if x["overflowX"]:
            probs.append(f"{x['cls']} overflows")
    for i in range(len(b)):
        for j in range(i+1, len(b)):
            p, q = b[i], b[j]
            if p["x0"] < q["x1"] and q["x0"] < p["x1"] and p["y0"] < q["y1"] and q["y0"] < p["y1"]:
                probs.append(f"overlap {p['cls']}/{q['cls']}")
    return probs


def render(spec, out_dir, page):
    slides = spec["slides"]
    total = sum(1 for s in slides if s["kind"] == "q")
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    report, ok = [], True
    for i, s in enumerate(slides, 1):
        page.set_content(html_for(s, total), wait_until="load")
        page.evaluate("document.fonts.ready")
        geo = page.evaluate(FIT_JS)
        probs = check(geo)
        if probs:
            ok = False
        else:
            png = page.screenshot()
            Image.open(io.BytesIO(png)).convert("RGB").save(out / f"slide_{i:02d}.jpg", quality=92, optimize=True)
        report.append({"slide": i, "scale": round(geo["scale"], 2), "problems": probs})
    return ok, report


def main(spec_path, out_dir):
    spec = json.loads(pathlib.Path(spec_path).read_text())
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        page = br.new_page(viewport={"width": W, "height": H})
        ok, report = render(spec, out_dir, page)
        br.close()
    print(json.dumps(report))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

"""Pinterest pin images (1000x1500), one per published post, from the post title and reel points.
Run: python3 _tools/make_pins.py   -> media/pinterest/<slug>.jpg"""
import json, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
import make_reel as mr
W, H = 1000, 1500
GOLD, BROWN, DARK, CREAM, BRIGHT = mr.GOLD, mr.BROWN, mr.DARK, mr.CREAM, mr.BRIGHT
MUTED = (205, 196, 180)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'media', 'pinterest')
os.makedirs(OUT, exist_ok=True)

def bg():
    im = Image.new('RGB', (W, H), DARK)
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(round(BROWN[i] + (DARK[i] - BROWN[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    glow = Image.new('RGB', (W, H), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((W - 520, -260, W + 260, 520), fill=(70, 50, 14))
    g.ellipse((-300, H - 420, 300, H + 180), fill=(46, 32, 10))
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    from PIL import ImageChops
    return ImageChops.add(im, glow)

def rtl(d, xy, text, f, fill, anchor='ra'):
    d.text(xy, text, font=f, fill=fill, anchor=anchor, direction='rtl', language='ar')

def make(post):
    reel = post['reel']
    title = post['title']
    head, _, tail = title.partition(':')
    head, tail = head.strip(), tail.strip()
    if not tail:
        head, tail = title, ''
    pts = reel['points'][:5]
    im = bg(); d = ImageDraw.Draw(im)
    R = W - 80   # right edge
    y = 90
    # tag pill
    f = mr.font(34, 700); tw = mr.width(reel['tag'], f)
    d.rounded_rectangle((R - tw - 56, y, R, y + 66), radius=33, outline=GOLD, width=2)
    rtl(d, (R - 28, y + 33), reel['tag'], f, GOLD, 'rm')
    y += 66 + 46
    # head
    size = 84
    while True:
        f = mr.font(size, 900); lines = mr.wrap(head, f, W - 160)
        if len(lines) == 1 or size <= 68: break
        size -= 2
    if len(lines) > 2:
        while len(lines) > 2 and size > 56:
            size -= 2; f = mr.font(size, 900); lines = mr.wrap(head, f, W - 160)
    elif len(lines) == 2:
        size = 80; f = mr.font(size, 900); lines = mr.wrap(head, f, W - 160)
        while len(lines) > 2: size -= 2; f = mr.font(size, 900); lines = mr.wrap(head, f, W - 160)
    for ln in lines:
        rtl(d, (R, y), ln, f, CREAM); y += int(size * 1.42)
    if tail:
        size2 = 52
        while True:
            f2 = mr.font(size2, 800); l2 = mr.wrap(tail, f2, W - 160)
            if len(l2) <= 2 or size2 <= 40: break
            size2 -= 3
        y += 4
        for ln in l2:
            rtl(d, (R, y), ln, f2, BRIGHT); y += int(size2 * 1.5)
    y += 26
    d.rounded_rectangle((R - 150, y, R, y + 6), radius=3, fill=GOLD)
    y += 50
    # points
    foot_top = H - 190
    avail = foot_top - y
    n = len(pts)
    step = min(190, avail // n)
    ft = mr.font(44 if step >= 165 else 40, 800); fs = mr.font(31 if step >= 165 else 28, 500)
    for i, p in enumerate(pts):
        cy = y + i * step
        d.ellipse((R - 68, cy + 4, R, cy + 72), fill=GOLD)
        d.text((R - 34, cy + 36), str(i + 1), font=mr.font(40, 900), fill=BROWN, anchor='mm')
        tx = R - 96
        t = p['title']; fT = ft; sz = ft.size
        while mr.width(t, fT) > W - 80 - 96 - 80 and sz > 30:
            sz -= 2; fT = mr.font(sz, 800)
        rtl(d, (tx, cy - 6), t, fT, CREAM)
        s = p.get('sub', ''); fS = fs; sz = fs.size
        while s and mr.width(s, fS) > W - 80 - 96 - 80 and sz > 22:
            sz -= 1; fS = mr.font(sz, 500)
        if s: rtl(d, (tx, cy + 58), s, fS, MUTED)
    # footer
    d.line((80, foot_top, W - 80, foot_top), fill=(120, 96, 50), width=2)
    rtl(d, (R, foot_top + 34), 'المقال كامل على', mr.font(32, 600), MUTED)
    d.text((R, foot_top + 86), 'kzamstudio.com', font=mr.font(50, 800), fill=BRIGHT, anchor='ra')
    d.text((80, foot_top + 60), 'Kzam Studio', font=mr.font(40, 700), fill=CREAM, anchor='la')
    d.text((80, foot_top + 112), 'كزام', font=mr.font(30, 600), fill=GOLD, anchor='la', direction='rtl', language='ar')
    path = os.path.join(OUT, post['slug'] + '.jpg')
    im.save(path, quality=90)
    return path

for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_content', 'posts', '*.json'))):
    p = json.load(open(f)); print(make(p), len(p['reel']['points']))

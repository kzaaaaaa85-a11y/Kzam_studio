#!/usr/bin/env python3
"""Render a 9:16 text reel (1080x1920, 30fps) from a small spec.

    python3 _tools/make_reel.py spec.json out.mp4 cover.jpg

spec.json:
{
  "tag":    "للمطاعم",                       short label above the hook (optional)
  "hook":   ["سطر أول", "سطر ثاني"],          1-3 short lines, last one is gold
  "points": [{"title": "...", "sub": "..."}], 3-5 points, sub is optional
  "cta":    ["سطر", "سطر"],                   1-2 lines on the end card
  "url":    "kzamstudio.com",                 optional, shown in a gold pill
  "theme":  "coffee"                          optional: coffee (brown), teal, night
}

The hook is on screen from the first frame. Needs Pillow (with raqm) and ffmpeg.
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, 'fonts', 'Cairo.ttf')
GOLD, BROWN, DARK, CREAM = (212, 175, 55), (62, 39, 35), (30, 17, 14), (245, 241, 232)
BRIGHT = (240, 196, 72)
# background gradient (top, bottom) per theme; gold and cream text stay the same on all three
THEMES = {
    'coffee': ((62, 39, 35), (30, 17, 14)),     # cafe days
    'teal': ((13, 66, 68), (5, 26, 30)),        # restaurant days
    'night': ((40, 44, 72), (12, 14, 26)),      # landing page days
}
SAFE_W = 900                       # text never goes wider than this

T_HOOK, T_POINT, T_END, T_FADE = 2.6, 2.3, 2.8, 0.32


def font(size, weight):
    f = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_axes([weight, 0])
    return f


def width(text, f):
    return f.getlength(text, direction='rtl', language='ar')


def wrap(text, f, max_w):
    lines, cur = [], ''
    for word in text.split():
        trial = (cur + ' ' + word).strip()
        if cur and width(trial, f) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def fit(text, weight, max_w, size, max_lines, min_size=44):
    """Largest size at which text wraps into max_lines within max_w."""
    while size > min_size:
        f = font(size, weight)
        lines = wrap(text, f, max_w)
        if len(lines) <= max_lines and all(width(l, f) <= max_w for l in lines):
            return f, lines
        size -= 3
    f = font(min_size, weight)
    return f, wrap(text, f, max_w)


def draw_text(d, xy, text, f, fill, shadow=True):
    if shadow:
        d.text((xy[0], xy[1] + 4), text, font=f, fill=(0, 0, 0, 120), anchor='mm',
               direction='rtl', language='ar')
    d.text(xy, text, font=f, fill=fill + (255,), anchor='mm', direction='rtl', language='ar')


def layer():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def background():
    g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top, bot = np.array(BROWN, np.float32), np.array(DARK, np.float32)
    arr = np.broadcast_to(top * (1 - g) + bot * g, (H, W, 3)).astype(np.uint8)
    return Image.fromarray(arr, 'RGB')


def glow(radius, alpha):
    size = radius * 2
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    r = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    a = np.clip(1 - r, 0, 1) ** 2 * alpha * 255
    arr = np.zeros((size, size, 4), np.uint8)
    arr[..., :3] = GOLD
    arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


def hook_layer(spec):
    im, d = layer()
    lines = [l for l in spec['hook'] if l.strip()][:3]
    y = 700 if len(lines) > 2 else 790
    if spec.get('tag'):
        f = font(46, 700)
        tw = width(spec['tag'], f) + 70
        d.rounded_rectangle([W / 2 - tw / 2, y - 190, W / 2 + tw / 2, y - 110], 40,
                            outline=GOLD + (255,), width=3)
        draw_text(d, (W / 2, y - 151), spec['tag'], f, GOLD, shadow=False)
    sizes = []
    for i, line in enumerate(lines):
        f, wrapped = fit(line, 900, SAFE_W, 128, 1, 70)
        sizes.append((f, wrapped[0]))
    underline = None
    for i, (f, text) in enumerate(sizes):
        last = i == len(sizes) - 1
        draw_text(d, (W / 2, y), text, f, BRIGHT if last else CREAM)
        if last:
            underline = (y + f.size * 0.78, width(text, f))
        y += int(f.size * 1.42)
    return im, underline


def point_layer(i, point):
    im, d = layer()
    cy = 690
    d.ellipse([W / 2 - 92, cy - 92, W / 2 + 92, cy + 92], fill=GOLD + (255,))
    d.text((W / 2, cy - 6), str(i + 1), font=font(120, 900), fill=BROWN + (255,), anchor='mm')
    f, lines = fit(point['title'], 900, SAFE_W, 104, 3, 60)
    y = 940
    for line in lines:
        draw_text(d, (W / 2, y), line, f, CREAM)
        y += int(f.size * 1.4)
    if point.get('sub'):
        y += 30
        f2, lines2 = fit(point['sub'], 600, SAFE_W - 60, 58, 3, 40)
        for line in lines2:
            draw_text(d, (W / 2, y), line, f2, BRIGHT, shadow=False)
            y += int(f2.size * 1.55)
    return im


def end_layer(spec):
    im, d = layer()
    y = 790
    for i, line in enumerate(spec.get('cta', [])[:2]):
        f, wrapped = fit(line, 900 if i == 0 else 700, SAFE_W, 96 if i == 0 else 64, 2, 44)
        for w_line in wrapped:
            draw_text(d, (W / 2, y), w_line, f, CREAM if i == 0 else BRIGHT)
            y += int(f.size * 1.45)
        y += 20
    url = spec.get('url', 'kzamstudio.com')
    if url:
        f = font(60, 800)
        tw = f.getlength(url) + 110
        y += 70
        d.rounded_rectangle([W / 2 - tw / 2, y - 62, W / 2 + tw / 2, y + 62], 62,
                            fill=GOLD + (255,))
        d.text((W / 2, y - 4), url, font=f, fill=BROWN + (255,), anchor='mm')
        y += 150
    d.text((W / 2, y), 'Kzam Studio', font=font(50, 700), fill=CREAM + (255,), anchor='mm')
    return im


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def place(frame, lay, alpha, dy):
    """Composite a full-size RGBA layer with extra opacity and a vertical offset."""
    if alpha <= 0.003:
        return
    if alpha < 0.997:
        a = lay.getchannel('A').point(lambda v: int(v * alpha))
        lay = lay.copy()
        lay.putalpha(a)
    if dy:
        shifted = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        shifted.paste(lay, (0, int(dy)))
        lay = shifted
    frame.alpha_composite(lay)


def render(spec, out_mp4, out_jpg):
    if not features.check('raqm'):
        sys.exit('Pillow has no raqm support: Arabic would render unshaped.')
    global BROWN, DARK
    BROWN, DARK = THEMES.get(spec.get('theme') or 'coffee', THEMES['coffee'])
    points = spec['points']
    if not 3 <= len(points) <= 5:
        sys.exit('points must have 3 to 5 items')
    hook, underline = hook_layer(spec)
    scenes = [(hook, T_HOOK)] + [(point_layer(i, p), T_POINT) for i, p in enumerate(points)]
    scenes.append((end_layer(spec), T_END))
    starts, t = [], 0.0
    for _, dur in scenes:
        starts.append(t)
        t += dur
    total = t
    bg = background()
    g1, g2 = glow(620, 0.20), glow(460, 0.14)
    n_seg = len(scenes)

    def frame_at(ts):
        fr = bg.convert('RGBA')
        a = ts / total * 2 * math.pi
        fr.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 0)))
        fr.paste(g1, (int(520 + 160 * math.cos(a)) - 620, int(360 + 120 * math.sin(a)) - 620), g1)
        fr.paste(g2, (int(240 - 140 * math.cos(a)) - 460, int(1520 - 90 * math.sin(a)) - 460), g2)
        d = ImageDraw.Draw(fr)
        # progress segments, one per scene
        gap, x0, x1, y = 12, 70, W - 70, 150
        seg_w = (x1 - x0 - gap * (n_seg - 1)) / n_seg
        for i in range(n_seg):
            sx = x1 - (i + 1) * seg_w - i * gap          # fills right to left (RTL)
            d.rounded_rectangle([sx, y, sx + seg_w, y + 8], 4, fill=(255, 255, 255, 60))
            u = (ts - starts[i]) / scenes[i][1]
            if u > 0:
                fw = seg_w * min(1.0, u)
                d.rounded_rectangle([sx + seg_w - fw, y, sx + seg_w, y + 8], 4,
                                    fill=BRIGHT + (255,))
        for i, (lay, dur) in enumerate(scenes):
            local = ts - starts[i]
            if local < -0.001 or local > dur + T_FADE:
                continue
            a_in = 1.0 if i == 0 else ease(local / T_FADE)      # hook is there at frame 0
            a_out = 1.0 if i == len(scenes) - 1 else 1 - ease((local - dur) / T_FADE)
            dy = 0 if i == 0 else (1 - a_in) * 70
            if local > dur:
                dy = -(1 - a_out) * 50
            place(fr, lay, a_in * a_out, dy)
            if i == 0 and underline and local <= dur:
                uy, uw = underline
                grow = ease(local / 0.5)
                ImageDraw.Draw(fr).rounded_rectangle(
                    [W / 2 + uw / 2 - uw * grow, uy, W / 2 + uw / 2, uy + 10], 5,
                    fill=BRIGHT + (int(255 * a_out),))
        return fr.convert('RGB')

    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    ff = subprocess.Popen([
        'ffmpeg', '-y', '-loglevel', 'error',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-shortest', '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.0',
        '-c:a', 'aac', '-b:a', '32k', '-movflags', '+faststart', out_mp4],
        stdin=subprocess.PIPE)
    n = int(round(total * FPS))
    for i in range(n):
        ff.stdin.write(frame_at(i / FPS).tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit('ffmpeg failed')
    frame_at(0.8).save(out_jpg, quality=86)
    return round(total, 1)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding='utf-8') as fh:
        seconds = render(json.load(fh), sys.argv[2], sys.argv[3])
    print(f'wrote {sys.argv[2]} ({seconds}s) and {sys.argv[3]}')

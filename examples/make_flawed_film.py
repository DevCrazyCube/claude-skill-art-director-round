#!/usr/bin/env python3
"""Draws a six-second, three-shot test film with five planted faults, to try the art-director round on.

    python3 make_flawed_film.py OUT.mp4

Shot 1 (0-2 s) is meant to be clean. The planted faults:

    shot 2, 2-4 s   1. the head is cut by the top of the frame            (Composition)
                    2. the mug floats above the desk, no contact shadow   (Props)
    shot 3, 4-6 s   3. the caption covers the character's eyes            (Finish)
                    4. a line of text sits in the bottom 20 % of the frame (Finish)
                    5. more than a quarter of the frame is empty wall     (Dead space)

Everything is drawn here as SVG; no footage or artwork from anywhere else.
Needs rsvg-convert (librsvg) and ffmpeg on the PATH.
"""
import os
import shutil
import subprocess
import sys
import tempfile

W, H = 540, 960
WALL, FLOOR, DESK, DESK_SIDE = '#f1e6d6', '#d8c4a8', '#b9834f', '#96673b'
BODY, BODY_DARK, INK = '#5b8def', '#3f6fd0', '#22262e'


def character(cx, cy, r, look=0.0, shadow=True):
    """A round character with two eyes. `look` shifts the pupils: -1 left, 1 right. No shadow when a desk hides its base."""
    eye = r * 0.2
    dx = look * eye * 0.4
    parts = [
        f'<ellipse cx="{cx}" cy="{cy + r * 0.92}" rx="{r * 0.8}" ry="{r * 0.14}" fill="#000" opacity="0.16"/>'
        if shadow else '',
        f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r * 0.94}" fill="{BODY}"/>',
        f'<path d="M {cx - r} {cy} A {r} {r * 0.94} 0 0 0 {cx + r} {cy} A {r} {r * 0.7} 0 0 1 {cx - r} {cy} Z" '
        f'fill="{BODY_DARK}" opacity="0.55"/>',
    ]
    for side in (-1, 1):
        ex, ey = cx + side * r * 0.36, cy - r * 0.18
        parts.append(f'<circle cx="{ex}" cy="{ey}" r="{eye}" fill="#fff"/>')
        parts.append(f'<circle cx="{ex + dx}" cy="{ey}" r="{eye * 0.52}" fill="{INK}"/>')
    parts.append(f'<path d="M {cx - r * 0.2} {cy + r * 0.3} Q {cx} {cy + r * 0.46} {cx + r * 0.2} {cy + r * 0.3}" '
                 f'stroke="{INK}" stroke-width="{max(2, r * 0.05)}" fill="none" stroke-linecap="round"/>')
    return '\n'.join(parts)


def mug(x, y, s=1.0, shadow=True):
    """A mug whose base sits at y."""
    w, h = 46 * s, 52 * s
    out = []
    if shadow:
        out.append(f'<ellipse cx="{x + w / 2}" cy="{y}" rx="{w * 0.62}" ry="{6 * s}" fill="#000" opacity="0.22"/>')
    out.append(f'<path d="M {x + w} {y - h * 0.75} q {20 * s} {h * 0.25} 0 {h * 0.5}" stroke="#e8553d" '
               f'stroke-width="{7 * s}" fill="none"/>')
    out.append(f'<rect x="{x}" y="{y - h}" width="{w}" height="{h}" rx="{6 * s}" fill="#f2664c"/>')
    out.append(f'<rect x="{x}" y="{y - h}" width="{w * 0.3}" height="{h}" rx="{6 * s}" fill="#fff" opacity="0.18"/>')
    return '\n'.join(out)


def room(floor_y):
    return (f'<rect width="{W}" height="{H}" fill="{WALL}"/>'
            f'<rect y="{floor_y}" width="{W}" height="{H - floor_y}" fill="{FLOOR}"/>')


def desk(x, y, w):
    return (f'<rect x="{x + 14}" y="{y + 22}" width="14" height="150" fill="{DESK_SIDE}"/>'
            f'<rect x="{x + w - 28}" y="{y + 22}" width="14" height="150" fill="{DESK_SIDE}"/>'
            f'<ellipse cx="{x + w / 2}" cy="{y + 176}" rx="{w * 0.5}" ry="10" fill="#000" opacity="0.12"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="24" rx="5" fill="{DESK}"/>'
            f'<rect x="{x}" y="{y + 16}" width="{w}" height="8" rx="3" fill="{DESK_SIDE}"/>')


def caption(text, y, size=34, box=True, x=W / 2):
    width = len(text) * size * 0.56 + 36
    out = ''
    if box:
        out += (f'<rect x="{x - width / 2}" y="{y - size * 1.05}" width="{width}" height="{size * 1.5}" '
                f'rx="10" fill="#fff"/>')
    out += (f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Noto Sans, DejaVu Sans, sans-serif" '
            f'font-weight="700" font-size="{size}" fill="{INK}">{text}</text>')
    return out


def shot_clean():
    """Character on the left third behind a desk, looking at a mug; window behind, plant in front."""
    return '\n'.join([
        room(690),
        # behind: a window, lit from the left
        '<rect x="300" y="250" width="170" height="210" rx="8" fill="#cfe6f5"/>',
        '<rect x="300" y="250" width="170" height="210" rx="8" fill="none" stroke="#fff" stroke-width="10"/>',
        '<path d="M 385 250 V 460 M 300 355 H 470" stroke="#fff" stroke-width="8"/>',
        character(180, 520, 96, look=1, shadow=False),
        desk(70, 600, 400),
        mug(350, 600),
        # in front: a plant, bottom left
        '<ellipse cx="72" cy="884" rx="60" ry="10" fill="#000" opacity="0.18"/>',
        '<rect x="34" y="800" width="76" height="84" rx="10" fill="#8a5a3c"/>',
        '<path d="M 72 800 C 20 740 30 690 60 660 C 70 720 80 750 72 800 Z" fill="#4e9d6b"/>',
        '<path d="M 72 800 C 130 750 130 700 104 672 C 92 730 80 760 72 800 Z" fill="#3f8a5b"/>',
        caption('Monday, 9:00', 200),
    ])


def shot_cut_head_floating_mug():
    return '\n'.join([
        room(500),
        character(230, 170, 220, look=1, shadow=False),  # fault 1: the top of the head is outside the frame
        desk(30, 370, 480),
        mug(380, 320, 1.5, shadow=False),                # fault 2: 50 px above the desk, no shadow
    ])


def shot_caption_on_eyes_text_low_empty_wall():
    cx, cy, r = 150, 770, 84
    return '\n'.join([
        room(800),                                  # fault 5: the upper two thirds are bare wall
        character(cx, cy, r, look=0),
        caption('No way.', cy - r * 0.18 + 14, 40, x=cx),  # fault 3: across the eyes
        caption('more in the next one', 925, 26, box=False),  # fault 4: in the bottom 20 %
    ])


def main(argv):
    if len(argv) != 1:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    for tool in ('rsvg-convert', 'ffmpeg'):
        if not shutil.which(tool):
            print(f'{tool} is not on the PATH', file=sys.stderr)
            return 2
    tmp = tempfile.mkdtemp(prefix='flawed-')
    try:
        listing = os.path.join(tmp, 'list.txt')
        with open(listing, 'w', encoding='utf-8') as f:
            for i, body in enumerate((shot_clean(), shot_cut_head_floating_mug(),
                                      shot_caption_on_eyes_text_low_empty_wall())):
                svg, png = os.path.join(tmp, f's{i}.svg'), os.path.join(tmp, f's{i}.png')
                with open(svg, 'w', encoding='utf-8') as s:
                    s.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
                            f'viewBox="0 0 {W} {H}">\n{body}\n</svg>\n')
                subprocess.run(['rsvg-convert', '-w', str(W * 2), '-o', png, svg], check=True)
                f.write(f"file '{png}'\nduration 2\n")
            f.write(f"file '{png}'\n")  # the concat demuxer needs the last picture twice to keep its duration
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', listing,
                        '-vf', 'fps=30,format=yuv420p', '-t', '6', '-c:v', 'libx264', '-crf', '18', argv[0]],
                       check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f'wrote {argv[0]}: 3 shots of 2 s, {W * 2}x{H * 2}, five planted faults (see the top of this file)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

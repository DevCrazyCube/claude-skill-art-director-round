#!/usr/bin/env python3
"""Pull review stills from a video: each at full size and at phone width, plus contact sheets.

    python3 stills.py FILM --out DIR                   one still a second
    python3 stills.py FILM --out DIR --every 0.5       one every half second
    python3 stills.py FILM --out DIR --at 0.4,3.1,6    at these times (seconds)
    python3 stills.py FILM --out DIR --phone 390       the phone width in pixels (default 390)

Writes DIR/full/tSSS.SS.png, DIR/phone/tSSS.SS.png, DIR/sheet-full.png, DIR/sheet-phone.png and DIR/index.json.
The file name is the time in the film, so a critic can name a fix by its time.

Needs ffmpeg and ffprobe on the PATH. Standard library only.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys


def probe(film):
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
         'stream=width,height:format=duration', '-of', 'json', film],
        capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    stream = data['streams'][0]
    return float(data['format']['duration']), int(stream['width']), int(stream['height'])


def times_every(duration, every):
    """Times from half a step in, so the first still is not the black first frame and the last is inside the film."""
    if every <= 0:
        raise ValueError('--every must be more than 0')
    if duration <= 0:
        raise ValueError('the film has no length')
    times = [round(every / 2 + i * every, 2) for i in range(math.floor(duration / every))]
    return times or [round(duration / 2, 2)]  # a film shorter than one step still gets its middle frame


def parse_times(text, duration):
    times = sorted({round(float(part), 2) for part in text.split(',') if part.strip()})
    bad = [t for t in times if t < 0 or t >= duration]
    if bad:
        raise ValueError(f'time {bad[0]:g} s is outside the film (0 to {duration:.2f} s)')
    if not times:
        raise ValueError('--at has no times')
    return times


def name_for(t):
    return f't{t:06.2f}.png'


def grab(film, t, path, width=None):
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', film, '-frames:v', '1']
    if width:
        cmd += ['-vf', f'scale={width}:-2:flags=lanczos']
    subprocess.run(cmd + [path], check=True)


def sheet(folder, names, out, tile_width, columns):
    """A contact sheet of the stills in `folder`, in time order."""
    rows = math.ceil(len(names) / columns)
    listing = os.path.join(folder, 'list.txt')
    with open(listing, 'w', encoding='utf-8') as f:
        for n in names:
            f.write(f"file '{n}'\nduration 1\n")
    try:
        subprocess.run(
            ['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', listing,
             '-vf', f'scale={tile_width}:-2,tile={columns}x{rows}:padding=8:margin=8:color=white',
             '-frames:v', '1', out], check=True)
    finally:
        os.remove(listing)


def run(film, out, every=1.0, at=None, phone=390, columns=None):
    duration, width, height = probe(film)
    times = parse_times(at, duration) if at else times_every(duration, every)
    full_dir, phone_dir = os.path.join(out, 'full'), os.path.join(out, 'phone')
    for d in (full_dir, phone_dir):
        os.makedirs(d, exist_ok=True)
    names = []
    for t in times:
        n = name_for(t)
        grab(film, t, os.path.join(full_dir, n))
        grab(film, t, os.path.join(phone_dir, n), phone)
        names.append(n)
    columns = columns or min(len(names), 6 if height > width else 4)
    sheet(full_dir, names, os.path.join(out, 'sheet-full.png'), min(width, 540), columns)
    sheet(phone_dir, names, os.path.join(out, 'sheet-phone.png'), min(phone, 195), columns)
    index = {'film': os.path.basename(film), 'duration': round(duration, 2), 'size': [width, height],
             'phone_width': phone, 'stills': [{'t': t, 'file': n} for t, n in zip(times, names)]}
    with open(os.path.join(out, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
    return index


def main(argv):
    ap = argparse.ArgumentParser(description='Review stills at full size and phone width.')
    ap.add_argument('film')
    ap.add_argument('--out', required=True)
    ap.add_argument('--every', type=float, default=1.0, help='seconds between stills (default 1)')
    ap.add_argument('--at', help='comma-separated times in seconds, instead of --every')
    ap.add_argument('--phone', type=int, default=390, help='phone width in pixels (default 390)')
    ap.add_argument('--columns', type=int, help='stills per row on the contact sheets')
    args = ap.parse_args(argv)
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            print(f'{tool} is not on the PATH', file=sys.stderr)
            return 2
    if not os.path.isfile(args.film):
        print(f'{args.film}: no such file', file=sys.stderr)
        return 2
    try:
        index = run(args.film, args.out, args.every, args.at, args.phone, args.columns)
    except (ValueError, subprocess.CalledProcessError) as err:
        print(f'stills: {err}', file=sys.stderr)
        return 2
    print(f"{len(index['stills'])} stills from {index['film']} ({index['duration']} s, "
          f"{index['size'][0]}x{index['size'][1]}) in {args.out}: full/, phone/ ({args.phone} px), two sheets")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

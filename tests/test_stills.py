"""python3 -m unittest discover -s tests

The film is generated here by ffmpeg: three seconds, one flat colour a second (red, green, blue), 360x640.
So a still's colour says which second it was taken from. No footage from anywhere else.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, '..', 'scripts', 'stills.py')
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import stills  # noqa: E402

HAVE_FFMPEG = bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))


def make_film(path):
    parts = ''.join(f'color=c={c}:s=360x640:r=30:d=1[v{i}];' for i, c in enumerate(('red', 'green', 'blue')))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-filter_complex', parts + '[v0][v1][v2]concat=n=3:v=1[out]',
                    '-map', '[out]', '-pix_fmt', 'yuv420p', path], check=True)


def size_of(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', path],
                         capture_output=True, text=True, check=True).stdout.strip()
    w, h = out.split(',')[:2]
    return int(w), int(h)


def colour_of(path):
    """The picture's average colour, as the name of its strongest channel."""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', 'scale=1:1', '-f', 'rawvideo',
                          '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return ('red', 'green', 'blue')[max(range(3), key=lambda i: raw[i])]


class Times(unittest.TestCase):
    def test_every_starts_half_a_step_in_and_stays_inside(self):
        self.assertEqual(stills.times_every(3.0, 1.0), [0.5, 1.5, 2.5])
        self.assertEqual(stills.times_every(2.0, 0.5), [0.25, 0.75, 1.25, 1.75])
        self.assertEqual(stills.times_every(3.4, 1.0), [0.5, 1.5, 2.5])

    def test_a_film_shorter_than_one_step_gets_its_middle(self):
        self.assertEqual(stills.times_every(0.6, 1.0), [0.3])

    def test_every_must_be_positive(self):
        with self.assertRaises(ValueError):
            stills.times_every(3.0, 0)

    def test_at_is_sorted_and_deduplicated(self):
        self.assertEqual(stills.parse_times('2, 0.4,2.0,1', 3.0), [0.4, 1.0, 2.0])

    def test_at_outside_the_film_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'outside the film'):
            stills.parse_times('0.5,3.0', 3.0)
        with self.assertRaisesRegex(ValueError, 'no times'):
            stills.parse_times(' , ', 3.0)

    def test_names_sort_in_time_order(self):
        names = [stills.name_for(t) for t in (10.0, 2.5, 100.25)]
        self.assertEqual(names, ['t010.00.png', 't002.50.png', 't100.25.png'])
        self.assertEqual(sorted(names), ['t002.50.png', 't010.00.png', 't100.25.png'])


@unittest.skipUnless(HAVE_FFMPEG, 'needs ffmpeg and ffprobe')
class OnAFilm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='stills-')
        cls.film = os.path.join(cls.tmp, 'film.mp4')
        make_film(cls.film)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_one_still_a_second_each_from_its_own_second(self):
        out = os.path.join(self.tmp, 'every')
        index = stills.run(self.film, out)
        self.assertEqual([s['t'] for s in index['stills']], [0.5, 1.5, 2.5])
        self.assertEqual(index['size'], [360, 640])
        for still, colour in zip(index['stills'], ('red', 'green', 'blue')):
            self.assertEqual(colour_of(os.path.join(out, 'full', still['file'])), colour)
            self.assertEqual(colour_of(os.path.join(out, 'phone', still['file'])), colour)

    def test_full_is_the_film_size_and_phone_is_the_phone_width(self):
        out = os.path.join(self.tmp, 'sizes')
        index = stills.run(self.film, out, at='1.5', phone=180)
        name = index['stills'][0]['file']
        self.assertEqual(size_of(os.path.join(out, 'full', name)), (360, 640))
        self.assertEqual(size_of(os.path.join(out, 'phone', name)), (180, 320))

    def test_sheets_hold_every_still_in_order(self):
        out = os.path.join(self.tmp, 'sheets')
        stills.run(self.film, out, phone=180)
        for name, tile in (('sheet-full.png', 360), ('sheet-phone.png', 180)):
            w, h = size_of(os.path.join(out, name))
            self.assertEqual(w, 3 * tile + 4 * 8, name)  # three tiles in a row, 8 px around and between
            self.assertEqual(h, tile * 640 // 360 + 2 * 8, name)
        self.assertFalse(os.path.exists(os.path.join(out, 'full', 'list.txt')), 'the listing is cleaned up')
        # left third red, right third blue
        left = os.path.join(self.tmp, 'left.png')
        right = os.path.join(self.tmp, 'right.png')
        sheet = os.path.join(out, 'sheet-full.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', sheet, '-vf', 'crop=300:300:40:100', left], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', sheet, '-vf', 'crop=300:300:780:100', right], check=True)
        self.assertEqual(colour_of(left), 'red')
        self.assertEqual(colour_of(right), 'blue')

    def test_command_line_writes_the_index_and_says_what_it_made(self):
        out = os.path.join(self.tmp, 'cli')
        done = subprocess.run([sys.executable, SCRIPT, self.film, '--out', out, '--at', '0.4,2.6'],
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('2 stills from film.mp4', done.stdout)
        with open(os.path.join(out, 'index.json'), encoding='utf-8') as f:
            index = json.load(f)
        self.assertEqual(index['stills'], [{'t': 0.4, 'file': 't000.40.png'}, {'t': 2.6, 'file': 't002.60.png'}])
        self.assertEqual(index['phone_width'], 390)

    def test_command_line_refuses_a_missing_film_and_a_time_outside_it(self):
        gone = subprocess.run([sys.executable, SCRIPT, os.path.join(self.tmp, 'nope.mp4'), '--out', self.tmp],
                              capture_output=True, text=True)
        self.assertEqual(gone.returncode, 2)
        self.assertIn('no such file', gone.stderr)
        late = subprocess.run([sys.executable, SCRIPT, self.film, '--out', os.path.join(self.tmp, 'late'), '--at', '9'],
                              capture_output=True, text=True)
        self.assertEqual(late.returncode, 2)
        self.assertIn('outside the film', late.stderr)


if __name__ == '__main__':
    unittest.main()

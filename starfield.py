#!/usr/bin/env python3
import time, random, sys, os, signal, math

def cleanup(*a):
    sys.stdout.write('\033[0m\033[?25h\033[2J\033[H')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

sys.stdout.write('\033[?25l\033[2J\033[H')

class Star:
    def __init__(self, cols, rows):
        self.reset(cols, rows, random.uniform(0, 8))

    def reset(self, cols, rows, z=None):
        self.x = random.uniform(-1, 1)
        self.y = random.uniform(-1, 1)
        self.z = z if z is not None else 8.0
        self.px, self.py = 0, 0
        self.cols = cols
        self.rows = rows

    def update(self, speed):
        self.z -= speed
        if self.z <= 0:
            self.reset(self.cols, self.rows)
            return
        cx, cy = self.cols / 2, self.rows / 2
        sx = int(self.x / self.z * cx + cx)
        sy = int(self.y / self.z * cy * 0.5 + cy)
        self.px, self.py = sx, sy

    def draw(self):
        sx, sy = self.px, self.py
        if not (0 <= sx < self.cols and 0 <= sy < self.rows):
            return None, None, None
        brightness = max(0.0, 1.0 - self.z / 8.0)
        if brightness > 0.9:
            char, color = '✦', '\033[97;1m'
        elif brightness > 0.6:
            char, color = '·', '\033[37m'
        elif brightness > 0.3:
            char, color = '·', '\033[90m'
        else:
            char, color = '·', '\033[90m'
        return sx, sy, color + char + '\033[0m'

try:
    cols = os.get_terminal_size().columns
    rows = os.get_terminal_size().lines
except Exception:
    cols, rows = 40, 24

NUM_STARS = min(cols * rows // 6, 300)
stars = [Star(cols, rows) for _ in range(NUM_STARS)]
frame = 0

while True:
    try:
        cols = os.get_terminal_size().columns
        rows = os.get_terminal_size().lines
    except Exception:
        pass

    speed = 0.12 + 0.06 * math.sin(frame * 0.02)
    cells = {}
    for star in stars:
        star.update(speed)
        x, y, ch = star.draw()
        if x is not None:
            cells[(x, y)] = ch

    out = ['\033[H']
    for row in range(rows):
        line = ''
        for col in range(cols):
            line += cells.get((col, row), ' ')
        out.append(line)
    sys.stdout.write(''.join(out))
    sys.stdout.flush()
    time.sleep(0.05)
    frame += 1

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
        self.cols = cols
        self.rows = rows
        self.reset(random.uniform(0, 8))

    def reset(self, z=None):
        self.x = random.uniform(-1, 1)
        self.y = random.uniform(-1, 1)
        self.z = z if z is not None else 8.0

    def update(self, speed):
        self.z -= speed
        if self.z <= 0:
            self.reset()

    def draw(self, cols, rows):
        cx, cy = cols / 2, rows / 2
        sx = int(self.x / self.z * cx + cx)
        sy = int(self.y / self.z * cy * 0.5 + cy)
        if not (0 <= sx < cols and 0 <= sy < rows):
            return None, None, None
        brightness = max(0.0, 1.0 - self.z / 8.0)
        if brightness > 0.85:
            char, color = '+', '\033[97;1m'
        elif brightness > 0.6:
            char, color = '*', '\033[37m'
        elif brightness > 0.3:
            char, color = '.', '\033[37m'
        else:
            char, color = '.', '\033[90m'
        return sx, sy, color + char + '\033[0m'

try:
    cols, rows = os.get_terminal_size()
except Exception:
    cols, rows = 40, 24

NUM_STARS = min(cols * rows // 5, 400)
stars = [Star(cols, rows) for _ in range(NUM_STARS)]
frame = 0

while True:
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        pass

    speed = 0.12 + 0.06 * math.sin(frame * 0.02)
    cells = {}
    for star in stars:
        star.update(speed)
        x, y, ch = star.draw(cols, rows)
        if x is not None:
            cells[(x, y)] = ch

    out = '\033[H'
    for row in range(rows):
        for col in range(cols):
            out += cells.get((col, row), ' ')
        if row < rows - 1:
            out += '\n'
    sys.stdout.write(out)
    sys.stdout.flush()
    time.sleep(0.05)
    frame += 1

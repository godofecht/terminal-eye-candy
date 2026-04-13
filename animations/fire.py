#!/usr/bin/env python3
import time, sys, os, signal, random

def cleanup(*a):
    sys.stdout.write('\033[0m\033[?25h')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

sys.stdout.write('\033[?25l')

# true-color fire palette: black -> dark red -> orange -> yellow -> white
PALETTE = [
    (0,0,0),(20,0,0),(40,0,0),(60,0,0),(80,0,0),(100,0,0),
    (120,0,0),(140,0,0),(160,0,0),(180,10,0),(200,20,0),
    (210,40,0),(220,60,0),(230,80,0),(240,100,0),(245,120,0),
    (250,140,0),(252,160,0),(254,180,0),(255,200,0),(255,215,0),
    (255,225,20),(255,235,60),(255,240,100),(255,245,140),
    (255,250,180),(255,252,210),(255,254,230),(255,255,245),(255,255,255),
]
N = len(PALETTE)
CHARS = ' .,`^*xX#@'

try:
    cols, rows = os.get_terminal_size()
except Exception:
    cols, rows = 80, 24

fire = [[0] * (cols + 2) for _ in range(rows + 1)]

while True:
    try:
        c, r = os.get_terminal_size()
        if c != cols or r != rows:
            cols, rows = c, r
            fire = [[0] * (cols + 2) for _ in range(rows + 1)]
    except Exception:
        pass

    # Seed bottom
    for x in range(cols + 2):
        v = N - 1 if random.random() > 0.15 else max(0, N - 3 - random.randint(0, 3))
        fire[rows][x] = v

    # Propagate upward
    for y in range(rows):
        for x in range(1, cols + 1):
            s = fire[y+1][x] + fire[y+1][x + random.randint(-1, 1)]
            fire[y][x] = max(0, s // 2 - random.randint(0, 2))

    out = '\033[H'
    for y in range(rows):
        for x in range(1, cols + 1):
            heat = fire[y][x]
            r2, g, b = PALETTE[min(heat, N-1)]
            ci = min(int(heat * len(CHARS) / N), len(CHARS) - 1)
            out += f'\033[38;2;{r2};{g};{b}m{CHARS[ci]}'
        if y < rows - 1:
            out += '\n'
    out += '\033[0m'
    sys.stdout.write(out)
    sys.stdout.flush()
    time.sleep(0.05)

#!/usr/bin/env python3
import time, sys, os, signal, random

def cleanup(*a):
    sys.stdout.write('\033[0m\033[?25h')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

sys.stdout.write('\033[?25l')

COLORS = ['\033[32m', '\033[92m', '\033[96m', '\033[93m', '\033[97;1m']

def init(cols, rows):
    return [[random.random() > 0.65 for _ in range(cols)] for _ in range(rows)]

def step(g, cols, rows):
    n = [[False]*cols for _ in range(rows)]
    for y in range(rows):
        for x in range(cols):
            nb = sum(g[(y+dy)%rows][(x+dx)%cols]
                     for dy in (-1,0,1) for dx in (-1,0,1) if (dy,dx)!=(0,0))
            n[y][x] = nb in (2,3) if g[y][x] else nb == 3
    return n

try:
    cols, rows = os.get_terminal_size()
except Exception:
    cols, rows = 80, 24

grid = init(cols, rows)
age  = [[0]*cols for _ in range(rows)]

while True:
    try:
        c, r = os.get_terminal_size()
        if c != cols or r != rows:
            cols, rows = c, r
            grid = init(cols, rows)
            age  = [[0]*cols for _ in range(rows)]
    except Exception:
        pass

    ng = step(grid, cols, rows)
    live = 0
    for y in range(rows):
        for x in range(cols):
            if ng[y][x]:
                age[y][x] = min(age[y][x]+1, len(COLORS)-1)
                live += 1
            else:
                age[y][x] = 0

    out = '\033[H'
    for y in range(rows):
        for x in range(cols):
            if ng[y][x]:
                out += COLORS[age[y][x]] + '#\033[0m'
            else:
                out += ' '
        if y < rows - 1:
            out += '\n'

    if live < cols * rows * 0.02:
        grid = init(cols, rows)
        age  = [[0]*cols for _ in range(rows)]
    else:
        grid = ng

    sys.stdout.write(out)
    sys.stdout.flush()
    time.sleep(0.07)

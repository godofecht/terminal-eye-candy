#!/usr/bin/env python3
import time, sys, os, signal, math

def cleanup(*a):
    sys.stdout.write('\033[0m\033[?25h')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

sys.stdout.write('\033[?25l')

CHARS = ' .:-=+*#%@'

def hsv2rgb(h, s=1.0, v=1.0):
    h = h % 360
    i = int(h / 60)
    f = h / 60 - i
    p, q, t = v*(1-s), v*(1-s*f), v*(1-s*(1-f))
    rgb = [(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)][i]
    return tuple(int(x*255) for x in rgb)

t = 0.0
while True:
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 80, 24

    out = '\033[H'
    for y in range(rows):
        for x in range(cols):
            v  = math.sin(x * 0.25 + t)
            v += math.sin(y * 0.5 + t * 1.3)
            v += math.sin((x + y) * 0.15 + t * 0.7)
            v += math.sin(math.sqrt((x - cols/2)**2 + (y - rows/2)**2) * 0.3 + t)
            v = (v + 4) / 8.0
            hue = (v * 300 + t * 40) % 360
            r, g, b = hsv2rgb(hue)
            ch = CHARS[int(v * (len(CHARS)-1))]
            out += f'\033[38;2;{r};{g};{b}m{ch}'
        if y < rows - 1:
            out += '\n'
    out += '\033[0m'
    sys.stdout.write(out)
    sys.stdout.flush()
    t += 0.07
    time.sleep(0.04)

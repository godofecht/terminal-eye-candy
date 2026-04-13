#!/usr/bin/env python3
import time, sys, os, signal, datetime

def cleanup(*a):
    sys.stdout.write('\033[0m\033[?25h')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

D = {
    '0': ['▓▓▓', '▓ ▓', '▓ ▓', '▓ ▓', '▓▓▓'],
    '1': ['  ▓', '  ▓', '  ▓', '  ▓', '  ▓'],
    '2': ['▓▓▓', '  ▓', '▓▓▓', '▓  ', '▓▓▓'],
    '3': ['▓▓▓', '  ▓', '▓▓▓', '  ▓', '▓▓▓'],
    '4': ['▓ ▓', '▓ ▓', '▓▓▓', '  ▓', '  ▓'],
    '5': ['▓▓▓', '▓  ', '▓▓▓', '  ▓', '▓▓▓'],
    '6': ['▓▓▓', '▓  ', '▓▓▓', '▓ ▓', '▓▓▓'],
    '7': ['▓▓▓', '  ▓', '  ▓', '  ▓', '  ▓'],
    '8': ['▓▓▓', '▓ ▓', '▓▓▓', '▓ ▓', '▓▓▓'],
    '9': ['▓▓▓', '▓ ▓', '▓▓▓', '  ▓', '▓▓▓'],
    ':': ['   ', ' ▓ ', '   ', ' ▓ ', '   '],
}

sys.stdout.write('\033[?25l')

while True:
    now = datetime.datetime.now()
    t = now.strftime('%H:%M:%S')
    try:
        cols = os.get_terminal_size().columns
        rows = os.get_terminal_size().lines
    except Exception:
        cols, rows = 80, 24

    lines = ['' for _ in range(5)]
    for ch in t:
        for i, row in enumerate(D.get(ch, ['   '] * 5)):
            lines[i] += row + ' '

    w = len(lines[0])
    lpad = max(0, (cols - w) // 2)
    tpad = max(0, (rows - 8) // 2)

    out = '\033[H\033[2J'
    out += '\n' * tpad
    for line in lines:
        out += ' ' * lpad + '\033[92;1m' + line + '\033[0m\n'

    date_str = now.strftime('%A, %B %d %Y')
    out += '\n'
    dpad = max(0, (cols - len(date_str)) // 2)
    out += ' ' * dpad + '\033[36m' + date_str + '\033[0m\n'

    sys.stdout.write(out)
    sys.stdout.flush()
    time.sleep(1)

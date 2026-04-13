#!/usr/bin/env python3
import time, random, sys, os, signal

def cleanup(*a):
    sys.stdout.write('\033[0m\033[?25h\n')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

CHARS = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789'
sys.stdout.write('\033[?25l')

while True:
    try:
        cols = os.get_terminal_size().columns
    except Exception:
        cols = 80
    line = ''
    for _ in range(cols):
        r = random.random()
        c = random.choice(CHARS)
        if r < 0.04:   line += f'\033[97;1m{c}\033[0m'
        elif r < 0.30: line += f'\033[92m{c}\033[0m'
        elif r < 0.55: line += f'\033[32m{c}\033[0m'
        else:           line += ' '
    print(line, flush=True)
    time.sleep(0.04)

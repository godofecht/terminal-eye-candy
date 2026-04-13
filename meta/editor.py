#!/usr/bin/env python3
"""terminal-eye-candy — CLAUDE.md click editor"""
import os, sys, signal, time, termios, tty, select

CLAUDE_MD = os.path.expanduser('~/terminal-eye-candy/CLAUDE.md')
GUTTER    = 5   # " NNN " column

old_tty = None
fd      = sys.stdin.fileno()

def term_restore():
    if old_tty:
        try: termios.tcsetattr(fd, termios.TCSADRAIN, old_tty)
        except Exception: pass

def cleanup(*_):
    sys.stdout.write('\033[?1000l\033[?1006l\033[0m\033[?25h\033[2J\033[H')
    sys.stdout.flush()
    term_restore()
    sys.exit(0)

signal.signal(signal.SIGINT,  cleanup)
signal.signal(signal.SIGTERM, cleanup)

old_tty = termios.tcgetattr(fd)
tty.setraw(fd)
# hide cursor, enable SGR mouse, clear screen
sys.stdout.write('\033[?25l\033[?1000h\033[?1006h\033[2J\033[H')
sys.stdout.flush()

def load():
    try:    return open(CLAUDE_MD).read().splitlines()
    except: return ['']

def save(lines):
    os.makedirs(os.path.dirname(CLAUDE_MD), exist_ok=True)
    open(CLAUDE_MD, 'w').write('\n'.join(lines))

lines  = load()
cx, cy = 0, 0
scroll = 0
dirty  = False
status = ''
status_t   = 0.0
prev_size  = (0, 0)

def clamp_cx():
    global cx
    cx = min(cx, len(lines[cy]))

def set_status(msg):
    global status, status_t
    status, status_t = msg, time.time()

def hl(line):
    if line.startswith('# '):                         return '\033[97;1m'
    if line.startswith('## '):                        return '\033[96;1m'
    if line.startswith('### '):                       return '\033[93m'
    if line.startswith('- ') or line.startswith('* '): return '\033[37m'
    if line.startswith('```'):                        return '\033[32m'
    return '\033[90m'

def render():
    global prev_size
    try:    cols, rows = os.get_terminal_size()
    except: cols, rows = 80, 24
    text_rows = rows - 2

    cur_size = (cols, rows)
    if cur_size != prev_size:
        sys.stdout.write('\033[2J')   # full clear on resize
        prev_size = cur_size

    out = '\033[H'   # move home, then overwrite line-by-line

    # ── header ────────────────────────────────────────────────────────────────
    mark  = ' [+]' if dirty else '     '
    left  = f'  CLAUDE.md{mark}'
    right = '  Ctrl-S save   Ctrl-Q quit  '
    hdr   = (left + ' ' * max(0, cols - len(left) - len(right)) + right)[:cols]
    out  += f'\033[7m{hdr}\033[0m\n'

    # ── file content ──────────────────────────────────────────────────────────
    for i in range(text_rows):
        r = scroll + i
        if r >= len(lines):
            out += '\033[90m~\033[K\033[0m\n'
            continue

        line     = lines[r]
        lnum     = f'{r+1:>{GUTTER-1}} '       # always GUTTER chars wide
        lnum_col = '\033[33m' if r == cy else '\033[90m'
        disp     = line[:cols - GUTTER]
        c        = hl(disp)

        if r == cy:
            scx = min(cx, len(disp))
            ch  = disp[scx] if scx < len(disp) else ' '
            body = c + disp[:scx] + '\033[7m' + ch + '\033[27m' + c + disp[scx+1:]
        else:
            body = c + disp

        out += f'{lnum_col}{lnum}\033[0m{body}\033[0m\033[K\n'

    # ── status bar ────────────────────────────────────────────────────────────
    pos  = f' Ln {cy+1}/{len(lines)}  Col {cx+1} '
    msg  = (' ' + status + '  ') if status and time.time() - status_t < 3 else ''
    sbar = (msg + ' ' * max(0, cols - len(msg) - len(pos)) + pos)[:cols]
    out += f'\033[7m{sbar}\033[0m'

    sys.stdout.write(out)
    sys.stdout.flush()

def parse_mouse(raw):
    try:
        s     = raw.decode('ascii', errors='ignore').lstrip('<').rstrip('Mm')
        b,x,y = (int(v) for v in s.split(';'))
        press = not raw.endswith(b'm')
        return b, x-1, y-1, press   # 0-indexed col/row
    except:
        return None

# ── initial draw ──────────────────────────────────────────────────────────────
render()

# ── main loop ─────────────────────────────────────────────────────────────────
while True:
    try:    cols, rows = os.get_terminal_size()
    except: cols, rows = 80, 24
    text_rows = rows - 2

    ready, _, _ = select.select([sys.stdin], [], [], 0.5)
    if not ready:
        render()   # idle tick (catches resize)
        continue

    raw = os.read(fd, 256)
    if not raw:
        continue

    # Ctrl-Q
    if raw == b'\x11':
        cleanup()

    # Ctrl-S
    elif raw == b'\x13':
        save(lines)
        dirty = False
        set_status('Saved!')

    # SGR mouse  ESC [ < ...
    elif b'\x1b[<' in raw:
        idx    = raw.index(b'\x1b[<')
        parsed = parse_mouse(raw[idx+2:])
        if parsed:
            btn, mx, my, press = parsed
            if press and btn == 0:             # left-click down
                nr = scroll + (my - 1)         # row 0 = header
                if 0 <= nr < len(lines):
                    cy = nr
                    cx = max(0, min(mx - GUTTER, len(lines[cy])))

    # arrow / special keys
    elif raw.startswith(b'\x1b['):
        key = raw[2:]
        if   key == b'A':   cy = max(cy-1, 0);               clamp_cx()
        elif key == b'B':   cy = min(cy+1, len(lines)-1);    clamp_cx()
        elif key == b'C':
            if cx < len(lines[cy]): cx += 1
            elif cy < len(lines)-1: cy += 1; cx = 0
        elif key == b'D':
            if cx > 0: cx -= 1
            elif cy > 0: cy -= 1; cx = len(lines[cy])
        elif key == b'H':   cx = 0
        elif key == b'F':   cx = len(lines[cy])
        elif key == b'3~':                                    # Delete
            row = lines[cy]
            if cx < len(row):
                lines[cy] = row[:cx] + row[cx+1:]; dirty = True
            elif cy < len(lines)-1:
                lines[cy] += lines.pop(cy+1);     dirty = True

    # bare ESC — ignore
    elif raw == b'\x1b':
        pass

    # Enter
    elif raw in (b'\r', b'\n'):
        row = lines[cy]
        lines[cy] = row[:cx]; lines.insert(cy+1, row[cx:])
        cy += 1; cx = 0; dirty = True

    # Backspace
    elif raw in (b'\x7f', b'\x08'):
        if cx > 0:
            lines[cy] = lines[cy][:cx-1] + lines[cy][cx:]; cx -= 1; dirty = True
        elif cy > 0:
            cx = len(lines[cy-1]); lines[cy-1] += lines.pop(cy); cy -= 1; dirty = True

    # printable text
    else:
        ch = raw.decode('utf-8', errors='ignore')
        if ch and all(ord(c) >= 32 for c in ch):
            lines[cy] = lines[cy][:cx] + ch + lines[cy][cx:]
            cx += len(ch); dirty = True

    # keep scroll in sync with cursor
    if cy < scroll:               scroll = cy
    if cy >= scroll + text_rows:  scroll = cy - text_rows + 1
    scroll = max(0, scroll)

    render()

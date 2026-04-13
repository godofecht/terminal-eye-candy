#!/usr/bin/env python3
"""terminal-eye-candy — CLAUDE.md editor  (click, type, Ctrl-S to save)"""
import os, sys, signal, time, termios, tty, select

CLAUDE_MD = os.path.expanduser('~/terminal-eye-candy/CLAUDE.md')
MARGIN    = 4   # left gutter width (line numbers + space)

# ── terminal setup ────────────────────────────────────────────────────────────

old_tty = None
fd      = sys.stdin.fileno()

def term_restore():
    if old_tty:
        try: termios.tcsetattr(fd, termios.TCSADRAIN, old_tty)
        except Exception: pass

def cleanup(*_):
    sys.stdout.write('\033[?1000l\033[?1006l')   # disable mouse
    sys.stdout.write('\033[0m\033[?25h\033[2J\033[H')
    sys.stdout.flush()
    term_restore()
    sys.exit(0)

signal.signal(signal.SIGINT,  cleanup)
signal.signal(signal.SIGTERM, cleanup)

old_tty = termios.tcgetattr(fd)
tty.setraw(fd)
sys.stdout.write('\033[?25l')                    # hide cursor while drawing
sys.stdout.write('\033[?1000h\033[?1006h')       # enable SGR mouse reporting
sys.stdout.flush()

# ── file I/O ──────────────────────────────────────────────────────────────────

def load():
    try:
        return open(CLAUDE_MD).read().split('\n')
    except FileNotFoundError:
        return ['']

def save(lines):
    os.makedirs(os.path.dirname(CLAUDE_MD), exist_ok=True)
    open(CLAUDE_MD, 'w').write('\n'.join(lines))

# ── state ─────────────────────────────────────────────────────────────────────

lines    = load()
cx, cy   = 0, 0        # cursor col, row  (into lines[])
scroll   = 0           # first visible line
dirty    = False
status   = 'Ctrl-S save  Ctrl-Q quit  click to move cursor'
status_t = time.time()

def clamp_cx():
    global cx
    cx = max(0, min(cx, len(lines[cy])))

# ── input reader ──────────────────────────────────────────────────────────────

def read_input():
    """Return one logical key/event or None."""
    r, _, _ = select.select([sys.stdin], [], [], 0.05)
    if not r:
        return None
    raw = os.read(fd, 128)
    return raw

def parse_sgr_mouse(seq):
    """Parse ESC[<Cb;Cx;CyM  →  (btn, col-1, row-1, press)."""
    # seq = b'<Cb;Cx;CyM' or b'<...m'
    try:
        s    = seq.decode('ascii', errors='ignore')
        press= s.endswith('M')
        s    = s.lstrip('<').rstrip('Mm')
        b, x, y = (int(v) for v in s.split(';'))
        return b, x-1, y-1, press
    except Exception:
        return None

# ── renderer ──────────────────────────────────────────────────────────────────

def colorize(line):
    if line.startswith('# '):   return '\033[97;1m'
    if line.startswith('## '):  return '\033[96;1m'
    if line.startswith('### '): return '\033[93m'
    if line.startswith('- ') or line.startswith('* '): return '\033[37m'
    if line.startswith('```'):  return '\033[32m'
    return '\033[37m'

def render():
    try: cols, rows = os.get_terminal_size()
    except Exception: cols, rows = 80, 24

    text_rows = rows - 2   # reserve top bar + bottom status

    out = '\033[H'   # move to top-left (no clear — avoids flicker)

    # ── header ────────────────────────────────────────────────────────────────
    fname   = os.path.basename(CLAUDE_MD)
    marker  = ' [+]' if dirty else ''
    title   = f'  CLAUDE.md editor — {fname}{marker}'
    hint    = '  Ctrl-S save  Ctrl-Q quit'
    gap     = cols - len(title) - len(hint)
    bar     = title + ' '*max(0,gap) + hint
    out    += f'\033[7m{bar[:cols]:<{cols}}\033[0m\n'

    # ── content ───────────────────────────────────────────────────────────────
    visible = lines[scroll : scroll + text_rows]
    for i, line in enumerate(visible):
        abs_row  = scroll + i
        lnum     = f'{abs_row+1:>{MARGIN-1}} '
        lnum_col = '\033[93m' if abs_row == cy else '\033[90m'

        # truncate to fit
        text_w   = cols - MARGIN
        disp     = line[:text_w]

        col_code = colorize(disp)

        if abs_row == cy:
            # draw cursor inside this line
            safe_cx = min(cx, len(disp))
            before  = disp[:safe_cx]
            cur_ch  = disp[safe_cx] if safe_cx < len(disp) else ' '
            after   = disp[safe_cx+1:] if safe_cx < len(disp) else ''
            row_out = (col_code + before +
                       '\033[7m' + cur_ch + '\033[27m' +
                       col_code + after)
        else:
            row_out = col_code + disp

        out += f'{lnum_col}{lnum}\033[0m{row_out}\033[0m\033[K\n'

    # pad remaining rows
    for _ in range(text_rows - len(visible)):
        out += '\033[90m~\033[0m\033[K\n'

    # ── status bar ────────────────────────────────────────────────────────────
    pos_info = f'Ln {cy+1}/{len(lines)}  Col {cx+1}'
    msg      = status if time.time() - status_t < 4 else ''
    gap2     = cols - len(pos_info) - len(msg) - 2
    sbar     = f' {msg}{" "*max(0,gap2)}{pos_info} '
    out     += f'\033[7m{sbar[:cols]:<{cols}}\033[0m'

    sys.stdout.write(out)
    sys.stdout.flush()

# ── main loop ─────────────────────────────────────────────────────────────────

def set_status(msg):
    global status, status_t
    status  = msg
    status_t = time.time()

while True:
    try: cols, rows = os.get_terminal_size()
    except Exception: cols, rows = 80, 24
    text_rows = rows - 2

    render()

    raw = read_input()
    if raw is None:
        continue

    # ── parse escape sequences ────────────────────────────────────────────────
    if raw == b'\x11':           # Ctrl-Q
        cleanup()

    elif raw == b'\x13':         # Ctrl-S
        save(lines)
        dirty = False
        set_status('Saved!')

    elif raw.startswith(b'\x1b[<'):   # SGR mouse
        parsed = parse_sgr_mouse(raw[2:])
        if parsed:
            btn, mx, my, press = parsed
            if press and btn == 0:   # left click
                clicked_row = scroll + my - 1   # -1 for header bar
                if 0 <= clicked_row < len(lines):
                    cy = clicked_row
                    cx = max(0, min(mx - MARGIN, len(lines[cy])))

    elif raw.startswith(b'\x1b['):
        key = raw[2:]
        if   key == b'A':   # up
            if cy > 0: cy -= 1; clamp_cx()
            if cy < scroll: scroll = cy
        elif key == b'B':   # down
            if cy < len(lines)-1: cy += 1; clamp_cx()
            if cy >= scroll + text_rows: scroll = cy - text_rows + 1
        elif key == b'C':   # right
            if cx < len(lines[cy]): cx += 1
            elif cy < len(lines)-1: cy += 1; cx = 0
        elif key == b'D':   # left
            if cx > 0: cx -= 1
            elif cy > 0: cy -= 1; cx = len(lines[cy])
        elif key == b'H':   cx = 0                          # Home
        elif key == b'F':   cx = len(lines[cy])             # End
        elif key == b'5~':  scroll = max(0, scroll-text_rows); cy = max(cy-text_rows, 0)  # PgUp
        elif key == b'6~':  scroll = min(len(lines)-1, scroll+text_rows); cy = min(cy+text_rows, len(lines)-1)  # PgDn
        elif key == b'3~':  # Delete
            row = lines[cy]
            if cx < len(row):
                lines[cy] = row[:cx] + row[cx+1:]
            elif cy < len(lines)-1:
                lines[cy] = row + lines.pop(cy+1)
            dirty = True

    elif raw == b'\x1b':   pass   # bare ESC — ignore

    elif raw in (b'\r', b'\n'):   # Enter
        row = lines[cy]
        lines[cy]    = row[:cx]
        lines.insert(cy+1, row[cx:])
        cy += 1; cx = 0
        if cy >= scroll + text_rows: scroll += 1
        dirty = True

    elif raw in (b'\x7f', b'\x08'):  # Backspace
        if cx > 0:
            lines[cy] = lines[cy][:cx-1] + lines[cy][cx:]
            cx -= 1
        elif cy > 0:
            cx = len(lines[cy-1])
            lines[cy-1] += lines.pop(cy)
            cy -= 1
            if cy < scroll: scroll = cy
        dirty = True

    else:
        ch = raw.decode('utf-8', errors='ignore')
        if ch and all(ord(c) >= 32 for c in ch):
            lines[cy] = lines[cy][:cx] + ch + lines[cy][cx:]
            cx += len(ch)
            dirty = True

    # keep scroll in sync
    if cy < scroll: scroll = cy
    if cy >= scroll + text_rows: scroll = cy - text_rows + 1
    scroll = max(0, scroll)

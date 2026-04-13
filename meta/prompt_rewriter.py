#!/usr/bin/env python3
"""Pane 3 — Interactive system prompt editor (AI rewrites its own instructions)"""
import os, sys, signal, time, termios, tty, select, textwrap, datetime

CLAUDE_MD = os.path.expanduser('~/.claude/CLAUDE.md')

old_tty = None
def cleanup(*a):
    if old_tty:
        try: termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_tty)
        except Exception: pass
    sys.stdout.write('\033[0m\033[?25h')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

fd = sys.stdin.fileno()
old_tty = termios.tcgetattr(fd)
tty.setraw(fd)

def read_key():
    r, _, _ = select.select([sys.stdin], [], [], 0.1)
    if not r: return None
    ch = os.read(fd, 1)
    if ch == b'\x1b':
        r2, _, _ = select.select([sys.stdin], [], [], 0.05)
        if r2:
            ch2 = os.read(fd, 1)
            if ch2 == b'[':
                return 'ESC[' + os.read(fd, 1).decode('ascii', errors='?')
    return ch.decode('utf-8', errors='ignore')

def read_md():
    if not os.path.exists(CLAUDE_MD): return ''
    try: return open(CLAUDE_MD).read()
    except Exception: return ''

def write_md(content):
    os.makedirs(os.path.dirname(CLAUDE_MD), exist_ok=True)
    open(CLAUDE_MD, 'w').write(content)

def read_line_raw(prompt_str):
    """Read a line of input with raw terminal."""
    termios.tcsetattr(fd, termios.TCSADRAIN, old_tty)
    sys.stdout.write('\033[?25h')
    sys.stdout.flush()
    try:
        line = input(prompt_str)
    except (EOFError, KeyboardInterrupt):
        line = ''
    tty.setraw(fd)
    sys.stdout.write('\033[?25l')
    return line

MODE_VIEW   = 'view'
MODE_ADD    = 'add'
MODE_CONFIRM= 'confirm'
mode        = MODE_VIEW
pending_rule= ''
status_msg  = ''
status_time = 0.0

frame = 0

while True:
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 80, 24

    content = read_md()
    bline   = '─' * cols
    exists  = os.path.exists(CLAUDE_MD)

    # ── render ──────────────────────────────────────────────────────────────
    out = '\033[H\033[2J'
    out += f'\033[36m{bline}\033[0m\n'
    out += f'\033[91;1m  PROMPT REWRITER  \033[90m{CLAUDE_MD}\033[0m\n'
    out += f'\033[36m{bline}\033[0m\n'

    if mode == MODE_VIEW:
        lines  = content.splitlines() if content else []
        avail  = rows - 9
        out   += '\n'

        if not lines:
            out += '  \033[90m(no CLAUDE.md — press \033[97ma\033[90m to create one)\033[0m\n'
        else:
            for line in lines[:avail]:
                if line.startswith('#'):
                    out += f'  \033[96m{line[:cols-4]}\033[0m\n'
                elif line.startswith('- ') or line.startswith('* '):
                    out += f'  \033[90m·\033[0m \033[37m{line[2:cols-4]}\033[0m\n'
                else:
                    out += f'  \033[90m{line[:cols-4]}\033[0m\n'
            if len(lines) > avail:
                out += f'  \033[90m… +{len(lines)-avail} lines\033[0m\n'

        out += '\n'
        out += f'  \033[36m{bline[:cols-2]}\033[0m\n'
        if status_msg and time.time() - status_time < 3.0:
            out += f'  \033[92m✓ {status_msg}\033[0m\n'
        else:
            out += f'  \033[90ma\033[37m add rule   \033[90mx\033[37m clear all   \033[90mq\033[37m quit\033[0m\n'

    elif mode == MODE_ADD:
        out += '\n'
        out += '  \033[93mAdd a new instruction rule:\033[0m\n'
        out += '  \033[90m(this will be injected into the AI\'s system prompt)\033[0m\n\n'
        out += f'  \033[97m> {pending_rule}\033[93m_\033[0m\n\n'
        out += '  \033[90mType the rule, Enter to confirm, Esc to cancel\033[0m\n'

    elif mode == MODE_CONFIRM:
        out += '\n'
        out += '  \033[93mAbout to append to CLAUDE.md:\033[0m\n\n'
        for ln in textwrap.wrap(pending_rule, cols-6):
            out += f'  \033[92m+ {ln}\033[0m\n'
        out += '\n'
        out += '  \033[90mEnter\033[37m to save   \033[90mEsc\033[37m to cancel\033[0m\n'

    sys.stdout.write(out)
    sys.stdout.flush()

    # ── input ───────────────────────────────────────────────────────────────
    key = read_key()
    if key is None:
        frame += 1
        continue

    if mode == MODE_VIEW:
        if key in ('q', '\x03', '\x04'):
            cleanup()
        elif key == 'a':
            mode = MODE_ADD
            pending_rule = ''
        elif key == 'x':
            if exists:
                write_md('')
                status_msg  = 'Cleared CLAUDE.md'
                status_time = time.time()

    elif mode == MODE_ADD:
        if key == '\x1b' or key == '\x03':
            mode = MODE_VIEW
            pending_rule = ''
        elif key in ('\r', '\n'):
            if pending_rule.strip():
                mode = MODE_CONFIRM
        elif key == '\x7f':  # backspace
            pending_rule = pending_rule[:-1]
        elif key and len(key) == 1 and ord(key) >= 32:
            pending_rule += key

    elif mode == MODE_CONFIRM:
        if key in ('\r', '\n'):
            # Append rule to CLAUDE.md
            ts   = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            prev = read_md()
            if not prev.strip():
                new_content = f'# Claude Instructions\n\n- {pending_rule}\n'
            else:
                new_content = prev.rstrip('\n') + f'\n- {pending_rule}\n'
            write_md(new_content)
            status_msg  = f'Rule saved → CLAUDE.md'
            status_time = time.time()
            mode = MODE_VIEW
            pending_rule = ''
        elif key == '\x1b':
            mode = MODE_VIEW
            pending_rule = ''

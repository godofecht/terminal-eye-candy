#!/usr/bin/env python3
"""Pane 4 — Live diff watcher: shows every change to CLAUDE.md in real time"""
import os, sys, signal, time, hashlib, difflib, datetime

def cleanup(*a):
    sys.stdout.write('\033[0m\033[?25h')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)
sys.stdout.write('\033[?25l')

CLAUDE_MD = os.path.expanduser('~/terminal-eye-candy/CLAUDE.md')
history   = []   # list of (timestamp, old_lines, new_lines)
prev_text = None
prev_hash = None

def read_md():
    if not os.path.exists(CLAUDE_MD): return ''
    try: return open(CLAUDE_MD).read()
    except Exception: return ''

frame = 0
while True:
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 80, 24

    cur_text = read_md()
    cur_hash = hashlib.md5(cur_text.encode()).hexdigest()

    if prev_hash is not None and cur_hash != prev_hash:
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        history.append((ts, (prev_text or '').splitlines(), cur_text.splitlines()))

    prev_text = cur_text
    prev_hash = cur_hash

    bline = '─' * cols
    out   = '\033[H\033[2J'
    out  += f'\033[36m{bline}\033[0m\n'
    out  += f'\033[91;1m  LIVE DIFF  \033[90mCLAUDE.md changes\033[0m\n'
    out  += f'\033[36m{bline}\033[0m\n'

    if not history:
        out += '\n'
        out += '  \033[90mWaiting for changes to CLAUDE.md…\033[0m\n'
        out += '  \033[90mUse the Prompt Rewriter pane to add rules.\033[0m\n\n'

        # Show current state anyway
        if cur_text:
            out += f'  \033[36m{bline[:cols-2]}\033[0m\n'
            out += '  \033[90mCurrent content:\033[0m\n'
            avail = rows - 10
            for line in cur_text.splitlines()[:avail]:
                out += f'  \033[37m{line[:cols-4]}\033[0m\n'
    else:
        avail = rows - 5
        lines_used = 0
        # Show most recent diff(s), newest first
        for ts, old_lines, new_lines in reversed(history):
            if lines_used >= avail:
                break
            diff = list(difflib.unified_diff(old_lines, new_lines,
                                             fromfile='before', tofile='after', lineterm=''))
            out += f'\n  \033[90m@ {ts}\033[0m\n'
            lines_used += 2
            for dline in diff:
                if lines_used >= avail:
                    break
                if dline.startswith('+++') or dline.startswith('---') or dline.startswith('@@'):
                    out += f'  \033[36m{dline[:cols-4]}\033[0m\n'
                elif dline.startswith('+'):
                    out += f'  \033[92m{dline[:cols-4]}\033[0m\n'
                elif dline.startswith('-'):
                    out += f'  \033[91m{dline[:cols-4]}\033[0m\n'
                else:
                    out += f'  \033[90m{dline[:cols-4]}\033[0m\n'
                lines_used += 1
            out += f'  \033[36m{bline[:cols-2]}\033[0m\n'
            lines_used += 1

    sys.stdout.write(out)
    sys.stdout.flush()
    frame += 1
    time.sleep(1)

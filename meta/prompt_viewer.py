#!/usr/bin/env python3
"""Pane 1 — Live system prompt viewer (CLAUDE.md watcher)"""
import os, sys, signal, time, hashlib

def cleanup(*a):
    sys.stdout.write('\033[0m\033[?25h')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)
sys.stdout.write('\033[?25l')

PROJECT_ROOT = os.path.expanduser('~/terminal-eye-candy')
PATHS = [
    os.path.join(PROJECT_ROOT, 'CLAUDE.md'),
    os.path.join(PROJECT_ROOT, '.claude/CLAUDE.md'),
    os.path.expanduser('~/.claude/CLAUDE.md'),
]

def find_claude_md():
    for p in PATHS:
        if os.path.exists(p):
            return p
    return None

def colorize(line):
    if line.startswith('# '):
        return f'\033[97;1m{line}\033[0m'
    if line.startswith('## '):
        return f'\033[96;1m{line}\033[0m'
    if line.startswith('### '):
        return f'\033[93m{line}\033[0m'
    if line.startswith('- ') or line.startswith('* '):
        bullet = line[0:2]
        rest   = line[2:]
        return f'\033[90m{bullet}\033[0m\033[37m{rest}\033[0m'
    if line.startswith('```'):
        return f'\033[32m{line}\033[0m'
    if line.strip() == '':
        return ''
    return f'\033[37m{line}\033[0m'

last_hash = ''

while True:
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 80, 24

    path = find_claude_md()
    bar  = '─' * cols

    if not path:
        out  = '\033[H\033[2J'
        out += f'\033[36m{bar}\033[0m\n'
        out += f'\033[93m  SYSTEM PROMPT  \033[90m(CLAUDE.md)\033[0m\n'
        out += f'\033[36m{bar}\033[0m\n'
        out += '\n'
        out += '\033[90m  No CLAUDE.md found.\033[0m\n'
        out += '\033[90m  Create ~/.claude/CLAUDE.md to set AI instructions.\033[0m\n'
        out += '\n'
        out += f'\033[90m  Searched:\033[0m\n'
        for p in PATHS:
            out += f'\033[90m    {p}\033[0m\n'
        sys.stdout.write(out)
        sys.stdout.flush()
        time.sleep(2)
        continue

    try:
        content = open(path).read()
    except Exception:
        time.sleep(1)
        continue

    h = hashlib.md5(content.encode()).hexdigest()
    if h == last_hash:
        time.sleep(1)
        continue
    last_hash = h

    lines = content.splitlines()
    short = os.path.relpath(path, os.path.expanduser('~'))

    out  = '\033[H\033[2J'
    out += f'\033[36m{bar}\033[0m\n'
    out += f'\033[93;1m  SYSTEM PROMPT  \033[90m~/{short}\033[0m\n'
    out += f'\033[36m{bar}\033[0m\n'

    avail = rows - 4
    for line in lines[:avail]:
        out += '  ' + colorize(line) + '\n'

    if len(lines) > avail:
        out += f'\033[90m  … +{len(lines)-avail} more lines\033[0m\n'

    sys.stdout.write(out)
    sys.stdout.flush()
    time.sleep(1)

#!/usr/bin/env python3
"""Pane 2 — Context window visualizer"""
import os, sys, signal, time, math, glob, datetime

def cleanup(*a):
    sys.stdout.write('\033[0m\033[?25h')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)
sys.stdout.write('\033[?25l')

CLAUDE_DIR = os.path.expanduser('~/.claude')
MEM_DIR    = os.path.join(CLAUDE_DIR, 'projects')

CLAUDE_LIMIT = 200_000   # ~200k token context window
CHARS_PER_TOK = 3.5

def bar(filled, total, width, fg='\033[92m', bg='\033[90m', empty='░', full='█'):
    n = int(filled / total * width) if total else 0
    n = max(0, min(n, width))
    return fg + full * n + bg + empty * (width - n) + '\033[0m'

def count_tokens(path):
    try:
        return int(os.path.getsize(path) / CHARS_PER_TOK)
    except Exception:
        return 0

def fmt_k(n):
    return f'{n/1000:.1f}k' if n >= 1000 else str(n)

frame = 0
while True:
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 80, 24

    bar_w = max(10, cols - 24)
    bline = '─' * cols

    # Gather memory files
    mem_files = []
    for pat in [os.path.join(MEM_DIR, '**', 'memory', '*.md'),
                os.path.join(CLAUDE_DIR, 'memory', '*.md')]:
        mem_files.extend(glob.glob(pat, recursive=True))

    # CLAUDE.md files
    claude_files = []
    for p in [os.path.expanduser('~/.claude/CLAUDE.md'),
              os.path.join(os.getcwd(), 'CLAUDE.md')]:
        if os.path.exists(p):
            claude_files.append(p)

    total_toks  = sum(count_tokens(f) for f in claude_files + mem_files)
    sys_toks    = sum(count_tokens(f) for f in claude_files)
    mem_toks    = sum(count_tokens(f) for f in mem_files)
    ctx_pct     = total_toks / CLAUDE_LIMIT

    # Animated usage pulse
    pulse = 0.5 + 0.5 * math.sin(frame * 0.15)
    pct_col = '\033[92m' if ctx_pct < 0.5 else ('\033[93m' if ctx_pct < 0.8 else '\033[91m')

    out  = '\033[H\033[2J'
    out += f'\033[36m{bline}\033[0m\n'
    out += f'\033[93;1m  CONTEXT WINDOW  \033[90m~200k token budget\033[0m\n'
    out += f'\033[36m{bline}\033[0m\n\n'

    out += f'  \033[37mTotal loaded   \033[0m{pct_col}{fmt_k(total_toks)} tok\033[0m\n'
    out += f'  {bar(total_toks, CLAUDE_LIMIT, bar_w, pct_col)} {pct_col}{ctx_pct*100:.1f}%\033[0m\n\n'

    c_cyan, c_mag = '\033[96m', '\033[95m'
    n_cf = len(claude_files); s_cf = 's' if n_cf != 1 else ''
    n_mf = len(mem_files);    s_mf = 's' if n_mf != 1 else ''
    out += f'  \033[37mSystem prompt  \033[0m{c_cyan}{fmt_k(sys_toks)} tok\033[0m\n'
    out += f'  {bar(sys_toks, CLAUDE_LIMIT, bar_w, c_cyan)} \033[90m({n_cf} file{s_cf})\033[0m\n\n'

    out += f'  \033[37mAuto-memory    \033[0m{c_mag}{fmt_k(mem_toks)} tok\033[0m\n'
    out += f'  {bar(mem_toks, CLAUDE_LIMIT, bar_w, c_mag)} \033[90m({n_mf} file{s_mf})\033[0m\n\n'

    out += f'  \033[36m{bline[:cols-2]}\033[0m\n'
    out += f'  \033[37mMemory files:\033[0m\n'
    shown = 0
    avail = rows - 16
    for f in sorted(mem_files, key=os.path.getmtime, reverse=True)[:avail]:
        name  = os.path.basename(f)
        toks  = count_tokens(f)
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f)).strftime('%m/%d %H:%M')
        out += f'  \033[90m{mtime}  \033[95m{name:<30}\033[90m {fmt_k(toks)} tok\033[0m\n'
        shown += 1
    if not mem_files:
        out += '  \033[90m  (none)\033[0m\n'

    sys.stdout.write(out)
    sys.stdout.flush()
    frame += 1
    time.sleep(2)

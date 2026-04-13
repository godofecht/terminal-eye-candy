#!/usr/bin/env python3
import subprocess, time, sys, os, signal, math, termios, tty, select

old_tty = None

def cleanup(*a):
    if old_tty is not None:
        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_tty)
        except Exception:
            pass
    sys.stdout.write('\033[0m\033[?25h')
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

sys.stdout.write('\033[?25l')

fd = sys.stdin.fileno()
old_tty = termios.tcgetattr(fd)
tty.setraw(fd)

def read_key():
    r, _, _ = select.select([sys.stdin], [], [], 0)
    if not r:
        return None
    ch = os.read(fd, 1)
    if ch == b'\x1b':
        r2, _, _ = select.select([sys.stdin], [], [], 0.05)
        if r2:
            ch2 = os.read(fd, 1)
            if ch2 == b'[':
                ch3 = os.read(fd, 1)
                return 'ESC[' + ch3.decode('ascii', errors='?')
    return ch.decode('utf-8', errors='ignore')

def run_as(src):
    try:
        r = subprocess.run(['osascript','-e',src], capture_output=True, text=True, timeout=4)
        return r.stdout.strip()
    except Exception:
        return ''

APPS = {
    'Spotify': {
        'get': '''
            tell application "System Events"
                if exists process "Spotify" then
                    tell application "Spotify"
                        set s to player state
                        if s is playing or s is paused then
                            return name of current track & "||" & artist of current track & "||" & (player position as integer) & "||" & (duration of current track / 1000 as integer) & "||" & (s as string)
                        end if
                    end tell
                end if
            end tell''',
        'seek': lambda p: f'tell application "Spotify" to set player position to {p}',
        'pp':   'tell application "Spotify" to playpause',
        'vol+': 'tell application "Spotify" to set sound volume to min(sound volume + 10, 100)',
        'vol-': 'tell application "Spotify" to set sound volume to max(sound volume - 10, 0)',
    },
    'Music': {
        'get': '''
            tell application "System Events"
                if exists process "Music" then
                    tell application "Music"
                        set s to player state
                        if s is playing or s is paused then
                            return name of current track & "||" & artist of current track & "||" & (player position as integer) & "||" & (duration of current track as integer) & "||" & (s as string)
                        end if
                    end tell
                end if
            end tell''',
        'seek': lambda p: f'tell application "Music" to set player position to {p}',
        'pp':   'tell application "Music" to playpause',
        'vol+': 'tell application "Music" to set sound volume to min(sound volume + 10, 100)',
        'vol-': 'tell application "Music" to set sound volume to max(sound volume - 10, 0)',
    },
}

def get_track():
    for name, cfg in APPS.items():
        out = run_as(cfg['get'])
        if out:
            p = out.split('||')
            return {
                'app':    name,
                'title':  p[0] if len(p)>0 else '?',
                'artist': p[1] if len(p)>1 else '?',
                'pos':    int(p[2]) if len(p)>2 and p[2].strip().lstrip('-').isdigit() else 0,
                'dur':    int(p[3]) if len(p)>3 and p[3].strip().lstrip('-').isdigit() else 0,
                'state':  p[4].strip() if len(p)>4 else 'unknown',
            }
    return None

def fmt(s):
    s = max(0, int(s))
    return f'{s//60}:{s%60:02d}'

frame     = 0
last_get  = 0
track     = None
local_pos = 0.0
TICK      = 0.1

while True:
    now = time.time()

    # Refresh from source every ~1 s
    if now - last_get >= 1.0:
        t = get_track()
        if t:
            if track is None or t['title'] != track['title']:
                local_pos = t['pos']   # new track: hard-sync
            track = t
        else:
            track = None
        last_get = now

    # Advance local position smoothly while playing
    if track and track['state'] == 'playing':
        local_pos = min(local_pos + TICK, track['dur'])

    # Input
    key = read_key()
    if key in ('q', '\x03', '\x04'):
        cleanup()
    elif key and track:
        app = track['app']
        cfg = APPS[app]
        if key == 'ESC[C':              # →  seek +5s
            local_pos = min(local_pos + 5, track['dur'])
            run_as(cfg['seek'](int(local_pos)))
        elif key == 'ESC[D':            # ←  seek -5s
            local_pos = max(local_pos - 5, 0)
            run_as(cfg['seek'](int(local_pos)))
        elif key == 'ESC[A':            # ↑  vol+
            run_as(cfg['vol+'])
        elif key == 'ESC[B':            # ↓  vol-
            run_as(cfg['vol-'])
        elif key == ' ':                # space  play/pause
            run_as(cfg['pp'])
            track['state'] = 'paused' if track['state'] == 'playing' else 'playing'

    # Render
    try:
        cols, rows = os.get_terminal_size()
    except Exception:
        cols, rows = 80, 6

    bar  = '\033[36m' + '─' * cols + '\033[0m'
    out  = '\033[H\033[2J'

    if track:
        playing = track['state'] == 'playing'

        # Equalizer
        EQ = '_.-:=|*#'
        eq = ''
        for i in range(10):
            if playing:
                h = int((math.sin(frame * 0.4 + i * 0.9) + 1) * 3.5)
                eq += '\033[92m' + EQ[h] + '\033[0m'
            else:
                eq += '\033[90m' + '-' + '\033[0m'

        icon   = '>' if playing else '|'
        title  = track['title'][:cols-18]
        artist = track['artist'][:cols-6]
        dur    = track['dur']
        pos    = local_pos

        # Scrub bar
        if dur > 0:
            pct   = min(pos / dur, 1.0)
            pw    = max(0, cols - 16)
            fill  = int(pct * pw)
            scrub = (f'\033[90m{fmt(pos)}\033[0m '
                     f'\033[92m{"#"*fill}\033[90m{"."*(pw-fill)}\033[0m'
                     f' \033[90m{fmt(dur)}\033[0m')
        else:
            scrub = ''

        hint = '\033[90m<- -> seek  up dn vol  space play/pause  q quit\033[0m'

        out += bar + '\n'
        out += f' {eq}  \033[97;1m{icon} {title}\033[0m  \033[90m[{track["app"]}]\033[0m\n'
        out += f'            \033[93m{artist}\033[0m\n'
        if scrub:
            out += f' {scrub}\n'
        out += f' {hint}\n'
        out += bar
    else:
        out += bar + '\n'
        out += ' \033[90m♪  nothing playing — open Spotify or Apple Music\033[0m\n'
        out += bar

    sys.stdout.write(out)
    sys.stdout.flush()
    frame += 1
    time.sleep(TICK)

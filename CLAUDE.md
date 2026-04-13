# terminal-eye-candy

A library of terminal widgets and animations for WezTerm (and any terminal emulator).

## Structure

- `animations/` — full-screen visual animations (fire, matrix rain, starfield, plasma, Game of Life)
- `widgets/` — interactive terminal widgets (clock, now-playing with FTXUI)
- `meta/` — AI meta-dashboard: live system prompt viewer, context window monitor, prompt rewriter, live diff

## Running animations

```bash
python3 animations/starfield.py
python3 animations/fire.py
python3 animations/matrix_rain.py
python3 animations/plasma.py
python3 animations/game_of_life.py
```

Ctrl-C cleanly exits any animation.

## Running widgets

```bash
python3 widgets/clock.py
python3 widgets/nowplaying/nowplaying.py   # Spotify / Apple Music — macOS only

# C++ FTXUI now-playing (build first):
cd widgets/nowplaying/ftxui && cmake -B build && cmake --build build -j4
./widgets/nowplaying/ftxui/build/nowplaying
```

## Running the meta dashboard (4-pane AI introspection)

Open four WezTerm panes and run one script per pane:

| Pane | Script | What it shows |
|------|--------|---------------|
| 1 | `meta/prompt_viewer.py` | Live view of `~/.claude/CLAUDE.md` with syntax highlighting |
| 2 | `meta/context_window.py` | Token budget bar — system prompt + auto-memory usage |
| 3 | `meta/prompt_rewriter.py` | Interactive editor: press `a` to add a rule, `x` to clear |
| 4 | `meta/prompt_diff.py` | Live unified diff whenever CLAUDE.md changes |

## Coding conventions

- Pure Python 3 stdlib only (no pip dependencies) for all animations and Python widgets
- ANSI escape codes for color — 24-bit truecolor where possible, 256-color fallback
- Always restore terminal on exit: `\033[0m\033[?25h` + `sys.exit(0)` in signal handlers
- C++ widgets use FTXUI v5.0.0 via CMake FetchContent
- macOS-only features (osascript, AppleScript) are isolated to `widgets/nowplaying/`

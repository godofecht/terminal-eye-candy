# terminal-eye-candy

Terminal animations and widgets in pure Python 3. No dependencies, no install
step. Every script runs on its own:

```
python3 animations/starfield.py
```

Press `Ctrl-C` to quit. Each script restores the cursor and resets colours on
exit, through a signal handler, so a terminal is never left in a broken state.

Requires Python 3 and a terminal with 24-bit colour and ANSI escape support.

## Animations

| Script | What it draws |
| --- | --- |
| `animations/starfield.py` | 3D starfield with perspective projection |
| `animations/matrix_rain.py` | Falling glyph columns |
| `animations/fire.py` | Cellular fire simulation |
| `animations/plasma.py` | Sine-field plasma |
| `animations/game_of_life.py` | Conway's Game of Life |

## Widgets

| Script | What it does |
| --- | --- |
| `widgets/clock.py` | Block-digit clock |
| `widgets/nowplaying/nowplaying.py` | Current macOS track, read over AppleScript |

`widgets/nowplaying/ftxui/` holds a C++ version of the now-playing widget,
built with FTXUI v5.0.0 via CMake FetchContent:

```
cmake -B build widgets/nowplaying/ftxui && cmake --build build
```

## Meta panes

A set of panes that watch and edit the instructions given to a coding agent.
They are written to sit side by side in a tiled terminal.

| Script | Pane |
| --- | --- |
| `meta/prompt_viewer.py` | Live view of `CLAUDE.md` |
| `meta/context_window.py` | Context window usage |
| `meta/prompt_rewriter.py` | Interactive editor for the instructions |
| `meta/prompt_diff.py` | Every change to `CLAUDE.md`, as it happens |
| `meta/editor.py` | Click-to-edit `CLAUDE.md` |

Split them into panes with WezTerm:

```
wezterm cli split-pane -- python3 meta/prompt_viewer.py
```

## Licence

MIT. See [LICENSE](LICENSE).

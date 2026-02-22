# Fit Coder

`fit-coder` is a simple terminal app that reminds programmers to exercise during long work sessions.

## What it does

- Asks how many exercises you want in your routine
- Asks how long each break should be (minutes)
- Collects exercise names
- Runs an ongoing timer and rotates through exercises
- Rings a stronger alarm when break time is over (system sound first, terminal bell fallback)
- Prompts you to enter reps after each exercise round
- Tracks and displays session stats (total reps + per-exercise totals)
- Supports an optional mini movable widget window
- Shows running countdown timer + progress bar
- Shows current status (what is next)
- Shows live stats (reps, rounds, per-exercise totals)
- Allows adjustable size by dragging edges or quick `S/M/L` buttons

The app runs continuously until you stop it with `Ctrl+C`.

## Run

```bash
python3 fit_coder.py
```

## Install As Global Command

If `~/.local/bin` is on your `PATH` (it is on your machine), create a symlink:

```bash
ln -sf "$(pwd)/fit_coder.py" ~/.local/bin/fitcoder
```

Then run from anywhere:

```bash
fitcoder
```

## Widget Notes

- The widget uses Python `tkinter` (standard library).
- If `tkinter` or a GUI display is unavailable, the app automatically falls back to CLI-only mode.
- Use `Pin` in the widget header to keep it always on top or allow normal stacking.

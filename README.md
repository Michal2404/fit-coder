# Fit Coder

`fit-coder` is a simple terminal app that reminds programmers to exercise during long work sessions.

## What it does

- Asks how many exercises you want in your routine
- Asks how long each break should be (minutes)
- Collects exercise names
- Runs an ongoing timer and rotates through exercises
- Prompts you to enter reps after each exercise round
- Tracks and displays session stats (total reps + per-exercise totals)

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

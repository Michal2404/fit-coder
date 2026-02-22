# Fit Coder

`fit-coder` is a simple app that reminds programmers to exercise during long work sessions.

## What it does

- Opens a movable widget window when you run `fitcoder`
- Lets you configure everything inside the widget
- Set number of exercises
- Set break length (minutes)
- Set exercise names
- Runs the timer and rotates through exercises
- Rings a stronger alarm when break time is over (system sound first, terminal bell fallback)
- Click anywhere in the widget to mute an active alarm
- Lets you log reps directly in the widget when the break ends
- Tracks and displays session stats (total reps + per-exercise totals)
- Auto-shrinks during breaks to a compact timer-only widget
- Keeps the widget compact during both timer and reps-entry phases
- Compact mode shows timer, progress bar, `Next:` exercise, and a `View stats` button
- Compact mode also includes a `Pause/Resume` button for the timer
- During reps-entry phase, compact mode adds only the reps input controls
- Window size can be adjusted by dragging edges

The app runs until you close it.

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
- If `tkinter` or a GUI display is unavailable, the app automatically falls back to CLI mode.
- Use `Pin` in the widget header to keep it always on top or allow normal stacking.

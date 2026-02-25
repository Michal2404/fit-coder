# Fit Coder

`fit-coder` is a small app that reminds programmers to exercise during long work sessions.

## Features

- Routine setup in the widget (exercise count, names, break length)
- Compact movable timer widget with progress bar and `Next` exercise info
- Reps logging after each break and per-exercise stats table
- Alarm when break time is over, with click-to-mute support
- CLI fallback when `tkinter` or GUI display is unavailable

## Quick Start

Run locally:

```bash
python3 fit_coder.py
```

or

```bash
python3 -m fitcoder
```

Install as global command:

```bash
ln -sf "$(pwd)/fit_coder.py" ~/.local/bin/fitcoder
fitcoder
```

## Project Structure

```text
fit_coder.py          # thin launcher for backward compatibility
fitcoder/
  app.py              # app entrypoint (widget first, CLI fallback)
  widget.py           # Tk widget UI and session flow
  cli.py              # terminal fallback flow
  alarm.py            # cross-platform alarm helpers
  stats.py            # formatting and stats table helpers
  models.py           # shared data models
```

## Screenshots

Setup:

![Fit Coder setup](images/input.png)

Timer:

![Fit Coder timer](images/timer.png)

Stats:

![Fit Coder stats](images/stats.png)

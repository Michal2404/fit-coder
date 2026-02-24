## Running With Docker Compose

CLI mode (no GUI/X11 mount, works on any Docker setup):

```bash
docker compose up --build fitcoder
```

GUI mode (Linux X11):

```bash
xhost +local:docker
docker compose --profile gui up --build fitcoder-gui
```

The container runs `fit_coder.py` in interactive mode (`tty` + `stdin_open`).
In GUI mode, the Tk widget is shown when X11 is reachable.

Stop the app:

- In the container terminal: `Ctrl+C`
- Then optionally clean up: `docker compose down`
- Optionally reset X11 access: `xhost -local:docker`

## Notes

- This is a terminal app, not an HTTP server, so no ports are exposed.
- If a display is unavailable/unreachable, the app falls back to CLI mode.
- `requirements.txt` is present for project convention, but there are no external
  Python packages required at the moment.
- If you use Docker Desktop for GUI mode, ensure `/tmp/.X11-unix` is shared in
  Docker file sharing settings.

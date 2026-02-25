from __future__ import annotations

from .cli import run_cli_fallback
from .widget import FitCoderWidgetApp, tk, tk_is_available


def run() -> None:
    print("Starting fit coder...")

    if not tk_is_available() or tk is None:
        run_cli_fallback()
        return

    try:
        root = tk.Tk()
    except Exception:
        run_cli_fallback()
        return

    FitCoderWidgetApp(root)
    root.mainloop()

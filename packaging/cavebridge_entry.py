# SPDX-FileCopyrightText: (C) 2026 Leonard Li and CaveBridge contributors
# SPDX-License-Identifier: BSD-2-Clause
"""PyInstaller entry point — bundles the cavebridge package into one executable.

On Windows the console exe also works when double-clicked (it opens its own
cmd/PowerShell window). If it errors before the game loop, pause so the window
stays open long enough to read the message instead of flashing shut.
"""
import os
import sys

from cavebridge.__main__ import main


def _run() -> None:
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        import traceback

        traceback.print_exc()
        if os.name == "nt":
            try:
                input("\nPress Enter to exit...")
            except EOFError:
                pass
        raise


if __name__ == "__main__":
    _run()

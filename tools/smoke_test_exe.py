"""Run the packaged app headlessly, checking startup and the Playlists toggle."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4


def main():
    executable = Path(sys.argv[1]).resolve()
    test_dir = Path("build") / ("packaged-smoke-" + uuid4().hex)
    test_dir.mkdir(parents=True)
    try:
        # Keep verification separate from the user's real preferences and library.
        target = test_dir.resolve() / executable.name
        shutil.copy2(executable, target)
        result = subprocess.run(
            [str(target), "--smoke-test"],
            env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
            capture_output=True, text=True, timeout=45,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        print(f"Packaged startup and Playlists toggle: exit {result.returncode}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode
    finally:
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    sys.exit(main())

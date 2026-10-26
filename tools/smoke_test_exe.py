"""Run the packaged app headlessly, checking startup and the Playlists toggle."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4


def main():
    executable = Path(sys.argv[1]).resolve()
    workspace=Path.cwd().resolve()
    test_root=(workspace/'build').resolve()
    if not test_root.is_relative_to(workspace):raise RuntimeError('Smoke-test root is outside the workspace')
    test_dir = test_root / ("packaged-smoke-" + uuid4().hex)
    test_dir.mkdir(parents=True)
    try:
        # Keep verification separate from the user's real preferences and library.
        target = test_dir.resolve() / executable.name
        shutil.copy2(executable, target)
        if '--keep' in sys.argv:print('Diagnostic folder:',test_dir.resolve(),flush=True)
        environment=dict(os.environ,QT_QPA_PLATFORM="windows" if '--native' in sys.argv else "offscreen")
        if '--workspace-temp' in sys.argv:
            runtime=test_dir.resolve()/'runtime'
            runtime.mkdir()
            environment.update(TMP=str(runtime),TEMP=str(runtime))
        result = subprocess.run(
            [str(target), "--smoke-test"],
            env=environment,
            capture_output=True, text=True, timeout=120 if '--keep' in sys.argv else 90 if '--native' in sys.argv else 45,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        print(f"Packaged startup, Playlists toggle and appearance previews ({'native UI' if '--native' in sys.argv else 'offscreen'}): exit {result.returncode}")
        diagnostic=test_dir / '.smoke-test-error.txt'
        if diagnostic.exists():print(diagnostic.read_text(encoding='utf-8'))
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode
    finally:
        if '--keep' not in sys.argv:
            if test_dir.resolve().parent!=test_root:raise RuntimeError('Invalid smoke-test cleanup path')
            shutil.rmtree(test_dir)


if __name__ == "__main__":
    sys.exit(main())

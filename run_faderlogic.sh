#!/bin/sh
# Launch from a project venv, or from app-local dependencies without a venv.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$script_dir"
if [ "${1:-}" = "--no-venv" ]; then
    if [ ! -d "$script_dir/.packages" ]; then
        printf '%s\n' 'First run: python3 -m pip install --target .packages -r requirements.txt'
        exit 1
    fi
    export PYTHONPATH="$script_dir/.packages${PYTHONPATH:+:$PYTHONPATH}"
    exec python3 main.py
fi
if [ ! -x "$script_dir/.venv/bin/python" ]; then
    printf '%s\n' 'Create the venv using the README, or run: sh run_faderlogic.sh --no-venv'
    exit 1
fi
exec "$script_dir/.venv/bin/python" main.py

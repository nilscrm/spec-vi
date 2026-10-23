#!/usr/bin/env python3
"""Run pinned Vine with a 64 MiB compiler stack (macOS usable maximum: 65520 KiB)."""
import os
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
# macOS Python setrlimit rejects this otherwise-valid limit on this host; zsh's
# built-in applies it successfully. Arguments are passed as argv, never interpolated.
os.execv('/bin/zsh', ['zsh','-c','ulimit -s 65520 || exit 1; exec "$@"',
                     'vine-exec',str(root/'work/bin/vine'),*sys.argv[1:]])

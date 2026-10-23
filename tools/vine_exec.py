#!/usr/bin/env python3
"""Run pinned Vine with a 64 MiB compiler stack (macOS usable maximum: 65520 KiB)."""
import os
from pathlib import Path
import resource
import sys
root=Path(__file__).resolve().parents[1]
vine=str(root/'work/bin/vine')
STACK_KIB=65520
if sys.platform=='darwin':
    # macOS Python setrlimit rejects this otherwise-valid limit on this host; zsh's
    # built-in applies it successfully. Arguments are passed as argv, never interpolated.
    os.execv('/bin/zsh', ['zsh','-c',f'ulimit -s {STACK_KIB} || exit 1; exec "$@"',
                         'vine-exec',vine,*sys.argv[1:]])
_,hard=resource.getrlimit(resource.RLIMIT_STACK)
resource.setrlimit(resource.RLIMIT_STACK,(STACK_KIB*1024,hard))
os.execv(vine,[vine,*sys.argv[1:]])

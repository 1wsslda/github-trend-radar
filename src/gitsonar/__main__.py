from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    src_root = Path(__file__).resolve().parents[1]
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    from gitsonar.runtime.app import main
else:
    from .runtime.app import main


if __name__ == "__main__":
    main()

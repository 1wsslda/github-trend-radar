"""GitSonar application package."""

from __future__ import annotations

import importlib
import sys as _sys

_COMPAT_MODULE_PATHS = {
    "app_runtime": ".runtime.app",
    "runtime_http": ".runtime.http",
    "runtime_paths": ".runtime.paths",
    "runtime_settings": ".runtime.settings",
    "runtime_shell": ".runtime.shell",
    "runtime_startup": ".runtime.startup",
    "runtime_state": ".runtime.state",
    "runtime_translation": ".runtime.translation",
    "runtime_utils": ".runtime.utils",
}


def _load_compat_module(name: str):
    module = importlib.import_module(_COMPAT_MODULE_PATHS[name], __name__)
    globals()[name] = module
    _sys.modules.setdefault(f"{__name__}.{name}", module)
    return module


def __getattr__(name: str):
    if name == "main":
        from .runtime.app import main as runtime_main

        globals()["main"] = runtime_main
        return runtime_main
    if name in _COMPAT_MODULE_PATHS:
        return _load_compat_module(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["main", *_COMPAT_MODULE_PATHS.keys()]

"""GitSonar application package."""

import sys as _sys

from .runtime import app as app_runtime
from .runtime import http as runtime_http
from .runtime import paths as runtime_paths
from .runtime import settings as runtime_settings
from .runtime import shell as runtime_shell
from .runtime import startup as runtime_startup
from .runtime import state as runtime_state
from .runtime import translation as runtime_translation
from .runtime import utils as runtime_utils
from .runtime.app import main

_COMPAT_MODULES = {
    "app_runtime": app_runtime,
    "runtime_http": runtime_http,
    "runtime_paths": runtime_paths,
    "runtime_settings": runtime_settings,
    "runtime_shell": runtime_shell,
    "runtime_startup": runtime_startup,
    "runtime_state": runtime_state,
    "runtime_translation": runtime_translation,
    "runtime_utils": runtime_utils,
}

for _name, _module in _COMPAT_MODULES.items():
    _sys.modules.setdefault(f"{__name__}.{_name}", _module)

__all__ = ["app_runtime", "main", *_COMPAT_MODULES.keys()]

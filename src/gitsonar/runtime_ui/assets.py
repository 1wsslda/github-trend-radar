#!/usr/bin/env python3
from __future__ import annotations

from .css.cards import CSS as CSS_CARDS
from .css.controls import CSS as CSS_CONTROLS
from .css.overlays import CSS as CSS_OVERLAYS
from .css.responsive import CSS as CSS_RESPONSIVE
from .css.shell import CSS as CSS_SHELL
from .css.tokens import CSS as CSS_TOKENS
from .js.actions import JS as JS_ACTIONS
from .js.boot import JS as JS_BOOT
from .js.cards import JS as JS_CARDS
from .js.constants import JS as JS_CONSTANTS
from .js.discovery import JS as JS_DISCOVERY
from .js.helpers import JS as JS_HELPERS
from .js.menus import JS as JS_MENUS
from .js.overlays import JS as JS_OVERLAYS
from .js.panels import JS as JS_PANELS
from .js.prompt_profiles import JS as JS_PROMPT_PROFILES
from .js.state import JS as JS_STATE

CSS = "\n\n".join(
    (
        CSS_TOKENS,
        CSS_CONTROLS,
        CSS_CARDS,
        CSS_OVERLAYS,
        CSS_SHELL,
        CSS_RESPONSIVE,
    )
)

JS = "\n\n".join(
    (
        JS_PROMPT_PROFILES,
        JS_CONSTANTS,
        JS_HELPERS,
        JS_STATE,
        JS_DISCOVERY,
        JS_MENUS,
        JS_CARDS,
        JS_OVERLAYS,
        JS_ACTIONS,
        JS_PANELS,
        JS_BOOT,
    )
)

__all__ = ["CSS", "JS"]

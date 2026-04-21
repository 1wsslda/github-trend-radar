#!/usr/bin/env python3
from __future__ import annotations

from ..prompt_profiles import (
    DEFAULT_PROMPT_PROFILE,
    PROMPT_PROFILE_DEFINITIONS_JSON,
    PROMPT_PROFILE_LEGACY_ALIASES_JSON,
    PROMPT_PROFILE_MENU_GROUPS_JSON,
    PROMPT_PROFILE_ORDER_JSON,
)

JS = r"""const DEFAULT_PROMPT_PROFILE = "__DEFAULT_PROMPT_PROFILE__";
const PROMPT_PROFILE_ORDER = __PROMPT_PROFILE_ORDER__;
const PROMPT_PROFILE_MENU_GROUPS = __PROMPT_PROFILE_MENU_GROUPS__;
const PROMPT_PROFILE_LEGACY_ALIASES = __PROMPT_PROFILE_LEGACY_ALIASES__;
const PROMPT_PROFILE_DEFINITIONS = __PROMPT_PROFILE_DEFINITIONS__;
const PROMPT_PROFILE_LABELS = Object.fromEntries(
  PROMPT_PROFILE_ORDER.map(key => [key, String(PROMPT_PROFILE_DEFINITIONS[key]?.label || key)]),
);
const PROMPT_PROFILE_DESCRIPTIONS = Object.fromEntries(
  PROMPT_PROFILE_ORDER.map(key => [key, String(PROMPT_PROFILE_DEFINITIONS[key]?.description || "")]),
);
const VALID_PROMPT_PROFILES = new Set(PROMPT_PROFILE_ORDER);

function normalizePromptProfile(value){
  const key = String(value || "").trim();
  const normalized = PROMPT_PROFILE_LEGACY_ALIASES[key] || key;
  return VALID_PROMPT_PROFILES.has(normalized) ? normalized : DEFAULT_PROMPT_PROFILE;
}

function promptProfileDefinition(value){
  const key = normalizePromptProfile(value);
  return PROMPT_PROFILE_DEFINITIONS[key] || PROMPT_PROFILE_DEFINITIONS[DEFAULT_PROMPT_PROFILE] || {};
}

function promptProfileLabel(value){
  const key = normalizePromptProfile(value);
  return PROMPT_PROFILE_LABELS[key] || PROMPT_PROFILE_LABELS[DEFAULT_PROMPT_PROFILE];
}

function promptProfileDescription(value){
  const key = normalizePromptProfile(value);
  return PROMPT_PROFILE_DESCRIPTIONS[key] || PROMPT_PROFILE_DESCRIPTIONS[DEFAULT_PROMPT_PROFILE];
}

function currentPromptProfileLabel(){
  return promptProfileLabel(promptProfile);
}

function currentPromptProfileDescription(){
  return promptProfileDescription(promptProfile);
}"""

JS = (
    JS.replace("__DEFAULT_PROMPT_PROFILE__", DEFAULT_PROMPT_PROFILE)
    .replace("__PROMPT_PROFILE_ORDER__", PROMPT_PROFILE_ORDER_JSON)
    .replace("__PROMPT_PROFILE_MENU_GROUPS__", PROMPT_PROFILE_MENU_GROUPS_JSON)
    .replace("__PROMPT_PROFILE_LEGACY_ALIASES__", PROMPT_PROFILE_LEGACY_ALIASES_JSON)
    .replace("__PROMPT_PROFILE_DEFINITIONS__", PROMPT_PROFILE_DEFINITIONS_JSON)
)

__all__ = ["JS"]

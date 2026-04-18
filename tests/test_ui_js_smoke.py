from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gitsonar.runtime_ui.assets import JS


def function_body(source: str, name: str) -> str:
    marker = f"function {name}("
    start = source.find(marker)
    if start == -1:
        raise AssertionError(f"missing function {name}")
    brace_start = source.find("{", start)
    if brace_start == -1:
        raise AssertionError(f"missing opening brace for {name}")

    depth = 0
    in_single = False
    in_double = False
    in_template = False
    escaped = False
    for index in range(brace_start, len(source)):
        char = source[index]
        if escaped:
            escaped = False
            continue
        if char == "\\" and (in_single or in_double or in_template):
            escaped = True
            continue
        if char == "'" and not in_double and not in_template:
            in_single = not in_single
            continue
        if char == '"' and not in_single and not in_template:
            in_double = not in_double
            continue
        if char == "`" and not in_single and not in_double:
            in_template = not in_template
            continue
        if in_single or in_double or in_template:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[brace_start + 1 : index]
    raise AssertionError(f"unterminated function {name}")


class UIJSSmokeTests(unittest.TestCase):
    def test_tab_switch_closes_control_drawer(self):
        body = function_body(JS, "setPanel")
        self.assertIn("closeControlDrawer();", body)
        self.assertIn("render();", body)

    def test_control_drawer_sync_targets_real_nodes(self):
        body = function_body(JS, "syncControlDrawer")
        self.assertIn('document.getElementById("control-drawer-trigger")', body)
        self.assertIn('document.getElementById("control-drawer-list")', body)
        self.assertIn('document.getElementById("control-drawer-discover")', body)
        self.assertIn('document.getElementById("control-drawer-updates")', body)
        self.assertIn('panel === DISCOVER_PANEL_KEY', body)
        self.assertIn('panel === UPDATE_PANEL_KEY', body)

    def test_escape_closes_inline_control_drawer(self):
        self.assertIn('drawer.hidden = !nextVisible;', function_body(JS, "toggleControlDrawer"))
        self.assertIn('drawer.classList.toggle("show", nextVisible);', function_body(JS, "toggleControlDrawer"))
        self.assertIn('drawer.hidden = true;', function_body(JS, "closeControlDrawer"))
        self.assertIn("closeControlDrawer();", JS.split('window.addEventListener("keydown", event => {', 1)[1])

    def test_discovery_empty_and_result_states_have_distinct_paths(self):
        body = function_body(JS, "renderDiscoverEmptyState")
        self.assertIn("if(discoveryBusy && !results.length)", body)
        self.assertIn('if(results.length) return "";', body)
        self.assertIn("toggleControlDrawer(true)", body)
        self.assertIn("runDiscovery()", body)
        self.assertIn("workspace-empty-title", body)

    def test_render_pipeline_updates_header_strip_and_canvas(self):
        body = function_body(JS, "render")
        self.assertIn("syncWorkspaceHeader();", body)
        self.assertIn("syncWorkspaceCanvas();", body)
        self.assertIn("syncControlStates();", body)
        self.assertIn("syncDiscoveryPanel();", body)

    def test_custom_select_sync_scans_dom_instead_of_hard_coded_ids(self):
        body = function_body(JS, "syncAllCustomSelects")
        self.assertIn('document.querySelectorAll("[data-custom-select-for]")', body)
        self.assertIn("syncCustomSelect(root.dataset.customSelectFor || \"\");", body)
        self.assertNotIn("CUSTOM_SELECT_IDS", JS)

    def test_menu_state_sync_restores_aria_and_host_elevation(self):
        body = function_body(JS, "syncMenuRootState")
        self.assertIn('node.setAttribute("aria-expanded", expanded ? "true" : "false");', body)
        self.assertIn('host.classList.toggle("menu-host-open", expanded);', body)
        self.assertIn("resetMenuPanelPosition(root);", body)

    def test_toggle_menu_repositions_and_position_menu_corrects_overflow(self):
        toggle_body = function_body(JS, "toggleMenu")
        position_body = function_body(JS, "positionMenu")
        self.assertIn("closeMenus(willOpen ? id : \"\");", toggle_body)
        self.assertIn("requestAnimationFrame(() => positionMenu(root));", toggle_body)
        self.assertIn("panelRect.bottom > window.innerHeight - MENU_VIEWPORT_MARGIN", position_body)
        self.assertIn('panel.classList.add("upward");', position_body)
        self.assertIn("panelRect.right > window.innerWidth - MENU_VIEWPORT_MARGIN", position_body)

    def test_token_status_validation_uses_dedicated_settings_endpoint(self):
        body = function_body(JS, "validateTokenStatus")
        self.assertIn('"/api/settings/token-status"', body)
        self.assertIn('applyTokenStatus({state:"checking"', body)
        self.assertIn('applyTokenStatus(data.status || null);', body)


if __name__ == "__main__":
    unittest.main()

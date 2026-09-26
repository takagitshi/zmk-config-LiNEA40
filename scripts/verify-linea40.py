#!/usr/bin/env python3
"""Verify LiNEA40's editable source-level firmware contract."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise AssertionError(message)


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        fail(f"missing file: {relative}")
    return path.read_text(encoding="utf-8")


def require(text: str, expected: str, source: str) -> None:
    if expected not in text:
        fail(f"{source}: missing {expected!r}")


def layer_body(keymap: str, layer_id: int) -> str:
    match = re.search(
        rf"^\s*layer_{layer_id}\s*\{{(?P<body>.*?)^\s*\}};",
        keymap,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        fail(f"config/LiNEA40.keymap: missing layer_{layer_id}")
    return match.group("body")


def node_body(text: str, label: str) -> str:
    match = re.search(
        rf"^\s*{re.escape(label)}\s*:\s*[A-Za-z0-9_@-]+\s*\{{(?P<body>.*?)^\s*\}};",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        fail(f"missing node {label}")
    return match.group("body")


def binding_behaviors(body: str) -> list[str]:
    match = re.search(r"bindings\s*=\s*<(?P<body>.*?)>;", body, re.DOTALL)
    if match is None:
        fail("layer has no bindings")
    return re.findall(r"&([A-Za-z0-9_]+)\b", match.group("body"))


def main() -> None:
    west = read("config/west.yml")
    for pin in (
        "edf5c0814fd3ea202e43aad2d68fd32e882a518c",
        "1d9c2c68ca76012e1b1e5f6ef02fa5eadc4ca399",
        "8756cb7b8114069fa3c25c6f6c990f24988fceff",
    ):
        require(west, pin, "config/west.yml")
    if re.search(r"revision:\s+(main|v0\.2\.1)\s*$", west, re.MULTILINE):
        fail("config/west.yml: mutable or obsolete dependency revision")

    workflow = read(".github/workflows/build.yml")
    for expected in (
        "make verify",
        "scripts/sync-aml-exclusions.py",
        "scripts/verify-built-firmware.py",
        "west build",
        "actions/upload-artifact/merge@v4",
    ):
        require(workflow, expected, ".github/workflows/build.yml")
    if "build-user-config.yml" in workflow:
        fail("workflow cannot synchronize AML inside the reusable build checkout")

    build = read("build.yaml")
    for artifact in (
        "LiNEA40_left_peripheral",
        "LiNEA40_right_central_studio",
        "settings_reset-seeeduino_xiao_ble",
    ):
        require(build, f"artifact-name: {artifact}", "build.yaml")

    keymap = read("config/LiNEA40.keymap")
    found_layers = sorted(
        int(value)
        for value in re.findall(r"^\s*layer_(\d+)\s*\{", keymap, re.MULTILINE)
    )
    if found_layers != list(range(10)):
        fail(f"keymap must contain exactly layers 0-9, found {found_layers}")

    expected_names = [
        "Base",
        "Mouse",
        "Scroll",
        "Gesture 1",
        "Gesture 2",
        "symbol",
        "number",
        "move",
        "setting",
        "Precision",
    ]
    layers: list[str] = []
    for layer_id, name in enumerate(expected_names):
        body = layer_body(keymap, layer_id)
        require(body, f'display-name = "{name}";', "config/LiNEA40.keymap")
        behaviors = binding_behaviors(body)
        if len(behaviors) != 41:
            fail(f"layer_{layer_id}: expected 41 bindings, found {len(behaviors)}")
        layers.append(body)

    base = layers[0]
    for layer_id in (2, 3, 4, 5, 6, 7):
        access_layers = base + (layers[1] if layer_id == 4 else "")
        if f"&lt {layer_id} " not in access_layers and f"&mo {layer_id}" not in access_layers:
            location = "Base or Mouse" if layer_id == 4 else "Base"
            fail(f"layer {layer_id} must remain reachable from {location}")
    require(layers[5], "&mo 8", "symbol layer")

    for layer_id in (3, 4):
        gesture_behaviors = binding_behaviors(layers[layer_id])
        for position in (7, 16, 18, 27):
            if gesture_behaviors[position] in {"trans", "none"}:
                fail(
                    f"Gesture layer {layer_id} position {position} must be an editable normal binding"
                )

    mouse_behaviors = binding_behaviors(layers[1])
    configured_mouse_positions = [
        index
        for index, behavior in enumerate(mouse_behaviors)
        if behavior not in {"trans", "none"}
    ]
    overlay = read("config/boards/shields/LiNEA40/LiNEA40_right.overlay")
    excluded = re.search(r"excluded-positions\s*=\s*<([^>]*)>;", overlay)
    if excluded is None:
        fail("right overlay: AML excluded-positions missing")
    excluded_positions = [int(value) for value in excluded.group(1).split()]
    if excluded_positions != configured_mouse_positions:
        fail(
            "right overlay: AML exclusions do not match Mouse layer actions: "
            f"{excluded_positions} != {configured_mouse_positions}"
        )
    if 19 not in configured_mouse_positions:
        fail("Mouse position 19 (right of MB2) must remain assigned")

    listener_order = re.search(
        r"&trackball_listener\s*\{.*?input-processors\s*=\s*"
        r"<&gesture_2_processor>,\s*<&gesture_processor>,\s*"
        r"<&zip_temp_layer 1 10000>;",
        overlay,
        re.DOTALL,
    )
    if listener_order is None:
        fail("right overlay: Gesture 2, Gesture 1, AML processor order changed")
    for expected in (
        "require-prior-idle-ms = <300>;",
        "&gesture_2_processor",
        "layers = <2>;",
        "snipe-layers = <9>;",
        "<&zip_xy_transform INPUT_TRANSFORM_Y_INVERT>",
        "<&zip_xy_to_scroll_mapper>",
        "<&scroll_scaler 1 40>;",
        "&mkp_input_listener",
    ):
        require(overlay, expected, "LiNEA40_right.overlay")
    for obsolete in ("automouse-layer", "scroll-layers"):
        if obsolete in overlay:
            fail(f"LiNEA40_right.overlay: obsolete driver policy {obsolete!r}")

    dtsi = read("config/boards/shields/LiNEA40/LiNEA40.dtsi")
    for label, layer_id in (("gesture_processor", 3), ("gesture_2_processor", 4)):
        body = node_body(dtsi, label)
        for expected in (
            'compatible = "zmk,input-processor-gesture";',
            f"layer = <{layer_id}>;",
            f"binding-layer = <{layer_id}>;",
            "up-position = <7>;",
            "left-position = <16>;",
            "right-position = <18>;",
            "down-position = <27>;",
            "threshold = <40>;",
            "cooldown-ms = <150>;",
            "reset-on-layer = <2>;",
        ):
            require(body, expected, f"LiNEA40.dtsi {label}")

    right_conf = read("config/boards/shields/LiNEA40/LiNEA40_right.conf")
    for preserved in (
        "CONFIG_PMW3610_SMART_ALGORITHM=y",
        "CONFIG_PMW3610_CPI=800",
        "CONFIG_PMW3610_SNIPE_CPI=400",
        "CONFIG_PMW3610_POLLING_RATE_125_SW=y",
        "CONFIG_PMW3610_RUN_DOWNSHIFT_TIME_MS=3264",
        "CONFIG_PMW3610_REST1_SAMPLE_TIME_MS=40",
        "CONFIG_PMW3610_REST1_DOWNSHIFT_TIME_MS=9600",
        "CONFIG_PMW3610_INVERT_X=y",
        "CONFIG_PMW3610_INVERT_Y=y",
        "CONFIG_RGBLED_WIDGET_SHOW_LAYER_COLORS=y",
        "CONFIG_LINEA40_CUSTOM_GESTURE2_MIGRATION=y",
    ):
        require(right_conf, preserved, "LiNEA40_right.conf")
    expected_colors = [0, 7, 2, 3, 5, 4, 2, 6, 1, 3]
    for layer_id, color in enumerate(expected_colors):
        require(
            right_conf,
            f"CONFIG_RGBLED_WIDGET_LAYER_{layer_id}_COLOR={color}",
            "LiNEA40_right.conf",
        )

    migration = read("src/keymap_migration.c")
    for expected in (
        'settings_load_subtree_direct("keymap"',
        'delete_setting("keymap/layer_order")',
        '"keymap/l_n/%u"',
        '"keymap/l/%u/%u"',
        "MIGRATION_SETTINGS_KEY",
        "SYS_INIT(migrate_saved_keymap, APPLICATION, 89)",
    ):
        require(migration, expected, "src/keymap_migration.c")
    for forbidden in ('settings_delete("bt/', 'settings_delete("rgbled/'):
        if forbidden in migration:
            fail(f"migration must not delete unrelated setting {forbidden!r}")

    left_conf = read("config/boards/shields/LiNEA40/LiNEA40_left.conf")
    for central_only in (
        "CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_PROXY",
        "CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING",
        "CONFIG_LINEA40_CUSTOM_GESTURE2_MIGRATION",
        "CONFIG_RGBLED_WIDGET_SHOW_LAYER_COLORS",
    ):
        if central_only in left_conf:
            fail(f"LiNEA40_left.conf: central-only option {central_only!r}")

    editor = json.loads(read("config/LiNEA40.json"))
    sensors = editor.get("sensors", [])
    if not sensors or sensors[0].get("ref") != "left_encoder" or not sensors[0].get("enabled"):
        fail("config/LiNEA40.json: left_encoder must be enabled")

    fallback = read("config/boards/shields/LiNEA40/LiNEA40.keymap").strip()
    if fallback != (
        "/* The user configuration is the single source of truth. */\n"
        '#include "../../../LiNEA40.keymap"'
    ):
        fail("shield fallback keymap must include the canonical user keymap")

    for required in (
        "CMakeLists.txt",
        "Kconfig",
        "zephyr/module.yml",
        "scripts/sync-aml-exclusions.py",
        "scripts/verify-built-firmware.py",
        "src/gesture_state.c",
        "src/input_processor_gesture.c",
        "include/linea40/gesture_state.h",
        "dts/bindings/input_processors/zmk,input-processor-gesture.yaml",
    ):
        read(required)

    print("verify-linea40: PASS")


if __name__ == "__main__":
    main()

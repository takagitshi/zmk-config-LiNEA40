#!/usr/bin/env python3
"""Verify LiNEA40's source-level firmware contract."""

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
    require(workflow, "make verify", ".github/workflows/build.yml")
    require(workflow, "build-user-config.yml@v0.3.0", ".github/workflows/build.yml")

    build = read("build.yaml")
    for artifact in (
        "LiNEA40_left_peripheral",
        "LiNEA40_right_central_studio",
        "settings_reset-seeeduino_xiao_ble",
    ):
        require(build, f"artifact-name: {artifact}", "build.yaml")

    keymap = read("config/LiNEA40.keymap")
    expected_names = [
        "Base",
        "Mouse",
        "Scroll",
        "Gesture",
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

    for expected in (
        "require-prior-idle-ms = <300>;",
        "<&gesture_processor>,",
        "<&zip_temp_layer 1 10000>;",
        "layers = <2>;",
        "snipe-layers = <8>;",
        "<&scroll_scaler 1 40>;",
        "&mkp_input_listener",
    ):
        require(overlay, expected, "LiNEA40_right.overlay")
    for obsolete in ("automouse-layer", "scroll-layers"):
        if obsolete in overlay:
            fail(f"LiNEA40_right.overlay: obsolete driver policy {obsolete!r}")

    dtsi = read("config/boards/shields/LiNEA40/LiNEA40.dtsi")
    for expected in (
        'compatible = "zmk,input-processor-gesture";',
        "layer = <3>;",
        "binding-layer = <3>;",
        "up-position = <7>;",
        "left-position = <16>;",
        "right-position = <18>;",
        "down-position = <27>;",
        "threshold = <40>;",
        "cooldown-ms = <150>;",
    ):
        require(dtsi, expected, "LiNEA40.dtsi")

    gesture_behaviors = binding_behaviors(layers[3])
    expected_gesture_positions = {7: "kp", 16: "kp", 18: "kp", 27: "kp"}
    for position, behavior in expected_gesture_positions.items():
        if gesture_behaviors[position] != behavior:
            fail(f"Gesture layer position {position} is not editable key behavior")

    right_conf = read("config/boards/shields/LiNEA40/LiNEA40_right.conf")
    for preserved in (
        "CONFIG_PMW3610_SMART_ALGORITHM=y",
        "CONFIG_PMW3610_CPI=800",
        "CONFIG_PMW3610_RUN_DOWNSHIFT_TIME_MS=3264",
        "CONFIG_PMW3610_REST1_SAMPLE_TIME_MS=40",
        "CONFIG_PMW3610_REST1_DOWNSHIFT_TIME_MS=9600",
        "CONFIG_PMW3610_INVERT_X=y",
        "CONFIG_PMW3610_INVERT_Y=y",
    ):
        require(right_conf, preserved, "LiNEA40_right.conf")

    left_conf = read("config/boards/shields/LiNEA40/LiNEA40_left.conf")
    for central_only in (
        "CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_PROXY",
        "CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING",
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
        "src/gesture_state.c",
        "src/input_processor_gesture.c",
        "include/linea40/gesture_state.h",
        "dts/bindings/input_processors/zmk,input-processor-gesture.yaml",
    ):
        read(required)

    print("verify-linea40: PASS")


if __name__ == "__main__":
    main()

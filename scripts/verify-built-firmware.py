#!/usr/bin/env python3
"""Verify generated Devicetree and Kconfig for each LiNEA40 artifact."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise AssertionError(message)


def require(text: str, expected: str, source: str) -> None:
    if expected not in text:
        fail(f"{source}: missing {expected!r}")


def require_config(config: str, symbol: str, value: str = "y") -> None:
    require(config, f"CONFIG_{symbol}={value}", ".config")


def node_body(dts: str, label: str) -> str:
    match = re.search(
        rf"^\s*{re.escape(label)}\s*:\s*[A-Za-z0-9_@-]+\s*\{{(?P<body>.*?)^\s*\}};",
        dts,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        fail(f"zephyr.dts: missing node {label}")
    return match.group("body")


def property_cells(body: str, property_name: str) -> list[int]:
    match = re.search(rf"\b{re.escape(property_name)}\s*=\s*<([^>]*)>;", body)
    if match is None:
        fail(f"zephyr.dts: missing property {property_name}")
    return [int(value, 0) for value in match.group(1).split() if not value.startswith("&")]


def require_keymap(dts: str) -> None:
    layers = sorted(int(value) for value in re.findall(r"\blayer_(\d+)\s*\{", dts))
    if layers != list(range(10)):
        fail(f"generated keymap must contain exactly layers 0-9, found {layers}")
    for name in (
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
    ):
        require(dts, f'display-name = "{name}";', "zephyr.dts")


def configured_mouse_positions() -> list[int]:
    keymap = (ROOT / "config/LiNEA40.keymap").read_text(encoding="utf-8")
    layer = re.search(
        r"^\s*layer_1\s*\{(?P<body>.*?)^\s*\};",
        keymap,
        re.MULTILINE | re.DOTALL,
    )
    if layer is None:
        fail("config/LiNEA40.keymap: missing Mouse layer")
    bindings = re.search(r"bindings\s*=\s*<(?P<body>.*?)>;", layer.group("body"), re.DOTALL)
    if bindings is None:
        fail("config/LiNEA40.keymap: Mouse layer has no bindings")
    behaviors = re.findall(r"&([A-Za-z0-9_]+)\b", bindings.group("body"))
    if len(behaviors) != 41:
        fail(f"Mouse layer must have 41 bindings, found {len(behaviors)}")
    return [
        position
        for position, behavior in enumerate(behaviors)
        if behavior not in {"trans", "none"}
    ]


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: verify-built-firmware.py ARTIFACT DTS CONFIG")

    artifact, dts_path, config_path = sys.argv[1:]
    dts = Path(dts_path).read_text(encoding="utf-8")
    config = Path(config_path).read_text(encoding="utf-8")

    if artifact == "settings_reset-seeeduino_xiao_ble":
        require_config(config, "ZMK_SETTINGS_RESET_ON_START")
        if "CONFIG_LINEA40_CUSTOM_GESTURE2_MIGRATION=y" in config:
            fail("settings reset must not contain the LiNEA40 keymap migration")
        print(f"verify-built-firmware: PASS ({artifact})")
        return

    require_keymap(dts)
    require_config(config, "ZMK_SPLIT")
    require_config(config, "ZMK_POINTING")

    if artifact == "LiNEA40_left_peripheral":
        require_config(config, "SHIELD_LiNEA40_LEFT")
        require_config(config, "EC11")
        require(dts, 'compatible = "alps,ec11";', "zephyr.dts")
        if "CONFIG_LINEA40_CUSTOM_GESTURE2_MIGRATION=y" in config:
            fail("left peripheral must not migrate central Studio settings")
        if "CONFIG_RGBLED_WIDGET_SHOW_LAYER_COLORS=y" in config:
            fail("left peripheral must retain battery/status-only LED behavior")
    elif artifact == "LiNEA40_right_central_studio":
        require_config(config, "SHIELD_LiNEA40_RIGHT")
        require_config(config, "ZMK_STUDIO")
        require_config(config, "PMW3610")
        require_config(config, "PMW3610_SMART_ALGORITHM")
        require_config(config, "ZMK_INPUT_PROCESSOR_GESTURE")
        require_config(config, "LINEA40_CUSTOM_GESTURE2_MIGRATION")
        require_config(config, "RGBLED_WIDGET_SHOW_LAYER_COLORS")
        for expected in ('compatible = "pixart,pmw3610";',):
            require(dts, expected, "zephyr.dts")
        if dts.count('compatible = "zmk,input-processor-gesture";') != 2:
            fail("right central must contain exactly two gesture processors")
        for label, layer_id in (("gesture_processor", 3), ("gesture_2_processor", 4)):
            body = node_body(dts, label)
            require(body, 'status = "okay";', f"zephyr.dts {label}")
            expected_properties = {
                "layer": [layer_id],
                "binding-layer": [layer_id],
                "up-position": [7],
                "left-position": [16],
                "right-position": [18],
                "down-position": [27],
                "threshold": [40],
                "cooldown-ms": [150],
                "reset-on-layer": [2],
            }
            for property_name, expected in expected_properties.items():
                actual = property_cells(body, property_name)
                if actual != expected:
                    fail(
                        f"zephyr.dts {label}: {property_name} is {actual}, expected {expected}"
                    )
        expected_exclusions = configured_mouse_positions()
        actual_exclusions = property_cells(
            node_body(dts, "zip_temp_layer"), "excluded-positions"
        )
        if actual_exclusions != expected_exclusions:
            fail(
                "generated AML exclusions do not match active Mouse keys: "
                f"{actual_exclusions} != {expected_exclusions}"
            )
        trackball = node_body(dts, "trackball_listener")
        require(
            trackball,
            "input-processors = < &gesture_2_processor >, < &gesture_processor >, "
            "< &zip_temp_layer 0x1 0x2710 >;",
            "zephyr.dts trackball_listener",
        )
        if property_cells(trackball, "layers") != [2]:
            fail("generated scroll layer must remain Layer 2")
        if property_cells(node_body(dts, "trackball"), "snipe-layers") != [9]:
            fail("generated Precision layer must be Layer 9")
        for layer_id, color in enumerate((0, 7, 2, 3, 5, 4, 2, 6, 1, 3)):
            require_config(config, f"RGBLED_WIDGET_LAYER_{layer_id}_COLOR", str(color))
        for symbol, value in (
            ("PMW3610_CPI", "800"),
            ("PMW3610_SNIPE_CPI", "400"),
            ("PMW3610_RUN_DOWNSHIFT_TIME_MS", "3264"),
            ("PMW3610_REST1_SAMPLE_TIME_MS", "40"),
            ("PMW3610_REST1_DOWNSHIFT_TIME_MS", "9600"),
        ):
            require_config(config, symbol, value)
    else:
        fail(f"unknown artifact: {artifact}")

    print(f"verify-built-firmware: PASS ({artifact})")


if __name__ == "__main__":
    main()

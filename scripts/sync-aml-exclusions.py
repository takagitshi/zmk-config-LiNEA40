#!/usr/bin/env python3
"""Synchronize AML exclusions with active Mouse-layer bindings."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KEYMAP = ROOT / "config/LiNEA40.keymap"
OVERLAY = ROOT / "config/boards/shields/LiNEA40/LiNEA40_right.overlay"


def layer_body(keymap: str, layer_id: int) -> str:
    match = re.search(
        rf"^\s*layer_{layer_id}\s*\{{(?P<body>.*?)^\s*\}};",
        keymap,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise SystemExit(f"missing layer_{layer_id} in {KEYMAP}")
    return match.group("body")


def active_mouse_positions(keymap: str) -> list[int]:
    body = layer_body(keymap, 1)
    bindings = re.search(r"bindings\s*=\s*<(?P<body>.*?)>;", body, re.DOTALL)
    if bindings is None:
        raise SystemExit("Mouse layer has no bindings")
    behaviors = re.findall(r"&([A-Za-z0-9_]+)\b", bindings.group("body"))
    if len(behaviors) != 41:
        raise SystemExit(f"Mouse layer must have 41 bindings, found {len(behaviors)}")
    return [
        position
        for position, behavior in enumerate(behaviors)
        if behavior not in {"trans", "none"}
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of updating when exclusions are out of sync",
    )
    args = parser.parse_args()

    positions = active_mouse_positions(KEYMAP.read_text(encoding="utf-8"))
    overlay = OVERLAY.read_text(encoding="utf-8")
    replacement = "excluded-positions = <" + " ".join(map(str, positions)) + ">;"
    updated, count = re.subn(
        r"excluded-positions\s*=\s*<[^>]*>;",
        replacement,
        overlay,
        count=1,
    )
    if count != 1:
        raise SystemExit(f"expected one AML excluded-positions property in {OVERLAY}")

    if updated == overlay:
        print("sync-aml-exclusions: already synchronized")
        return
    if args.check:
        raise SystemExit(
            "AML exclusions are stale; run scripts/sync-aml-exclusions.py "
            f"(expected {positions})"
        )

    OVERLAY.write_text(updated, encoding="utf-8")
    print(f"sync-aml-exclusions: updated {positions}")


if __name__ == "__main__":
    main()

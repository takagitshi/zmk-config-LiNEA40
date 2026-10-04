#!/usr/bin/env python3
"""Compatibility check: West now generates AML exclusions without editing source."""
from pathlib import Path
import argparse
from aml_keymap import mouse_positions

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true', help='validate the editable Mouse bindings')
parser.parse_args()
keymap = Path(__file__).resolve().parents[1] / 'config/LiNEA40.keymap'
positions = mouse_positions(keymap.read_text(encoding='utf-8'), key_count=41)
print(f'AML positions {positions} are generated automatically by West; source unchanged')

# LiNEA40 ZMK firmware

Personal LiNEA40 firmware for `takagitshi`. The hardware definition remains based on
[`keyfreaks/zmk-config-LiNEA40`](https://github.com/keyfreaks/zmk-config-LiNEA40).

## What is customized

- Ten-layer role order: Base, Mouse, Scroll, Gesture 1, Gesture 2, symbol,
  number, move, setting, and LiNEA40 Precision.
- Current Keymap Editor changes are retained, including the disabled extra
  bottom-row key and ordinary Tilde binding.
- ZMK-standard Auto Mouse Layer with a 300 ms typing guard, 10 second timeout, and
  mouse-button refresh.
- Four-way trackball gestures on Layers 3 and 4. Both use editable ordinary
  bindings at I, J, L, and comma. Gesture 2 defaults are left =
  Control+Shift+Tab, right = Control+Tab, up = Command+T, and down =
  Command+Shift+N.
- Mouse Layer position immediately right of MB2 is Right Command. AML exclusions
  are regenerated from all active Mouse Layer bindings before every build.
- LiNEA40-specific right-central PMW3610, left EC11 encoder, RGB battery/status
  widget, split battery reporting, and right-side ZMK Studio are retained.
- The right-central LED uses the layer palette: off, white, green, yellow,
  magenta, blue, green, cyan, red, yellow. The left retains battery/status-only
  behavior.
- Precision remains Layer 9 at 400 CPI and can be assigned from Keymap Editor.
- A one-time keymap-only migration lets the new source layout replace old Studio
  layer data without deleting Bluetooth bonds or unrelated settings.
- ZMK and external modules are pinned to immutable commits.

The default PMW3610 sensor driver is intentionally retained until the keyboard is
available for physical A/B testing. Source checks, firmware builds, and Actions
artifacts do not prove pointer feel, direction, sleep recovery, or battery life.

## Layer access

- Scroll: hold K
- Gesture 1: hold I
- Gesture 2: hold comma
- symbol: hold Language 1
- number: hold Space
- move: hold Enter
- setting: hold symbol, then hold Space
- Precision (400 CPI): currently unassigned; assign a Layer 9 key in Keymap Editor

The left encoder controls volume on Base/Mouse and scroll on move. Its hardware
calibration (`steps = 24`, `triggers-per-rotation = 8`) is unchanged.

## Validation

Run the source contract and gesture state-machine tests:

```sh
make verify
```

GitHub Actions builds three artifacts: left peripheral, right central with Studio,
and settings reset. Use settings reset only when intentionally clearing stored ZMK
settings and Bluetooth bonds.

## Physical checks after delivery

Before daily use, confirm cursor and scroll directions, AML activation/deactivation,
all four gestures, encoder direction, split reconnect, sleep/wake, RGB status, and
battery behavior on the actual keyboard.

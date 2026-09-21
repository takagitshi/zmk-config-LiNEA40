# LiNEA40 ZMK firmware

Personal LiNEA40 firmware for `takagitshi`. The hardware definition remains based on
[`keyfreaks/zmk-config-LiNEA40`](https://github.com/keyfreaks/zmk-config-LiNEA40).

## What is customized

- LisM-compatible 9-layer role order: Base, Mouse, Scroll, Gesture, symbol, number,
  move, setting, and LiNEA40 Precision.
- LiNEA40's extra bottom-row key remains a dedicated Insert key.
- ZMK-standard Auto Mouse Layer with a 300 ms typing guard, 10 second timeout, and
  mouse-button refresh.
- Four-way trackball gestures on Layer 3. The editable action slots are I, J, L,
  and comma.
- LiNEA40-specific right-central PMW3610, left EC11 encoder, RGB battery/status
  widget, split battery reporting, and right-side ZMK Studio are retained.
- Holding the Tilde key activates LiNEA40's native 400 CPI precision mode.
- ZMK and external modules are pinned to immutable commits.

The default PMW3610 sensor driver is intentionally retained until the keyboard is
available for physical A/B testing. Source checks, firmware builds, and Actions
artifacts do not prove pointer feel, direction, sleep recovery, or battery life.

## Layer access

- Scroll: K + L combo
- Gesture: I + O combo
- symbol: hold Language 1
- number: hold Space
- move: hold Enter
- setting: hold symbol, then hold Space
- Precision (400 CPI): hold Tilde

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

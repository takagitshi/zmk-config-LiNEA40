/*
 * Copyright (c) 2026 Takashi Imai
 *
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

enum linea40_gesture_direction {
    LINEA40_GESTURE_NONE,
    LINEA40_GESTURE_LEFT,
    LINEA40_GESTURE_RIGHT,
    LINEA40_GESTURE_UP,
    LINEA40_GESTURE_DOWN,
};

enum linea40_gesture_axis {
    LINEA40_GESTURE_AXIS_X,
    LINEA40_GESTURE_AXIS_Y,
};

struct linea40_gesture_state {
    int32_t x;
    int32_t y;
    int64_t cooldown_until_ms;
    bool cooling_down;
};

void linea40_gesture_state_reset(struct linea40_gesture_state *state);

enum linea40_gesture_direction linea40_gesture_state_update(struct linea40_gesture_state *state,
                                                       enum linea40_gesture_axis axis, int32_t value,
                                                       bool sync, int64_t now_ms,
                                                       uint32_t threshold, uint32_t cooldown_ms);

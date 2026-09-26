/*
 * Copyright (c) 2026 Takashi Imai
 *
 * SPDX-License-Identifier: MIT
 */

#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <zephyr/init.h>
#include <zephyr/logging/log.h>
#include <zephyr/settings/settings.h>
#include <zephyr/sys/util.h>

LOG_MODULE_REGISTER(linea40_keymap_migration, CONFIG_ZMK_LOG_LEVEL);

#define MIGRATION_SETTINGS_ROOT "linea40_custom"
#define MIGRATION_SETTINGS_KEY MIGRATION_SETTINGS_ROOT "/gesture2_v1"
#define KEYMAP_LAYER_COUNT 10
#define KEYMAP_POSITION_COUNT 41

struct keymap_settings_inventory {
    bool layer_order;
    uint16_t layer_names;
    uint64_t bindings[KEYMAP_LAYER_COUNT];
};

static int marker_callback(const char *key, size_t len, settings_read_cb read_cb, void *cb_arg,
                           void *param) {
    bool *migration_complete = param;

    ARG_UNUSED(read_cb);
    ARG_UNUSED(cb_arg);

    if (strcmp(key, "gesture2_v1") == 0 && len > 0) {
        *migration_complete = true;
    }

    return 0;
}

static int inventory_callback(const char *key, size_t len, settings_read_cb read_cb, void *cb_arg,
                              void *param) {
    struct keymap_settings_inventory *inventory = param;
    unsigned int layer;
    unsigned int position;

    ARG_UNUSED(read_cb);
    ARG_UNUSED(cb_arg);

    if (len == 0) {
        return 0;
    }

    if (strcmp(key, "layer_order") == 0) {
        inventory->layer_order = true;
    } else if (sscanf(key, "l_n/%u", &layer) == 1 && layer < KEYMAP_LAYER_COUNT) {
        inventory->layer_names |= BIT(layer);
    } else if (sscanf(key, "l/%u/%u", &layer, &position) == 2 &&
               layer < KEYMAP_LAYER_COUNT && position < KEYMAP_POSITION_COUNT) {
        inventory->bindings[layer] |= BIT64(position);
    }

    return 0;
}

static int delete_setting(const char *key) {
    const int ret = settings_delete(key);

    if (ret < 0) {
        LOG_ERR("Unable to delete %s: %d", key, ret);
    }
    return ret;
}

static int migrate_saved_keymap(void) {
    bool migration_complete = false;
    struct keymap_settings_inventory inventory = {0};
    char key[24];
    int ret = settings_subsys_init();

    if (ret < 0) {
        LOG_ERR("Settings initialization failed: %d", ret);
        return ret;
    }

    ret = settings_load_subtree_direct(MIGRATION_SETTINGS_ROOT, marker_callback,
                                       &migration_complete);
    if (ret < 0 || migration_complete) {
        return ret;
    }

    ret = settings_load_subtree_direct("keymap", inventory_callback, &inventory);
    if (ret < 0) {
        LOG_ERR("Unable to inspect saved keymap: %d", ret);
        return ret;
    }

    if (inventory.layer_order && delete_setting("keymap/layer_order") < 0) {
        return -EIO;
    }

    for (unsigned int layer = 0; layer < KEYMAP_LAYER_COUNT; layer++) {
        if (inventory.layer_names & BIT(layer)) {
            snprintf(key, sizeof(key), "keymap/l_n/%u", layer);
            if (delete_setting(key) < 0) {
                return -EIO;
            }
        }

        for (unsigned int position = 0; position < KEYMAP_POSITION_COUNT; position++) {
            if (inventory.bindings[layer] & BIT64(position)) {
                snprintf(key, sizeof(key), "keymap/l/%u/%u", layer, position);
                if (delete_setting(key) < 0) {
                    return -EIO;
                }
            }
        }
    }

    const uint8_t marker = 1;
    ret = settings_save_one(MIGRATION_SETTINGS_KEY, &marker, sizeof(marker));
    if (ret < 0) {
        LOG_ERR("Unable to save migration marker: %d", ret);
        return ret;
    }

    LOG_INF("Saved Studio keymap migrated to Gesture 2 layout");
    return 0;
}

SYS_INIT(migrate_saved_keymap, APPLICATION, 89);

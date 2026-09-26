if(CONFIG_SHIELD_LiNEA40_LEFT OR CONFIG_SHIELD_LiNEA40_RIGHT)
  zephyr_library()
  zephyr_include_directories(${CMAKE_CURRENT_LIST_DIR}/include)
  zephyr_library_sources_ifdef(CONFIG_ZMK_INPUT_PROCESSOR_GESTURE
    src/gesture_state.c
    src/input_processor_gesture.c)
  zephyr_library_sources_ifdef(CONFIG_LINEA40_CUSTOM_GESTURE2_MIGRATION
    src/keymap_migration.c)
endif()

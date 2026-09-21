if((CONFIG_SHIELD_LiNEA40_LEFT OR CONFIG_SHIELD_LiNEA40_RIGHT) AND
   CONFIG_ZMK_INPUT_PROCESSOR_GESTURE)
  zephyr_library()
  zephyr_include_directories(${CMAKE_CURRENT_LIST_DIR}/include)
  zephyr_library_sources(
    src/gesture_state.c
    src/input_processor_gesture.c)
endif()

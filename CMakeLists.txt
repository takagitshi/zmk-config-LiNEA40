# Zephyr appends DTS inputs after the early AML hook. Keep one rule per input.
get_property(linea40_configure_inputs DIRECTORY "${APPLICATION_SOURCE_DIR}" PROPERTY CMAKE_CONFIGURE_DEPENDS)
set(linea40_configure_inputs_normalized)
foreach(linea40_configure_input IN LISTS linea40_configure_inputs)
  get_filename_component(linea40_configure_input "${linea40_configure_input}" ABSOLUTE BASE_DIR "${APPLICATION_SOURCE_DIR}")
  list(APPEND linea40_configure_inputs_normalized "${linea40_configure_input}")
endforeach()
list(REMOVE_DUPLICATES linea40_configure_inputs_normalized)
set_property(DIRECTORY "${APPLICATION_SOURCE_DIR}" PROPERTY CMAKE_CONFIGURE_DEPENDS "${linea40_configure_inputs_normalized}")

if(CONFIG_SHIELD_LiNEA40_LEFT OR CONFIG_SHIELD_LiNEA40_RIGHT)
  if(CONFIG_SHIELD_LiNEA40_RIGHT AND NOT KEYMAP_FILE STREQUAL linea40_aml_keymap)
    message(FATAL_ERROR "LiNEA40 AML and ZMK selected different keymaps")
  endif()
  zephyr_library()
  zephyr_include_directories(${CMAKE_CURRENT_LIST_DIR}/include)
  zephyr_library_sources_ifdef(CONFIG_ZMK_INPUT_PROCESSOR_GESTURE
    src/gesture_state.c
    src/input_processor_gesture.c)
  zephyr_library_sources_ifdef(CONFIG_LINEA40_CUSTOM_GESTURE2_MIGRATION
    src/keymap_migration.c)
endif()

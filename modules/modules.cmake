# Zephyr v3.5 runs module extensions before Devicetree preprocessing, after
# ZMK's keymap module has selected the actual keymap used by this build.
if("LiNEA40_right" IN_LIST SHIELD_AS_LIST)
  if(NOT KEYMAP_FILE)
    message(FATAL_ERROR "LiNEA40 AML generation requires a selected KEYMAP_FILE")
  endif()
  set(linea40_aml_keymap "${KEYMAP_FILE}")
  set(linea40_aml_generator "${CMAKE_CURRENT_LIST_DIR}/../scripts/generate-aml-exclusions.py")
  set(linea40_aml_header "${CMAKE_BINARY_DIR}/aml-exclusions.h")
  set(linea40_aml_depfile "${CMAKE_BINARY_DIR}/aml-keymap-inputs.txt")
  execute_process(
    COMMAND "${PYTHON_EXECUTABLE}" "${linea40_aml_generator}"
      "${linea40_aml_keymap}" "${linea40_aml_header}"
      --mouse-layer 1 --key-count 41 --depfile "${linea40_aml_depfile}"
    RESULT_VARIABLE linea40_aml_result
    ERROR_VARIABLE linea40_aml_error
  )
  if(NOT linea40_aml_result EQUAL 0)
    message(FATAL_ERROR "LiNEA40 AML generation failed: ${linea40_aml_error}")
  endif()
  file(STRINGS "${linea40_aml_depfile}" linea40_aml_inputs)
  # Zephyr 3.5 can lose a dependency when GCC packs multiple inputs on a line.
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    ${linea40_aml_inputs} "${linea40_aml_generator}"
    "${CMAKE_CURRENT_LIST_DIR}/../scripts/aml_keymap.py")
  list(APPEND DTS_EXTRA_CPPFLAGS "-I${CMAKE_BINARY_DIR}")
endif()

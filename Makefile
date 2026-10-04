.PHONY: verify test-gesture test-aml

verify: test-gesture test-aml
	python3 scripts/verify-linea40.py

test-aml:
	python3 tests/aml_exclusions_test.py

test-gesture:
	@TEST_BIN="$$(mktemp -t linea40-gesture-state-test.XXXXXX)"; \
		trap 'rm -f "$${TEST_BIN}"' EXIT; \
		cc -std=c11 -Wall -Wextra -Werror -Iinclude \
			src/gesture_state.c tests/gesture_state_test.c -o "$${TEST_BIN}"; \
		"$${TEST_BIN}"

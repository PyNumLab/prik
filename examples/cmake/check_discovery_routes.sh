#!/usr/bin/env bash
# Build this example once per PRIK CMake discovery route, then call the result.
#
# Run it from the repository root. Name routes as arguments to run a subset:
#   examples/cmake/check_discovery_routes.sh module-path find-package-dir
set -u

EXAMPLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PRIK_EXAMPLE_PYTHON:-python3}"
WORKSPACE="$(mktemp -d)"
trap 'rm -rf "$WORKSPACE"' EXIT

ALL_ROUTES=(module-path find-package-dir install-prefix scikit-build-core)
ROUTES=("$@")
if [ "${#ROUTES[@]}" -eq 0 ]; then
  ROUTES=("${ALL_ROUTES[@]}")
fi

failures=()
skips=()

prik() {
  "$PYTHON" -m prik "$@"
}

report() {  # outcome route detail
  printf '%-16s %-20s %s\n' "$1" "$2" "${3:-}"
}

call_built_module() {  # build_dir
  local artifact module_dir
  artifact="$(find "$1" -name 'heat*.so' -print -quit)"
  if [ -z "$artifact" ]; then
    echo "no built extension under $1" >&2
    return 1
  fi
  module_dir="$(dirname "$artifact")"
  PYTHONPATH="$module_dir${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" - <<'PYTHON'
import numpy

import heat

values = numpy.array([0.0, 1.0, 0.0])
stepped = heat.kernel.diffuse(values, numpy.float64(0.25))
assert stepped.tolist() == [0.0, 0.5, 0.0], stepped
assert heat.kernel.total(values) == 1.0
print(f"    diffuse({values.tolist()}, 0.25) -> {stepped.tolist()}")
PYTHON
}

configure_and_call() {  # route build_dir cmake_argument...
  local route="$1" build="$2"
  shift 2
  if ! cmake -S "$EXAMPLE_DIR" -B "$build" -DPython_EXECUTABLE="$("$PYTHON" -c 'import sys; print(sys.executable)')" \
       "$@" >"$build.log" 2>&1 ||
     ! cmake --build "$build" -j2 >>"$build.log" 2>&1; then
    tail -20 "$build.log" >&2
    failures+=("$route")
    report FAILED "$route" "see $build.log"
    return 1
  fi
  call_built_module "$build" || {
    failures+=("$route")
    report FAILED "$route" "built extension did not answer"
    return 1
  }
  report OK "$route"
}

route_module_path() {
  local module_dir
  module_dir="$(prik cmake-dir)" || {
    skips+=("module-path")
    report SKIPPED module-path "prik cmake-dir is unavailable"
    return 0
  }
  configure_and_call module-path "$WORKSPACE/module-path" \
    -DPRIK_DISCOVERY=include -DCMAKE_MODULE_PATH="$module_dir"
}

route_find_package_dir() {
  local module_dir
  module_dir="$(prik cmake-dir)" || {
    skips+=("find-package-dir")
    report SKIPPED find-package-dir "prik cmake-dir is unavailable"
    return 0
  }
  configure_and_call find-package-dir "$WORKSPACE/find-package-dir" \
    -DPRIK_DISCOVERY=find-package -DPRIK_DIR="$module_dir"
}

route_install_prefix() {
  local prefix
  if ! prefix="$(prik install-dir 2>/dev/null)"; then
    skips+=("install-prefix")
    report SKIPPED install-prefix "PRIK is not installed; run this route against an installed PRIK"
    return 0
  fi
  configure_and_call install-prefix "$WORKSPACE/install-prefix" \
    -DPRIK_DISCOVERY=find-package -DCMAKE_PREFIX_PATH="$prefix"
}

route_scikit_build_core() {
  local environment="$WORKSPACE/skbc" wheel
  "$PYTHON" -m venv "$environment" >/dev/null 2>&1
  if ! "$environment/bin/python" -m pip install --quiet scikit-build-core "$EXAMPLE_DIR/../.." \
       >"$WORKSPACE/skbc-install.log" 2>&1; then
    tail -5 "$WORKSPACE/skbc-install.log" >&2
    skips+=("scikit-build-core")
    report SKIPPED scikit-build-core "cannot install scikit-build-core and PRIK"
    return 0
  fi
  if ! "$environment/bin/python" -m pip wheel --no-build-isolation --no-deps \
       --wheel-dir "$WORKSPACE/skbc-wheel" "$EXAMPLE_DIR" \
       >"$WORKSPACE/skbc-build.log" 2>&1; then
    tail -20 "$WORKSPACE/skbc-build.log" >&2
    failures+=("scikit-build-core")
    report FAILED scikit-build-core "see $WORKSPACE/skbc-build.log"
    return 1
  fi
  wheel="$(find "$WORKSPACE/skbc-wheel" -name 'prik_cmake_example-*.whl' -print -quit)"
  "$environment/bin/python" -m pip install --quiet "$wheel" >/dev/null 2>&1
  if ! "$environment/bin/python" -c '
import numpy, heat
values = numpy.array([0.0, 1.0, 0.0])
stepped = heat.kernel.diffuse(values, numpy.float64(0.25))
assert stepped.tolist() == [0.0, 0.5, 0.0], stepped
print(f"    installed wheel: diffuse -> {stepped.tolist()}")
'; then
    failures+=("scikit-build-core")
    report FAILED scikit-build-core "the built wheel did not answer"
    return 1
  fi
  report OK scikit-build-core
}

for route in "${ROUTES[@]}"; do
  case "$route" in
    module-path) route_module_path ;;
    find-package-dir) route_find_package_dir ;;
    install-prefix) route_install_prefix ;;
    scikit-build-core) route_scikit_build_core ;;
    *)
      echo "unknown route: $route (known: ${ALL_ROUTES[*]})" >&2
      exit 2
      ;;
  esac
done

if [ "${#skips[@]}" -gt 0 ]; then
  echo "skipped: ${skips[*]}"
fi
if [ "${#failures[@]}" -gt 0 ]; then
  echo "failed: ${failures[*]}" >&2
  exit 1
fi

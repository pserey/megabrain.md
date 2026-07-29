#!/bin/sh
# megabrain conformance checker [D-18].
#
# Validates this instance against the spec_version declared in megabrain.md
# and exits non-zero on any MUST violation [D-19]. Managed-file drift is
# reported as a warning and does not fail conformance [D-3].
#
# This is a managed file. It is replaced wholesale on upgrade, and local edits
# are overwritten -- they survive only in git history.
#
# Usage, from anywhere inside the instance:
#   scripts/doctor.sh                    check everything
#   scripts/doctor.sh --format json      machine-readable output
#   scripts/doctor.sh --only lock-present,note-schema
#   scripts/doctor.sh --list-checks      enumerate the check registry

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
instance_root=$(dirname -- "$script_dir")

if ! command -v python3 >/dev/null 2>&1; then
    echo "doctor: python3 is required but was not found on PATH" >&2
    echo "doctor: install python3, then run this script again" >&2
    exit 2
fi

if [ "${1:-}" = "--list-checks" ]; then
    exec python3 "$script_dir/megabrain.py" list-checks
fi

exec python3 "$script_dir/megabrain.py" doctor --root "$instance_root" "$@"

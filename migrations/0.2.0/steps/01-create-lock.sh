#!/bin/sh
# Migration 0.1.0 -> 0.2.0, step create-lock.
#
# Writes the lock file a 0.1.0 install would have had, so that the upgrade has
# an anchor [D-6] and can warn about drifted managed files before overwriting
# them [D-16]. Idempotent: does nothing if a lock file already exists.
#
# Run from the instance root.

set -eu

LOCK=".megabrain/lock.json"

# The managed set as of 0.1.0. Frozen: this list describes a version that has
# already shipped, and must not be updated when later releases change theirs.
MANAGED_0_1_0="skills/core/add-item.md
skills/core/briefing.md
skills/core/capture.md
skills/core/complete-item.md
skills/core/extend-brain.md"

release="${MEGABRAIN_RELEASE:-v0.1.0}"
source_repo="${MEGABRAIN_SOURCE:-https://github.com/pserey/megabrain.md}"

if [ ! -f megabrain.md ]; then
    echo "create-lock: no megabrain.md here; run this from the instance root" >&2
    exit 1
fi

if [ -f "$LOCK" ]; then
    echo "create-lock: $LOCK already exists, nothing to do"
    exit 0
fi

sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | cut -d' ' -f1
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | cut -d' ' -f1
    else
        echo "create-lock: neither sha256sum nor shasum is available" >&2
        exit 1
    fi
}

for path in $MANAGED_0_1_0; do
    if [ ! -f "$path" ]; then
        echo "create-lock: managed file $path is missing; this does not look like a 0.1.0 instance" >&2
        exit 1
    fi
done

mkdir -p .megabrain

{
    echo '{'
    echo '  "spec_version": "0.1.0",'
    printf '  "release": "%s",\n' "$release"
    printf '  "source": "%s",\n' "$source_repo"
    printf '  "installed_at": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo '  "managed": {'
    first=1
    for path in $MANAGED_0_1_0; do
        [ "$first" -eq 1 ] || echo ','
        first=0
        printf '    "%s": "%s"' "$path" "$(sha256 "$path")"
    done
    echo ''
    echo '  }'
    echo '}'
} > "$LOCK"

echo "create-lock: wrote $LOCK for spec_version 0.1.0"

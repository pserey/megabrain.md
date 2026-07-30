#!/bin/sh
# Migration 0.1.0 -> 0.2.0, step bump-spec-version.
#
# Declares spec_version 0.2.0 in the manifest, leaving every other declaration
# alone. Idempotent: a manifest already at 0.2.0 is left untouched.
#
# Run from the instance root.

set -eu

MANIFEST="megabrain.md"

if [ ! -f "$MANIFEST" ]; then
    echo "bump-spec-version: no $MANIFEST here; run this from the instance root" >&2
    exit 1
fi

current="$(sed -n 's/^spec_version:[[:space:]]*"\{0,1\}\([0-9][0-9.]*\)"\{0,1\}[[:space:]]*$/\1/p' \
    "$MANIFEST" | head -n 1)"

case "$current" in
    0.2.0)
        echo "bump-spec-version: $MANIFEST already declares 0.2.0, nothing to do"
        exit 0
        ;;
    0.1.0)
        ;;
    "")
        echo "bump-spec-version: $MANIFEST declares no spec_version" >&2
        exit 1
        ;;
    *)
        echo "bump-spec-version: $MANIFEST declares $current, expected 0.1.0; this pack is out of order" >&2
        exit 1
        ;;
esac

tmp="$(mktemp)"
sed 's/^spec_version:[[:space:]]*"\{0,1\}0\.1\.0"\{0,1\}[[:space:]]*$/spec_version: "0.2.0"/' \
    "$MANIFEST" > "$tmp"

if ! grep -q '^spec_version: "0.2.0"$' "$tmp"; then
    rm -f "$tmp"
    echo "bump-spec-version: the rewrite did not take; $MANIFEST is unchanged" >&2
    exit 1
fi

cat "$tmp" > "$MANIFEST"
rm -f "$tmp"

echo "bump-spec-version: $MANIFEST now declares spec_version 0.2.0"

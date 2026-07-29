#!/usr/bin/env bash
#
# Build the release tarball. Used by the release workflow and by anyone
# testing an install locally, so that what is tested is what ships.
#
#   tools/build-release.sh [output-directory]
#
# The tarball carries template/ (what an install produces), migrations/ (every
# pack, so a whole chain is executable from one download [D-21]), MANAGED (the
# release's managed-file set) and VERSION.

set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
out_dir="${1:-$repo_root/dist}"
asset="megabrain-template.tar.gz"

cd "$repo_root"

version="$(tr -d '[:space:]' < VERSION)"
[ -n "$version" ] || { echo "build: VERSION is empty" >&2; exit 1; }

manifest_version="$(sed -n 's/^spec_version:[[:space:]]*"\{0,1\}\([0-9][0-9.]*\)"\{0,1\}[[:space:]]*$/\1/p' \
    template/megabrain.md | head -n 1)"
if [ "$manifest_version" != "$version" ]; then
    echo "build: VERSION is $version but template/megabrain.md declares ${manifest_version:-nothing}" >&2
    exit 1
fi

# Every managed path the release declares must actually be in the template.
missing=0
while IFS= read -r line; do
    case "$line" in ''|'#'*) continue ;; esac
    if [ ! -f "template/$line" ]; then
        echo "build: MANAGED declares template/$line, which does not exist" >&2
        missing=1
    fi
done < MANAGED
[ "$missing" -eq 0 ] || exit 1

if [ ! -d migrations ]; then
    echo "build: no migrations/ directory" >&2
    exit 1
fi

mkdir -p "$out_dir"
rm -f "$out_dir/$asset"

# Reproducible-ish: sorted entries, no owner metadata, no macOS extended attrs.
COPYFILE_DISABLE=1 tar \
    --format=ustar \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    -czf "$out_dir/$asset" \
    template migrations MANAGED VERSION

echo "built $out_dir/$asset for megabrain $version"

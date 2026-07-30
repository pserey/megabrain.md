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

# The managed set as of 0.1.0, with the SHA-256 each file had as 0.1.0 shipped
# it. Frozen: this describes a version that has already shipped, and must not
# be updated when a later release changes its managed set or its contents.
#
# The reference hashes, not the hashes of the files on disk, are what gets
# written to the lock. Hashing what is already there would record a user's
# local edits as if they were the release, and the drift warning of [D-16]
# would never fire for anything modified before this lock existed -- which is
# precisely the case this lock is here to catch.
MANAGED_0_1_0="skills/core/add-item.md:72b9e617fbb99803fd298719c9d7d7af9c65cb1c457335be84463bba766d76f7
skills/core/briefing.md:b83344d3f4c11ed7e2d4cbb57b30d0ae10d91a642d79ead0b3e9feaee3b555ef
skills/core/capture.md:d1811c522f42cfbf15c24d1df405378741f60a3aee9e5cb35be714b8148d94b5
skills/core/complete-item.md:cef62662533cbbc156d114079db1de26badec52f371756c6862d87b64770c113
skills/core/extend-brain.md:deffd4b5fa0b0a658250274ab21ff5ff00c477be7c467551c0468dce83ac3273"

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

for entry in $MANAGED_0_1_0; do
    path="${entry%%:*}"
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
    for entry in $MANAGED_0_1_0; do
        [ "$first" -eq 1 ] || echo ','
        first=0
        printf '    "%s": "%s"' "${entry%%:*}" "${entry##*:}"
    done
    echo ''
    echo '  }'
    echo '}'
} > "$LOCK"

drifted=0
for entry in $MANAGED_0_1_0; do
    path="${entry%%:*}"
    if [ "$(sha256 "$path")" != "${entry##*:}" ]; then
        echo "create-lock: $path differs from the 0.1.0 release"
        drifted=$((drifted + 1))
    fi
done

echo "create-lock: wrote $LOCK for spec_version 0.1.0 ($drifted of 5 managed files drifted)"

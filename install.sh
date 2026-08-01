#!/usr/bin/env bash
#
# megabrain installer.
#
# Scaffolds a new megabrain instance from a tagged release, initialises it as a
# plain private git repository, and stamps .megabrain/lock.json as the upgrade
# anchor [D-4]. The instance has no fork relationship with the spec repository,
# so it is private by construction.
#
#   curl -fsSL https://megabrain.serey.uk/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --dir ~/brain --version 0.2.0
#
# The installer asks nothing. Tailoring the brain -- timezone, domains, entity
# types -- is the agent's job, through the onboard procedure the template ships
# with. Run `bash install.sh --help` for the flags.

set -euo pipefail

DEFAULT_SOURCE="https://github.com/pserey/megabrain.md"
ASSET="megabrain-template.tar.gz"

target_dir="megabrain"
version=""
source_repo="$DEFAULT_SOURCE"
local_tarball=""
force=0

die() { printf 'install: %s\n' "$*" >&2; exit 1; }
info() { printf '  %s\n' "$*"; }

usage() {
    cat <<'EOF'
megabrain installer

Usage: install.sh [options]

  --dir PATH        where to create the instance (default: ./megabrain)
  --version X.Y.Z   install this release (default: the latest release)
  --source URL      spec repository to install from
  --tarball PATH    install from a local tarball instead of downloading;
                    for developing the standard, not for normal use
  --force           install into a directory that is not empty
  --help            show this message

The installer never prompts. Once it finishes, point your agent at the new
repository and ask it to onboard you.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --dir) [ $# -ge 2 ] || die "--dir needs a path"; target_dir="$2"; shift 2 ;;
        --version) [ $# -ge 2 ] || die "--version needs a version"; version="$2"; shift 2 ;;
        --source) [ $# -ge 2 ] || die "--source needs a URL"; source_repo="${2%/}"; shift 2 ;;
        --tarball) [ $# -ge 2 ] || die "--tarball needs a path"; local_tarball="$2"; shift 2 ;;
        --force) force=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) die "unknown option '$1' (try --help)" ;;
    esac
done

# --- dependencies ----------------------------------------------------------

for tool in tar git python3; do
    command -v "$tool" >/dev/null 2>&1 || die "$tool is required but was not found on PATH"
done

download() {
    local url="$1" dest="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$dest"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$dest" "$url"
    else
        die "curl or wget is required to download a release"
    fi
}

# --- target ----------------------------------------------------------------

if [ -e "$target_dir" ] && [ ! -d "$target_dir" ]; then
    die "$target_dir exists and is not a directory"
fi
if [ -d "$target_dir" ] && [ -n "$(ls -A "$target_dir" 2>/dev/null)" ] && [ "$force" -eq 0 ]; then
    die "$target_dir is not empty (pass --force to install into it anyway)"
fi
if [ -f "$target_dir/megabrain.md" ]; then
    die "$target_dir already holds a megabrain; upgrade it by asking your agent to upgrade this brain"
fi

mkdir -p "$target_dir"
target_dir="$(cd "$target_dir" && pwd)"

work="$(mktemp -d)"
cleanup() { rm -rf "$work"; }
trap cleanup EXIT

# --- fetch -----------------------------------------------------------------

echo "megabrain installer"

if [ -n "$local_tarball" ]; then
    [ -f "$local_tarball" ] || die "no such tarball: $local_tarball"
    info "using local tarball $local_tarball"
    cp "$local_tarball" "$work/$ASSET"
    release="local"
else
    if [ -n "$version" ]; then
        url="$source_repo/releases/download/v$version/$ASSET"
        release="v$version"
    else
        url="$source_repo/releases/latest/download/$ASSET"
        release=""
    fi
    info "downloading $url"
    download "$url" "$work/$ASSET" || die "could not download the release from $url"
fi

mkdir -p "$work/unpacked"
tar -xzf "$work/$ASSET" -C "$work/unpacked" || die "the release tarball could not be extracted"

# Tolerate a tarball with or without a single top-level wrapper directory.
payload="$work/unpacked"
if [ ! -d "$payload/template" ]; then
    inner="$(find "$work/unpacked" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
    [ -n "$inner" ] && [ -d "$inner/template" ] || die "the tarball has no template/ directory"
    payload="$inner"
fi
for required in template MANAGED VERSION; do
    [ -e "$payload/$required" ] || die "the tarball is malformed: no $required"
done

spec_version="$(tr -d '[:space:]' < "$payload/VERSION")"
[ -n "$spec_version" ] || die "the tarball's VERSION file is empty"
[ -n "$release" ] || release="v$spec_version"

manifest_version="$(sed -n 's/^spec_version:[[:space:]]*"\{0,1\}\([0-9][0-9.]*\)"\{0,1\}[[:space:]]*$/\1/p' \
    "$payload/template/megabrain.md" | head -n 1)"
if [ "$manifest_version" != "$spec_version" ]; then
    die "the release is malformed: VERSION says $spec_version but the template manifest says ${manifest_version:-nothing}"
fi

info "installing megabrain $spec_version ($release) into $target_dir"

# --- scaffold --------------------------------------------------------------

cp -R "$payload/template/." "$target_dir/"

if [ ! -d "$target_dir/.git" ]; then
    git -C "$target_dir" init -q
    info "initialised a git repository (no fork relationship with $source_repo)"
fi

python3 "$target_dir/scripts/megabrain.py" lock write \
    --root "$target_dir" \
    --release "$release" \
    --source "$source_repo" \
    --spec-version "$spec_version" \
    --managed-list "$payload/MANAGED" \
    | sed 's/^/  /'

# --- first commit ----------------------------------------------------------

git -C "$target_dir" add -A
if git -C "$target_dir" -c user.name=megabrain -c user.email=megabrain@localhost \
        commit -q -m "add: megabrain instance from $release" 2>/dev/null; then
    info "committed the initial tree"
else
    info "could not create the initial commit; the tree is staged, commit it yourself"
fi

# --- verify ----------------------------------------------------------------

echo ""
if sh "$target_dir/scripts/doctor.sh"; then
    :
else
    echo ""
    echo "install: the instance was created but does not pass conformance." >&2
    echo "install: report the violations above against $source_repo." >&2
    exit 1
fi

cat <<EOF

Done. Your megabrain is at $target_dir

Next, point an agent at it and ask it to onboard you -- the template ships an
onboard procedure for exactly this, reachable by saying "set up my brain". The
agent is the primary operator: it reads AGENTS.md, follows the procedures in
skills/, and is the only supported way to upgrade when a new release lands.

  cd $target_dir
EOF

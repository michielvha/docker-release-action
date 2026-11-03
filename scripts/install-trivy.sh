#!/usr/bin/env bash
# Copyright 2026 Michiel VH. Licensed under the Apache License, Version 2.0.
set -euo pipefail

version=${1:?Expected a Trivy version}
architecture=${2:?Expected a runner architecture}
destination=${3:?Expected an installation directory}
script_directory=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [[ ! "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo 'Expected a stable Trivy version such as v0.69.3' >&2
  exit 1
fi
case "$architecture" in
  X64) platform=Linux-64bit ;;
  ARM64) platform=Linux-ARM64 ;;
  *) echo "Unsupported Linux runner architecture: $architecture" >&2; exit 1 ;;
esac

asset="trivy_${version#v}_${platform}.tar.gz"

# Match exactly one asset; never pass unrelated paths from the downloaded list
# to sha256sum. Expected digests belong to this reviewed action commit, so
# replacing an upstream archive and checksum file cannot replace the pin.
expected=$(awk -v asset="$asset" '$2 == asset { print $1 }' "$script_directory/trivy-checksums.txt")
if [[ ! "$expected" =~ ^[[:xdigit:]]{64}$ ]]; then
  echo "Expected exactly one SHA-256 checksum for $asset" >&2
  exit 1
fi
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
base="https://github.com/aquasecurity/trivy/releases/download/$version"
curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
  --retry 3 --connect-timeout 15 --max-time 180 \
  "$base/$asset" --output "$temporary/$asset"
printf '%s  %s\n' "$expected" "$asset" > "$temporary/selected-checksum.txt"
(cd "$temporary" && sha256sum --check selected-checksum.txt)

# Extract only the executable and reject links or special files before install.
tar -xzf "$temporary/$asset" -C "$temporary" -- trivy
if [[ ! -f "$temporary/trivy" || -L "$temporary/trivy" ]]; then
  echo 'The Trivy release did not contain a regular executable' >&2
  exit 1
fi
mkdir -p "$destination"
install -m 0755 "$temporary/trivy" "$destination/trivy"

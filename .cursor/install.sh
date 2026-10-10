#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

export DEBIAN_FRONTEND=noninteractive
if ! command -v pandoc >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y --no-install-recommends pandoc unzip
fi

bash .cursor/verify-repo.sh

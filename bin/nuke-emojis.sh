#!/usr/bin/env bash
set -euo pipefail

find . -type f -name '*.md' -exec \
    perl -CSD -pi -e 's/[\x{1F300}-\x{1FAFF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}\x{2300}-\x{23FF}\x{FE0F}]\s*//g' {} +

exit 0
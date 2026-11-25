#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

help_output="$(uv run agridrone --help)"

for command in mock analyze mission openapi db; do
    if ! grep -Eq "(^|[[:space:]])${command}([[:space:]]|$)" <<<"${help_output}"; then
        echo "Command '${command}' is missing from 'agridrone --help'" >&2
        exit 1
    fi
done

uv run agridrone openapi --check

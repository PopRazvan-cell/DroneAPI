#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

export AGRIDRONE_UID="${AGRIDRONE_UID:-$(id -u)}"
export AGRIDRONE_GID="${AGRIDRONE_GID:-$(id -g)}"

if [[ ! -f .env ]]; then
    cp .env.example .env
fi

mkdir -p data/store/_uploads data/synthetic data/public data/samples data/work

docker compose --env-file .env -f infra/docker-compose.yml up -d --wait --wait-timeout 420

for service in postgis redis tusd worker; do
    container_id="$(docker compose --env-file .env -f infra/docker-compose.yml ps -q "${service}")"
    if [[ -z "${container_id}" ]]; then
        echo "Service ${service} has no container" >&2
        exit 1
    fi
    status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_id}")"
    if [[ "${status}" != "healthy" ]]; then
        echo "Service ${service} is ${status}, expected healthy" >&2
        exit 1
    fi
    echo "Service ${service}: healthy"
done

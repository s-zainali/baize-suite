#!/usr/bin/env bash
set -euo pipefail
IMAGE=baize-local
docker build -f Dockerfile.local -t "$IMAGE" \
  --build-arg VITE_LICENSE_SERVER_URL="${VITE_LICENSE_SERVER_URL:-https://license.baize.pk}" .
echo "✓ built $IMAGE — backend is a compiled binary, not .py"
if [ "${1:-}" = "run" ]; then
  docker run --rm -p 5000:5000 \
    -e DATABASE_URL="${DATABASE_URL:?set DATABASE_URL}" \
    -e ENFORCE_LICENSE=1 -e DEVICE_BINDING=on \
    -e LICENSE_SERVER_URL="${LICENSE_SERVER_URL:-https://license.baize.pk}" \
    -e LICENSE_PUBLIC_KEY="${LICENSE_PUBLIC_KEY:?set LICENSE_PUBLIC_KEY}" \
    "$IMAGE"
fi
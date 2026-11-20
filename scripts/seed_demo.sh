#!/usr/bin/env bash
# Load the sample corpus into a running RAGForge server.
# Usage: scripts/seed_demo.sh <username> <password> [api-url]
set -euo pipefail

USER_NAME=${1:?username required}
PASSWORD=${2:?password required}
API=${3:-http://localhost:8000}
ROOT=$(cd "$(dirname "$0")/.." && pwd)

login() {
  curl -sf -X POST "$API/auth/$1" -H 'Content-Type: application/json' \
    -d "{\"username\": \"$USER_NAME\", \"password\": \"$PASSWORD\"}"
}
TOKEN=$( (login login || login register) | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

for file in "$ROOT"/samples/corpus/*; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" \
    -F "file=@$file" -F collection=samples "$API/documents")
  echo "$code $(basename "$file")"
done

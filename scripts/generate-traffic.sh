#!/usr/bin/env bash
# Generates realistic API traffic so the Grafana dashboard has live data.
# Usage: scripts/generate-traffic.sh [base_url] [seconds]
set -euo pipefail
BASE="${1:-http://pantrypal.localtest.me}"
DURATION="${2:-120}"
end=$(( $(date +%s) + DURATION ))
names=(Oats Lentils Tomatoes Cheddar Butter Pasta Honey Coffee Apples Tofu)
cats=(Grains Grains Produce Dairy Dairy Grains Other Beverages Produce Other)
echo "Sending traffic to $BASE for ${DURATION}s..."
while [ "$(date +%s)" -lt "$end" ]; do
  i=$(( RANDOM % ${#names[@]} ))
  curl -s -o /dev/null "$BASE/api/items"
  curl -s -o /dev/null "$BASE/api/items/stats"
  curl -s -o /dev/null "$BASE/api/items?category=${cats[$i]}"
  id=$(curl -s -X POST "$BASE/api/items" -H 'content-type: application/json' \
        -d "{\"name\":\"${names[$i]}\",\"category\":\"${cats[$i]}\",\"quantity\":$(( RANDOM % 5 + 1 )),\"unit\":\"pcs\"}" \
        | sed -E 's/.*"id":([0-9]+).*/\1/')
  curl -s -o /dev/null "$BASE/api/items/$id"
  curl -s -o /dev/null -X PUT "$BASE/api/items/$id" -H 'content-type: application/json' -d '{"quantity":1}'
  curl -s -o /dev/null -X DELETE "$BASE/api/items/$id"
  curl -s -o /dev/null "$BASE/api/items/999999"   # deliberate 404s
  sleep 0.2
done
echo "done"

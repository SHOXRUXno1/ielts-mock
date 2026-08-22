#!/bin/bash
set -euo pipefail
echo '=== backend last 200 speaking/error lines ==='
docker logs --since 2h ielts-mock-backend-1 2>&1 | tail -n 250

#!/bin/bash
# Install one Practice Set B test into the running production backend.
#
# Runs ON THE SERVER. Expects the test's files already staged in /tmp/pb_stage:
#   /tmp/pb_stage/media/practice_b_t<N>_*        audio and images
#   /tmp/pb_stage/scripts/*.py                   seed, verify and check scripts
#   /tmp/pb_stage/scripts/data/practice_b_t<N>/  passages and section titles
#
# The test is only published when both gates pass, so a half-authored test
# cannot become visible to students.
#
# Usage (from the workstation):
#   scp -i <key> ... root@<host>:/tmp/pb_stage/...
#   ssh -i <key> root@<host> "bash /tmp/pb_stage/deploy_practice_b.sh 1 --publish"

set -euo pipefail

N="${1:?usage: deploy_practice_b.sh <test-number> [--publish]}"
PUBLISH="${2:-}"
C=ielts-mock-backend-1
STAGE=/tmp/pb_stage

echo "=== media ==="
shopt -s nullglob
for f in "$STAGE"/media/practice_b_t${N}_*.mp3; do
  docker cp "$f" $C:/app/media/audio/
  echo "  audio  $(basename "$f")"
done
for f in "$STAGE"/media/practice_b_t${N}_*.png; do
  docker cp "$f" $C:/app/media/images/
  echo "  image  $(basename "$f")"
done

echo
echo "=== scripts ==="
docker exec $C sh -c "mkdir -p /app/scripts/data/practice_b_t${N}"
for f in "$STAGE"/scripts/*.py; do
  docker cp "$f" $C:/app/scripts/
done
for f in "$STAGE"/scripts/data/practice_b_t${N}/*; do
  docker cp "$f" $C:/app/scripts/data/practice_b_t${N}/
done
echo "  copied $(ls "$STAGE"/scripts/*.py | wc -l) script(s) and the test's data files"

echo
echo "=== seed ==="
docker exec -w /app $C python scripts/seed_practice_b_bootstrap.py "$N"
for skill in listening reading writing speaking; do
  docker exec -w /app $C python "scripts/seed_practice_b_t${N}_${skill}.py"
done

echo
echo "=== gate: structure and media ==="
docker exec -w /app $C python scripts/verify_practice_b.py "$N" | tail -n 20

echo
echo "=== gate: marking ==="
docker exec -w /app $C python scripts/check_practice_b_scoring.py "$N"

if [ "$PUBLISH" = "--publish" ]; then
  echo
  echo "=== publish ==="
  docker exec -w /app $C python scripts/publish_practice_b.py "$N"
else
  echo
  echo "Not published. Re-run with --publish to make it visible to students."
fi

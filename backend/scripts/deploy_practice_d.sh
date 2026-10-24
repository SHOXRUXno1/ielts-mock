#!/bin/bash
# Install one Practice Set D test into the running production backend.
#
# Runs ON THE SERVER. Expects the test's files already staged in /tmp/pd_stage:
#   /tmp/pd_stage/media/practice_d_t<N>_*        audio and images
#   /tmp/pd_stage/scripts/*.py                   seed, verify and check scripts
#   /tmp/pd_stage/scripts/data/practice_d_t<N>/  passages and section titles
#
# The test is only published when both gates pass, so a half-authored test
# cannot become visible to students.
#
# Usage (from the workstation):
#   scp -i <key> ... root@<host>:/tmp/pd_stage/...
#   ssh -i <key> root@<host> "bash /tmp/pd_stage/deploy_practice_d.sh 1 --publish"

set -euo pipefail

N="${1:?usage: deploy_practice_d.sh <test-number> [--publish]}"
PUBLISH="${2:-}"
C=ielts-mock-backend-1
STAGE=/tmp/pd_stage

case "$N" in
  1) TASK1_ASSET=practice_d_t1_writing_task1_v2.svg ;;
  2) TASK1_ASSET=practice_d_t2_writing_task1_v2.jpg ;;
  3|4) TASK1_ASSET="practice_d_t${N}_writing_task1.png" ;;
  *) TASK1_ASSET= ;;
esac
if [ -n "$TASK1_ASSET" ]; then
  docker exec "$C" test -f "/app/scripts/assets/$TASK1_ASSET" || {
    echo "Missing canonical Writing Task 1 image: $TASK1_ASSET" >&2
    exit 1
  }
fi

echo "=== media ==="
shopt -s nullglob
for f in "$STAGE"/media/practice_d_t${N}_*.mp3; do
  docker cp "$f" $C:/app/media/audio/
  echo "  audio  $(basename "$f")"
done
for f in "$STAGE"/media/practice_d_t${N}_*.png \
         "$STAGE"/media/practice_d_t${N}_*.jpg \
         "$STAGE"/media/practice_d_t${N}_*.jpeg \
         "$STAGE"/media/practice_d_t${N}_*.svg; do
  docker cp "$f" $C:/app/media/images/
  echo "  image  $(basename "$f")"
done
# Canonical Writing Task 1 assets ship with the backend image. Apply them last
# so stale manually staged files cannot silently restore an unrelated chart.
if [ -n "$TASK1_ASSET" ]; then
  docker exec "$C" cp "/app/scripts/assets/$TASK1_ASSET" /app/media/images/
  echo "  image  $TASK1_ASSET (canonical)"
fi

echo
echo "=== scripts ==="
docker exec $C sh -c "mkdir -p /app/scripts/data/practice_d_t${N}"
for f in "$STAGE"/scripts/*.py; do
  docker cp "$f" $C:/app/scripts/
done
for f in "$STAGE"/scripts/data/practice_d_t${N}/*; do
  docker cp "$f" $C:/app/scripts/data/practice_d_t${N}/
done
echo "  copied $(ls "$STAGE"/scripts/*.py | wc -l) script(s) and the test's data files"

echo
echo "=== seed ==="
docker exec -w /app $C python scripts/seed_practice_d_bootstrap.py "$N"
for skill in listening reading writing speaking; do
  docker exec -w /app $C python "scripts/seed_practice_d_t${N}_${skill}.py"
done

echo
echo "=== gate: structure and media ==="
docker exec -w /app $C python scripts/verify_practice_d.py "$N" | tail -n 20

echo
echo "=== gate: marking ==="
docker exec -w /app $C python scripts/check_practice_d_scoring.py "$N"

if [ "$PUBLISH" = "--publish" ]; then
  echo
  echo "=== publish ==="
  docker exec -w /app $C python scripts/publish_practice_d.py "$N"
else
  echo
  echo "Not published. Re-run with --publish to make it visible to students."
fi

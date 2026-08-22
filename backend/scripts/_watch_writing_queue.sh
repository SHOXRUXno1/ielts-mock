#!/bin/sh
# Sample writing job queue every 2s for 6 minutes.
end=$(( $(date +%s) + 360 ))
echo "ts,pending,processing,done,failed"
while [ "$(date +%s)" -lt "$end" ]; do
  row=$(docker exec ielts-mock-db-1 psql -U postgres -d ielts_mock -tAc "
    SELECT
      COALESCE(SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END),0),
      COALESCE(SUM(CASE WHEN status='processing' THEN 1 ELSE 0 END),0),
      COALESCE(SUM(CASE WHEN status='done' THEN 1 ELSE 0 END),0),
      COALESCE(SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END),0)
    FROM evaluation_jobs
    WHERE section_type='writing'
      AND created_at > NOW() - INTERVAL '20 minutes';
  " | tr -d ' ')
  echo "$(date -u +%H:%M:%S),$row"
  sleep 2
done

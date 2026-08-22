#!/bin/bash
set -euo pipefail
docker cp /tmp/_probe_groq_stt.py ielts-mock-backend-1:/tmp/_probe_groq_stt.py
docker exec -w /app -e PYTHONPATH=/app ielts-mock-backend-1 python /tmp/_probe_groq_stt.py

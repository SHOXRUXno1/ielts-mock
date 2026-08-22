#!/usr/bin/env python3
"""Measure the real rate ceiling of the production Gemini key.

Fires a burst of concurrent generateContent calls and reports how many are
accepted versus rejected with 429 RESOURCE_EXHAUSTED. Google returns the
tripped quota metric and a retry delay in the 429 body, which tells us whether
the wall is per-minute or per-day.

Run from a network Google does not block:

  $env:PROD_GEMINI_KEY='...'; py scripts/_probe_gemini_quota.py --burst 20
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time
from collections import Counter

import httpx

MODEL = os.getenv("PROD_GEMINI_MODEL", "gemini-3.1-flash-lite")
URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
)


async def one_call(client: httpx.AsyncClient, key: str, idx: int) -> dict:
    started = time.perf_counter()
    try:
        resp = await client.post(
            URL,
            params={"key": key},
            json={"contents": [{"parts": [{"text": f"Say OK. #{idx}"}]}]},
        )
    except Exception as exc:  # noqa: BLE001
        return {"idx": idx, "status": "ERR", "detail": f"{type(exc).__name__}: {exc}"}

    elapsed = (time.perf_counter() - started) * 1000
    out = {"idx": idx, "status": resp.status_code, "ms": round(elapsed)}
    if resp.status_code != 200:
        try:
            err = resp.json().get("error", {})
        except Exception:  # noqa: BLE001
            err = {}
        out["detail"] = err.get("message", resp.text[:120])
        quotas = []
        for item in err.get("details", []) or []:
            for viol in item.get("violations", []) or []:
                metric = viol.get("quotaMetric", "") or viol.get("quotaId", "")
                if metric:
                    quotas.append(metric.split("/")[-1])
            if item.get("retryDelay"):
                out["retry_after"] = item["retryDelay"]
        if quotas:
            out["quota"] = ",".join(sorted(set(quotas)))
    return out


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--burst", type=int, default=20)
    args = parser.parse_args()

    key = os.getenv("PROD_GEMINI_KEY", "")
    if not key:
        raise SystemExit("Set PROD_GEMINI_KEY first")

    print(f"model={MODEL}  firing {args.burst} concurrent requests\n")
    async with httpx.AsyncClient(timeout=90.0) as client:
        started = time.perf_counter()
        results = await asyncio.gather(
            *(one_call(client, key, i) for i in range(1, args.burst + 1))
        )
        wall = time.perf_counter() - started

    counts = Counter(str(r["status"]) for r in results)
    ok = counts.get("200", 0)
    print(f"wall clock: {wall:.1f}s")
    print(f"accepted:   {ok}/{args.burst}")
    print(f"statuses:   {dict(counts)}\n")

    latencies = sorted(r["ms"] for r in results if r["status"] == 200)
    if latencies:
        p50 = latencies[len(latencies) // 2]
        print(f"200 latency p50={p50}ms  max={latencies[-1]}ms\n")

    seen: set[str] = set()
    for r in results:
        if r["status"] == 200:
            continue
        sig = f"{r['status']}|{r.get('quota', '')}|{str(r.get('detail'))[:80]}"
        if sig in seen:
            continue
        seen.add(sig)
        print(f"  HTTP {r['status']}")
        if r.get("quota"):
            print(f"    quota tripped: {r['quota']}")
        if r.get("retry_after"):
            print(f"    retry after:   {r['retry_after']}")
        print(f"    message:       {str(r.get('detail'))[:200]}")


if __name__ == "__main__":
    asyncio.run(main())

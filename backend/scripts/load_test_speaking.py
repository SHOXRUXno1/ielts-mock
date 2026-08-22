#!/usr/bin/env python3
"""Speaking burst load test — N students run full AI examiner sessions at once.

Each simulated student walks the real live-examiner flow: Simli token, /start,
then ~13 turns of (upload audio -> Groq Whisper STT -> next question -> TTS),
then Gemini scoring. Answers come from pre-rendered MP3s so Whisper receives
genuine speech.

Generate the audio once first:
  python scripts/_gen_speaking_audio.py

Then run, e.g. against production:
  python scripts/load_test_speaking.py \\
      --base-url https://mock.shox-software.uz \\
      --admin-login Adminbek --admin-password '...' \\
      --students 20

Reports per-endpoint latency percentiles, upstream Whisper time, TTS fallback
rate, Simli video-vs-audio-only split, per-session wall time and every error.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import httpx

AUDIO_DIR = Path(__file__).parent / "_speaking_audio"
# Hard stop so a runaway session can never loop forever; the server forces the
# end at MAX_EXAMINER_TURNS=15.
MAX_TURNS = 18


def load_audio() -> list[bytes]:
    clips = sorted(AUDIO_DIR.glob("turn_*.mp3"))
    if not clips:
        raise SystemExit(
            f"No audio in {AUDIO_DIR}. Run scripts/_gen_speaking_audio.py first."
        )
    return [p.read_bytes() for p in clips]


@dataclass
class Metrics:
    latency: dict[str, list[float]] = field(default_factory=dict)
    whisper_ms: list[int] = field(default_factory=list)
    tts_ms: list[int] = field(default_factory=list)
    tts_errors: Counter = field(default_factory=Counter)
    tts_cache_hits: Counter = field(default_factory=Counter)
    simli: Counter = field(default_factory=Counter)
    http_errors: Counter = field(default_factory=Counter)

    def add(self, name: str, seconds: float) -> None:
        self.latency.setdefault(name, []).append(seconds)

    def report_latency(self) -> None:
        print("\n=== Latency (seconds) ===")
        print(f"{'endpoint':34s} {'n':>5}  {'p50':>7} {'p95':>7} {'max':>7}")
        for name, vals in sorted(self.latency.items()):
            if not vals:
                continue
            ordered = sorted(vals)
            p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
            print(
                f"{name:34s} {len(vals):5d}  "
                f"{statistics.median(ordered):7.2f} {p95:7.2f} {max(ordered):7.2f}"
            )


async def timed(metrics: Metrics, name: str, coro):
    t0 = time.perf_counter()
    try:
        return await coro
    finally:
        metrics.add(name, time.perf_counter() - t0)


@dataclass
class SessionResult:
    phone: str
    session_id: str | None = None
    band: float | None = None
    turns: int = 0
    simli_enabled: bool | None = None
    wall_seconds: float = 0.0
    error: str | None = None


async def provision_student(
    client: httpx.AsyncClient, admin_jwt: str, phone: str, metrics: Metrics
) -> str:
    create = await client.post(
        "/admin/students/",
        headers={"Authorization": f"Bearer {admin_jwt}"},
        json={
            "phone": phone,
            "full_name": f"LoadSpeaking {phone[-4:]}",
            "group_name": "load-speaking",
        },
    )
    if create.status_code not in (200, 201, 400, 409):
        create.raise_for_status()

    login = await timed(
        metrics,
        "POST /auth/login",
        client.post("/auth/login", json={"login": phone, "password": phone}),
    )
    login.raise_for_status()
    return login.json()["access_token"]


def record_timings(metrics: Metrics, body: dict) -> None:
    timings = body.get("timings") or {}
    if not isinstance(timings, dict):
        return
    if isinstance(timings.get("whisper_ms"), int):
        metrics.whisper_ms.append(timings["whisper_ms"])
    if isinstance(timings.get("tts_ms"), int):
        metrics.tts_ms.append(timings["tts_ms"])
    if timings.get("tts_cache_hit") is not None:
        metrics.tts_cache_hits[bool(timings["tts_cache_hit"])] += 1


async def run_session(
    base_url: str,
    token: str,
    phone: str,
    clips: list[bytes],
    metrics: Metrics,
    gate: asyncio.Event,
    think_seconds: float,
) -> SessionResult:
    out = SessionResult(phone=phone)
    started = time.perf_counter()
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(180.0, connect=30.0),
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        try:
            await gate.wait()

            simli = await timed(
                metrics,
                "GET /simli-token",
                client.get("/admin/speaking-examiner/simli-token"),
            )
            if simli.status_code == 200:
                body = simli.json()
                out.simli_enabled = bool(body.get("enabled"))
                metrics.simli[
                    "video" if out.simli_enabled else f"fallback:{body.get('reason')}"
                ] += 1
            else:
                metrics.http_errors[f"simli-token {simli.status_code}"] += 1

            start = await timed(
                metrics,
                "POST /start",
                client.post("/admin/speaking-examiner/start", json={}),
            )
            if start.status_code != 200:
                out.error = f"start {start.status_code}: {start.text[:200]}"
                return out
            turn = start.json()
            out.session_id = turn.get("session_id")
            record_timings(metrics, turn)

            for i in range(MAX_TURNS):
                if turn.get("is_end"):
                    break
                if think_seconds:
                    await asyncio.sleep(think_seconds)

                clip = clips[min(i, len(clips) - 1)]
                resp = await timed(
                    metrics,
                    "POST /transcribe-and-respond",
                    client.post(
                        "/admin/speaking-examiner/transcribe-and-respond",
                        params={"session_id": out.session_id},
                        files={"file": ("answer.mp3", clip, "audio/mpeg")},
                    ),
                )
                if resp.status_code != 200:
                    metrics.http_errors[
                        f"transcribe-and-respond {resp.status_code}"
                    ] += 1
                    out.error = (
                        f"turn {i + 1} transcribe {resp.status_code}: "
                        f"{resp.text[:200]}"
                    )
                    return out
                turn = resp.json()
                out.turns += 1
                record_timings(metrics, turn)

                # The live flow defers TTS, so the client always asks for audio.
                if not turn.get("audio_base64"):
                    synth = await timed(
                        metrics,
                        "POST /synthesize-turn",
                        client.post(
                            "/admin/speaking-examiner/synthesize-turn",
                            json={
                                "text": turn.get("text") or "",
                                "part": turn.get("part") or 1,
                                "cue_card": turn.get("cue_card"),
                            },
                        ),
                    )
                    if synth.status_code == 200:
                        sbody = synth.json()
                        record_timings(metrics, sbody)
                        err = sbody.get("tts_error")
                        metrics.tts_errors[err or "ok"] += 1
                        if not sbody.get("audio_base64"):
                            metrics.tts_errors["EMPTY_AUDIO"] += 1
                    else:
                        metrics.http_errors[
                            f"synthesize-turn {synth.status_code}"
                        ] += 1

            score = await timed(
                metrics,
                "POST /score",
                client.post(
                    "/admin/speaking-examiner/score",
                    json={"session_id": out.session_id, "conversation_history": []},
                ),
            )
            if score.status_code != 200:
                metrics.http_errors[f"score {score.status_code}"] += 1
                out.error = f"score {score.status_code}: {score.text[:200]}"
                return out
            out.band = score.json().get("overall_band")
            return out
        except Exception as exc:  # noqa: BLE001 — record, never abort the run
            out.error = f"{type(exc).__name__}: {exc}"
            metrics.http_errors[type(exc).__name__] += 1
            return out
        finally:
            out.wall_seconds = time.perf_counter() - started


async def main_async(args: argparse.Namespace) -> int:
    clips = load_audio()
    audio_kb = sum(len(c) for c in clips) / 1024
    print(f"Loaded {len(clips)} audio clips ({audio_kb:.0f} KB)")

    metrics = Metrics()
    async with httpx.AsyncClient(base_url=args.base_url, timeout=60.0) as admin:
        login = await admin.post(
            "/auth/login",
            json={"login": args.admin_login, "password": args.admin_password},
        )
        login.raise_for_status()
        admin_jwt = login.json()["access_token"]

        run_tag = uuid.uuid4().hex[:6]
        phones = [f"+99891{run_tag}{i:02d}" for i in range(args.students)]
        print(f"Provisioning {len(phones)} students (tag {run_tag})…")
        tokens = await asyncio.gather(
            *[provision_student(admin, admin_jwt, p, metrics) for p in phones]
        )

    gate = asyncio.Event()
    tasks = [
        asyncio.create_task(
            run_session(
                args.base_url,
                tok,
                phone,
                clips,
                metrics,
                gate,
                args.think_seconds,
            )
        )
        for phone, tok in zip(phones, tokens)
    ]

    print(f"Releasing {len(tasks)} simultaneous Speaking sessions…")
    burst_start = time.perf_counter()
    gate.set()
    results: list[SessionResult] = await asyncio.gather(*tasks)
    burst_wall = time.perf_counter() - burst_start

    print("\n=== Per-session outcome ===")
    ok = 0
    for r in sorted(results, key=lambda x: x.wall_seconds):
        video = "video" if r.simli_enabled else "audio-only"
        if r.error:
            print(f"FAIL {r.phone}  turns={r.turns:2d}  {video}  {r.error}")
        else:
            ok += 1
            print(
                f"OK   {r.phone}  turns={r.turns:2d}  {video}  "
                f"band={r.band}  {r.wall_seconds:.1f}s"
            )

    print(f"\nSucceeded: {ok}/{len(results)}")
    print(f"Burst wall time: {burst_wall:.1f}s")
    walls = [r.wall_seconds for r in results]
    if walls:
        ordered = sorted(walls)
        print(
            f"Session duration: min={ordered[0]:.1f}s "
            f"p50={statistics.median(ordered):.1f}s max={ordered[-1]:.1f}s"
        )
    bands = [r.band for r in results if r.band is not None]
    if bands:
        print(
            f"Bands: n={len(bands)} min={min(bands)} max={max(bands)} "
            f"mean={statistics.mean(bands):.2f}"
        )

    metrics.report_latency()

    print("\n=== Upstream services ===")
    if metrics.whisper_ms:
        w = sorted(metrics.whisper_ms)
        print(
            f"Groq Whisper: n={len(w)} p50={w[len(w) // 2]}ms "
            f"p95={w[max(0, int(len(w) * 0.95) - 1)]}ms max={max(w)}ms"
        )
    if metrics.tts_ms:
        t = sorted(metrics.tts_ms)
        print(
            f"TTS: n={len(t)} p50={t[len(t) // 2]}ms "
            f"p95={t[max(0, int(len(t) * 0.95) - 1)]}ms max={max(t)}ms"
        )
    print(f"TTS outcomes: {dict(metrics.tts_errors)}")
    print(f"TTS cache hits: {dict(metrics.tts_cache_hits)}")
    print(f"Simli split: {dict(metrics.simli)}")
    print(f"Errors: {dict(metrics.http_errors) or 'none'}")
    return 0 if ok == len(results) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--students", type=int, default=20)
    p.add_argument("--admin-login", default="admin")
    p.add_argument("--admin-password", required=True)
    p.add_argument(
        "--think-seconds",
        type=float,
        default=0.0,
        help="pause before each answer; 0 keeps turns aligned for worst-case load",
    )
    return p


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async(build_parser().parse_args())))

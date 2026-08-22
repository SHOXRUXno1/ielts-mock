#!/usr/bin/env python3
"""Writing burst load test — N students submit Task 1 + Task 2 at once.

Runs a whole-section Writing practice attempt per student so the run exercises
only the Writing path: answer autosave -> finish -> EvaluationJob -> Gemini.

Usage (API already running):
  python scripts/load_test_writing.py --test-id <UUID> \\
      --admin-login admin --admin-password <pw> --students 15

Reports per-endpoint latency percentiles, the submit-burst wall time, per-student
time-to-band, and a correctness audit of every scored job.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
import uuid
from dataclasses import dataclass, field

import httpx

# On-topic answers for Cambridge IELTS 16 Test 1. Long enough to clear the IELTS
# minimums (T1 >= 150, T2 >= 250 words) so no under-length penalty skews bands.
T1_ON_TOPIC = (
    "The two charts illustrate how the ownership of household electrical "
    "appliances and the number of hours spent on domestic work changed in one "
    "country between 1920 and 2019. Overall, ownership of all three appliances "
    "rose dramatically over the century, while the time devoted to housework "
    "fell by a comparable margin, suggesting a clear relationship between the "
    "two trends. In 1920 washing machines were owned by only around forty per "
    "cent of households, and both refrigerators and vacuum cleaners were "
    "almost unknown, standing close to zero. Vacuum cleaners then rose "
    "steeply, reaching virtually every home by the early 1970s, and washing "
    "machines followed a similar though slightly slower path to near universal "
    "ownership. Refrigerators started latest but climbed most sharply, "
    "overtaking washing machines around 1960 and reaching one hundred per cent "
    "by 1980. Meanwhile, the time spent on housework declined from "
    "approximately fifty hours per week in 1920 to only about ten hours in "
    "2019. The steepest fall occurred between 1920 and 1980, precisely the "
    "period in which appliance ownership expanded most rapidly, after which "
    "the figure levelled off."
)

T2_ON_TOPIC = (
    "In a number of countries, a growing number of residents are curious about "
    "the past of the houses and buildings they occupy. In my view this "
    "interest stems mainly from a desire for personal identity and a sense of "
    "belonging, and it can be satisfied through a combination of official "
    "records and local knowledge. There are several reasons why people are "
    "drawn to the history of their homes. The most powerful is the wish to "
    "feel rooted in a place. As populations become more mobile and families "
    "disperse, knowing that previous generations lived and worked within the "
    "same walls gives residents a comforting sense of continuity. A second "
    "reason is simple curiosity fuelled by the media, since television "
    "programmes about restoring period properties and tracing family trees "
    "have made this kind of research fashionable and accessible. A more "
    "practical motive also exists: owners of older properties often need to "
    "understand the original construction before undertaking renovation, and "
    "documented historical value can significantly increase a building's price. "
    "Fortunately, researching a property has never been easier. The most "
    "reliable starting point is the local land registry or council archive, "
    "where title deeds, planning applications and old maps record successive "
    "owners and alterations. Census returns and parish registers, many of which "
    "are now digitised and searchable online, reveal who occupied the address "
    "in particular years. Beyond written sources, elderly neighbours and local "
    "history societies frequently hold photographs and recollections that no "
    "archive contains. In conclusion, the appeal of house history lies in the "
    "human need for connection and continuity, and anyone wishing to explore "
    "it can combine official archives with the memories of the surrounding "
    "community."
)

# Deliberately irrelevant answers, used with --off-topic to check that the
# examiner penalises task relevance without nullifying the language criteria.
T1_OFF_TOPIC = (
    "The two charts compare how much money was spent on a range of consumer "
    "goods in two separate countries over a period of several years. Overall, "
    "expenditure rose in both countries across the whole period, although the "
    "pattern of growth differed noticeably between the two. Spending on "
    "electronic devices increased most sharply, more than doubling by the end "
    "of the period, whereas outlay on household furniture grew only modestly "
    "and even fell slightly in the final year. In the first country, food and "
    "clothing together accounted for the largest share at the start, but their "
    "combined proportion declined steadily as spending shifted towards "
    "technology and leisure. The second country showed the opposite tendency: "
    "expenditure on food remained the dominant category throughout, and its "
    "share fell by only a small margin. Another clear difference is the pace of "
    "change. The first country recorded rapid year on year increases between "
    "the middle years, while the second country grew far more gradually and "
    "without any pronounced peaks. By the final year, however, total spending "
    "in both countries had converged to broadly similar levels, suggesting "
    "that the second country simply reached the same point along a slower and "
    "steadier path than the first."
)

T2_OFF_TOPIC = (
    "It is often argued that consumers today have access to a far wider range "
    "of products than previous generations, and opinions differ as to whether "
    "this abundance is beneficial. In my view, greater choice brings real "
    "advantages, but it also creates problems that individuals and governments "
    "cannot afford to ignore. The clearest benefit of wider choice is "
    "competition. When many companies offer comparable goods, they are forced "
    "to improve quality and reduce prices in order to attract customers. A "
    "shopper looking for a laptop, for example, can compare dozens of models "
    "across several price brackets, and this pressure has made technology far "
    "more affordable than it was two decades ago. Choice also allows people to "
    "match purchases to their particular circumstances, whether that means "
    "buying locally produced food or selecting products designed for a small "
    "household. However, an excess of options carries genuine costs. Consumers "
    "frequently report feeling overwhelmed when confronted with too many "
    "similar alternatives, and this can lead to poor decisions or to "
    "postponing a purchase altogether. More seriously, the constant "
    "availability of cheap goods encourages people to replace items long "
    "before they wear out, which generates enormous quantities of waste and "
    "places pressure on natural resources. Fast fashion is a well documented "
    "example, since garments are now discarded after only a handful of wears. "
    "In conclusion, although the expansion of consumer choice has driven down "
    "prices and improved standards, its environmental and psychological costs "
    "are substantial. I therefore believe that governments should regulate "
    "misleading marketing and promote repairable products, so that the "
    "benefits of choice are not outweighed by the damage caused by "
    "overconsumption."
)


def essay_for(task: int, seed: int, *, off_topic: bool) -> str:
    """Per-student variation so no two submissions are byte-identical."""
    if off_topic:
        base = T1_OFF_TOPIC if task == 1 else T2_OFF_TOPIC
    else:
        base = T1_ON_TOPIC if task == 1 else T2_ON_TOPIC
    return f"{base} This response was written by candidate {seed}."


@dataclass
class Timings:
    samples: dict[str, list[float]] = field(default_factory=dict)

    def add(self, name: str, seconds: float) -> None:
        self.samples.setdefault(name, []).append(seconds)

    def report(self) -> None:
        print("\n=== Latency (seconds) ===")
        print(f"{'endpoint':30s} {'n':>4}  {'p50':>7} {'p95':>7} {'max':>7}")
        for name, vals in sorted(self.samples.items()):
            if not vals:
                continue
            ordered = sorted(vals)
            p50 = statistics.median(ordered)
            p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
            print(
                f"{name:30s} {len(vals):4d}  {p50:7.3f} {p95:7.3f} {max(ordered):7.3f}"
            )


async def timed(timings: Timings, name: str, coro):
    t0 = time.perf_counter()
    try:
        return await coro
    finally:
        timings.add(name, time.perf_counter() - t0)


async def admin_token(base_url: str, login: str, password: str) -> str:
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        resp = await client.post(
            "/auth/login", json={"login": login, "password": password}
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def find_writing_questions(
    base_url: str, token: str, test_id: str
) -> dict[str, str]:
    """Return {'task_1': question_id, 'task_2': question_id}."""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(
        base_url=base_url, timeout=30.0, headers=headers
    ) as client:
        detail = await client.get(f"/tests/{test_id}")
        detail.raise_for_status()
        sections = detail.json().get("sections") or []
        writing = [s for s in sections if s.get("type") == "writing"]
        if not writing:
            raise SystemExit("Test has no writing section")

        mapping: dict[str, str] = {}
        for section in writing:
            qs = await client.get(f"/sections/{section['id']}/questions")
            qs.raise_for_status()
            for q in qs.json():
                num = q.get("task_number") or q.get("order")
                if num in (1, 2):
                    mapping.setdefault(f"task_{num}", q["id"])
        if len(mapping) < 2:
            raise SystemExit(f"Expected 2 writing tasks, found {sorted(mapping)}")
        return mapping


async def provision_student(
    base_url: str, admin_jwt: str, phone: str, timings: Timings
) -> str:
    """Create the student if missing, then log in and return their JWT."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        create = await client.post(
            "/admin/students/",
            headers={"Authorization": f"Bearer {admin_jwt}"},
            json={
                "phone": phone,
                "full_name": f"LoadWriting {phone[-4:]}",
                "group_name": "load-writing",
            },
        )
        if create.status_code not in (200, 201, 400, 409):
            create.raise_for_status()

        login = await timed(
            timings,
            "POST /auth/login",
            client.post("/auth/login", json={"login": phone, "password": phone}),
        )
        login.raise_for_status()
        return login.json()["access_token"]


@dataclass
class StudentResult:
    phone: str
    attempt_id: str | None = None
    writing_band: float | None = None
    finish_at: float | None = None
    band_at: float | None = None
    error: str | None = None
    job_status: str | None = None

    @property
    def wait_seconds(self) -> float | None:
        if self.finish_at is None or self.band_at is None:
            return None
        return self.band_at - self.finish_at


async def run_student(
    base_url: str,
    test_id: str,
    token: str,
    phone: str,
    task_ids: dict[str, str],
    seed: int,
    timings: Timings,
    gate: asyncio.Event,
    poll_seconds: int,
    off_topic: bool,
) -> StudentResult:
    out = StudentResult(phone=phone)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(
        base_url=base_url, timeout=120.0, headers=headers
    ) as client:
        try:
            start = await timed(
                timings,
                "POST /practice-attempts",
                client.post(
                    f"/tests/{test_id}/practice-attempts",
                    json={"section_type": "writing", "scope": "section"},
                ),
            )
            if start.status_code not in (200, 201):
                out.error = f"start {start.status_code}: {start.text[:200]}"
                return out
            out.attempt_id = start.json()["id"]

            # Hold every student here so answers+finish land simultaneously.
            await gate.wait()

            save = await timed(
                timings,
                "POST /answers (T1+T2)",
                client.post(
                    f"/attempts/{out.attempt_id}/answers",
                    json={
                        "answers": [
                            {
                                "question_id": task_ids["task_1"],
                                "response": {
                                    "answer": essay_for(
                                        1, seed, off_topic=off_topic
                                    )
                                },
                            },
                            {
                                "question_id": task_ids["task_2"],
                                "response": {
                                    "answer": essay_for(
                                        2, seed, off_topic=off_topic
                                    )
                                },
                            },
                        ]
                    },
                ),
            )
            if save.status_code != 200:
                out.error = f"answers {save.status_code}: {save.text[:200]}"
                return out

            finish = await timed(
                timings,
                "POST /finish",
                client.post(f"/attempts/{out.attempt_id}/finish"),
            )
            if finish.status_code != 200:
                out.error = f"finish {finish.status_code}: {finish.text[:200]}"
                return out
            out.finish_at = time.perf_counter()

            deadline = time.perf_counter() + poll_seconds
            while time.perf_counter() < deadline:
                detail = await timed(
                    timings,
                    "GET /results/{id}",
                    client.get(f"/results/{out.attempt_id}"),
                )
                if detail.status_code == 200:
                    body = detail.json()
                    jobs = body.get("evaluation_jobs") or []
                    writing = [j for j in jobs if j.get("section_type") == "writing"]
                    settled = writing and all(
                        j.get("status") in ("done", "failed") for j in writing
                    )
                    if settled:
                        out.job_status = writing[0].get("status")
                        out.writing_band = writing[0].get("band_score")
                        out.band_at = time.perf_counter()
                        return out
                await asyncio.sleep(2.0)

            out.error = f"timeout after {poll_seconds}s waiting for writing band"
            return out
        except Exception as exc:  # noqa: BLE001 — report, never abort the run
            out.error = f"{type(exc).__name__}: {exc}"
            return out


async def audit(base_url: str, token: str, results: list[StudentResult]) -> None:
    """Correctness pass over every scored job — the part a band alone hides."""
    print("\n=== Correctness audit ===")
    problems: list[str] = []
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=60.0,
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        for r in results:
            if not r.attempt_id:
                continue
            resp = await client.get(f"/results/{r.attempt_id}")
            if resp.status_code != 200:
                problems.append(f"{r.attempt_id} results HTTP {resp.status_code}")
                continue
            body = resp.json()
            jobs = [
                j
                for j in (body.get("evaluation_jobs") or [])
                if j.get("section_type") == "writing"
            ]
            if len(jobs) != 1:
                problems.append(f"{r.attempt_id} has {len(jobs)} writing jobs (want 1)")
                continue
            job = jobs[0]
            if job.get("status") != "done":
                problems.append(
                    f"{r.attempt_id} job {job.get('status')}: "
                    f"{(job.get('error_message') or '')[:120]}"
                )
                continue
            if job.get("retry_count"):
                problems.append(
                    f"{r.attempt_id} needed {job['retry_count']} retries"
                )
            tasks = ((job.get("result") or {}).get("tasks")) or {}
            for key in ("task_1", "task_2"):
                task = tasks.get(key)
                if not task:
                    problems.append(f"{r.attempt_id} missing {key} in result")
                    continue
                band = task.get("overall_band")
                if band is None:
                    problems.append(f"{r.attempt_id} {key} band is null")
                elif not 0 <= float(band) <= 9:
                    problems.append(f"{r.attempt_id} {key} band out of range: {band}")
                wc = task.get("word_count")
                if wc is not None and wc < (150 if key == "task_1" else 250):
                    problems.append(f"{r.attempt_id} {key} word_count={wc} under min")
            if job.get("band_score") is None:
                problems.append(f"{r.attempt_id} writing band_score is null")

    if problems:
        print(f"{len(problems)} issue(s):")
        for p in problems:
            print(f"  - {p}")
    else:
        print("No issues: 1 job per attempt, both tasks scored, bands in range.")


async def main_async(args: argparse.Namespace) -> int:
    timings = Timings()
    admin_jwt = await admin_token(args.base_url, args.admin_login, args.admin_password)
    task_ids = await find_writing_questions(args.base_url, admin_jwt, args.test_id)
    print(f"Writing tasks: {task_ids}")

    run_tag = uuid.uuid4().hex[:6]
    phones = [f"+99890{run_tag}{i:02d}" for i in range(args.students)]
    print(f"Provisioning {len(phones)} students (tag {run_tag})…")
    tokens = await asyncio.gather(
        *[provision_student(args.base_url, admin_jwt, p, timings) for p in phones]
    )

    gate = asyncio.Event()
    tasks = [
        asyncio.create_task(
            run_student(
                args.base_url,
                args.test_id,
                tok,
                phone,
                task_ids,
                seed,
                timings,
                gate,
                args.poll_seconds,
                args.off_topic,
            )
        )
        for seed, (phone, tok) in enumerate(zip(phones, tokens), start=1)
    ]

    # Let every attempt exist before releasing the simultaneous submit.
    await asyncio.sleep(2.0)
    print(f"Releasing simultaneous submit for {len(tasks)} students…")
    burst_start = time.perf_counter()
    gate.set()
    results: list[StudentResult] = await asyncio.gather(*tasks)
    burst_wall = time.perf_counter() - burst_start

    print("\n=== Per-student outcome ===")
    ok = 0
    for r in sorted(results, key=lambda x: x.wait_seconds or 1e9):
        if r.error:
            print(f"FAIL {r.phone}  {r.error}")
        else:
            ok += 1
            wait = r.wait_seconds
            print(
                f"OK   {r.phone}  band={r.writing_band}  "
                f"job={r.job_status}  wait={wait:.1f}s"
            )

    waits = [r.wait_seconds for r in results if r.wait_seconds is not None]
    print(f"\nSucceeded: {ok}/{len(results)}")
    print(f"Burst wall time (submit -> last band): {burst_wall:.1f}s")
    if waits:
        ordered = sorted(waits)
        print(
            f"Time-to-band: min={ordered[0]:.1f}s "
            f"p50={statistics.median(ordered):.1f}s "
            f"max={ordered[-1]:.1f}s"
        )
    timings.report()
    await audit(args.base_url, admin_jwt, results)
    return 0 if ok == len(results) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--test-id", required=True)
    p.add_argument("--students", type=int, default=15)
    p.add_argument("--admin-login", default="admin")
    p.add_argument("--admin-password", required=True)
    p.add_argument("--poll-seconds", type=int, default=600)
    p.add_argument(
        "--off-topic",
        action="store_true",
        help="submit irrelevant essays to exercise the off-topic penalty path",
    )
    return p


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async(build_parser().parse_args())))

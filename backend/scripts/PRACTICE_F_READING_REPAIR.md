# Audited Practice Set F Reading repair

This patch restores source question wording/context for Tests 1, 2, 5 and 6,
returns Test 5 Q14 to the candle classification task, and adds source-listed
accepted response variants for Test 5 Q29/31/32/34 and Test 6 Q26/27.
Reading MCQ/multi-select text in all six tests also has its embedded A/B/C
prefix removed, because the UI already renders that prefix. Matching-list
labels stay intact. Tests 3/4 have no wording, structure or key changes.
Passages, Listening, Writing and Speaking are not changed.

## Existing published tests

**Do not run bootstrap or reading seeds on the production database.** Those
commands clear questions and can cascade into saved answers. Use
`repair_practice_f_reading.py`, which updates existing rows instead.

Before running, deliver the revised `seed_practice_f_reading.py`, this repair
script, and the revised Reading question/key JSON files to the backend image
or its scripts directory. The rest of the existing Practice Set F data must
remain available alongside them.

Run from the backend container's `/app` directory:

```sh
python scripts/repair_practice_f_reading.py
```

Review the dry-run counts. The audited original dataset produces 29 updates
for Test 1, 41 for Test 2, 4 for Test 3, 12 for Test 4, 29 for Test 5 and 10
for Test 6. The verified intermediate content repair is also accepted;
from that state only duplicate choice prefixes are changed. Only the obsolete,
now-empty Test 5 Q14 group shell is removed. All question IDs remain intact.

If the dry run matches the reviewed dataset and there are no unfinished Full
Mock or Reading practice attempts on the affected tests:

```sh
python scripts/repair_practice_f_reading.py --apply --backup /tmp/practice_f_reading_before_YYYYMMDD_HHMMSS.json
python scripts/repair_practice_f_reading.py
```

The second dry run must report zero updates. Also run the existing
`verify_practice_f.py N` and `check_practice_f_scoring.py N` for all six
test, then check the Student preview of the restored compound tasks and the
Test 5 passage boundaries (1–14, 15–27, 28–40).

## Safety guarantees and limits

- Dry run does not assign or commit changes.
- Apply checks the complete Reading fingerprint against the audited baseline
  or the already-repaired state. Unexpected edits cause an abort.
- Test rows are locked before inspecting unfinished attempts, blocking new
  attempt FK inserts until the short transaction finishes. Lock/statement
  timeouts are bounded. There is no force flag.
- Legacy/ambiguous unfinished practice attempts are treated conservatively.
- A new, exclusive backup file is synced before changing database rows.
- The entire patch uses one transaction. Post-write fingerprints and the
  exact question-ID set are verified before commit.
- Moving/reordered question rows use a temporary disjoint positive order
  range inside that transaction, respecting the migrated database's unique
  `(question_group_id, order)` constraint without disabling it.
- Responses, attempt records, progress/deadlines and historical scores are
  not rewritten or automatically regraded. As elsewhere in this platform,
  published question content is shared with historical result views.
- A rerun against the completed repair is a no-op, even if new attempts have
  since started.

The backup contains old Reading group/question fields and their IDs, not
student responses or credentials. Keep it restricted. A rollback must be
reviewed separately, particularly if students have started the repaired test.

## Regression coverage

`tests/test_practice_f_reading_repair.py` covers all six compiled Readings,
source response variants, original Q14, complete summary/chart/note context,
invalid blank structures, unexpected content drift, idempotence, unfinished
attempt refusal, exclusive backups and an isolated real-ORM/foreign-key
rehearsal preserving a historical answer and score. SQLite rehearses writes;
PostgreSQL row-lock behavior still requires a production preflight or a
separate PostgreSQL integration environment.

## Source and completed verification (2026-10-19)

Question wording and structures were compared against the corresponding
Engnovate Reading test pages, e.g.
https://engnovate.com/ielts-reading-tests/barrons-ielts-practice-exams-academic-reading-test-5/
and the same URL pattern for Tests 1–6. Accepted variants additionally follow:
- https://engnovate.com/ielts-reading-answers/animal-camouflage/
- https://engnovate.com/ielts-reading-answers/paleolithic-cave-art/

The repaired compiler passes all 480 independently sourced Listening/Reading
slots plus the listed source alternatives. The live database passes scoring,
publication and local-media checks for all six tests. This is not a claim of
480 browser form submissions: browser checks were preview smoke tests, and
scoring was exercised read-only without creating student attempts.

The production repair was rehearsed first against an isolated PostgreSQL
database using the real migrated schema, including the unique group/order
constraint. Before/after invariants checked all question IDs, finished-attempt
score checksums, other skills, passages, timing and publication. The checked
historical cohort contained no saved F Reading responses; nonempty historical
answer preservation is covered by the isolated ORM regression test instead.

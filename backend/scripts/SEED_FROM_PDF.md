# How to add a full mock from a printed PDF / book

This is the **only supported way** to add Cambridge / Longman / Practice Set
tests into this product. There is **no admin “Upload PDF” button**. Agents must
follow this playbook end-to-end.

Copy an existing finished set and change numbers/content. Do not invent a new
pipeline.

| Finished reference | Student name | Source book (internal only) |
|---|---|---|
| Practice Set A (`practice-set-a`) | IELTS Practice Set A | Cambridge / booster A |
| Practice Set B Test 1 | IELTS Practice Set B — Test 1 | IELTS Practice Tests Plus 2 |

Students must **never** see publisher names (Longman, Plus 2, Cambridge book
title). Those stay in script comments / `SOURCE_BOOK` only.

---

## Mental model (read this first)

```
PDF + Audio on disk
   → YOU author seed scripts + passage txt + media files
   → git push main            updates Docker IMAGE (code only)
   → scp + deploy_*.sh        fills Postgres + /app/media on VPS
   → verify + scoring gates
   → publish                  students see the test
```

**Git deploy does not seed the database and does not copy media.**
If you only `git push`, the catalogue will not gain a new published test.

---

## Inputs the human must provide

1. **PDF** (often a scan) of the practice book.
2. **Audio** for Listening (usually 4 tracks per test, or one file to split).
3. Optional: improved crops of maps / charts / diagrams.

Typical local paths (Windows):

- `C:\Users\brawl\Desktop\Ielts boosters\<Book Name>\<Book>.pdf`
- `...\ <Book> Audio\`

Rendered scan pages (gitignored helper, optional):

- `backend/scripts/_plus2_pages/pNNN.png` ≈ printed page N

---

## Product naming

Edit / extend `seed_practice_<set>_common.py`:

| Field | Example (Set B) |
|---|---|
| `BOOK_NAME` | `IELTS Practice Set B` |
| `BOOK_SLUG` | `practice-set-b` |
| `SOURCE_BOOK` | `IELTS Practice Tests Plus 2` (comments only) |
| `test_number` | `1` … `6` |

Catalogue title becomes: `{BOOK_NAME} — Test {N}`.

---

## One mock = 11 sections

| Skill | Section `order` | Content |
|---|---|---|
| Listening Part 1–4 | `1`–`4` | 40 Q + `audio_url` + optional map image |
| Reading Passage 1–3 | `10`–`12` | 40 Q + passage text |
| Writing | `20` | Task 1 (+ chart) + Task 2 |
| Speaking Part 1–3 | `30`–`32` | Part prompts / cue card (no examiner admin) |

Listening and Reading must total **40 marks each** before publish.

---

## Files you must create for Test N

Example for Practice Set B Test 2 (`N=2`). Mirror Test 1.

### Committed (git)

```
backend/scripts/seed_practice_b_common.py          # URL templates (usually already there)
backend/scripts/seed_practice_b_bootstrap.py       # usually already there; data-driven
backend/scripts/seed_practice_b_t{N}_listening.py
backend/scripts/seed_practice_b_t{N}_reading.py
backend/scripts/seed_practice_b_t{N}_writing.py
backend/scripts/seed_practice_b_t{N}_speaking.py
backend/scripts/verify_practice_b.py               # already there
backend/scripts/check_practice_b_scoring.py        # already there
backend/scripts/publish_practice_b.py              # already there
backend/scripts/deploy_practice_b.sh               # already there
backend/scripts/data/practice_b_t{N}/
  sections.json
  reading_p1.txt
  reading_p2.txt
  reading_p3.txt
```

`sections.json` shape:

```json
{
  "description": "Academic practice test: Listening, Reading, Writing and Speaking.",
  "titles": {
    "listening:1": "Part 1 — …",
    "listening:2": "Part 2 — …",
    "listening:3": "Part 3 — …",
    "listening:4": "Part 4 — …",
    "reading:10": "Passage 1 — …",
    "reading:11": "Passage 2 — …",
    "reading:12": "Passage 3 — …",
    "speaking:30": "Part 1 — …",
    "speaking:31": "Part 2 — …",
    "speaking:32": "Part 3 — …"
  }
}
```

Reading txt: **first line = passage title**, rest = body.

### Not committed (media, gitignored)

```
backend/media/audio/practice_b_t{N}_listening_p1.mp3
backend/media/audio/practice_b_t{N}_listening_p2.mp3
backend/media/audio/practice_b_t{N}_listening_p3.mp3
backend/media/audio/practice_b_t{N}_listening_p4.mp3
backend/media/images/practice_b_t{N}_listening_map.png      # if needed
backend/media/images/practice_b_t{N}_writing_task1.png      # Academic Task 1
backend/media/images/practice_b_t{N}_reading_*.png          # diagrams
```

DB stores paths like `/media/audio/practice_b_t2_listening_p1.mp3`.

---

## Question typing rules

Map paper tasks to platform types (see existing `seed_practice_b_t1_*.py`):

| Paper look | Platform type |
|---|---|
| Notes / form / table / summary / flow with blanks | compound: `note_completion`, `form_completion`, `table_completion`, `summary_completion`, `flow_chart_completion` |
| Diagram labels with typed words | `diagram_labeling` (notes-shaped structure + `image_url`) |
| A/B/C (or more) choose one | `mcq` |
| Choose TWO letters | `multi_select` |
| Match headings / features / information | `matching_headings` / `matching_features` / `matching_information` |
| Map with A–I labels | `map_labeling` |
| TRUE/FALSE/NG, YES/NO/NG | `true_false_ng` / `yes_no_ng` |
| Writing | `essay` Task 1 + Task 2 |
| Speaking | `speaking_part` |

**Compound gaps:** structure must contain real gap segments (`{gap}` / `{gap1}`), not plain text that only looks like a blank. Server error `… structure must contain at least one gap` means Save was pressed with zero parsed gaps.

**Do not seed from the book:**

- Tip Strip / strategy boxes
- Publisher branding
- Fake list titles the paper does not print (e.g. inventing “List of People / Places”)
- Speaking examiner admin scripts

Answer keys: take from the book’s answer key pages; accept common variants (`£95` / `95 pounds`, etc.) where the key allows.

---

## Local seed order (mandatory)

From `backend/` with venv Python:

```bash
python scripts/seed_practice_b_bootstrap.py 2
python scripts/seed_practice_b_t2_listening.py
python scripts/seed_practice_b_t2_reading.py
python scripts/seed_practice_b_t2_writing.py
python scripts/seed_practice_b_t2_speaking.py
python scripts/verify_practice_b.py 2
python scripts/check_practice_b_scoring.py 2
```

- Bootstrap creates the Test + 11 empty sections (unpublished).
- Each skill script **clears that skill’s sections** then rewrites them.
- Do **not** call `publish_practice_b.py` until both gates pass locally (or on VPS).

---

## Ship code (git)

Commit **only** seed scripts + `data/practice_b_t{N}/`.  
Do **not** commit: `_inspect_*.py`, `openapi_tmp.json`, `_plus2_pages/`, media audio/images, unrelated WIP.

```bash
git add backend/scripts/seed_practice_b_t2_*.py \
        backend/scripts/data/practice_b_t2/ \
        # plus any shared helper edits
git commit -m "Add Practice Set B Test 2 seed (unpublished)."
git push origin main
```

Wait for GitHub Actions **Deploy to production** to succeed. That refreshes the backend image so VPS has the new scripts.

---

## Ship content on VPS (mandatory second step)

Staging layout expected by `deploy_practice_b.sh`:

```
/tmp/pb_stage/
  media/practice_b_t{N}_*.mp3
  media/practice_b_t{N}_*.png
  scripts/*.py                    # seed + verify + publish + common
  scripts/data/practice_b_t{N}/*  # passages + sections.json
  deploy_practice_b.sh
```

From the workstation (adjust key/host):

```bash
# 1) stage files via scp into /tmp/pb_stage/...
# 2) run on server:
ssh -i ~/.ssh/ielts-mock root@<VPS_HOST> \
  "bash /tmp/pb_stage/deploy_practice_b.sh {N} --publish"
```

The script:

1. `docker cp` media → `ielts-mock-backend-1:/app/media/{audio,images}/`
2. `docker cp` scripts + data into the container
3. Runs bootstrap + four skill seeds
4. Runs `verify_practice_b.py` and `check_practice_b_scoring.py`
5. Publishes **only if** `--publish` and gates pass

Container name: `ielts-mock-backend-1`.  
Compose dir on VPS: `/opt/ielts-mock` (`docker-compose.prod.yml`).

### Tiny fixes without full re-deploy

| Change | Action |
|---|---|
| Better PNG, same URL | Replace file locally + `docker cp` into `/app/media/images/` |
| One skill’s wording/keys | Edit seed → push → `docker cp` script → `python scripts/seed_practice_b_t{N}_listening.py` (etc.) |
| UI bug (map not shown) | Frontend fix + `git push main` only |

Full `deploy_practice_b.sh` **wipes and reseeds** sections — avoid for a one-line typo if a single skill re-seed is enough.

---

## Checklist before telling the human “done”

- [ ] 40 Listening + 40 Reading scoring slots
- [ ] All audio/image URLs resolve on disk / in container (`verify_practice_b`)
- [ ] Scoring smoke check green (`check_practice_b_scoring`)
- [ ] No publisher name in `Test.title` / student UI
- [ ] Preview: Listening map/MCQ images, Reading diagram, Writing Task 1 chart
- [ ] Published on prod **or** explicitly left unpublished with reason
- [ ] Media on VPS volume (not only on laptop)
- [ ] Seed scripts committed and pushed

---

## Adding Practice Set A Test N

Same playbook; swap prefixes:

- `seed_practice_a_*`
- `data/practice_a_t{N}/`
- `deploy_practice_a.sh`
- media: `practice_a_t{N}_*`

---

## What NOT to do

1. Do not paste the whole PDF into the admin wizard by hand for a full mock (too slow / inconsistent).
2. Do not expect `git push` alone to publish content.
3. Do not commit large media or generated page scans.
4. Do not publish if verify/scoring fails.
5. Do not show Tip Strips or book branding to students.
6. Do not start Plus 3 / Set B Tests 2–6 without copying the Test 1 file layout first.

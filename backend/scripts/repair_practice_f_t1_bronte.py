"""Fix one audited diacritic in F1 Passage 3, without reseeding any content.

Default: read-only dry run. Apply requires a new absolute backup file.
Only sections.passage is updated; questions, answers, attempts and keys are not.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.config import settings  # noqa: E402
from app.models.section import Section  # noqa: E402
from app.models.test import Test  # noqa: E402

TEST_ID = uuid.UUID('418a37cf-d0e7-46a8-8e06-62cae4116c7c')
BEFORE_SHA256 = '74534087c63a1959a0d1b81ad0e2bbe8fd52dd3f24bf406f71c1779d0c44bbf8'
OLD_NAME = 'Charlotte Bronte'
NEW_NAME = 'Charlotte Bront\u00eb'


def corrected(passage: str) -> str:
    if OLD_NAME not in passage and passage.count(NEW_NAME) == 1:
        original = passage.replace(NEW_NAME, OLD_NAME, 1)
    else:
        original = passage
    if hashlib.sha256(original.encode('utf-8')).hexdigest() != BEFORE_SHA256:
        raise ValueError('Passage differs from the audited original; refusing overwrite')
    if original.count(OLD_NAME) != 1:
        raise ValueError('Expected exactly one occurrence')
    return original.replace(OLD_NAME, NEW_NAME, 1)


async def main(apply: bool, backup: Path | None):
    if apply and (backup is None or not backup.is_absolute()):
        raise ValueError('Apply requires --backup /absolute/new-file.json')
    engine = create_async_engine(settings.database_url)
    try:
        async with AsyncSession(engine) as db:
            await db.execute(text("SET LOCAL lock_timeout = '2s'"))
            await db.execute(text("SET LOCAL statement_timeout = '10s'"))
            if not apply:
                await db.execute(text('SET TRANSACTION READ ONLY'))
            query = select(Section).join(Test, Section.test_id == Test.id).where(
                Test.id == TEST_ID, Test.book_slug == 'practice-set-f', Test.test_number == 1,
                Section.type == 'reading', Section.order == 12, Section.title == 'The Luddites')
            section = (await db.execute(query.with_for_update(of=Section) if apply else query)).scalar_one()
            before = section.passage or ''
            after = corrected(before)
            if before == after:
                print('Already correct: Charlotte Bront\u00eb; no database writes')
                await db.rollback()
                return
            if not apply:
                print('Dry run: exactly one e -> U+00EB in F1 Passage 3; no database writes')
                await db.rollback()
                return
            fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                json.dump({'test_id': str(TEST_ID), 'section_id': str(section.id),
                           'passage_before': before, 'sha256_before': BEFORE_SHA256}, handle, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            result = await db.execute(update(Section).where(Section.id == section.id, Section.passage == before)
                                      .values(passage=after).execution_options(synchronize_session=False))
            if result.rowcount != 1:
                raise ValueError('Concurrent change; aborting')
            actual = (await db.execute(select(Section.passage).where(Section.id == section.id))).scalar_one()
            if actual != after or corrected(actual) != actual:
                raise ValueError('Post-write verification failed')
            await db.commit()
            print('Applied: one diacritic in one passage. Question IDs, keys, answers and attempts untouched.')
    finally:
        await engine.dispose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--backup', type=Path)
    arguments = parser.parse_args()
    asyncio.run(main(arguments.apply, arguments.backup))

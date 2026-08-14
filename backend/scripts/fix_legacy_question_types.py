"""
One-off script: normalise legacy question_type values in question_groups table.

Maps:
  table -> table_completion
  notes -> note_completion
  form  -> form_completion
  flow  -> flow_chart_completion
"""

import asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine

LEGACY_MAP = {
    "table": "table_completion",
    "notes": "note_completion",
    "form": "form_completion",
    "flow": "flow_chart_completion",
}

async def main():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        for old, new in LEGACY_MAP.items():
            result = await conn.execute(
                text(
                    "UPDATE question_groups SET question_type = :new WHERE question_type = :old"
                ),
                {"old": old, "new": new},
            )
            if result.rowcount:
                print(f"  {old} -> {new}: {result.rowcount} row(s)")
            else:
                print(f"  {old} -> {new}: no rows")
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())

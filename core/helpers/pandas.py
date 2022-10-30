import pandas as pd
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine
from sqlalchemy.types import Text


async def get_df_from_sql(stmt: Text, engine: AsyncEngine) -> pd.DataFrame:
    def _read_sql(con: AsyncConnection, stmt):
        return pd.read_sql_query(stmt, con)

    async with engine.connect() as conn:
        data = await conn.run_sync(_read_sql, stmt)
    return data

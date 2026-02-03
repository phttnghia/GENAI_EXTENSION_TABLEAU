from sqlalchemy import text
from app.db.session import engine
from pathlib import Path


class BaseDAL:
    QUERY_PATH = Path(__file__).parent / "queries"

    def _load_sql(self, filename: str) -> str:
        return (self.QUERY_PATH / filename).read_text()

    def execute_file_query(self, sql_file: str, params: dict | None = None):
        query = text(self._load_sql(sql_file))

        with engine.connect() as conn:
            result = conn.execute(query, params or {})
            return result.mappings().all()
    
    def execute_query(self, sql_query: str):
        with engine.connect() as conn:
            result = conn.execute(sql_query)
            conn.commit()
            return result.rowcount

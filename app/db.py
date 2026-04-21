from contextlib import contextmanager
from typing import Any, Dict, List


try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None


class OracleExecutor:
    def __init__(self, dsn: str, user: str, password: str, timeout_sec: int = 8):
        self.dsn = dsn
        self.user = user
        self.password = password
        self.timeout_sec = timeout_sec

    @contextmanager
    def _connect(self):
        if oracledb is None:
            raise RuntimeError("oracledb package суулгагдаагүй байна.")
        conn = oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, sql: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.callTimeout = self.timeout_sec * 1000
                cur.execute(sql)
                col_names = [d[0] for d in (cur.description or [])]
                rows = cur.fetchall()

        return [dict(zip(col_names, row)) for row in rows]

    def get_columns(self, view_name: str) -> List[str]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {view_name} WHERE 1=0")
                return [d[0] for d in (cur.description or [])]


class MockExecutor:
    def execute(self, sql: str) -> List[Dict[str, Any]]:
        return [
            {
                "SQL_PREVIEW": sql,
                "INFO": "Mock mode ажиллаж байна. Oracle credential тохируулсны дараа бодит query ажиллана.",
            }
        ]

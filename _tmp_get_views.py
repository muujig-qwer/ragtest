import os, sys
sys.path.insert(0, '/Users/ganaa/Documents/GitHub/ragtest')
from dotenv import load_dotenv
load_dotenv('/Users/ganaa/Documents/GitHub/ragtest/.env')
from app.db import OracleExecutor

executor = OracleExecutor(
    dsn=os.getenv('DB_DSN'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    timeout_sec=8
)

with executor._connect() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT view_name FROM all_views WHERE view_name LIKE 'PRI_%' ORDER BY view_name FETCH FIRST 30 ROWS ONLY")
        views = [row[0] for row in cur.fetchall()]
        print(f"Нийт {len(views)} PRI_* view олдлоо:\n")
        
        for v in views:
            cur.execute(f"SELECT column_name FROM all_tab_columns WHERE table_name = '{v}' ORDER BY column_id")
            cols = [row[0] for row in cur.fetchall()]
            print(f"  {v}")
            print(f"    -> {', '.join(cols)}")
            print()

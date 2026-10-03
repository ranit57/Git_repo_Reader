import psycopg2
from psycopg2.extras import RealDictCursor

# Connection from .env
conn = psycopg2.connect(
    "postgresql://postgres:MMita%40123@localhost:5432/repo_ai",
    cursor_factory=RealDictCursor
)

with conn.cursor() as cur:
    # List all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    print("=== Tables ===")
    for t in tables:
        print(f"  {t['table_name']}")
    
    # Check each table for row counts
    print("\n=== Row Counts ===")
    for t in tables:
        table_name = t['table_name']
        cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        count = cur.fetchone()['count']
        print(f"  {table_name}: {count} rows")
    
    # Sample data from each table
    print("\n=== Sample Data ===")
    for t in tables:
        table_name = t['table_name']
        cur.execute(f"SELECT * FROM {table_name} LIMIT 5")
        rows = cur.fetchall()
        if rows:
            print(f"\n  {table_name}:")
            for row in rows:
                print(f"    {dict(row)}")

conn.close()
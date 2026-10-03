import argparse

from config.settings import settings
from storage.postgres_client import PostgresClient


def main():
    parser = argparse.ArgumentParser(description="List files stored for a repo")
    parser.add_argument("repo_id", help="Repository ID to inspect")
    args = parser.parse_args()

    pg = PostgresClient(settings.postgres_url)

    rows = pg.list_files(args.repo_id)
    print(f"Repo: {args.repo_id}")
    print(f"Stored files: {len(rows)}")
    for r in rows[:50]:
        print(f"- {r['path']} (file_id={r['file_id']}, language={r.get('language')}, file_type={r.get('file_type')})")

    pg.close()


if __name__ == '__main__':
    main()

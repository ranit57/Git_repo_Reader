import argparse

from config.settings import settings
from storage.postgres_client import PostgresClient


def main():
    parser = argparse.ArgumentParser(description="Check ingestion results for a repo")
    parser.add_argument("repo_id", help="Repository ID to inspect")
    args = parser.parse_args()

    pg = PostgresClient(settings.postgres_url)

    files = pg.count_files(args.repo_id)
    chunks = pg.count_chunks(args.repo_id)

    print(f"Repo: {args.repo_id}")
    print(f"Files: {files}")
    print(f"Chunks: {chunks}")

    if chunks > 0:
        print("Sample chunks:")
        for row in pg.sample_chunks(args.repo_id, limit=5):
            print(f"- {row['path']} [{row['start_line']}-{row['end_line']}]: {row['symbol_id']}\n  {row['content'][:200].strip()}...\n")

    pg.close()


if __name__ == '__main__':
    main()

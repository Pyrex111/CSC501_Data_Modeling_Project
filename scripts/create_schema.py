"""Create the agreed schema in a NEW local database without loading demo data."""

import argparse
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True, type=Path,
                        help='new SQLite database file; an existing file is never overwritten')
    args = parser.parse_args()
    if sqlite3.sqlite_version_info < (3, 37, 0):
        parser.error('SQLite 3.37.0 or later is required for STRICT tables')
    path = args.database.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb'):
            pass
    except FileExistsError:
        parser.error(f'Database already exists: {path}. Choose a new path.')

    connection = None
    try:
        connection = sqlite3.connect(path)
        connection.executescript((ROOT / 'src/dal/sql/schema.sql').read_text())
        if connection.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
            raise RuntimeError('Foreign-key enforcement could not be enabled')
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Fresh database failed its integrity check')
        count = connection.execute("SELECT COUNT(*) FROM sqlite_schema WHERE type = 'table'").fetchone()[0]
        connection.close()
        connection = None
        print(f'Created {count} empty model tables in {path}')
        print('Next: load demo data in a validated transaction; no sample data was inserted.')
    except Exception:
        if connection is not None:
            connection.close()
        path.unlink(missing_ok=True)
        raise
    return 0


if __name__ == '__main__':
    sys.exit(main())

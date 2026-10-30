"""Read snapshot exports only in a disposable, filesystem-denied SQLite database."""

import sqlite3

from inputs import InputError


def read_snapshot(text):
    connection = sqlite3.connect(":memory:")
    connection.enable_load_extension(False)
    allowed = {sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_CREATE_INDEX,
               sqlite3.SQLITE_INSERT, sqlite3.SQLITE_READ, sqlite3.SQLITE_SELECT,
               sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_REINDEX}

    def authorize(action, first, second, database, trigger):
        if database not in {None, "main"} or trigger is not None:
            return sqlite3.SQLITE_DENY
        if action in allowed:
            return sqlite3.SQLITE_OK
        # SQLite's own CREATE TABLE/INDEX updates its in-memory catalog.
        if action == sqlite3.SQLITE_UPDATE and first == "sqlite_master":
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and second == "json_valid":
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_PRAGMA and first == "foreign_keys" and second in {"ON", "1"}:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    connection.set_authorizer(authorize)
    ticks = 0

    def limit():
        nonlocal ticks
        ticks += 1
        return int(ticks > 10_000)

    connection.set_progress_handler(limit, 1000)
    try:
        if len(text.encode()) > 5_000_000:
            raise InputError("SQL artifact exceeds extraction bound")
        connection.executescript(text)
        if connection.in_transaction:
            raise InputError("SQL snapshot leaves an open transaction")
        names = [r[0] for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        tables = {}
        for name in names:
            quoted = '"' + name.replace('"', '""') + '"'
            cursor = connection.execute("SELECT * FROM " + quoted)
            columns = [column[0] for column in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor]
            tables[name] = {"columns": columns, "rows": rows}
        return tables
    except sqlite3.Error as exc:
        raise InputError("Unsafe or invalid SQL snapshot: " + str(exc)) from exc
    finally:
        connection.close()

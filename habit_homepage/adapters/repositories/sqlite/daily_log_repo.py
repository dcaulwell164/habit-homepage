import sqlite3
from datetime import date, datetime

from habit_homepage.domain.daily_log import DailyLog
from habit_homepage.domain.habit_entry import HabitEntry
from habit_homepage.domain.value_objects import HabitSource
from habit_homepage.ports.repositories.daily_log_repo import DailyLogRepository


class SQLiteDailyLogRepository(DailyLogRepository):
    """
    Outbound adapter:
    Implements the persistence port using SQLite.
    Follows hexagonal architecture - infrastructure implements domain-defined interface.
    """

    def __init__(self, db_path: str) -> None:
        # check_same_thread=False allows connection to be used across threads
        # This is safe for our use case since SQLite serializes writes internally
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS habit_entries (
                date TEXT NOT NULL,
                habit_id TEXT NOT NULL,
                value REAL NOT NULL,
                recorded_at TEXT NOT NULL,
                source TEXT NOT NULL,
                PRIMARY KEY (date, habit_id),
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
            );
        """)
        self.conn.commit()

    def get_by_date(self, target_date: date) -> DailyLog | None:
        """
        Retrieve all habit entries for a specific date.
        Returns None if no entries exist, otherwise returns DailyLog with entries.
        """
        date_str = target_date.isoformat()
        rows = self.conn.execute(
            """
            SELECT date, habit_id, value, recorded_at, source
            FROM habit_entries
            WHERE date = ?
            """,
            (date_str,),
        ).fetchall()

        if not rows:
            return None

        # Build DailyLog with all entries
        log = DailyLog(date=target_date)
        for row in rows:
            entry = self._row_to_entry(row)
            log.entries[entry.habit_id] = entry

        return log

    def get_by_date_range(self, start: date, end: date) -> list[DailyLog]:
        """Retrieve all daily logs within a date range (inclusive)."""
        rows = self.conn.execute(
            """
            SELECT date, habit_id, value, recorded_at, source
            FROM habit_entries
            WHERE date >= ? AND date <= ?
            ORDER BY date
            """,
            (start.isoformat(), end.isoformat()),
        ).fetchall()

        # Group entries by date
        logs_by_date: dict[date, DailyLog] = {}
        for row in rows:
            entry = self._row_to_entry(row)
            if entry.date not in logs_by_date:
                logs_by_date[entry.date] = DailyLog(date=entry.date)
            logs_by_date[entry.date].entries[entry.habit_id] = entry

        return list(logs_by_date.values())

    def get_entries_by_habit(
        self, habit_id: str, start: date, end: date
    ) -> list[HabitEntry]:
        """Retrieve all entries for a specific habit within a date range."""
        rows = self.conn.execute(
            """
            SELECT date, habit_id, value, recorded_at, source
            FROM habit_entries
            WHERE habit_id = ? AND date >= ? AND date <= ?
            ORDER BY date
            """,
            (habit_id, start.isoformat(), end.isoformat()),
        ).fetchall()

        return [self._row_to_entry(row) for row in rows]

    def save(self, log: DailyLog) -> None:
        """
        Save all habit entries for a daily log.
        Uses UPSERT to handle updates to existing entries.
        """
        for entry in log.entries.values():
            self.conn.execute(
                """
                INSERT INTO habit_entries (date, habit_id, value, recorded_at, source)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(date, habit_id) DO UPDATE SET
                    value=excluded.value,
                    recorded_at=excluded.recorded_at,
                    source=excluded.source;
                """,
                (
                    entry.date.isoformat(),
                    entry.habit_id,
                    entry.value,
                    entry.recorded_at.isoformat(),
                    entry.source.value,
                ),
            )
        self.conn.commit()

    def _row_to_entry(self, row: tuple) -> HabitEntry:
        """Convert a database row to a HabitEntry entity."""
        return HabitEntry(
            date=date.fromisoformat(row[0]),
            habit_id=row[1],
            value=row[2],
            recorded_at=datetime.fromisoformat(row[3]),
            source=HabitSource(row[4]),
        )

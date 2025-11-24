import json
import sqlite3

from habit_homepage.domain.habit import Habit
from habit_homepage.domain.value_objects import CategoryType, HabitSource
from habit_homepage.ports.repositories.habit_repo import HabitRepository


class SQLiteHabitRepository(HabitRepository):
    """
    Outbound adapter:
    Implements the HabitRepository port using SQLite.

    Responsibilities:
    - Persist and retrieve habit data
    - Does NOT define what habits exist (that's application layer)
    - Does NOT seed habits (that's application layer)

    Follows hexagonal architecture - infrastructure implements domain-defined interface.
    """

    def __init__(self, db_path: str) -> None:
        # check_same_thread=False allows connection to be used across threads
        # This is safe for our use case since SQLite serializes writes internally
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                unit TEXT NOT NULL,
                source TEXT NOT NULL,
                description TEXT,
                category_id TEXT,
                provider_config TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            );
        """)
        self.conn.commit()

    def get_by_id(self, habit_id: str) -> Habit | None:
        row = self.conn.execute(
            """
            SELECT id, name, unit, source, description, category_id, provider_config
            FROM habits WHERE id = ?
            """,
            (habit_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_habit(row)

    def get_all(self) -> list[Habit]:
        rows = self.conn.execute(
            "SELECT id, name, unit, source, description, category_id, provider_config FROM habits"
        ).fetchall()

        return [self._row_to_habit(row) for row in rows]

    def save(self, habit: Habit) -> None:
        provider_config_json = (
            json.dumps(habit.provider_config) if habit.provider_config else None
        )
        category_id_str = habit.category_id.value if habit.category_id else None

        self.conn.execute(
            """
            INSERT INTO habits (id, name, unit, source, description, category_id, provider_config)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                unit=excluded.unit,
                source=excluded.source,
                description=excluded.description,
                category_id=excluded.category_id,
                provider_config=excluded.provider_config;
            """,
            (
                habit.id,
                habit.name,
                habit.unit,
                habit.source.value,
                habit.description,
                category_id_str,
                provider_config_json,
            ),
        )
        self.conn.commit()

    def delete(self, habit_id: str) -> None:
        self.conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        self.conn.commit()

    def _row_to_habit(self, row: tuple) -> Habit:
        """Convert a database row to a Habit entity."""
        provider_config = json.loads(row[6]) if row[6] else None
        category_id = CategoryType(row[5]) if row[5] else None

        return Habit(
            id=row[0],
            name=row[1],
            unit=row[2],
            source=HabitSource(row[3]),
            description=row[4] or "",
            category_id=category_id,
            provider_config=provider_config,
        )

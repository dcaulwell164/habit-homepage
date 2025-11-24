import sqlite3
from datetime import date

from habit_homepage.domain.goal import Goal, GoalComparison, GoalPeriod
from habit_homepage.ports.repositories.goal_repo import GoalRepository


class SQLiteGoalRepository(GoalRepository):
    """
    Outbound adapter:
    Implements the GoalRepository port using SQLite.
    """

    def __init__(self, db_path: str) -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                habit_id TEXT NOT NULL,
                target_value REAL NOT NULL,
                comparison TEXT NOT NULL,
                period TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                description TEXT,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
            );
        """)
        self.conn.commit()

    def get_by_id(self, goal_id: str) -> Goal | None:
        row = self.conn.execute(
            """
            SELECT id, habit_id, target_value, comparison, period,
                   start_date, end_date, description
            FROM goals WHERE id = ?
            """,
            (goal_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_goal(row)

    def get_all(self) -> list[Goal]:
        rows = self.conn.execute(
            """
            SELECT id, habit_id, target_value, comparison, period,
                   start_date, end_date, description
            FROM goals
            """
        ).fetchall()

        return [self._row_to_goal(row) for row in rows]

    def get_by_habit(self, habit_id: str) -> list[Goal]:
        rows = self.conn.execute(
            """
            SELECT id, habit_id, target_value, comparison, period,
                   start_date, end_date, description
            FROM goals WHERE habit_id = ?
            """,
            (habit_id,),
        ).fetchall()

        return [self._row_to_goal(row) for row in rows]

    def get_active_goals(self, habit_id: str, check_date: date) -> list[Goal]:
        """Retrieve all active goals for a habit on a specific date."""
        check_date_str = check_date.isoformat()
        rows = self.conn.execute(
            """
            SELECT id, habit_id, target_value, comparison, period,
                   start_date, end_date, description
            FROM goals
            WHERE habit_id = ?
              AND start_date <= ?
              AND (end_date IS NULL OR end_date >= ?)
            """,
            (habit_id, check_date_str, check_date_str),
        ).fetchall()

        return [self._row_to_goal(row) for row in rows]

    def save(self, goal: Goal) -> None:
        end_date_str = goal.end_date.isoformat() if goal.end_date else None

        self.conn.execute(
            """
            INSERT INTO goals (id, habit_id, target_value, comparison, period,
                             start_date, end_date, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                habit_id=excluded.habit_id,
                target_value=excluded.target_value,
                comparison=excluded.comparison,
                period=excluded.period,
                start_date=excluded.start_date,
                end_date=excluded.end_date,
                description=excluded.description;
            """,
            (
                goal.id,
                goal.habit_id,
                goal.target_value,
                goal.comparison.value,
                goal.period.value,
                goal.start_date.isoformat(),
                end_date_str,
                goal.description,
            ),
        )
        self.conn.commit()

    def delete(self, goal_id: str) -> None:
        self.conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        self.conn.commit()

    def _row_to_goal(self, row: tuple) -> Goal:
        """Convert a database row to a Goal entity."""
        return Goal(
            id=row[0],
            habit_id=row[1],
            target_value=row[2],
            comparison=GoalComparison(row[3]),
            period=GoalPeriod(row[4]),
            start_date=date.fromisoformat(row[5]),
            end_date=date.fromisoformat(row[6]) if row[6] else None,
            description=row[7] or "",
        )

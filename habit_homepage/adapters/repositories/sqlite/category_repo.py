import sqlite3

from habit_homepage.domain.category import Category
from habit_homepage.domain.value_objects import CategoryType
from habit_homepage.ports.repositories.category_repo import CategoryRepository


class SQLiteCategoryRepository(CategoryRepository):
    """
    Outbound adapter:
    Implements the CategoryRepository port using SQLite.
    """

    def __init__(self, db_path: str) -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()
        self._seed_default_categories()

    def _create_table(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def get_by_id(self, category_id: CategoryType) -> Category | None:
        row = self.conn.execute(
            """
            SELECT id, name, description, color
            FROM categories WHERE id = ?
            """,
            (category_id.value,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_category(row)

    def get_all(self) -> list[Category]:
        rows = self.conn.execute(
            "SELECT id, name, description, color FROM categories"
        ).fetchall()

        return [self._row_to_category(row) for row in rows]

    def save(self, category: Category) -> None:
        self.conn.execute(
            """
            INSERT INTO categories (id, name, description, color)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                color=excluded.color;
            """,
            (
                category.id.value,
                category.name,
                category.description,
                category.color,
            ),
        )
        self.conn.commit()

    def delete(self, category_id: CategoryType) -> None:
        self.conn.execute("DELETE FROM categories WHERE id = ?", (category_id.value,))
        self.conn.commit()

    def _row_to_category(self, row: tuple) -> Category:
        """Convert a database row to a Category entity."""
        return Category(
            id=CategoryType(row[0]),
            name=row[1],
            description=row[2] or "",
            color=row[3],
        )

    def _seed_default_categories(self) -> None:
        """Seed default categories if the table is empty."""
        existing = self.get_all()
        if existing:
            return

        default_categories = [
            Category(
                id=CategoryType.HEALTH,
                name="Health",
                description="Physical and mental health habits",
                color="#22c55e",
            ),
            Category(
                id=CategoryType.LEARNING,
                name="Learning",
                description="Education and skill development",
                color="#3b82f6",
            ),
            Category(
                id=CategoryType.PRODUCTIVITY,
                name="Productivity",
                description="Work and task completion",
                color="#f59e0b",
            ),
            Category(
                id=CategoryType.SOCIAL,
                name="Social",
                description="Relationships and social activities",
                color="#ec4899",
            ),
            Category(
                id=CategoryType.FINANCE,
                name="Finance",
                description="Financial habits and goals",
                color="#10b981",
            ),
        ]

        for category in default_categories:
            self.save(category)

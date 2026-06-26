"""Local SQLite-backed MCP-like server for ERP demo data."""
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from config import DB_PATH


class ERPServer:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    order_date TEXT NOT NULL,
                    FOREIGN KEY(customer_id) REFERENCES customers(id),
                    FOREIGN KEY(product_id) REFERENCES products(id)
                )
                """
            )
            conn.commit()

        if self._table_is_empty("products"):
            self._seed_products()
        if self._table_is_empty("customers"):
            self._seed_customers()
        if self._table_is_empty("orders"):
            self._seed_orders()

    def _table_is_empty(self, table_name: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
            return int(row["count"]) == 0

    def _seed_products(self) -> None:
        products = [
            ("لپ‌تاپ لنوو ThinkPad X1", "لپ‌تاپ", "Lenovo", 68000000, 12),
            ("لپ‌تاپ ایسوس Zenbook 14", "لپ‌تاپ", "ASUS", 54000000, 8),
            ("کیبورد مکانیکال Corsair K70", "کیبورد", "Corsair", 9500000, 15),
            ("کیبورد بی‌سیم Logitech MX Keys", "کیبورد", "Logitech", 12800000, 10),
            ("لپ‌تاپ اپل MacBook Air", "لپ‌تاپ", "Apple", 72000000, 6),
        ]
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO products (name, category, brand, price, stock) VALUES (?, ?, ?, ?, ?)",
                products,
            )
            conn.commit()

    def _seed_customers(self) -> None:
        customers = [
            ("سارا محمدی", "تهران", "09120001122", "sara@example.com"),
            ("امیررضا قاسمی", "قزوین", "09121112233", "amir@example.com"),
            ("نرگس کریمی", "تهران", "09132223344", "narges@example.com"),
            ("مهراد صادقی", "مشهد", "09143334455", "mehrad@example.com"),
            ("فاطمه احمدی", "قزوین", "09154445566", "fatemeh@example.com"),
        ]
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO customers (name, city, phone, email) VALUES (?, ?, ?, ?)",
                customers,
            )
            conn.commit()

    def _seed_orders(self) -> None:
        orders = [
            (1, 1, 2, 136000000, "2026-05-12"),
            (2, 3, 1, 9500000, "2026-05-15"),
            (3, 2, 3, 162000000, "2026-05-18"),
            (5, 4, 1, 12800000, "2026-05-20"),
        ]
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO orders (customer_id, product_id, quantity, total_amount, order_date) VALUES (?, ?, ?, ?, ?)",
                orders,
            )
            conn.commit()

    def get_tools_definition(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_db_schema",
                    "description": "بازگرداندن ساختار دیتابیس شامل جدول‌ها و ستون‌ها",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_read_query",
                    "description": "اجرا کردن یک کوئری SELECT امن روی دیتابیس محلی",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "یک کوئری SELECT معتبر برای خواندن داده‌ها",
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    def get_db_schema(self) -> Dict[str, Any]:
        tables = []
        with self._connect() as conn:
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ):
                table_name = row["name"]
                columns = [
                    column[1]
                    for column in conn.execute(f"PRAGMA table_info({table_name})")
                ]
                tables.append({"name": table_name, "columns": columns})
        return {"tables": tables}

    def execute_read_query(self, query: str) -> Dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("کوئری باید یک رشته‌ی معتبر باشد.")

        normalized = re.sub(r"\s+", " ", query.strip())
        upper = normalized.upper()
        forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "REPLACE", "ATTACH", "DETACH", "PRAGMA", "VACUUM", "TRUNCATE"]
        if not upper.startswith("SELECT") and not upper.startswith("WITH"):
            raise ValueError("فقط کوئری‌های SELECT مجاز هستند.")
        if any(keyword in upper for keyword in forbidden_keywords):
            raise ValueError("این نوع کوئری مجاز نیست.")

        with self._connect() as conn:
            cursor = conn.execute(query)
            rows = [dict(row) for row in cursor.fetchall()]
        return {"row_count": len(rows), "rows": rows}

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any] | None = None) -> Dict[str, Any]:
        args = arguments or {}
        if tool_name == "get_db_schema":
            return self.get_db_schema()
        if tool_name == "execute_read_query":
            query = args.get("query", "")
            return self.execute_read_query(query)
        raise ValueError(f"ابزار ناشناخته: {tool_name}")

    def close(self) -> None:
        return None


if __name__ == "__main__":
    server = ERPServer()
    print(json.dumps(server.get_db_schema(), ensure_ascii=False, indent=2))
    server.close()

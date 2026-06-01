"""wellbeing-mcp: a local health tracking MCP server."""

import sqlite3
from pathlib import Path
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# ---------- 数据库位置 ----------
DB_PATH = Path.home() / ".wellbeing-mcp" / "wellbeing.db"


def get_db():
    """打开数据库连接，第一次会自动建文件和文件夹。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建表（如果还没建）。"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            meal_time TEXT,
            meal_type TEXT,
            content TEXT NOT NULL,
            location TEXT,
            raw_input TEXT
        )
    """)
    conn.commit()
    conn.close()


# ---------- 创建 MCP server ----------
mcp = FastMCP("wellbeing")


# ---------- 工具 1: 存饮食 ----------
@mcp.tool()
def save_meal(
    content: str,
    meal_type: str = "",
    meal_time: str = "",
    location: str = "",
    raw_input: str = "",
) -> str:
    """记录一条饮食。

    Args:
        content: 吃了什么，比如 "粥、鸡蛋"（必填）
        meal_type: 餐次，早餐/午餐/晚餐/加餐
        meal_time: 吃饭时间，ISO 格式，比如 "2026-06-01T08:00"
        location: 在哪吃的，家/公司/外卖/餐厅
        raw_input: 用户的原话
    """
    conn = get_db()
    conn.execute(
        "INSERT INTO meals (created_at, meal_time, meal_type, content, location, raw_input) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), meal_time, meal_type, content, location, raw_input),
    )
    conn.commit()
    conn.close()
    return f"已记录饮食：{content}"


# ---------- 工具 2: 查最近记录 ----------
@mcp.tool()
def query_recent(table: str, days: int = 7) -> str:
    """查询最近 N 天某张表的记录。

    Args:
        table: 表名，目前支持 meals
        days: 最近多少天，默认 7
    """
    if table != "meals":
        return f"暂不支持查询表：{table}"
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM meals WHERE created_at >= datetime('now', ?) ORDER BY created_at DESC",
        (f"-{days} days",),
    ).fetchall()
    conn.close()
    if not rows:
        return f"最近 {days} 天没有 {table} 记录。"
    lines = [f"最近 {days} 天的 {table} 记录（{len(rows)} 条）："]
    for r in rows:
        lines.append(f"- [{r['created_at']}] {r['meal_type']} {r['content']} @ {r['location']}")
    return "\n".join(lines)


# ---------- 启动时建表 ----------
init_db()
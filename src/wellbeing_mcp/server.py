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
    """建所有表（如果还没建）。"""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            meal_time TEXT,
            meal_type TEXT,
            content TEXT NOT NULL,
            location TEXT,
            raw_input TEXT
        );
        CREATE TABLE IF NOT EXISTS sleeps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            sleep_at TEXT,
            wake_at TEXT,
            quality INTEGER,
            wake_count INTEGER,
            wake_duration INTEGER,
            raw_input TEXT
        );
        CREATE TABLE IF NOT EXISTS moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            mood_at TEXT,
            score INTEGER NOT NULL,
            trigger TEXT,
            raw_input TEXT
        );
        CREATE TABLE IF NOT EXISTS symptoms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            onset_at TEXT,
            body_part TEXT NOT NULL,
            symptom_type TEXT NOT NULL,
            severity INTEGER,
            duration_status TEXT,
            notes TEXT,
            raw_input TEXT
        );
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            exercise_at TEXT,
            activity_type TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            intensity TEXT,
            location TEXT,
            notes TEXT,
            raw_input TEXT
        );
    """)
    conn.commit()
    conn.close()


# ---------- 创建 MCP server ----------
mcp = FastMCP("wellbeing")


# ========== 存储类工具 ==========

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


@mcp.tool()
def save_sleep(
    sleep_at: str,
    wake_at: str,
    quality: int = 0,
    wake_count: int = 0,
    wake_duration: int = 0,
    raw_input: str = "",
) -> str:
    """记录一条睡眠。

    Args:
        sleep_at: 几点睡着，ISO 格式（必填）
        wake_at: 几点醒，ISO 格式（必填）
        quality: 睡眠质量，1-10 分
        wake_count: 中途醒来次数
        wake_duration: 中途清醒总时长（分钟）
        raw_input: 用户的原话
    """
    conn = get_db()
    conn.execute(
        "INSERT INTO sleeps (created_at, sleep_at, wake_at, quality, wake_count, wake_duration, raw_input) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), sleep_at, wake_at, quality, wake_count, wake_duration, raw_input),
    )
    conn.commit()
    conn.close()
    return f"已记录睡眠：{sleep_at} 到 {wake_at}"


@mcp.tool()
def save_mood(
    score: int,
    mood_at: str = "",
    trigger: str = "",
    raw_input: str = "",
) -> str:
    """记录一条情绪。

    Args:
        score: 情绪评分，1-10 分（必填）
        mood_at: 什么时候的情绪，ISO 格式
        trigger: 触发原因/事件（score < 4 时建议追问后填入）
        raw_input: 用户的原话
    """
    conn = get_db()
    conn.execute(
        "INSERT INTO moods (created_at, mood_at, score, trigger, raw_input) "
        "VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), mood_at, score, trigger, raw_input),
    )
    conn.commit()
    conn.close()
    return f"已记录情绪：{score} 分"


@mcp.tool()
def save_symptom(
    body_part: str,
    symptom_type: str,
    severity: int,
    onset_at: str = "",
    duration_status: str = "持续",
    notes: str = "",
    raw_input: str = "",
    related_id: int = 0,
) -> str:
    """记录一条症状，或更新已有症状。

    使用前建议先调用 query_active_symptoms 查同部位的活跃症状。
    如果这是已有症状的延续，传入 related_id 来更新它（只更新 severity 和 duration_status）；
    否则不传 related_id，新建一条记录。

    Args:
        body_part: 身体部位，比如 "腰"、"头"、"喉咙"（必填）
        symptom_type: 症状类型，比如 "疼"、"咳嗽"、"无力"（必填）
        severity: 严重程度，1-5 分（必填）
        onset_at: 症状开始时间，ISO 格式
        duration_status: 持续/间歇/恶化中/已缓解
        notes: 附加描述，比如吃了什么药
        raw_input: 用户的原话
        related_id: 若是已有症状的延续，传入该症状的 id 来更新
    """
    conn = get_db()
    if related_id:
        conn.execute(
            "UPDATE symptoms SET severity = ?, duration_status = ? WHERE id = ?",
            (severity, duration_status, related_id),
        )
        conn.commit()
        conn.close()
        return f"已更新症状 #{related_id}：{body_part}{symptom_type}，严重度 {severity}，状态 {duration_status}"
    else:
        cur = conn.execute(
            "INSERT INTO symptoms (created_at, onset_at, body_part, symptom_type, severity, duration_status, notes, raw_input) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), onset_at, body_part, symptom_type, severity, duration_status, notes, raw_input),
        )
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return f"已记录症状 #{new_id}：{body_part}{symptom_type}，严重度 {severity}"


@mcp.tool()
def save_exercise(
    activity_type: str,
    duration_minutes: int,
    exercise_at: str = "",
    intensity: str = "",
    location: str = "",
    notes: str = "",
    raw_input: str = "",
) -> str:
    """记录一条运动。

    Args:
        activity_type: 运动类型，比如 "跑步"、"瑜伽"（必填）
        duration_minutes: 时长，分钟（必填）
        exercise_at: 运动时间，ISO 格式
        intensity: 强度，轻/中/高
        location: 地点，公园/健身房/家
        notes: 附加描述，比如距离、配速、感受
        raw_input: 用户的原话
    """
    conn = get_db()
    conn.execute(
        "INSERT INTO exercises (created_at, exercise_at, activity_type, duration_minutes, intensity, location, notes, raw_input) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), exercise_at, activity_type, duration_minutes, intensity, location, notes, raw_input),
    )
    conn.commit()
    conn.close()
    return f"已记录运动：{activity_type} {duration_minutes} 分钟"


# ========== 查询类工具 ==========

@mcp.tool()
def query_recent(table: str, days: int = 7) -> str:
    """查询最近 N 天某张表的记录。

    Args:
        table: 表名，支持 meals/sleeps/moods/symptoms/exercises
        days: 最近多少天，默认 7
    """
    valid = {"meals", "sleeps", "moods", "symptoms", "exercises"}
    if table not in valid:
        return f"暂不支持查询表：{table}。支持的表：{', '.join(valid)}"
    conn = get_db()
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE created_at >= datetime('now', ?) ORDER BY created_at DESC",
        (f"-{days} days",),
    ).fetchall()
    conn.close()
    if not rows:
        return f"最近 {days} 天没有 {table} 记录。"
    lines = [f"最近 {days} 天的 {table} 记录（{len(rows)} 条）："]
    for r in rows:
        d = dict(r)
        d.pop("raw_input", None)
        parts = [f"{k}={v}" for k, v in d.items() if v not in (None, "", 0)]
        lines.append("- " + " | ".join(parts))
    return "\n".join(lines)


@mcp.tool()
def query_active_symptoms(days: int = 7) -> str:
    """查询最近 N 天内未结束的症状（duration_status 不是"已缓解"）。

    记录新症状前先调用此工具，判断是否是已有症状的延续。

    Args:
        days: 最近多少天，默认 7
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM symptoms WHERE created_at >= datetime('now', ?) "
        "AND duration_status != '已缓解' ORDER BY created_at DESC",
        (f"-{days} days",),
    ).fetchall()
    conn.close()
    if not rows:
        return f"最近 {days} 天没有未结束的症状。"
    lines = [f"最近 {days} 天未结束的症状（{len(rows)} 条）："]
    for r in rows:
        lines.append(
            f"- #{r['id']} {r['body_part']}{r['symptom_type']} "
            f"严重度{r['severity']} 状态{r['duration_status']} 记录于{r['created_at'][:10]}"
        )
    return "\n".join(lines)


# ========== 分析类工具 ==========

@mcp.tool()
def weekly_summary(week_start_date: str = "") -> str:
    """生成本周的结构化健康统计（供 agent 进一步分析）。

    Args:
        week_start_date: 本周起始日期，ISO 格式如 "2026-05-26"。留空则默认最近 7 天。
    """
    conn = get_db()
    if week_start_date:
        cond = "created_at >= ?"
        param = (week_start_date,)
    else:
        cond = "created_at >= datetime('now', '-7 days')"
        param = ()

    meal_count = conn.execute(f"SELECT COUNT(*) FROM meals WHERE {cond}", param).fetchone()[0]
    sleep_avg = conn.execute(f"SELECT AVG(quality) FROM sleeps WHERE {cond} AND quality > 0", param).fetchone()[0]
    mood_avg = conn.execute(f"SELECT AVG(score) FROM moods WHERE {cond}", param).fetchone()[0]
    mood_low = conn.execute(f"SELECT COUNT(*) FROM moods WHERE {cond} AND score < 4", param).fetchone()[0]
    symptom_count = conn.execute(f"SELECT COUNT(*) FROM symptoms WHERE {cond}", param).fetchone()[0]
    active_symptoms = conn.execute(
        f"SELECT COUNT(*) FROM symptoms WHERE {cond} AND duration_status != '已缓解'", param
    ).fetchone()[0]
    exercise_count = conn.execute(f"SELECT COUNT(*) FROM exercises WHERE {cond}", param).fetchone()[0]
    exercise_minutes = conn.execute(
        f"SELECT SUM(duration_minutes) FROM exercises WHERE {cond}", param
    ).fetchone()[0]
    conn.close()

    return "\n".join([
        "本周健康统计：",
        f"- 饮食记录：{meal_count} 条",
        f"- 平均睡眠质量：{round(sleep_avg, 1) if sleep_avg else '无数据'}",
        f"- 平均情绪分：{round(mood_avg, 1) if mood_avg else '无数据'}（低于4分 {mood_low} 次）",
        f"- 症状记录：{symptom_count} 条（未结束 {active_symptoms} 条）",
        f"- 运动：{exercise_count} 次，共 {exercise_minutes or 0} 分钟",
    ])


# ---------- 启动时建表 ----------
init_db()


if __name__ == "__main__":
    mcp.run()
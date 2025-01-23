import os

import asyncpg
from home_template import HTML_TEMPLATE
from quart import Quart, g, jsonify, render_template_string

app = Quart(__name__)


async def get_db_pool():
    if not hasattr(g, "db_pool"):
        g.db_pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=10)
    return g.db_pool


@app.teardown_appcontext
async def close_db_pool(exc):
    if hasattr(g, "db_pool"):
        pool = g.db_pool
        await pool.close()


@app.route("/")
async def home():
    return await render_template_string(HTML_TEMPLATE)


@app.route("/log-click/<button_id>", methods=["POST"])
async def log_click(button_id):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO clicks (button_id) VALUES ($1)", button_id)
    return jsonify({"status": "success"})


@app.route("/clicks")
async def get_clicks():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT button_id, clicked_at FROM clicks ORDER BY clicked_at DESC LIMIT 10"
        )
        clicks = [
            {
                "button_id": row["button_id"],
                "clicked_at": row["clicked_at"].strftime("%Y-%m-%d %H:%M:%S"),
            }
            for row in rows
        ]
    return jsonify(clicks)


@app.route("/stats")
async def get_stats():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT button_id, COUNT(*) as count 
            FROM clicks 
            GROUP BY button_id 
            ORDER BY count DESC
            """
        )
        stats = [{"button_id": row["button_id"], "count": row["count"]} for row in rows]
    return jsonify(stats)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8087)

import os
import time

import asyncpg
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, Summary, generate_latest
from quart import Quart, Response, g, jsonify, request
from quart_cors import cors  # Pour gérer les CORS

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Permettre les requêtes cross-origin

# Define metrics with more specific names and labels
HTTP_REQUEST_TOTAL = Counter(
    "http_requests_total", "Total number of HTTP requests", ["endpoint", "method", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint", "method"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
)

# Add summary metrics for better statistical analysis
HTTP_REQUEST_SUMMARY = Summary(
    "http_request_summary_seconds", "HTTP request latency summary", ["endpoint", "method"]
)

# Database metrics
DB_CONNECTION_TOTAL = Counter(
    "db_connections_total", "Total number of database connections created"
)

DB_REQUEST_DURATION_SECONDS = Histogram(
    "db_request_duration_seconds",
    "Database request duration in seconds",
    ["query_type"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
)


async def get_db_pool():
    if not hasattr(g, "db_pool"):
        g.db_pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=10)
    return g.db_pool


@app.teardown_appcontext
async def close_db_pool(exc):
    if hasattr(g, "db_pool"):
        pool = g.db_pool
        await pool.close()


@app.before_request
async def before_request():
    g.start_time = time.time()


@app.after_request
async def after_request(response):
    # Calculate request duration
    duration = time.time() - g.start_time

    # Get endpoint and method
    endpoint = request.endpoint or "unknown"
    method = request.method

    # Record metrics with more specific labels
    HTTP_REQUEST_TOTAL.labels(endpoint=endpoint, method=method, status=response.status_code).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(endpoint=endpoint, method=method).observe(duration)

    HTTP_REQUEST_SUMMARY.labels(endpoint=endpoint, method=method).observe(duration)

    return response


@app.route("/metrics")
async def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/")
async def home():
    return jsonify({"message": "Balloon de Oro API"})


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


@app.route("/health")
async def health():
    try:
        # Vérifier la connexion à la base de données
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return jsonify({"status": "healthy"}), 200
    except Exception:
        return jsonify({"status": "unhealthy"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8087)

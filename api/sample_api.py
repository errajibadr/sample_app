import os
import time

import asyncpg
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from quart import Quart, Response, g, jsonify, request
from quart_cors import cors  # Pour gérer les CORS

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Permettre les requêtes cross-origin

# Utiliser des dictionnaires pour stocker les métriques par endpoint
requests_metrics = {}
latency_metrics = {}


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
    endpoint = request.endpoint
    method = request.method

    # Créer les métriques pour cet endpoint si elles n'existent pas encore
    metric_key = f"{method}_{endpoint}"
    if metric_key not in requests_metrics:
        requests_metrics[metric_key] = Counter(
            "api_requests_total", "Total number of API requests", ["method", "endpoint", "status"]
        )
        latency_metrics[metric_key] = Histogram(
            "api_request_duration_seconds",
            "Request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
        )

    # Calculer la latence
    latency = time.time() - g.start_time

    # Enregistrer les métriques
    requests_metrics[metric_key].labels(
        method=method, endpoint=endpoint, status=response.status_code
    ).inc()

    latency_metrics[metric_key].labels(method=method, endpoint=endpoint).observe(latency)

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

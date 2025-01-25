from unittest.mock import AsyncMock, MagicMock

import pytest
from quart.testing import QuartClient


@pytest.fixture
def test_app():
    from api.sample_api import app

    app.config["TESTING"] = True
    return app


@pytest.fixture
def test_client(test_app) -> QuartClient:
    return test_app.test_client()


@pytest.fixture
def mock_pool(mocker):
    # Créer un mock pour le pool de connexion
    pool = AsyncMock()

    # Créer un mock pour la connexion
    conn = AsyncMock()

    # Mock pour fetchrow
    conn.fetchrow = AsyncMock()
    # Mock pour fetch
    conn.fetch = AsyncMock(return_value=[])
    # Mock pour execute
    conn.execute = AsyncMock()

    # Configure le pool pour retourner la connexion mockée
    pool.acquire.return_value.__aenter__.return_value = conn

    # Patch la fonction create_pool
    mocker.patch("asyncpg.create_pool", return_value=pool)

    return pool


@pytest.fixture
def mock_db(mock_pool):
    """Fixture qui configure les retours par défaut pour différents cas de test"""
    conn = mock_pool.acquire.return_value.__aenter__.return_value

    # Mock pour /clicks
    conn.fetch.return_value = [
        {
            "button_id": f"button{i}",
            "clicked_at": MagicMock(strftime=lambda x: "2024-01-01 12:00:00"),
        }
        for i in range(3)
    ]

    # Mock pour /stats
    conn.fetch.return_value = [
        {"button_id": "button1", "count": 3},
        {"button_id": "button2", "count": 2},
        {"button_id": "button3", "count": 1},
    ]

    return mock_pool

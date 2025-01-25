import pytest


@pytest.mark.asyncio
async def test_home(test_client):
    async with test_client as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = await response.get_json()
        assert data["message"] == "Balloon de Oro API"

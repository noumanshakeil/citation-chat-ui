import pytest

@pytest.mark.asyncio
async def test_refuse_without_sources(client):
    r = await client.post("/api/chat", json={"question": "What is our refund policy?"})
    assert r.status_code == 200
    assert r.json()["refused"] is True

@pytest.mark.asyncio
async def test_grounded_with_source(client):
    await client.post("/api/sources", json={"title": "Policy", "body": "Refunds within 30 days for unused seats.", "url": "https://example.com/policy"})
    r = await client.post("/api/chat", json={"question": "unused seats refund window"})
    assert r.status_code == 200
    assert r.json()["refused"] is False
    assert r.json()["citations"]

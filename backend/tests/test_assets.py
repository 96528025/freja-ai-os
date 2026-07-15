def test_capture_and_search_idea(client, monkeypatch):
    monkeypatch.setattr("app.services.vector_store.VectorStore.index", lambda *args, **kwargs: None)
    response = client.post(
        "/api/v1/assets/ideas",
        json={"content": "我有一个想法：做一个 AI 学习计划生成器"},
    )
    assert response.status_code == 201
    asset = response.json()
    assert asset["type"] == "idea"
    assert "ai" in asset["tags"]
    assert asset["metadata"]["captured_via"] == "inbox"
    assert asset["created_at"].endswith("Z")

    result = client.get("/api/v1/assets", params={"query": "学习计划"})
    assert result.status_code == 200
    assert result.json()["total"] == 1


def test_dashboard_counts_assets(client, monkeypatch):
    monkeypatch.setattr("app.services.vector_store.VectorStore.index", lambda *args, **kwargs: None)
    client.post("/api/v1/assets/ideas", json={"content": "Build a personal research agent"})
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    assert response.json()["stats"]["ideas"] == 1
    assert response.json()["latest_ideas"][0]["type"] == "idea"

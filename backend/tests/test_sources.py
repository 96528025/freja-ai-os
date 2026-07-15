def test_sources_are_independently_configurable(client):
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    sources = {source["id"]: source for source in response.json()}
    assert sources["openai_blog"]["acquisition"] == "RSS"
    assert "hacker_news" not in sources
    assert sources["reddit"]["availability"] == "needs_auth"
    assert sources["xiaohongshu"]["availability"] == "needs_auth"
    assert sources["xiaohongshu"]["name"] == "小红书 / Rednote"
    assert sources["linkedin"]["availability"] == "planned"

    updated = client.patch("/api/v1/sources/github_trending", json={"enabled": False})
    assert updated.status_code == 200
    assert next(item for item in updated.json() if item["id"] == "github_trending")["enabled"] is False


def test_planned_source_cannot_be_enabled(client):
    response = client.patch("/api/v1/sources/linkedin", json={"enabled": True})
    assert response.status_code == 409


def test_sources_can_be_selected_and_cleared_in_bulk(client):
    selected = client.patch("/api/v1/sources", json={"enabled": True})
    assert selected.status_code == 200
    sources = {source["id"]: source for source in selected.json()}
    assert sources["openai_blog"]["enabled"] is True
    assert sources["github_trending"]["enabled"] is True
    assert sources["reddit"]["enabled"] is False
    assert sources["linkedin"]["enabled"] is False

    cleared = client.patch("/api/v1/sources", json={"enabled": False})
    assert cleared.status_code == 200
    assert not any(source["enabled"] for source in cleared.json())

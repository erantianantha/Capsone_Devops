from datetime import date, timedelta


def test_create_item(client):
    resp = client.post("/api/items", json={"name": "Rice", "category": "Grains", "quantity": 5, "unit": "kg"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["name"] == "Rice"
    assert body["quantity"] == 5
    assert body["expiry_date"] is None


def test_create_item_rejects_empty_name(client):
    resp = client.post("/api/items", json={"name": ""})
    assert resp.status_code == 422


def test_create_item_rejects_negative_quantity(client):
    resp = client.post("/api/items", json={"name": "Eggs", "quantity": -1})
    assert resp.status_code == 422


def test_list_items_empty(client):
    resp = client.get("/api/items")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_items_filters_by_category_and_search(client, sample_item):
    client.post("/api/items", json={"name": "Apples", "category": "Produce"})
    assert len(client.get("/api/items").json()) == 2
    dairy = client.get("/api/items", params={"category": "Dairy"}).json()
    assert [i["name"] for i in dairy] == ["Milk"]
    found = client.get("/api/items", params={"search": "app"}).json()
    assert [i["name"] for i in found] == ["Apples"]


def test_list_items_sorted_by_expiry(client):
    later = (date.today() + timedelta(days=30)).isoformat()
    sooner = (date.today() + timedelta(days=2)).isoformat()
    client.post("/api/items", json={"name": "No expiry"})
    client.post("/api/items", json={"name": "Later", "expiry_date": later})
    client.post("/api/items", json={"name": "Sooner", "expiry_date": sooner})
    names = [i["name"] for i in client.get("/api/items").json()]
    assert names == ["Sooner", "Later", "No expiry"]


def test_get_item(client, sample_item):
    resp = client.get(f"/api/items/{sample_item['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Milk"


def test_get_missing_item_returns_404(client):
    assert client.get("/api/items/9999").status_code == 404


def test_update_item_partial(client, sample_item):
    resp = client.put(f"/api/items/{sample_item['id']}", json={"quantity": 0.5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["quantity"] == 0.5
    assert body["name"] == "Milk"  # untouched fields are preserved


def test_update_missing_item_returns_404(client):
    assert client.put("/api/items/9999", json={"quantity": 1}).status_code == 404


def test_delete_item(client, sample_item):
    resp = client.delete(f"/api/items/{sample_item['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/items/{sample_item['id']}").status_code == 404


def test_delete_missing_item_returns_404(client):
    assert client.delete("/api/items/9999").status_code == 404


def test_stats_counts_expiring_and_expired(client):
    today = date.today()
    client.post("/api/items", json={"name": "Old bread", "category": "Bakery",
                                    "expiry_date": (today - timedelta(days=1)).isoformat()})
    client.post("/api/items", json={"name": "Yogurt", "category": "Dairy",
                                    "expiry_date": (today + timedelta(days=1)).isoformat()})
    client.post("/api/items", json={"name": "Salt", "category": "Spices"})
    stats = client.get("/api/items/stats").json()
    assert stats["total_items"] == 3
    assert stats["expired"] == 1
    assert stats["expiring_soon"] == 1
    assert stats["by_category"] == {"Bakery": 1, "Dairy": 1, "Spices": 1}

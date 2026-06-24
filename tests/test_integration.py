"""Tests d'intégration : le serveur Flask tourne réellement, requêtes via `requests`."""

import requests


def test_root_returns_welcome(base_url):
    """GET / renvoie 200 et le message de bienvenue."""
    resp = requests.get(f"{base_url}/", timeout=5)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Hello World!"


def test_list_items_returns_json_list(base_url):
    """GET /items renvoie une liste JSON cohérente avec son compteur."""
    resp = requests.get(f"{base_url}/items", timeout=5)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["items"], list)
    assert body["count"] == len(body["items"])


def test_add_item(base_url):
    """POST /items ajoute l'item et le retrouve ensuite dans la liste."""
    resp = requests.post(f"{base_url}/items", json={"name": "Nouvel item"}, timeout=5)
    assert resp.status_code == 201
    created = resp.json()["item"]
    assert created["name"] == "Nouvel item"

    listing = requests.get(f"{base_url}/items", timeout=5).json()
    assert any(item["id"] == created["id"] for item in listing["items"])


def test_add_item_requires_name(base_url):
    """POST /items sans 'name' est rejeté avec un code 400."""
    resp = requests.post(f"{base_url}/items", json={}, timeout=5)
    assert resp.status_code == 400


def test_delete_item(base_url):
    """DELETE /items/<id> supprime l'item, qui disparaît ensuite de la liste."""
    created = requests.post(
        f"{base_url}/items", json={"name": "À supprimer"}, timeout=5
    ).json()["item"]

    resp = requests.delete(f"{base_url}/items/{created['id']}", timeout=5)
    assert resp.status_code == 200

    listing = requests.get(f"{base_url}/items", timeout=5).json()
    assert all(item["id"] != created["id"] for item in listing["items"])


def test_delete_missing_item_returns_404(base_url):
    """DELETE d'un id inexistant renvoie 404."""
    resp = requests.delete(f"{base_url}/items/999999", timeout=5)
    assert resp.status_code == 404

"""API Flask de démonstration pour la chaîne CI/CD (tests -> Docker -> GHCR -> Render).

Routes :
    GET    /                -> message de bienvenue
    GET    /items           -> liste JSON d'items factices
    POST   /items           -> ajoute un item, retourne une confirmation
    DELETE /items/<id>      -> supprime un item (support du test "suppression")
"""

import os

from flask import Flask, jsonify, request


def create_app():
    """Fabrique l'application Flask (pattern factory, pratique pour les tests)."""
    app = Flask(__name__)
    app.config["APP_NAME"] = os.environ.get("APP_NAME", "flask-api-demo")

    # Stockage en mémoire (factice) — réinitialisé à chaque démarrage du process.
    items = [
        {"id": 1, "name": "Item Alpha"},
        {"id": 2, "name": "Item Beta"},
    ]
    state = {"next_id": 3}

    @app.get("/")
    def index():
        return jsonify(message="Hello World!", app=app.config["APP_NAME"])

    @app.get("/items")
    def list_items():
        return jsonify(items=items, count=len(items))

    @app.post("/items")
    def create_item():
        data = request.get_json(silent=True)
        if not data or not data.get("name"):
            return jsonify(error="Le champ 'name' est requis"), 400
        item = {"id": state["next_id"], "name": data["name"]}
        state["next_id"] += 1
        items.append(item)
        return jsonify(message="Item créé avec succès", item=item), 201

    @app.delete("/items/<int:item_id>")
    def delete_item(item_id):
        for index, current in enumerate(items):
            if current["id"] == item_id:
                removed = items.pop(index)
                return jsonify(message="Item supprimé avec succès", item=removed)
        return jsonify(error="Item introuvable"), 404

    return app


# Instance au niveau module pour gunicorn : "app.main:app"
app = create_app()


if __name__ == "__main__":
    # Exécution locale en direct (serveur de dev Flask).
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

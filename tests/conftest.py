"""Fixtures pytest : démarre un vrai serveur Flask pour des tests d'intégration HTTP.

Les tests utilisent la librairie `requests` contre ce serveur lancé dans un thread,
on valide donc l'application telle qu'elle répond réellement sur le réseau.
"""

import threading
import time

import pytest
import requests
from werkzeug.serving import make_server

from app.main import create_app


class _ServerThread(threading.Thread):
    """Lance le serveur WSGI dans un thread démon, arrêtable proprement."""

    def __init__(self, host="127.0.0.1", port=5005):
        super().__init__(daemon=True)
        self._server = make_server(host, port, create_app())
        self.base_url = f"http://{host}:{port}"

    def run(self):
        self._server.serve_forever()

    def stop(self):
        self._server.shutdown()


@pytest.fixture(scope="session")
def base_url():
    """Démarre le serveur, attend qu'il réponde, fournit l'URL de base, puis l'arrête."""
    server = _ServerThread()
    server.start()

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            requests.get(f"{server.base_url}/", timeout=0.5)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(0.1)
    else:
        server.stop()
        raise RuntimeError("Le serveur de test n'a pas démarré dans le délai imparti.")

    yield server.base_url
    server.stop()

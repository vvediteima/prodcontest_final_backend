from .api import app
from src.app.infrastructure import database

@app.route("/ping", methods=["GET"])
def ping():
    return "PROOOOOOD"
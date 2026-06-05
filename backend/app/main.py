import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dbos import DBOS, DBOSConfig

from .api import router
from .db import init_db

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

app = FastAPI(title="Shipment Visibility", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

config: DBOSConfig = {
    "name": "shipment-visibility",
    "system_database_url": os.environ["DBOS_SYSTEM_DATABASE_URL"],
}
if key := os.environ.get("DBOS_CONDUCTOR_KEY"):
    config["conductor_key"] = key  # type: ignore[typeddict-unknown-key]

DBOS(fastapi=app, config=config)

app.include_router(router)

# Serve built React SPA — only present in the production/Docker image
_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="spa")

DBOS.launch()
init_db()
